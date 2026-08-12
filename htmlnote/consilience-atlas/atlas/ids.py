"""Stable identity generation.

The same underlying epistemic identity must survive across resolutions
(Paper -> Series -> Global), so atom IDs are derived deterministically from
the paper id plus the canonical source span, not from row order.
"""
from __future__ import annotations

import hashlib
import re


def slugify(text: str, maxlen: int = 40) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower()).strip("-")
    return (s[:maxlen] or "item")


def paper_id_from_title(title: str) -> str:
    base = slugify(title, 30)
    h = hashlib.sha1(title.encode("utf-8")).hexdigest()[:6]
    return f"P-{base}-{h}"


def atom_id(paper_id: str, start: int, end: int, text: str) -> str:
    """Deterministic, span-anchored atom id.

    Boundaries can be frozen; reusing the same (paper, span, text) yields the
    same id so re-ingestion reuses canonical boundaries.
    """
    key = f"{paper_id}|{start}|{end}|{text}".encode("utf-8")
    return f"A-{hashlib.sha1(key).hexdigest()[:12]}"


def series_id_from_name(name: str) -> str:
    return f"S-{slugify(name, 30)}-{hashlib.sha1(name.encode()).hexdigest()[:6]}"


def bridge_id(a: str, b: str, kind: str) -> str:
    key = f"{a}->{b}:{kind}".encode()
    return f"B-{hashlib.sha1(key).hexdigest()[:12]}"
