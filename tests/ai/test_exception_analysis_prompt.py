from decimal import Decimal
from types import SimpleNamespace

from app.ai.prompts.exception_analysis import (
    build_exception_analysis_prompt,
)


def create_exception():
    return SimpleNamespace(
        exception_id="EXC_TEST_001",
        transaction_id="TXN_TEST_001",
        exception_type="AMOUNT_MISMATCH",
        severity="HIGH",
        status="OPEN",
        description="Payment amount does not match settlement amount.",
    )


def test_prompt_contains_exception_details():
    exception = create_exception()

    intelligence = {
        "classification": "UNEXPLAINED_AMOUNT_MISMATCH",
        "root_cause": "Settlement amount differs from payment amount.",
        "recommended_action": "HUMAN_REVIEW",
        "confidence": Decimal("0.9500"),
    }

    evidence = [
        {
            "evidence_type": "PAYMENT",
            "description": "Payment amount was 100.00 INR.",
        },
        {
            "evidence_type": "SETTLEMENT",
            "description": "Settlement amount was 95.00 INR.",
        },
    ]

    prompt = build_exception_analysis_prompt(
        exception=exception,
        intelligence=intelligence,
        evidence=evidence,
    )

    assert "EXC_TEST_001" in prompt
    assert "TXN_TEST_001" in prompt
    assert "AMOUNT_MISMATCH" in prompt
    assert "HIGH" in prompt
    assert "OPEN" in prompt

    assert "UNEXPLAINED_AMOUNT_MISMATCH" in prompt
    assert "Settlement amount differs from payment amount." in prompt
    assert "HUMAN_REVIEW" in prompt
    assert "0.9500" in prompt

    assert "Payment amount was 100.00 INR." in prompt
    assert "Settlement amount was 95.00 INR." in prompt


def test_prompt_handles_empty_evidence():
    exception = create_exception()

    intelligence = {
        "classification": "MISSING_SETTLEMENT",
        "root_cause": "No settlement found.",
        "recommended_action": "ESCALATE",
        "confidence": Decimal("1.0000"),
    }

    prompt = build_exception_analysis_prompt(
        exception=exception,
        intelligence=intelligence,
        evidence=[],
    )

    assert "No supporting evidence available." in prompt


def test_prompt_uses_default_confidence():
    exception = create_exception()

    intelligence = {
        "classification": "UNKNOWN",
        "root_cause": "Unknown",
        "recommended_action": "HUMAN_REVIEW",
    }

    prompt = build_exception_analysis_prompt(
        exception=exception,
        intelligence=intelligence,
        evidence=[],
    )

    assert "0.0000" in prompt


def test_prompt_requires_json_response():
    exception = create_exception()

    prompt = build_exception_analysis_prompt(
        exception=exception,
        intelligence={},
        evidence=[],
    )

    assert "Return ONLY valid JSON." in prompt
    assert "Do not output markdown." in prompt
    assert "Do not wrap the response in ```json." in prompt
    assert '"summary"' in prompt
    assert '"root_cause"' in prompt
    assert '"risk_level"' in prompt
    assert '"recommended_action"' in prompt
    assert '"confidence"' in prompt