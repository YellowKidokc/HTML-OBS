"""Graph construction, computed markers, and the Ψ topology audit (spec T).

Ψ never changes epistemic standing. It produces diagnostic evidence only.
Computed markers (13 usage/runs, 14 graph_degree) are calculated here, never
supplied by the AI.
"""
from __future__ import annotations

import networkx as nx


def build_graph(atoms: list[dict], relations: list[dict]) -> nx.DiGraph:
    g = nx.DiGraph()
    for a in atoms:
        g.add_node(a["atom_id"], **a)
    for r in relations:
        if r["src"] in g and r["dst"] in g:
            g.add_edge(r["src"], r["dst"], kind=r.get("kind", "depends_on"))
    return g


def computed_degrees(g: nx.DiGraph) -> dict[str, int]:
    """Marker 14 — graph degree, computed."""
    return {n: g.degree(n) for n in g.nodes}


def psi_audit(g: nx.DiGraph) -> dict:
    """Emergent topology diagnostics. Read-only w.r.t. standing."""
    undirected = g.to_undirected()
    report: dict = {
        "n_nodes": g.number_of_nodes(),
        "n_edges": g.number_of_edges(),
        "isolates": list(nx.isolates(g)),
        "articulation_points": [],
        "hubs": [],
        "communities": [],
        "components": nx.number_connected_components(undirected) if g.number_of_nodes() else 0,
    }
    if g.number_of_nodes() == 0:
        return report
    # hubs by degree centrality
    dc = nx.degree_centrality(g)
    report["hubs"] = sorted(dc, key=dc.get, reverse=True)[:5]
    try:
        report["articulation_points"] = list(nx.articulation_points(undirected))
    except Exception:
        pass
    try:
        comms = nx.community.greedy_modularity_communities(undirected)
        report["communities"] = [sorted(c) for c in comms]
    except Exception:
        report["communities"] = []
    return report


def load_bearing(g: nx.DiGraph) -> dict[str, dict]:
    """Compute load-bearing flag + blast radius (spec N, simplified v1).

    An atom is load-bearing if it is an articulation point OR removing it
    disconnects downstream nodes that currently reach it.
    """
    result: dict[str, dict] = {}
    undirected = g.to_undirected()
    arts = set(nx.articulation_points(undirected)) if g.number_of_nodes() > 2 else set()
    for n in g.nodes:
        # blast radius = ancestors (things that depend on n through the graph)
        try:
            affected = nx.ancestors(g, n)
        except Exception:
            affected = set()
        reasons = []
        if n in arts:
            reasons.append("articulation_point")
        if len(affected) >= 2:
            reasons.append("supports_multiple_downstream")
        result[n] = {
            "load_bearing": bool(reasons),
            "load_bearing_reasons": reasons,
            "blast_radius": {"affected_atoms": sorted(affected)},
        }
    return result
