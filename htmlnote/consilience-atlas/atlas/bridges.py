"""Bridge lifecycle (spec P). Bridges are EARNED, never auto-admitted."""
from __future__ import annotations

STATES = ["Candidate", "Provisional", "Admitted", "Suspended", "Rejected", "Revoked"]

# allowed transitions
TRANSITIONS = {
    "Candidate": {"Provisional", "Rejected"},
    "Provisional": {"Admitted", "Rejected"},
    "Admitted": {"Suspended"},
    "Suspended": {"Admitted", "Revoked"},
    "Rejected": set(),   # archived
    "Revoked": set(),    # archived
}


def can_transition(frm: str, to: str) -> bool:
    return to in TRANSITIONS.get(frm, set())
