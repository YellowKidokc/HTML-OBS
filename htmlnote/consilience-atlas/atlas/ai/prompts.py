"""Versioned prompt bodies (spec X).

CRITICAL FIREWALL: the cold Ascent extraction/classification prompts must NOT
be told the expected theological/Descent answer. Passes A-C stay neutral.
"""
from __future__ import annotations

PROMPT_VERSION = "ingest-v1"

# PASS A — source-preserving atom candidate extraction.
PASS_A_SYSTEM = """You segment a source document into candidate epistemic atoms.
An atom is an ADDRESSABLE SPAN of the source, not necessarily one sentence.
Split a span whenever it would need two conflicting values on any classification
axis (function, source, commitment, standing, dispute, claim family, modality, scope).
Preserve exact character offsets into the ORIGINAL text you are given.
Do NOT interpret, judge, or assume any conclusion. Only segment.
Return strict JSON: {"candidates":[{"start":int,"end":int,"text":str,"label":str,"section":str}]}"""

# PASS B — multi-axis classification grammar (neutral).
PASS_B_SYSTEM = """You classify each atom span on multiple INDEPENDENT axes.
Axes: function (Definition|Claim|Derivation|Evidence|Verdict), claim_family,
object_type, source, commitment, standing, dispute, scope, modality,
provenance, reference_architecture (E=Endogenous, N=Naturally constrained,
F=Formally constrained, T=Claimed transcendent). These are PARALLEL, not a ladder.
Never assume T is superior. Do not assume any external reference is reached.
Give a numeric confidence 0.00-1.00 and a confidence_basis
(explicit|strong_context|inferred|ambiguous) per atom. Confidence is uncertainty,
NOT truth probability.
Return strict JSON: {"classified":[{"start":int,"end":int,"confidence":float,
"confidence_basis":str,"classification":{...axes...}}]}"""

# PASS C — relations.
PASS_C_SYSTEM = """You identify relations between atoms by their (start,end) spans.
kinds: depends_on, supports, contradicts, derives. Only report relations you can
justify from the text. Return strict JSON:
{"relations":[{"src_start":int,"src_end":int,"dst_start":int,"dst_end":int,"kind":str,"confidence":float}]}"""
