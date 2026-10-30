"""Canonical JSON + HTML exports, plus backup/restore (spec AB, AC)."""
from __future__ import annotations

import json
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

import networkx as nx

from . import config, database, render


def export_paper(conn: sqlite3.Connection, paper_id: str) -> dict[str, Path]:
    config.ensure_dirs()
    paper = database.get_paper(conn, paper_id)
    atoms = database.atoms_for_paper(conn, paper_id)
    out = {}

    canonical = {
        "paper": dict(paper),
        "atoms": [],
        "relations": [dict(r) for r in database.relations_for_paper(conn, paper_id)],
        "grades": [dict(r) for r in conn.execute(
            "SELECT * FROM grade_records WHERE paper_id=?", (paper_id,))],
        "exported_at": datetime.utcnow().isoformat(),
        "schema_version": database.SCHEMA_VERSION,
    }
    for a in atoms:
        cl = database.classification_for(conn, a["atom_id"]) or {}
        canonical["atoms"].append({**dict(a), **cl})

    jpath = config.CANONICAL / f"{paper_id}.json"
    jpath.write_text(json.dumps(canonical, indent=2, default=str), encoding="utf-8")
    out["canonical_json"] = jpath

    # graph json
    g = render.paper_graph(conn, paper_id)
    gpath = config.EXPORTS / f"{paper_id}.graph.json"
    gpath.write_text(json.dumps(nx.node_link_data(g), indent=2, default=str), encoding="utf-8")
    out["graph_json"] = gpath

    # rendered html
    hpath = config.RENDERED / f"{paper_id}.html"
    hpath.write_text(render.render_local_table(conn, paper_id), encoding="utf-8")
    out["local_html"] = hpath

    return out


def backup_atlas() -> Path:
    config.ensure_dirs()
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    dest = config.BACKUPS / stamp
    dest.mkdir(parents=True, exist_ok=True)
    if config.DB_PATH.exists():
        shutil.copy2(config.DB_PATH, dest / "atlas.db")
    for folder in ("canonical",):
        src = config.DATA / folder
        if src.exists():
            shutil.copytree(src, dest / folder, dirs_exist_ok=True)
    for extra in (config.PROMPTS,):
        if extra.exists():
            shutil.copytree(extra, dest / extra.name, dirs_exist_ok=True)
    return dest


def restore_atlas(backup_dir: Path) -> None:
    backup_dir = Path(backup_dir)
    db = backup_dir / "atlas.db"
    if not db.exists():
        raise FileNotFoundError(f"No atlas.db in {backup_dir}")
    shutil.copy2(db, config.DB_PATH)


def list_backups() -> list[Path]:
    if not config.BACKUPS.exists():
        return []
    return sorted([p for p in config.BACKUPS.iterdir() if p.is_dir()], reverse=True)
