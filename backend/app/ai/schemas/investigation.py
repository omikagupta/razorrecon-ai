from pydantic import BaseModel, Field


class AIInvestigationReport(BaseModel):
    """
    Structured report returned by the AI investigation layer.
    """

    summary: str = Field(
        min_length=1,
    )

    root_cause: str = Field(
        min_length=1,
    )

    risk_level: str

    recommended_action: str

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    key_evidence: list[str] = Field(
        default_factory=list,
    )

    unresolved_questions: list[str] = Field(
        default_factory=list,
    )