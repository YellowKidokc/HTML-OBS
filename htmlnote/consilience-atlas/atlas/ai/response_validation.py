"""Validate raw AI JSON into typed schema objects. Structure only (spec M)."""
from __future__ import annotations

import json
from typing import Any


class AIResponseError(ValueError):
    pass


def parse_json_block(raw: str) -> dict[str, Any]:
    """Tolerant JSON extraction from a model response."""
    raw = raw.strip()
    if raw.startswith("```"):
        # strip ```json fences
        raw = raw.split("```", 2)
        raw = raw[1] if len(raw) > 1 else raw[0]
        if raw.lstrip().startswith("json"):
            raw = raw.lstrip()[4:]
    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1:
        raise AIResponseError("No JSON object found in AI response")
    try:
        return json.loads(raw[start:end + 1])
    except json.JSONDecodeError as e:
        raise AIResponseError(f"Invalid JSON from AI: {e}") from e
