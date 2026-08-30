from decimal import Decimal
import json

from app.models.reconciliation import ExceptionRecord


def build_exception_analysis_prompt(
    exception: ExceptionRecord,
    intelligence: dict,
    evidence: list[dict],
) -> str:
    """
    Build a structured prompt for AI-powered exception analysis.
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

    response_schema = {
        "summary": "Brief explanation of the exception",
        "root_cause": "Most likely root cause",
        "risk_level": "LOW | MEDIUM | HIGH | CRITICAL",
        "recommended_action": (
            "AUTO_RESOLVE | HUMAN_REVIEW | ESCALATE"
        ),
        "confidence": 0.0,
        "key_evidence": [
            "Evidence point 1",
            "Evidence point 2",
        ],
        "unresolved_questions": [
            "Question 1",
            "Question 2",
        ],
    }

    prompt = f"""
You are an AI financial reconciliation investigator.

Analyze the reconciliation exception using ONLY the deterministic
analysis and supporting evidence provided below.

CRITICAL RULES:
- Do not invent financial facts.
- Clearly distinguish evidence-based conclusions from uncertainty.
- Do not output markdown.
- Do not wrap the response in ```json.
- Return ONLY valid JSON.
- The response MUST follow this exact structure:

{json.dumps(response_schema, indent=2)}

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