from dataclasses import dataclass
from typing import Literal

RiskLevel = Literal["low", "medium", "high", "critical"]


@dataclass(frozen=True)
class RiskFactor:
    """One explainable contribution to a risk score."""

    name: str
    score: int
    weight: int
    description: str


@dataclass(frozen=True)
class RiskScore:
    """Normalized risk score and factor breakdown."""

    score: int
    level: RiskLevel
    confidence: float
    factors: tuple[RiskFactor, ...]


@dataclass(frozen=True)
class RiskScoringInput:
    """Minimal bug impact facts needed for risk scoring."""

    frame_count: int
    matched_frame_count: int
    impacted_file_count: int
    dependency_edge_count: int
    root_cause_score: float
    changed_file_match_count: int


class RiskScoringService:
    """Scores bug impact risk from grounded static-analysis factors."""

    def score_bug_impact(self, data: RiskScoringInput) -> RiskScore:
        factors = (
            self._factor(
                "stack_trace_match",
                round(self._ratio(data.matched_frame_count, data.frame_count) * 100),
                30,
                "How many stack frames matched repository files.",
            ),
            self._factor(
                "impact_radius",
                min(data.impacted_file_count * 18, 100),
                30,
                "How many files are directly implicated by trace and dependency edges.",
            ),
            self._factor(
                "dependency_density",
                min(data.dependency_edge_count * 4, 100),
                15,
                "How connected the repository graph is around the analysis.",
            ),
            self._factor(
                "root_cause_strength",
                round(data.root_cause_score * 100),
                15,
                "How strong the top root-cause candidate is.",
            ),
            self._factor(
                "recent_change_overlap",
                min(data.changed_file_match_count * 50, 100),
                10,
                "Whether recently changed files overlap the suspected area.",
            ),
        )
        total_weight = sum(factor.weight for factor in factors)
        score = round(sum(factor.score * factor.weight for factor in factors) / total_weight)
        confidence = min(
            0.95,
            0.25
            + self._ratio(data.matched_frame_count, data.frame_count) * 0.45
            + min(data.changed_file_match_count, 1) * 0.15
            + min(data.impacted_file_count, 5) / 5 * 0.1,
        )
        return RiskScore(
            score=score,
            level=self._level(score),
            confidence=confidence,
            factors=factors,
        )

    def _factor(self, name: str, score: int, weight: int, description: str) -> RiskFactor:
        return RiskFactor(
            name=name,
            score=max(0, min(score, 100)),
            weight=weight,
            description=description,
        )

    def _ratio(self, numerator: int, denominator: int) -> float:
        return numerator / denominator if denominator else 0.0

    def _level(self, score: int) -> RiskLevel:
        if score >= 80:
            return "critical"
        if score >= 60:
            return "high"
        if score >= 35:
            return "medium"
        return "low"
