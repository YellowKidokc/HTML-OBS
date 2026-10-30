"""Versioned grade families (spec Q).

C_I / C_E / C_C are tracked SEPARATELY. A score is a rubric score, NOT a truth
probability. Highest standing may not come from internal agreement alone (E).
Formulas are versioned so they can be revised after adversarial testing.
"""
from __future__ import annotations

from dataclasses import dataclass

GRADE_RUBRIC_VERSION = "grades-v1"


@dataclass
class GradeSet:
    g_i: int          # Internal Method Grade (0-100)
    g_e: int          # External Evidence / Correspondence Grade
    g_c: int          # Consilience Grade
    rubric: str = GRADE_RUBRIC_VERSION

    def interpretation(self) -> str:
        hi_i, hi_e = self.g_i >= 60, self.g_e >= 60
        if hi_i and hi_e:
            return "externally anchored convergence"
        if hi_i and not hi_e:
            return "CLOSED-SYSTEM COHERENCE WARNING"
        if not hi_i and hi_e:
            return "framework anomaly / revision pressure"
        return "unsupported"


def grade_paper(atoms: list[dict], relations: list[dict], bridges: list[dict]) -> GradeSet:
    """A transparent, deliberately simple v1 rubric.

    G_I: internal method — coherence of the derivation graph (relations present,
         few contradictions, atoms classified).
    G_E: external evidence — share of atoms with N/F reference architecture and
         an Evidence function or external receipt. Internal agreement can NOT
         drive this up on its own.
    G_C: consilience — presence of ADMITTED bridges only.
    """
    n = max(1, len(atoms))
    contradictions = sum(1 for r in relations if r.get("kind") == "contradicts")
    supports = sum(1 for r in relations if r.get("kind") in ("supports", "derives", "depends_on"))
    classified = sum(1 for a in atoms if a.get("function"))

    g_i = int(min(100, 40 + 60 * (classified / n) - 10 * contradictions + 5 * min(supports, 6)))
    g_i = max(0, g_i)

    evidence = sum(1 for a in atoms
                   if a.get("function") == "Evidence"
                   or a.get("reference_architecture") in ("N", "F")
                   or a.get("origin") == "external_receipt")
    g_e = int(min(100, 100 * (evidence / n)))

    admitted = sum(1 for b in bridges if b.get("state") == "Admitted")
    g_c = int(min(100, 25 * admitted))

    return GradeSet(g_i=g_i, g_e=g_e, g_c=g_c)


def evidence_grade_letter(atom_function: str, reference_arch: str, verified: bool) -> str:
    """Computed marker 12. Never fabricated by the AI — derived here."""
    if atom_function == "Evidence" and reference_arch in ("N", "F") and verified:
        return "A"
    if atom_function == "Evidence":
        return "B"
    if reference_arch in ("N", "F"):
        return "C"
    return "D"
