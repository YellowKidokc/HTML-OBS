"""Series aggregation (spec V/Series). Milestone-1 stub with real basics.

Full dedup / Φ comparison is future work; this computes honest counts now.
"""
from __future__ import annotations

import sqlite3


def series_summary(conn: sqlite3.Connection, series_id: str) -> dict:
    papers = list(conn.execute("SELECT * FROM papers WHERE series_id=?", (series_id,)))
    paper_ids = [p["paper_id"] for p in papers]
    atom_count = 0
    if paper_ids:
        q = "SELECT COUNT(*) c FROM atoms WHERE paper_id IN (%s)" % ",".join("?" * len(paper_ids))
        atom_count = conn.execute(q, paper_ids).fetchone()["c"]
    return {
        "papers": len(papers),
        "paper_titles": [p["title"] for p in papers],
        "unique_atoms": atom_count,
        "dedup_candidates": "not_computed_v1",
        "contradictions": "not_computed_v1",
        "bottleneck": "not_computed_v1",
    }
