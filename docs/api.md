# API reference

Base URL: `http://127.0.0.1:8000/api/v1`

Interactive OpenAPI documentation is available at `/docs`; the raw schema is
available at `/openapi.json`. Responses use JSON. Timestamps are ISO 8601 UTC
datetimes and monetary totals are serialized as two-decimal strings.

## System

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/health` | Reports API availability and database connectivity. A database outage returns `status: "degraded"` with HTTP 200. |
| `GET` | `/` | Returns service name, API version, and operating status. |

## Exceptions

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/exceptions` | Lists reconciliation exceptions. Supports optional `status`, `severity`, and `exception_type` query filters. Filter values are case-insensitive. |
| `GET` | `/exceptions/analytics/summary` | Returns exception counts, distributions, resolution rate, and total financial exposure. |
| `GET` | `/exceptions/{exception_id}` | Returns an exception with intelligence, evidence, previous human reviews, and transaction audit history. Returns `404` if unknown. |
| `POST` | `/exceptions/{exception_id}/investigate` | Runs an AI-assisted investigation when the configured provider is available, otherwise returns a deterministic fallback. Returns `404` if unknown and `500` if the investigation result cannot be produced or validated. |
| `POST` | `/exceptions/{exception_id}/review` | Records a human decision for an `OPEN` exception. Returns `404` if unknown and `409` when the exception is no longer open. |

### Submit a human review

```http
POST /api/v1/exceptions/EXC-001/review
Content-Type: application/json

{
  "reviewer": "finance.analyst@example.com",
  "action": "APPROVE",
  "reason": "Settlement was confirmed in the processor portal."
}
```

`action` is case-insensitive and must be one of:

| Action | Resulting exception state | Audit action |
| --- | --- | --- |
| `APPROVE` | `RESOLVED` | `EXCEPTION_RESOLVED` |
| `REJECT` | `ESCALATED` | `EXCEPTION_REJECTED` |
| `ESCALATE` | `ESCALATED` | `EXCEPTION_ESCALATED` |

Successful response:

```json
{
  "message": "Exception review recorded successfully.",
  "exception_id": "EXC-001",
  "transaction_id": "PAY-001",
  "reviewer": "finance.analyst@example.com",
  "action": "APPROVE",
  "previous_state": "OPEN",
  "new_state": "RESOLVED",
  "reason": "Settlement was confirmed in the processor portal.",
  "resolved_at": "2026-08-30T12:00:00"
}
```

The reviewer and reason must contain non-whitespace text. The API rejects an
invalid payload with FastAPI's standard `422` validation response.

### Investigation response

The investigation endpoint always returns deterministic analysis. It also
returns `ai_analysis` when the provider can produce a valid result.

```json
{
  "exception_id": "EXC-001",
  "investigation_mode": "AI_ASSISTED",
  "ai_provider_status": "SUCCESS",
  "evidence_count": 2,
  "deterministic_analysis": {},
  "ai_analysis": {
    "summary": "...",
    "root_cause": "...",
    "risk_level": "HIGH",
    "recommended_action": "...",
    "confidence": 0.86,
    "key_evidence": [],
    "unresolved_questions": []
  },
  "fallback_reason": null
}
```

When AI is disabled or unavailable, `investigation_mode` is
`DETERMINISTIC_FALLBACK`, `ai_analysis` is `null`, and `fallback_reason`
explains why.

## Dashboard

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/dashboard/summary` | Returns transaction counts, match rate, financial totals, and exception status/severity counts. |
| `GET` | `/dashboard/exception-trends` | Returns exception counts grouped by type, severity, and status. |

## Error format

Application errors use FastAPI's `detail` field. For domain errors it is an
object with a stable `error` code, a human-readable `message`, and the relevant
`exception_id`; invalid request bodies use the standard `422` validation
format.
