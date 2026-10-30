import tempfile
from pathlib import Path

from atlas import database, ingest
from atlas.ai.client import MockAIClient

TEXT = ("We define coherence as internal consistency. "
        "Experiments measured a reduction. "
        "Therefore the hypothesis is supported. "
        "God is the claimed grounded external reference here.")


def _tmp_db():
    d = Path(tempfile.mkdtemp())
    return d / "atlas.db"


def test_init_and_ingest_roundtrip(monkeypatch):
    db = _tmp_db()
    database.init_db(db)
    res = ingest.analyze_paper(title="Test Paper", raw_text=TEXT, kind="txt",
                               client=MockAIClient(), db_path=db)
    assert res.error is None, res.error
    assert res.n_atoms > 0
    with database.connect(db) as conn:
        papers = database.list_papers(conn)
        assert len(papers) == 1
        atoms = database.atoms_for_paper(conn, res.paper_id)
        assert len(atoms) == res.n_atoms
        # external-anchor (T) claim should be queued for review
        reasons = {r["reason"] for r in database.review_items(conn)}
        assert "external_anchor_candidate" in reasons


def test_frozen_boundary_survives_reingest():
    db = _tmp_db()
    database.init_db(db)
    r1 = ingest.analyze_paper(title="Freeze Test", raw_text=TEXT, kind="txt",
                              client=MockAIClient(), db_path=db)
    with database.connect(db) as conn:
        first = database.atoms_for_paper(conn, r1.paper_id)[0]["atom_id"]
        conn.execute("UPDATE atoms SET frozen=1 WHERE atom_id=?", (first,))
    ingest.analyze_paper(title="Freeze Test", raw_text=TEXT, kind="txt",
                         client=MockAIClient(), db_path=db)
    with database.connect(db) as conn:
        still = conn.execute("SELECT frozen FROM atoms WHERE atom_id=?", (first,)).fetchone()
        assert still is not None and still["frozen"] == 1
