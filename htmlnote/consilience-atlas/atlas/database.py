"""SQLite persistence.

Atoms stay relatively stable; changing classifications/mappings/events are
attached in separate tables (spec AA). Foreign keys on. Event history is
append-only (spec O, Z).
"""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Optional

from . import config

SCHEMA_VERSION = 1

SCHEMA = """
CREATE TABLE IF NOT EXISTS schema_meta (key TEXT PRIMARY KEY, value TEXT);

CREATE TABLE IF NOT EXISTS series (
    series_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    notes TEXT DEFAULT '',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS papers (
    paper_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    series_id TEXT,
    series_position INTEGER,
    source_file TEXT,
    notes TEXT DEFAULT '',
    prompt_version TEXT,
    model TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (series_id) REFERENCES series(series_id)
);

CREATE TABLE IF NOT EXISTS atoms (
    atom_id TEXT PRIMARY KEY,
    paper_id TEXT NOT NULL,
    section TEXT DEFAULT '',
    start_pos INTEGER NOT NULL,
    end_pos INTEGER NOT NULL,
    text TEXT NOT NULL,
    label TEXT DEFAULT '',
    frozen INTEGER DEFAULT 0,
    approved INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    FOREIGN KEY (paper_id) REFERENCES papers(paper_id)
);

CREATE TABLE IF NOT EXISTS classifications (
    atom_id TEXT PRIMARY KEY,
    data_json TEXT NOT NULL,          -- Classification
    provenance_json TEXT NOT NULL,    -- {field: Provenance}
    method_version TEXT,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (atom_id) REFERENCES atoms(atom_id)
);

CREATE TABLE IF NOT EXISTS dependencies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    src TEXT NOT NULL,
    dst TEXT NOT NULL,
    kind TEXT NOT NULL,               -- depends_on|supports|contradicts|derives
    provenance_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS grade_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    atom_id TEXT,
    paper_id TEXT,
    family TEXT NOT NULL,             -- G_I | G_E | G_C
    native_grade TEXT,
    normalized_atlas_grade INTEGER,
    rubric TEXT,
    detail_json TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS bridges (
    bridge_id TEXT PRIMARY KEY,
    src TEXT, dst TEXT, kind TEXT,
    state TEXT NOT NULL,              -- Candidate|Provisional|Admitted|Suspended|Rejected|Revoked
    data_json TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS bridge_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bridge_id TEXT NOT NULL,
    from_state TEXT, to_state TEXT, reason TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    atom_id TEXT,
    category TEXT NOT NULL,           -- RIGHT|OVERSTATED|WRONG|OPEN
    note TEXT,
    author TEXT DEFAULT 'system',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kind TEXT NOT NULL,
    subject_id TEXT,
    payload_json TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS review_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    atom_id TEXT,
    reason TEXT NOT NULL,             -- low_confidence|load_bearing|bridge_candidate|...
    detail TEXT,
    resolved INTEGER DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS prompt_versions (
    version TEXT PRIMARY KEY,
    pass_name TEXT,
    body TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS rubrics (
    version TEXT PRIMARY KEY,
    family TEXT,
    detail_json TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_atoms_paper ON atoms(paper_id);
CREATE INDEX IF NOT EXISTS idx_dep_src ON dependencies(src);
CREATE INDEX IF NOT EXISTS idx_dep_dst ON dependencies(dst);
CREATE INDEX IF NOT EXISTS idx_events_subject ON events(subject_id);
"""


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def connect(db_path: Optional[Path] = None) -> Iterator[sqlite3.Connection]:
    path = Path(db_path) if db_path else config.DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db(db_path: Optional[Path] = None) -> None:
    with connect(db_path) as conn:
        conn.executescript(SCHEMA)
        conn.execute(
            "INSERT OR REPLACE INTO schema_meta(key, value) VALUES ('schema_version', ?)",
            (str(SCHEMA_VERSION),),
        )


def log_event(conn: sqlite3.Connection, kind: str, subject_id: str, payload: dict | None = None) -> None:
    conn.execute(
        "INSERT INTO events(kind, subject_id, payload_json, created_at) VALUES (?,?,?,?)",
        (kind, subject_id, json.dumps(payload or {}), now()),
    )


# ---- Convenience readers used by the GUI --------------------------------

def list_papers(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return list(conn.execute("SELECT * FROM papers ORDER BY created_at DESC"))


def get_paper(conn: sqlite3.Connection, paper_id: str) -> Optional[sqlite3.Row]:
    return conn.execute("SELECT * FROM papers WHERE paper_id=?", (paper_id,)).fetchone()


def atoms_for_paper(conn: sqlite3.Connection, paper_id: str) -> list[sqlite3.Row]:
    return list(conn.execute(
        "SELECT * FROM atoms WHERE paper_id=? ORDER BY start_pos", (paper_id,)
    ))


def classification_for(conn: sqlite3.Connection, atom_id: str) -> Optional[dict]:
    row = conn.execute("SELECT * FROM classifications WHERE atom_id=?", (atom_id,)).fetchone()
    if not row:
        return None
    return {
        "classification": json.loads(row["data_json"]),
        "provenance": json.loads(row["provenance_json"]),
    }


def relations_for_paper(conn: sqlite3.Connection, paper_id: str) -> list[sqlite3.Row]:
    return list(conn.execute(
        """SELECT d.* FROM dependencies d
           JOIN atoms a ON a.atom_id = d.src
           WHERE a.paper_id = ?""",
        (paper_id,),
    ))


def review_items(conn: sqlite3.Connection, include_resolved: bool = False) -> list[sqlite3.Row]:
    q = "SELECT * FROM review_queue"
    if not include_resolved:
        q += " WHERE resolved=0"
    q += " ORDER BY created_at DESC"
    return list(conn.execute(q))
