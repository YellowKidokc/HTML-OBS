"""HTML rendering via Jinja2 + Plotly graph figures for the GUI."""
from __future__ import annotations

import json
import sqlite3

import networkx as nx

from . import config, database, topology
from jinja2 import Environment, FileSystemLoader, select_autoescape

_env = Environment(
    loader=FileSystemLoader(str(config.TEMPLATES)),
    autoescape=select_autoescape(["html"]),
)


def _atoms_dicts(conn, paper_id):
    atoms = []
    for a in database.atoms_for_paper(conn, paper_id):
        cl = database.classification_for(conn, a["atom_id"]) or {}
        classification = cl.get("classification", {})
        atoms.append({
            "atom_id": a["atom_id"], "label": a["label"], "text": a["text"],
            "start": a["start_pos"], "end": a["end_pos"], "section": a["section"],
            "frozen": a["frozen"], "approved": a["approved"],
            **classification,
        })
    return atoms


def paper_graph(conn: sqlite3.Connection, paper_id: str) -> nx.DiGraph:
    atoms = _atoms_dicts(conn, paper_id)
    rels = [{"src": r["src"], "dst": r["dst"], "kind": r["kind"]}
            for r in database.relations_for_paper(conn, paper_id)]
    return topology.build_graph(atoms, rels)


def graph_figure(g: nx.DiGraph, layout: str = "spring"):
    """Return a Plotly figure dict for a directed graph (emergent/dependency)."""
    import plotly.graph_objects as go
    if g.number_of_nodes() == 0:
        return go.Figure()
    pos = (nx.spring_layout(g, seed=42) if layout == "spring"
           else nx.kamada_kawai_layout(g) if g.number_of_nodes() > 1
           else {list(g.nodes)[0]: (0, 0)})
    ex, ey = [], []
    for u, v in g.edges:
        ex += [pos[u][0], pos[v][0], None]
        ey += [pos[u][1], pos[v][1], None]
    edge = go.Scatter(x=ex, y=ey, mode="lines",
                      line=dict(width=1, color="#888"), hoverinfo="none")
    nx_, ny_, txt, color = [], [], [], []
    palette = {"Definition": "#4c72b0", "Claim": "#dd8452", "Derivation": "#55a868",
               "Evidence": "#c44e52", "Verdict": "#8172b3"}
    for n in g.nodes:
        nx_.append(pos[n][0]); ny_.append(pos[n][1])
        d = g.nodes[n]
        txt.append(f"{d.get('label', n)}<br>{d.get('function', '')}")
        color.append(palette.get(d.get("function", ""), "#999"))
    node = go.Scatter(x=nx_, y=ny_, mode="markers", text=txt, hoverinfo="text",
                      marker=dict(size=14, color=color, line=dict(width=1, color="#fff")))
    fig = go.Figure(data=[edge, node])
    fig.update_layout(showlegend=False, margin=dict(l=0, r=0, t=0, b=0),
                      xaxis=dict(visible=False), yaxis=dict(visible=False), height=520)
    return fig


def render_local_table(conn: sqlite3.Connection, paper_id: str) -> str:
    paper = database.get_paper(conn, paper_id)
    atoms = _atoms_dicts(conn, paper_id)
    tmpl = _env.get_template("local_table.html")
    return tmpl.render(paper=dict(paper), atoms=atoms)


def render_atom_interior(conn: sqlite3.Connection, atom_id: str) -> str:
    a = conn.execute("SELECT * FROM atoms WHERE atom_id=?", (atom_id,)).fetchone()
    cl = database.classification_for(conn, atom_id) or {}
    audits = list(conn.execute("SELECT * FROM audits WHERE atom_id=? ORDER BY created_at", (atom_id,)))
    events = list(conn.execute("SELECT * FROM events WHERE subject_id=? ORDER BY created_at", (atom_id,)))
    tmpl = _env.get_template("atom_interior.html")
    return tmpl.render(atom=dict(a), classification=cl.get("classification", {}),
                       provenance=cl.get("provenance", {}),
                       audits=[dict(x) for x in audits], events=[dict(x) for x in events])
