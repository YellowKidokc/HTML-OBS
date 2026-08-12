import pytest
from atlas.schemas import Provenance, Origin, Classification, Markers


def test_ai_inference_requires_confidence():
    with pytest.raises(Exception):
        Provenance(value="x", origin=Origin.ai_inference_unverified)  # no confidence


def test_ai_inference_with_confidence_ok():
    p = Provenance(value="x", origin=Origin.ai_inference_unverified, confidence=0.7)
    assert p.is_ai and not p.verified


def test_human_origin_needs_no_confidence():
    p = Provenance(value="x", origin=Origin.human)
    assert p.verified


def test_markers_computed_fields_default_none_or_zero():
    m = Markers(m01_atom_id="A-1")
    assert m.m12_evidence_grade is None
    assert m.m13_usage_runs == 0 and m.m14_graph_degree == 0


def test_reference_architecture_is_parallel_not_ladder():
    c = Classification(reference_architecture="T")
    assert c.reference_architecture == "T"  # no implied ordering
