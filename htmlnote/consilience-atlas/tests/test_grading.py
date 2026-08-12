from atlas.grading import grade_paper, GradeSet


def test_internal_agreement_alone_does_not_max_external():
    # All internally consistent claims, NO evidence / N/F / receipts.
    atoms = [{"function": "Claim", "reference_architecture": "E"} for _ in range(6)]
    rels = [{"kind": "supports"} for _ in range(5)]
    gs = grade_paper(atoms, rels, bridges=[])
    assert gs.g_e == 0, "external grade must not rise from internal agreement"
    assert gs.interpretation() in ("CLOSED-SYSTEM COHERENCE WARNING", "unsupported")


def test_evidence_lifts_external_grade():
    atoms = [{"function": "Evidence", "reference_architecture": "N"} for _ in range(4)]
    gs = grade_paper(atoms, [], bridges=[])
    assert gs.g_e > 0


def test_consilience_needs_admitted_bridge():
    atoms = [{"function": "Claim", "reference_architecture": "E"}]
    assert grade_paper(atoms, [], bridges=[{"state": "Candidate"}]).g_c == 0
    assert grade_paper(atoms, [], bridges=[{"state": "Admitted"}]).g_c > 0


def test_interpretation_matrix():
    assert GradeSet(80, 80, 0).interpretation() == "externally anchored convergence"
    assert GradeSet(80, 10, 0).interpretation() == "CLOSED-SYSTEM COHERENCE WARNING"
    assert GradeSet(10, 80, 0).interpretation() == "framework anomaly / revision pressure"
    assert GradeSet(10, 10, 0).interpretation() == "unsupported"
