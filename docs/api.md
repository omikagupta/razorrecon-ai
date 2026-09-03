# API reference

Base URL: `http://localhost:8000`. Interactive OpenAPI documentation is available at `/docs` while the backend is running.

## Dashboard

| Method and path | Query/body | 200 response |
| --- | --- | --- |
| `GET /api/v1/dashboard/summary` | None | `transactions`, `financials`, and `exceptions` aggregates |
| `GET /api/v1/dashboard/exception-trends` | None | Counts grouped by exception type, severity, and status |

`/summary` returns:

```json
{
  "transactions": {"total": 0, "matched": 0, "amount_mismatch": 0, "missing_settlement": 0, "match_rate": 0.0},
  "financials": {"total_expected_amount": "0.00", "total_actual_settlement": "0.00", "total_difference": "0.00"},
  "exceptions": {"total": 0, "open": 0, "resolved": 0, "escalated": 0, "resolution_rate": 0.0, "high_severity": 0, "critical_severity": 0}
}
```

## Exceptions

| Method and path | Query/body | 200 response |
| --- | --- | --- |
| `GET /api/v1/exceptions` | `status` or `status_filter`, `severity`, `exception_type`, `page` (>=1), `page_size` (1-100) | Paginated `exceptions` list |
| `GET /api/v1/exceptions/analytics/summary` | None | Exception and financial analytics |
| `GET /api/v1/exceptions/{exception_id}` | Path ID | Exception, deterministic intelligence, evidence, reviews, audit logs |
| `GET /api/v1/exceptions/{exception_id}/investigations` | Path ID | Persisted investigation history, newest first |
| `POST /api/v1/exceptions/{exception_id}/investigate` | Path ID | Investigation response below |
| `POST /api/v1/exceptions/{exception_id}/review` | JSON review request | Recorded review and resulting status |

The list response has `total`, `page`, `page_size`, `pages`, and `exceptions`. Each exception contains `exception_id`, `transaction_id`, `exception_type`, `severity`, `status`, `confidence`, `description`, `created_at`, and `resolved_at`.

### Investigation response

```json
{
  "exception_id": "exc_123",
  "investigation_mode": "AI_ASSISTED",
  "ai_provider_status": "SUCCESS",
  "evidence_count": 3,
  "deterministic_analysis": {"classification": "UNEXPLAINED_AMOUNT_MISMATCH"},
  "ai_analysis": {"summary": "...", "root_cause": "...", "risk_level": "HIGH", "recommended_action": "HUMAN_REVIEW", "confidence": 0.95, "key_evidence": [], "unresolved_questions": []},
  "fallback_reason": null
}
```

`investigation_mode` is `AI_ASSISTED` or `DETERMINISTIC_FALLBACK`; provider status is `SUCCESS`, `UNAVAILABLE`, or `INVALID_RESPONSE`.

### Review request

```json
{"reviewer": "ops@example.com", "action": "APPROVE", "reason": "Fee policy and source records verified."}
```

Allowed actions are `APPROVE`, `REJECT`, and `ESCALATE`. Only an `OPEN` exception may be reviewed; an invalid state returns `409`.

## Reconciliation runs

| Method and path | Description |
| --- | --- |
| `POST /api/v1/reconciliation-runs` | Runs reconciliation and persists results, exceptions, evidence, and audit logs |
| `GET /api/v1/reconciliation-runs` | Lists run history |
| `GET /api/v1/reconciliation-runs/{run_id}` | Returns run metadata, results, status distribution, and financial summary |

An empty source dataset produces `400 RECONCILIATION_VALIDATION_ERROR` because there is no result set to persist. Unknown exception and run IDs return `404`. Unexpected processing errors return structured `500` responses.
