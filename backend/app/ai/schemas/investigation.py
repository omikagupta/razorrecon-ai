from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RecommendedAction(str, Enum):
    AUTO_RESOLVE = "AUTO_RESOLVE"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    ESCALATE = "ESCALATE"


class AIInvestigationReport(BaseModel):
    """
    Strictly validated structured report returned by the
    AI investigation layer.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    summary: str = Field(
        min_length=1,
        max_length=1000,
    )

    root_cause: str = Field(
        min_length=1,
        max_length=1000,
    )

    risk_level: RiskLevel

    recommended_action: RecommendedAction

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    key_evidence: list[str] = Field(
        default_factory=list,
        max_length=10,
    )

    unresolved_questions: list[str] = Field(
        default_factory=list,
        max_length=10,
    )