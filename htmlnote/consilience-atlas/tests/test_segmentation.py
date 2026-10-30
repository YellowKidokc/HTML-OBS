from atlas.ai.client import MockAIClient
from atlas import segment, classify, relations


TEXT = ("We define coherence as internal consistency. "
        "Experiments measured a 12% reduction. "
        "Therefore the hypothesis is supported.")


def test_normalize_html_strips_tags():
    out = segment.normalize_source("<p>Hello <b>world</b></p>", "html")
    assert "Hello" in out and "<p>" not in out


def test_segment_offsets_recover_exact_text():
    c = MockAIClient()
    cands = segment.segment(c, TEXT)
    assert cands, "expected candidates"
    for cand in cands:
        assert TEXT[cand.start:cand.end] == cand.text


def test_classify_produces_confidence():
    c = MockAIClient()
    cands = segment.segment(c, TEXT)
    cls = classify.classify(c, TEXT, cands)
    assert cls
    assert all(0.0 <= x.confidence <= 1.0 for x in cls)
    # "We define..." should be a Definition
    funcs = {x.classification.function for x in cls}
    assert "Definition" in funcs


def test_relations_derivation_depends_on_prior():
    c = MockAIClient()
    cands = segment.segment(c, TEXT)
    rels = relations.relations(c, TEXT, cands)
    assert any(r["kind"] == "depends_on" for r in rels)
