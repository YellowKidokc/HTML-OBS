"""Pass B — multi-axis classification with confidence."""
from __future__ import annotations

import json

from .ai.client import AIClient
from .ai import prompts
from .ai.response_validation import parse_json_block
from .schemas import AtomCandidate, Classification, ClassifiedAtom


def classify(client: AIClient, text: str, candidates: list[AtomCandidate]) -> list[ClassifiedAtom]:
    cand_payload = json.dumps([{"start": c.start, "end": c.end, "text": c.text} for c in candidates])
    user = f"PASS_B\n---CANDIDATES---\n{cand_payload}\n---TEXT---\n{text}"
    raw = client.chat(prompts.PASS_B_SYSTEM, user)
    data = parse_json_block(raw)
    out: list[ClassifiedAtom] = []
    for item in data.get("classified", []):
        try:
            cls = Classification(**item.get("classification", {}))
            out.append(ClassifiedAtom(
                start=item["start"], end=item["end"],
                classification=cls,
                confidence=float(item.get("confidence", 0.5)),
                confidence_basis=item.get("confidence_basis", "inferred"),
            ))
        except Exception:
            continue
    return out
