from decimal import Decimal

from app.models.reconciliation import ExceptionRecord


def build_exception_analysis_prompt(
    exception: ExceptionRecord,
    intelligence: dict,
    evidence: list[dict],
) -> str:
    """
    Build a structured prompt for AI-powered exception analysis.

    The AI receives deterministic reconciliation intelligence and
    supporting evidence, then produces a human-readable investigation
    summary and risk assessment.
    """

    evidence_text = "\n".join(
        [
            (
                f"- [{item.get('evidence_type', 'UNKNOWN')}] "
                f"{item.get('description', 'No description available')}"
            )
            for item in evidence
        ]
    )

    if not evidence_text:
        evidence_text = "- No supporting evidence available."

    confidence = intelligence.get(
        "confidence",
        Decimal("0.0000"),
    )

    prompt = f"""
You are an AI financial reconciliation investigator.

Your role is to analyze reconciliation exceptions using the
provided deterministic analysis and supporting financial evidence.

Do not invent financial facts.

You must distinguish clearly between:
- confirmed facts
- likely explanations
- unresolved risks

Return a concise investigation report in the following format:

SUMMARY:
<brief explanation of the exception>

ROOT_CAUSE:
<most likely root cause>

RISK_LEVEL:
LOW | MEDIUM | HIGH | CRITICAL

RECOMMENDED_ACTION:
AUTO_RESOLVE | HUMAN_REVIEW | ESCALATE

CONFIDENCE:
<number between 0 and 1>

KEY_EVIDENCE:
- evidence point 1
- evidence point 2

UNRESOLVED_QUESTIONS:
- question 1
- question 2


EXCEPTION DETAILS

Exception ID: {exception.exception_id}
Transaction ID: {exception.transaction_id}
Exception Type: {exception.exception_type}
Severity: {exception.severity}
Status: {exception.status}
Description: {exception.description}


DETERMINISTIC ANALYSIS

Classification: {intelligence.get('classification')}
Root Cause: {intelligence.get('root_cause')}
Recommended Action: {intelligence.get('recommended_action')}
Confidence: {confidence}


SUPPORTING EVIDENCE

{evidence_text}
"""

    return prompt.strip()