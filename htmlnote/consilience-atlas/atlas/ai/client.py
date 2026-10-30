"""AI client with a real DeepSeek path and a deterministic offline mock.

Provider abstraction: any OpenAI-compatible chat endpoint can be substituted.
If no key is present, callers should use MockAIClient so the GUI still works.
"""
from __future__ import annotations

import json
from typing import Optional

from .. import config
from . import prompts


class AIClient:
    """Base interface. chat() returns raw text."""
    name = "base"

    def chat(self, system: str, user: str) -> str:  # pragma: no cover - interface
        raise NotImplementedError


class DeepSeekClient(AIClient):
    name = "deepseek"

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or config.deepseek_api_key()
        self.model = model or config.deepseek_model()
        self.base_url = config.deepseek_base_url()
        if not self.api_key:
            raise RuntimeError("DEEPSEEK_API_KEY is not set")

    def chat(self, system: str, user: str) -> str:
        import httpx  # imported lazily so app opens without network deps loaded
        resp = httpx.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "temperature": 0.0,
                "response_format": {"type": "json_object"},
            },
            timeout=120.0,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


class MockAIClient(AIClient):
    """Deterministic, offline. Segments by sentence and applies simple heuristics.

    This is enough to exercise the full pipeline and tests without API cost.
    """
    name = "mock"
    model = "mock-deterministic"

    def chat(self, system: str, user: str) -> str:
        # The user payload always begins with a PASS marker line.
        first = user.splitlines()[0] if user else ""
        text = user.split("\n---TEXT---\n", 1)[-1]
        if first.startswith("PASS_A"):
            return json.dumps({"candidates": self._segment(text)})
        if first.startswith("PASS_B"):
            cands = json.loads(user.split("\n---CANDIDATES---\n", 1)[1].split("\n---TEXT---\n")[0])
            return json.dumps({"classified": [self._classify(c) for c in cands]})
        if first.startswith("PASS_C"):
            cands = json.loads(user.split("\n---CANDIDATES---\n", 1)[1].split("\n---TEXT---\n")[0])
            return json.dumps({"relations": self._relations(cands)})
        return "{}"

    # -- deterministic heuristics ----------------------------------------
    @staticmethod
    def _segment(text: str) -> list[dict]:
        import re
        cands = []
        for m in re.finditer(r"[^.!?\n]+[.!?]?", text):
            span = m.group().strip()
            if len(span) < 3:
                continue
            start = m.start() + (len(m.group()) - len(m.group().lstrip()))
            end = start + len(span)
            cands.append({
                "start": start, "end": end, "text": span,
                "label": span[:48], "section": "",
            })
        return cands

    @staticmethod
    def _classify(c: dict) -> dict:
        t = c["text"].lower()
        function = "Claim"
        if t.startswith(("we define", "let ", "define ")) or " is defined" in t:
            function = "Definition"
        elif any(k in t for k in ("therefore", "thus", "it follows", "hence")):
            function = "Derivation"
        elif any(k in t for k in ("observed", "measured", "data show", "experiment", "evidence")):
            function = "Evidence"
        elif any(k in t for k in ("we conclude", "in conclusion", "verdict")):
            function = "Verdict"
        ref = "E"
        if any(k in t for k in ("god", "christ", "transcend", "divine")):
            ref = "T"
        elif any(k in t for k in ("theorem", "proof", "axiom", "lemma")):
            ref = "F"
        elif any(k in t for k in ("observed", "measured", "empiric", "data")):
            ref = "N"
        disputed = any(k in t for k in ("however", "contested", "disputed", "some argue"))
        conf = 0.85 if function in ("Definition", "Evidence") else 0.6
        return {
            "start": c["start"], "end": c["end"],
            "confidence": conf,
            "confidence_basis": "explicit" if conf >= 0.8 else "inferred",
            "classification": {
                "function": function,
                "claim_family": "general",
                "object_type": "statement",
                "source": "endogenous",
                "commitment": "asserted",
                "standing": "contested" if disputed else "proposed",
                "dispute": "contested" if disputed else "uncontested",
                "scope": "local",
                "modality": "assertoric",
                "provenance": "in_paper",
                "reference_architecture": ref,
            },
        }

    @staticmethod
    def _relations(cands: list[dict]) -> list[dict]:
        rels = []
        # naive: each Derivation depends on the previous atom.
        for i in range(1, len(cands)):
            prev, cur = cands[i - 1], cands[i]
            t = cur["text"].lower()
            if any(k in t for k in ("therefore", "thus", "hence", "it follows")):
                rels.append({
                    "src_start": cur["start"], "src_end": cur["end"],
                    "dst_start": prev["start"], "dst_end": prev["end"],
                    "kind": "depends_on", "confidence": 0.55,
                })
        return rels


def get_client(prefer_mock: bool = False) -> AIClient:
    """Return the best available client. Falls back to mock automatically."""
    if prefer_mock or config.force_mock_ai() or not config.deepseek_api_key():
        return MockAIClient()
    try:
        return DeepSeekClient()
    except Exception:
        return MockAIClient()
