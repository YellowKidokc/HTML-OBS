"""Source normalization + Pass A candidate atom extraction."""
from __future__ import annotations

import re
from html.parser import HTMLParser

from .ai.client import AIClient
from .ai import prompts
from .ai.response_validation import parse_json_block
from .schemas import AtomCandidate


class _HTMLText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts: list[str] = []
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self._skip += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self._skip:
            self._skip -= 1

    def handle_data(self, data):
        if not self._skip:
            self.parts.append(data)


def normalize_source(raw: str, kind: str) -> str:
    """Return plain text with stable offsets. kind = md|txt|html."""
    if kind == "html":
        p = _HTMLText()
        p.feed(raw)
        text = "".join(p.parts)
    else:
        text = raw
    # normalize newlines; keep character positions meaningful
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+\n", "\n", text)
    return text.strip()


def segment(client: AIClient, text: str) -> list[AtomCandidate]:
    user = f"PASS_A\n---TEXT---\n{text}"
    raw = client.chat(prompts.PASS_A_SYSTEM, user)
    data = parse_json_block(raw)
    out: list[AtomCandidate] = []
    for c in data.get("candidates", []):
        try:
            cand = AtomCandidate(**c)
        except Exception:
            continue
        # sanity: clamp offsets into text; recover exact text from offsets
        s = max(0, min(cand.start, len(text)))
        e = max(s, min(cand.end, len(text)))
        exact = text[s:e]
        if len(exact.strip()) < 3:
            continue
        out.append(AtomCandidate(start=s, end=e, text=exact, label=cand.label or exact[:48], section=cand.section))
    return out
