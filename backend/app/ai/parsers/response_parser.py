import json


def parse_ai_json_response(
    response: str,
) -> dict:
    """
    Extract and parse a JSON object from an AI response.

    Handles:
    - Raw JSON
    - Markdown JSON code fences
    - Surrounding explanatory text
    """

    if not response or not response.strip():
        raise ValueError("AI response is empty.")

    cleaned = response.strip()

    # Remove markdown code fences when present.
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()

        if lines and lines[0].strip().startswith("```"):
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        cleaned = "\n".join(lines).strip()

    # First attempt: response is already valid JSON.
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        # Extract the outermost JSON object.
        start = cleaned.find("{")
        end = cleaned.rfind("}")

        if start == -1 or end == -1 or end <= start:
            raise ValueError(
                "No valid JSON object found in AI response."
            )

        json_candidate = cleaned[start : end + 1]

        try:
            parsed = json.loads(json_candidate)
        except json.JSONDecodeError as error:
            raise ValueError(
                "AI response contains invalid JSON."
            ) from error

    if not isinstance(parsed, dict):
        raise ValueError(
            "AI response must contain a JSON object."
        )

    return parsed