"""Pydantic schemas — the canonical data contracts.

Design rules enforced here:
  * AI inference MUST be identifiable as AI inference (Provenance.origin).
  * If origin starts with "ai_inference", numeric confidence is REQUIRED (L).
  * Confidence is a rubric/uncertainty value, NOT a truth probability.
  * Computed markers (12, 13, 14) are not carried in the AI schema at all.
"""
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, model_validator


# --------------------------------------------------------------------------
# Provenance (spec L) — attached to every important derived field.
# --------------------------------------------------------------------------
class Origin(str, Enum):
    source = "source"
    ai_inference_unverified = "ai_inference_unverified"
    ai_inference_verified_by_human = "ai_inference_verified_by_human"
    ai_inference_verified_by_formal_check = "ai_inference_verified_by_formal_check"
    computed = "computed"
    human = "human"
    external_receipt = "external_receipt"


class Provenance(BaseModel):
    value: str
    origin: Origin = Origin.ai_inference_unverified
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    confidence_basis: Optional[str] = None  # explicit | strong_context | inferred | ambiguous
    method_version: str = "method-0.1.0"
    timestamp: Optional[str] = None

    @model_validator(mode="after")
    def _require_conf_for_ai(self):
        if self.origin.value.startswith("ai_inference") and self.confidence is None:
            raise ValueError("ai_inference origin requires numeric confidence (0.00-1.00)")
        return self

    @property
    def is_ai(self) -> bool:
        return self.origin.value.startswith("ai_inference")

    @property
    def verified(self) -> bool:
        return self.origin in (
            Origin.ai_inference_verified_by_human,
            Origin.ai_inference_verified_by_formal_check,
            Origin.human,
            Origin.external_receipt,
        )


# --------------------------------------------------------------------------
# Multi-axis classification (spec J). NOT a single ladder.
# --------------------------------------------------------------------------
class Classification(BaseModel):
    function: str = "Claim"          # Definition|Claim|Derivation|Evidence|Verdict
    claim_family: str = "unspecified"
    object_type: str = "statement"
    source: str = "endogenous"       # where it came from
    commitment: str = "asserted"     # how strongly the paper commits
    standing: str = "proposed"       # proposed|established|contested|...
    dispute: str = "uncontested"     # uncontested|contested
    scope: str = "local"
    modality: str = "assertoric"     # assertoric|hypothetical|normative|...
    provenance: str = "in_paper"
    reference_architecture: str = "E"  # E|N|F|T (parallel, NOT a hierarchy)


REFERENCE_ARCHITECTURES = {
    "E": "Endogenous",
    "N": "Naturally / Empirically Constrained",
    "F": "Formally Constrained",
    "T": "Claimed Transcendent Reference",
}


# --------------------------------------------------------------------------
# The fifteen markers (spec K). Positions never change.
# Markers 12, 13, 14 are COMPUTED and must not be fabricated by AI.
# --------------------------------------------------------------------------
class Markers(BaseModel):
    m01_atom_id: str
    m02_home_domain: str = "unassigned"
    m03_native_domains: list[str] = Field(default_factory=list)
    m04_bridged_domains: list[str] = Field(default_factory=list)  # empty until a Bridge exists
    m05_object_type: str = "statement"
    m06_claim_family: str = "unspecified"
    m07_function_kind: str = "Claim"
    m08_source: str = "endogenous"
    m09_commitment: str = "asserted"
    m10_standing: str = "proposed"
    m11_dispute: str = "uncontested"
    m12_evidence_grade: Optional[str] = None   # COMPUTED
    m13_usage_runs: int = 0                     # COMPUTED
    m14_graph_degree: int = 0                   # COMPUTED
    m15_alert_state: str = "none"


# --------------------------------------------------------------------------
# Atom (spec I). Addressable epistemic object. NOT automatically true.
# --------------------------------------------------------------------------
class SourceSpan(BaseModel):
    source_file: str
    section: str = ""
    start: int
    end: int
    text: str


class Atom(BaseModel):
    atom_id: str
    paper_id: str
    span: SourceSpan
    label: str = ""                     # short human label
    classification: Classification = Field(default_factory=Classification)
    class_provenance: dict[str, Provenance] = Field(default_factory=dict)
    frozen: bool = False
    approved: bool = False


# --------------------------------------------------------------------------
# Relations (spec X, Pass C).
# --------------------------------------------------------------------------
class Relation(BaseModel):
    src: str        # atom_id
    dst: str        # atom_id
    kind: str       # depends_on | supports | contradicts | derives
    provenance: Provenance


# --------------------------------------------------------------------------
# AI response envelopes (validated in ai/response_validation.py).
# --------------------------------------------------------------------------
class AtomCandidate(BaseModel):
    start: int
    end: int
    text: str
    label: str = ""
    section: str = ""


class ClassifiedAtom(BaseModel):
    start: int
    end: int
    classification: Classification
    confidence: float = Field(ge=0.0, le=1.0)
    confidence_basis: str = "inferred"


class AnalysisResult(BaseModel):
    """The full result of one 'Analyze Paper' user action (Passes A-C)."""
    candidates: list[AtomCandidate] = Field(default_factory=list)
    classified: list[ClassifiedAtom] = Field(default_factory=list)
    relations: list[dict] = Field(default_factory=list)
    prompt_version: str = "unknown"
    model: str = "unknown"
