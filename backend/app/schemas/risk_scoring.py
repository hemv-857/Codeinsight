from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

RiskLevelResponse = Literal["low", "medium", "high", "critical"]


class RiskFactorResponse(BaseModel):
    """One explainable risk score factor."""

    name: str
    score: int = Field(ge=0, le=100)
    weight: int = Field(ge=0)
    description: str

    model_config = ConfigDict(frozen=True)


class RiskScoreResponse(BaseModel):
    """Normalized risk score response."""

    score: int = Field(ge=0, le=100)
    level: RiskLevelResponse
    confidence: float = Field(ge=0, le=1)
    factors: list[RiskFactorResponse]

    model_config = ConfigDict(frozen=True)
