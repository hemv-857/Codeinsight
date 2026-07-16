from backend.app.services.risk_scoring import RiskScoringInput, RiskScoringService


def test_risk_scoring_returns_level_and_factors() -> None:
    score = RiskScoringService().score_bug_impact(
        RiskScoringInput(
            frame_count=4,
            matched_frame_count=3,
            impacted_file_count=5,
            dependency_edge_count=12,
            root_cause_score=0.9,
            changed_file_match_count=1,
        )
    )

    assert score.score >= 60
    assert score.level in {"high", "critical"}
    assert score.confidence > 0.5
    assert [factor.name for factor in score.factors] == [
        "stack_trace_match",
        "impact_radius",
        "dependency_density",
        "root_cause_strength",
        "recent_change_overlap",
    ]


def test_risk_scoring_handles_missing_trace_evidence() -> None:
    score = RiskScoringService().score_bug_impact(
        RiskScoringInput(
            frame_count=0,
            matched_frame_count=0,
            impacted_file_count=0,
            dependency_edge_count=0,
            root_cause_score=0,
            changed_file_match_count=0,
        )
    )

    assert score.score == 0
    assert score.level == "low"
    assert score.confidence == 0.25
