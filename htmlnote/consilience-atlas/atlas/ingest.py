"""One user action = 'Analyze Paper'. Internally Passes A->C (+ persistence).

Milestone-1 pipeline stages surfaced to the GUI:
  1 source normalized  2 atom candidates  3 classification  4 relations
  5 schema validation  6 semantic checks  7 saved  8 rendered

A failed ingestion must NOT corrupt previously admitted data: we build the
whole atom set in memory and only write inside one transaction at the end.
"""
from __future__ import annotations

import json
import sqlite3
import traceback
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

from . import config, database, ids, segment, classify, relations, grading, topology
from .ai.client import AIClient, get_client
from .ai import prompts
from .schemas import Origin, Provenance

LoadBearingThreshold = 0.60  # confidence below this -> review queue


@dataclass
class IngestResult:
    paper_id: str
    title: str
    n_atoms: int = 0
    n_relations: int = 0
    stages: list[str] = field(default_factory=list)
    review_count: int = 0
    grades: Optional[dict] = None
    error: Optional[str] = None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _log_error(exc: Exception) -> Path:
    config.ensure_dirs()
    p = config.LOGS / f"ingest-error-{datetime.now().strftime('%Y%m%d-%H%M%S')}.log"
    p.write_text(traceback.format_exc(), encoding="utf-8")
    return p


def analyze_paper(
    *,
    title: str,
    raw_text: str,
    kind: str,                      # md|txt|html
    series_id: Optional[str] = None,
    series_position: Optional[int] = None,
    notes: str = "",
    client: Optional[AIClient] = None,
    progress: Optional[Callable[[str], None]] = None,
    db_path: Optional[Path] = None,
) -> IngestResult:
    """Run the full ingestion. Never raises to caller: errors captured in result."""
    config.ensure_dirs()
    client = client or get_client()
    paper_id = ids.paper_id_from_title(title)
    result = IngestResult(paper_id=paper_id, title=title)

    def step(msg: str):
        result.stages.append(msg)
        if progress:
            progress(msg)

    try:
        # 1. normalize + save source
        text = segment.normalize_source(raw_text, kind)
        src_file = config.SOURCES / f"{paper_id}.txt"
        src_file.write_text(text, encoding="utf-8")
        step("1 source normalized")

        # 2. candidates
        candidates = segment.segment(client, text)
        step(f"2 atom candidates ({len(candidates)})")

        # 3. classification
        classified = classify.classify(client, text, candidates)
        cls_by_span = {(c.start, c.end): c for c in classified}
        step(f"3 classification ({len(classified)})")

        # 4. relations
        rels = relations.relations(client, text, candidates)
        step(f"4 relations ({len(rels)})")

        # 5. build atoms (schema validation happens via Pydantic construction)
        atom_rows = []
        span_to_id: dict[tuple[int, int], str] = {}
        for c in candidates:
            aid = ids.atom_id(paper_id, c.start, c.end, c.text)
            span_to_id[(c.start, c.end)] = aid
            cl = cls_by_span.get((c.start, c.end))
            classification = cl.classification.model_dump() if cl else {}
            conf = cl.confidence if cl else 0.4
            basis = cl.confidence_basis if cl else "ambiguous"
            prov = Provenance(
                value="classification",
                origin=Origin.ai_inference_unverified,
                confidence=conf,
                confidence_basis=basis,
                method_version=config.METHOD_VERSION,
                timestamp=_now(),
            )
            atom_rows.append({
                "atom_id": aid, "paper_id": paper_id, "section": c.section,
                "start": c.start, "end": c.end, "text": c.text, "label": c.label,
                "classification": classification, "confidence": conf,
                "confidence_basis": basis, "provenance": prov.model_dump(),
            })
        step("5 schema validation")

        # map relations to atom ids
        rel_rows = []
        for r in rels:
            src = span_to_id.get((r["src_start"], r["src_end"]))
            dst = span_to_id.get((r["dst_start"], r["dst_end"]))
            if src and dst and src != dst:
                rel_rows.append({
                    "src": src, "dst": dst, "kind": r["kind"],
                    "confidence": r.get("confidence", 0.5),
                })

        # 6. semantic checks -> review queue (spec M/N)
        # graph for load-bearing computation
        graph_atoms = [{"atom_id": a["atom_id"], **a["classification"]} for a in atom_rows]
        g = topology.build_graph(graph_atoms, rel_rows)
        lb = topology.load_bearing(g)
        degrees = topology.computed_degrees(g)

        review = []
        for a in atom_rows:
            aid = a["atom_id"]
            is_lb = lb.get(aid, {}).get("load_bearing", False)
            a["load_bearing"] = is_lb
            a["degree"] = degrees.get(aid, 0)
            if a["confidence"] < LoadBearingThreshold:
                review.append((aid, "low_confidence",
                               f"conf={a['confidence']:.2f} basis={a['confidence_basis']}"))
            if is_lb:
                review.append((aid, "load_bearing",
                               "; ".join(lb[aid]["load_bearing_reasons"])))
            if a["classification"].get("dispute") == "contested":
                review.append((aid, "contradiction", "flagged contested at classification"))
            if a["classification"].get("reference_architecture") == "T":
                review.append((aid, "external_anchor_candidate",
                               "claimed transcendent reference — needs external support"))
        step(f"6 semantic checks ({len(review)} queued)")

        # grades (computed, versioned)
        gs = grading.grade_paper(graph_atoms, rel_rows, bridges=[])
        result.grades = {"g_i": gs.g_i, "g_e": gs.g_e, "g_c": gs.g_c,
                         "rubric": gs.rubric, "interpretation": gs.interpretation()}

        # 7. persist — single transaction
        _persist(db_path, paper_id, title, series_id, series_position, notes,
                 str(src_file), client, atom_rows, rel_rows, review, gs)
        step("7 saved")

        result.n_atoms = len(atom_rows)
        result.n_relations = len(rel_rows)
        result.review_count = len(review)
        return result

    except Exception as exc:  # fail visibly, never corrupt prior data
        log = _log_error(exc)
        result.error = f"{type(exc).__name__}: {exc}  (details: {log})"
        step(f"ERROR — {result.error}")
        return result


def _persist(db_path, paper_id, title, series_id, series_position, notes, src_file,
             client, atom_rows, rel_rows, review, gs):
    with database.connect(db_path) as conn:
        conn.execute(
            """INSERT OR REPLACE INTO papers
               (paper_id,title,series_id,series_position,source_file,notes,
                prompt_version,model,created_at)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (paper_id, title, series_id, series_position, src_file, notes,
             prompts.PROMPT_VERSION, getattr(client, "model", client.name), _now()),
        )
        # clear prior atoms for this paper (re-ingestion), preserving frozen ones
        frozen = {r["atom_id"] for r in conn.execute(
            "SELECT atom_id FROM atoms WHERE paper_id=? AND frozen=1", (paper_id,))}
        conn.execute("DELETE FROM atoms WHERE paper_id=? AND frozen=0", (paper_id,))
        conn.execute(
            "DELETE FROM dependencies WHERE src IN (SELECT atom_id FROM atoms WHERE paper_id=?)",
            (paper_id,))

        for a in atom_rows:
            if a["atom_id"] in frozen:
                continue  # keep frozen boundary
            conn.execute(
                """INSERT OR REPLACE INTO atoms
                   (atom_id,paper_id,section,start_pos,end_pos,text,label,frozen,approved,created_at)
                   VALUES (?,?,?,?,?,?,?,0,0,?)""",
                (a["atom_id"], paper_id, a["section"], a["start"], a["end"],
                 a["text"], a["label"], _now()),
            )
            conn.execute(
                """INSERT OR REPLACE INTO classifications
                   (atom_id,data_json,provenance_json,method_version,updated_at)
                   VALUES (?,?,?,?,?)""",
                (a["atom_id"], json.dumps(a["classification"]),
                 json.dumps({"classification": a["provenance"]}),
                 config.METHOD_VERSION, _now()),
            )
            database.log_event(conn, "atom_created", a["atom_id"],
                               {"confidence": a["confidence"]})

        for r in rel_rows:
            prov = Provenance(value=r["kind"], origin=Origin.ai_inference_unverified,
                              confidence=r["confidence"], confidence_basis="inferred",
                              method_version=config.METHOD_VERSION, timestamp=_now())
            conn.execute(
                """INSERT INTO dependencies(src,dst,kind,provenance_json,created_at)
                   VALUES (?,?,?,?,?)""",
                (r["src"], r["dst"], r["kind"], prov.model_dump_json(), _now()),
            )

        # review queue
        conn.execute("DELETE FROM review_queue WHERE atom_id IN "
                     "(SELECT atom_id FROM atoms WHERE paper_id=?)", (paper_id,))
        for aid, reason, detail in review:
            conn.execute(
                "INSERT INTO review_queue(atom_id,reason,detail,resolved,created_at) VALUES (?,?,?,0,?)",
                (aid, reason, detail, _now()),
            )

        for fam, val in (("G_I", gs.g_i), ("G_E", gs.g_e), ("G_C", gs.g_c)):
            conn.execute(
                """INSERT INTO grade_records
                   (paper_id,family,normalized_atlas_grade,rubric,detail_json,created_at)
                   VALUES (?,?,?,?,?,?)""",
                (paper_id, fam, val, gs.rubric,
                 json.dumps({"interpretation": gs.interpretation()}), _now()),
            )
        database.log_event(conn, "paper_ingested", paper_id,
                           {"atoms": len(atom_rows), "relations": len(rel_rows)})
