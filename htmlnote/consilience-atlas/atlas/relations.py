"""Pass C — relations between atoms (by span, mapped back to atom ids)."""
from __future__ import annotations

import json

from .ai.client import AIClient
from .ai import prompts
from .ai.response_validation import parse_json_block
from .schemas import AtomCandidate


def relations(client: AIClient, text: str, candidates: list[AtomCandidate]) -> list[dict]:
    cand_payload = json.dumps([{"start": c.start, "end": c.end, "text": c.text} for c in candidates])
    user = f"PASS_C\n---CANDIDATES---\n{cand_payload}\n---TEXT---\n{text}"
    raw = client.chat(prompts.PASS_C_SYSTEM, user)
    data = parse_json_block(raw)
    out = []
    for r in data.get("relations", []):
        try:
            out.append({
                "src_start": int(r["src_start"]), "src_end": int(r["src_end"]),
                "dst_start": int(r["dst_start"]), "dst_end": int(r["dst_end"]),
                "kind": r.get("kind", "depends_on"),
                "confidence": float(r.get("confidence", 0.5)),
            })
        except Exception:
            continue
    return out
