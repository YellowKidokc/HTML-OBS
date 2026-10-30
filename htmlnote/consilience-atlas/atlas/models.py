"""Domain-level helpers and registries.

The domain registry is extensible (spec K) — NOT a fixed ten-domain enum.
"""
from __future__ import annotations

# Seed domains; users/AI may extend at runtime via the DOMAINS page.
DEFAULT_DOMAINS = [
    "unassigned", "physics", "mathematics", "theology", "philosophy",
    "history", "psychology", "economics", "biology", "computer_science",
]

AUDIT_CATEGORIES = ["RIGHT", "OVERSTATED", "WRONG", "OPEN"]

REVIEW_REASONS = [
    "low_confidence", "load_bearing", "bridge_candidate", "standing_promotion",
    "contradiction", "anomaly", "external_anchor_candidate", "failed_validation",
]
