"""Consilience Atlas Engine — local Streamlit GUI.

The GUI is only a thin layer over atlas/*. It must open even with no API key.
Run:  streamlit run app.py   (or double-click run.bat on Windows)
"""
from __future__ import annotations

import json

import streamlit as st

from atlas import config, database, ingest, render, export, aggregation, models
from atlas.ai.client import get_client, MockAIClient, DeepSeekClient
from atlas import bridges as bridge_mod

st.set_page_config(page_title="Consilience Atlas", layout="wide", page_icon="🧭")

# --- one-time init (never crashes the GUI) --------------------------------
config.ensure_dirs()
try:
    database.init_db()
except Exception as e:  # surface, do not swallow
    st.error(f"Database init failed: {e}")


def has_key() -> bool:
    return bool(config.deepseek_api_key()) and not config.force_mock_ai()


# --- sidebar --------------------------------------------------------------
st.sidebar.title("🧭 Consilience Atlas")
st.sidebar.caption(f"v{__import__('atlas').__version__} · local-first · 127.0.0.1")

PAGES = ["Dashboard", "Ingest Paper", "Review Queue", "Papers", "Series",
         "Compare Series", "Global", "Domains", "Rubrics", "Prompts",
         "Database", "Export", "Settings"]
page = st.sidebar.radio("Navigate", PAGES, label_visibility="collapsed")

ai_mode = "🟢 DeepSeek" if has_key() else "🟡 Mock AI (no key / offline)"
st.sidebar.info(f"AI: {ai_mode}")
if st.sidebar.button("💾 Back up Atlas"):
    dest = export.backup_atlas()
    st.sidebar.success(f"Backup → {dest}")


# ==========================================================================
def page_dashboard():
    st.header("Dashboard")
    with database.connect() as conn:
        papers = database.list_papers(conn)
        n_atoms = conn.execute("SELECT COUNT(*) c FROM atoms").fetchone()["c"]
        n_review = len(database.review_items(conn))
    c1, c2, c3 = st.columns(3)
    c1.metric("Papers", len(papers))
    c2.metric("Atoms", n_atoms)
    c3.metric("Open review items", n_review)
    st.markdown("""
**Core design rule — INTERNAL COHERENCE IS NOT EXTERNAL TRUTH.**
Scores are rubric scores, not truth probabilities. AI inference is always
labelled; uncertainty and anomalies stay visible; bridges must be earned.
    """)
    if not papers:
        st.info("No papers yet. Go to **Ingest Paper** to analyze your first one. "
                "You can try it right now with **Mock AI** — no API key needed.")


def page_ingest():
    st.header("Ingest Paper")
    if not has_key():
        st.warning("No DeepSeek key detected — running in **Mock AI** mode "
                   "(deterministic, offline, free). Add a key in Settings for real analysis.")
    up = st.file_uploader("Upload a paper", type=["md", "txt", "html"])
    demo = st.checkbox("Use built-in demo text instead", value=not up)
    title = st.text_input("Paper title", value="Demo Paper" if demo else (up.name if up else ""))
    series = st.text_input("Series assignment (optional)")
    position = st.number_input("Series position (optional)", min_value=0, value=0, step=1)
    notes = st.text_area("Notes", "")
    force_mock = st.checkbox("Force Mock AI for this run", value=not has_key())

    if st.button("🔬 ANALYZE PAPER", type="primary"):
        if demo:
            raw = DEMO_TEXT
            kind = "txt"
        elif up:
            raw = up.read().decode("utf-8", errors="replace")
            kind = up.name.rsplit(".", 1)[-1].lower()
            kind = "md" if kind in ("md", "markdown") else ("html" if kind in ("html", "htm") else "txt")
        else:
            st.error("Provide a file or use the demo text.")
            return
        if not title.strip():
            st.error("Please enter a paper title.")
            return

        series_id = None
        if series.strip():
            from atlas import ids as _ids
            series_id = _ids.series_id_from_name(series.strip())
            with database.connect() as conn:
                conn.execute("INSERT OR IGNORE INTO series(series_id,name,created_at) VALUES (?,?,?)",
                             (series_id, series.strip(), database.now()))

        progress = st.empty()
        bar = st.progress(0.0)
        stages_seen = []

        def cb(msg):
            stages_seen.append(msg)
            progress.write(f"• {msg}")
            bar.progress(min(1.0, len(stages_seen) / 7))

        client = MockAIClient() if force_mock else get_client()
        result = ingest.analyze_paper(
            title=title.strip(), raw_text=raw, kind=kind,
            series_id=series_id, series_position=int(position) or None,
            notes=notes, client=client, progress=cb,
        )
        bar.progress(1.0)
        if result.error:
            st.error(f"Ingestion failed: {result.error}")
        else:
            st.success(f"Done — {result.n_atoms} atoms, {result.n_relations} relations, "
                       f"{result.review_count} review items.")
            if result.grades:
                g = result.grades
                st.write(f"**Grades** (rubric {g['rubric']}): "
                         f"G_I={g['g_i']} · G_E={g['g_e']} · G_C={g['g_c']} → *{g['interpretation']}*")
            with database.connect() as conn:
                export.export_paper(conn, result.paper_id)
            st.info(f"Canonical JSON + HTML exported. Open **Papers** to review atoms.")


def page_papers():
    st.header("Papers")
    with database.connect() as conn:
        papers = database.list_papers(conn)
        if not papers:
            st.info("No papers yet.")
            return
        labels = {f"{p['title']}  ·  {p['paper_id']}": p["paper_id"] for p in papers}
        sel = st.selectbox("Select paper", list(labels))
        paper_id = labels[sel]
        atoms = database.atoms_for_paper(conn, paper_id)

        tabs = st.tabs(["Periodic Table", "Atom Review", "Atom Dossier",
                        "Dependency Map", "Emergent Map", "Ψ Topology", "Grades"])

        with tabs[0]:
            st.components.v1.html(render.render_local_table(conn, paper_id), height=560, scrolling=True)

        with tabs[1]:
            st.caption("Approve / freeze boundaries. Frozen atoms survive re-ingestion.")
            for a in atoms:
                cl = database.classification_for(conn, a["atom_id"]) or {}
                c = cl.get("classification", {})
                with st.expander(f"{'🔒' if a['frozen'] else '○'} {a['label']}  "
                                 f"[{c.get('function','?')} · {c.get('reference_architecture','?')}]"):
                    st.write(a["text"])
                    cols = st.columns(4)
                    if cols[0].button("Approve", key=f"ap{a['atom_id']}"):
                        conn.execute("UPDATE atoms SET approved=1 WHERE atom_id=?", (a["atom_id"],))
                        database.log_event(conn, "classification_verified", a["atom_id"])
                        st.rerun()
                    if cols[1].button("Freeze", key=f"fz{a['atom_id']}"):
                        conn.execute("UPDATE atoms SET frozen=1 WHERE atom_id=?", (a["atom_id"],))
                        database.log_event(conn, "boundary_frozen", a["atom_id"])
                        st.rerun()
                    if cols[2].button("Reject", key=f"rj{a['atom_id']}"):
                        conn.execute("DELETE FROM atoms WHERE atom_id=? AND frozen=0", (a["atom_id"],))
                        st.rerun()

        with tabs[2]:
            amap = {f"{a['label']} · {a['atom_id']}": a["atom_id"] for a in atoms}
            if amap:
                asel = st.selectbox("Atom", list(amap), key="dossier")
                st.components.v1.html(render.render_atom_interior(conn, amap[asel]),
                                      height=620, scrolling=True)

        with tabs[3]:
            g = render.paper_graph(conn, paper_id)
            st.plotly_chart(render.graph_figure(g, "kamada"), use_container_width=True)
            st.caption(f"{g.number_of_nodes()} nodes · {g.number_of_edges()} edges (dependency/derivation).")

        with tabs[4]:
            g = render.paper_graph(conn, paper_id)
            st.plotly_chart(render.graph_figure(g, "spring"), use_container_width=True)
            st.caption("Emergent / force-directed layout of the SAME underlying graph.")

        with tabs[5]:
            from atlas import topology
            rep = topology.psi_audit(render.paper_graph(conn, paper_id))
            st.warning("Ψ is diagnostic only — it NEVER changes epistemic standing.")
            st.json(rep)

        with tabs[6]:
            rows = list(conn.execute("SELECT * FROM grade_records WHERE paper_id=?", (paper_id,)))
            for r in rows:
                st.write(f"**{r['family']}** = {r['normalized_atlas_grade']} "
                         f"(rubric {r['rubric']}) — {json.loads(r['detail_json']).get('interpretation','')}")


def page_review():
    st.header("Review Queue")
    st.caption("Load-bearing / low-confidence / anomaly / external-anchor items. "
               "Unverified AI inference alone cannot set strongest standing (semantic firewall).")
    with database.connect() as conn:
        items = database.review_items(conn)
        if not items:
            st.success("Queue empty.")
            return
        for it in items:
            atom = conn.execute("SELECT label,text FROM atoms WHERE atom_id=?",
                                (it["atom_id"],)).fetchone()
            lbl = atom["label"] if atom else it["atom_id"]
            with st.expander(f"[{it['reason']}] {lbl}"):
                if atom:
                    st.write(atom["text"])
                st.caption(it["detail"])
                if st.button("Mark resolved (human verified)", key=f"rv{it['id']}"):
                    conn.execute("UPDATE review_queue SET resolved=1 WHERE id=?", (it["id"],))
                    database.log_event(conn, "classification_verified", it["atom_id"],
                                       {"reason": it["reason"]})
                    st.rerun()


def page_series():
    st.header("Series")
    with database.connect() as conn:
        rows = list(conn.execute("SELECT * FROM series ORDER BY created_at DESC"))
        if not rows:
            st.info("No series yet. Assign a series when ingesting a paper.")
            return
        for s in rows:
            st.subheader(s["name"])
            st.json(aggregation.series_summary(conn, s["series_id"]))


def page_export():
    st.header("Export")
    with database.connect() as conn:
        papers = database.list_papers(conn)
        if not papers:
            st.info("Nothing to export yet.")
            return
        labels = {f"{p['title']} · {p['paper_id']}": p["paper_id"] for p in papers}
        sel = st.selectbox("Paper", list(labels))
        if st.button("Export canonical JSON + HTML + graph"):
            out = export.export_paper(conn, labels[sel])
            for k, v in out.items():
                st.success(f"{k}: {v}")


def page_database():
    st.header("Database")
    with database.connect() as conn:
        st.write(f"DB path: `{config.DB_PATH}`")
        for t in ("papers", "atoms", "dependencies", "review_queue", "events",
                  "grade_records", "bridges"):
            c = conn.execute(f"SELECT COUNT(*) c FROM {t}").fetchone()["c"]
            st.write(f"- **{t}**: {c} rows")
    st.divider()
    st.subheader("Restore from backup")
    backs = export.list_backups()
    if backs:
        b = st.selectbox("Backup", [str(p) for p in backs])
        if st.checkbox("I understand this overwrites the current database"):
            if st.button("RESTORE DATABASE"):
                export.restore_atlas(b)
                st.success("Restored. Reload the page.")
    else:
        st.caption("No backups yet.")


def page_settings():
    st.header("Settings")
    st.write(f"**Data folder:** `{config.DATA}`")
    st.write(f"**API key present:** {'yes' if config.deepseek_api_key() else 'no'}")
    st.write(f"**Model:** {config.deepseek_model()}")
    st.write(f"**Force mock:** {config.force_mock_ai()}")
    st.info("To add your DeepSeek key: copy `.env.example` to `.env` in the project "
            "folder and set `DEEPSEEK_API_KEY=...`, then restart the app.")


def page_prompts():
    st.header("Prompts")
    from atlas.ai import prompts
    st.write(f"Active prompt version: **{prompts.PROMPT_VERSION}**")
    st.caption("Cold Ascent passes never receive the expected Descent answer.")
    for name in ("PASS_A_SYSTEM", "PASS_B_SYSTEM", "PASS_C_SYSTEM"):
        with st.expander(name):
            st.code(getattr(prompts, name))


def page_domains():
    st.header("Domains")
    st.caption("Extensible registry — not a fixed enum.")
    st.write(models.DEFAULT_DOMAINS)


def page_rubrics():
    st.header("Rubrics")
    from atlas import grading
    st.write(f"Grade rubric version: **{grading.GRADE_RUBRIC_VERSION}**")
    st.markdown("""
- **G_I** Internal Method Grade — coherence of the derivation graph.
- **G_E** External Evidence — cannot be driven up by internal agreement alone.
- **G_C** Consilience — only ADMITTED bridges contribute.

Formulas are versioned and revisable after adversarial testing.
    """)


def page_compare():
    st.header("Compare Series (Φ)")
    st.info("Human-assisted Φ comparison arrives in Milestone 2. Bridges are never "
            "auto-admitted; A→B and B→A are separate mappings.")
    st.write("Bridge lifecycle states:", bridge_mod.STATES)


def page_global():
    st.header("Global Atlas")
    st.info("Milestone 3. Highest Global standing may NOT be produced by internal "
            "agreement alone. Theology may emerge as strongest attractor but is "
            "never hard-coded to.")


DEMO_TEXT = (
    "We define coherence as internal consistency of a framework. "
    "The framework predicts that observed anomalies decrease over time. "
    "Experiments measured a 12% reduction in anomalies. "
    "Therefore the coherence hypothesis is supported by the data. "
    "However, some argue the reduction reflects measurement drift. "
    "God is the claimed grounded external reference in this interpretation. "
    "We conclude the framework is externally anchored, pending independent replication."
)

ROUTES = {
    "Dashboard": page_dashboard, "Ingest Paper": page_ingest,
    "Review Queue": page_review, "Papers": page_papers, "Series": page_series,
    "Compare Series": page_compare, "Global": page_global, "Domains": page_domains,
    "Rubrics": page_rubrics, "Prompts": page_prompts, "Database": page_database,
    "Export": page_export, "Settings": page_settings,
}
ROUTES[page]()
