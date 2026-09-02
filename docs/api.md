# RazorRecon AI — API Reference

## Overview

RazorRecon AI exposes a versioned REST API for reconciliation, exception intelligence, AI-assisted investigation, human review, auditability, and dashboard analytics.

### Base URL

```text
http://127.0.0.1:8000/api/v1
```

For a Docker deployment using the default configuration:

```text
http://localhost:8000/api/v1
```

All responses use JSON.

Interactive OpenAPI documentation is available at:

```text
http://127.0.0.1:8000/docs
```

The raw OpenAPI schema is available at:

```text
http://127.0.0.1:8000/openapi.json
```

Timestamps are serialized as ISO 8601 datetimes. Monetary values are represented as decimal strings to avoid floating-point ambiguity.

---

# System

| Method | Path            | Description                                                |
| ------ | --------------- | ---------------------------------------------------------- |
| `GET`  | `/`             | Returns service name, API version, and operating status.   |
| `GET`  | `/health`       | Reports API availability and database connectivity.        |
| `GET`  | `/health/live`  | Liveness check indicating that the API process is running. |
| `GET`  | `/health/ready` | Readiness check verifying database connectivity.           |

## API Root

```http
GET /api/v1/
```

Example response:

```json
{
  "service": "RazorRecon AI",
  "status": "running",
  "version": "0.2.0"
}
```

## Health

```http
GET /api/v1/health
```

Healthy response:

```json
{
  "status": "healthy",
  "service": "RazorRecon AI",
  "database": "healthy"
}
```

If the database cannot be reached, the endpoint returns a degraded response:

```json
{
  "status": "degraded",
  "service": "RazorRecon AI",
  "database": "unhealthy"
}
```

The health endpoint intentionally reports database degradation using HTTP `200`. It is intended for service-health visibility rather than orchestration readiness decisions.

## Liveness

```http
GET /api/v1/health/live
```

Example:

```json
{
  "status": "alive",
  "service": "RazorRecon AI"
}
```

The liveness endpoint does not require a database query.

## Readiness

```http
GET /api/v1/health/ready
```

Example when ready:

```json
{
  "status": "ready",
  "service": "RazorRecon AI",
  "database": "healthy"
}
```

If the database is unavailable:

```json
{
  "status": "not_ready",
  "service": "RazorRecon AI",
  "database": "unhealthy"
}
```

---

# Reconciliation Runs

Reconciliation runs represent executions of the deterministic reconciliation engine over a set of financial records.

| Method | Path                            | Description                                        |
| ------ | ------------------------------- | -------------------------------------------------- |
| `GET`  | `/reconciliation-runs`          | Lists reconciliation runs.                         |
| `GET`  | `/reconciliation-runs/{run_id}` | Returns details for a specific reconciliation run. |

A reconciliation run contains aggregate execution information such as:

* Run identifier
* Processing status
* Total records
* Matched records
* Exception count
* Start timestamp
* Completion timestamp

The run identifier is the stable application-level identifier used to associate persisted reconciliation results with the execution that produced them.

---

# Exceptions

| Method | Path                                     | Description                                                                                                              |
| ------ | ---------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| `GET`  | `/exceptions`                            | Lists reconciliation exceptions.                                                                                         |
| `GET`  | `/exceptions/analytics/summary`          | Returns exception counts, distributions, resolution rate, and financial exposure.                                        |
| `GET`  | `/exceptions/{exception_id}`             | Returns an exception together with intelligence, evidence, investigations, human reviews, and transaction audit history. |
| `POST` | `/exceptions/{exception_id}/investigate` | Runs an AI-assisted investigation or deterministic fallback.                                                             |
| `POST` | `/exceptions/{exception_id}/review`      | Records a human decision for an open exception.                                                                          |

---

## List Exceptions

```http
GET /api/v1/exceptions
```

Optional query filters include:

```text
status
severity
exception_type
```

Example:

```http
GET /api/v1/exceptions?status=OPEN&severity=CRITICAL
```

Filter values are case-insensitive.

The endpoint returns reconciliation exceptions and their persisted exception intelligence.

---

## Exception Detail

```http
GET /api/v1/exceptions/{exception_id}
```

Example:

```http
GET /api/v1/exceptions/EXC-001
```

The detail response may include:

* Exception metadata
* Transaction identifier
* Exception type
* Severity
* Status
* Confidence
* Description
* Evidence
* Investigation history
* Previous human reviews
* Transaction audit history

If the exception does not exist, the API returns:

```text
404 Not Found
```

---

# Exception Analytics

```http
GET /api/v1/exceptions/analytics/summary
```

Returns aggregate exception intelligence including:

* Total exceptions
* Open exceptions
* Resolved exceptions
* Escalated exceptions
* Counts by exception type
* Counts by severity
* Resolution rate
* Total financial exposure

The analytics endpoint is intended for operational monitoring and dashboard consumption.

---

# AI Investigation

```http
POST /api/v1/exceptions/{exception_id}/investigate
```

Example:

```http
POST /api/v1/exceptions/EXC-001/investigate
```

The investigation pipeline follows a deterministic-first architecture.

The API always performs deterministic analysis from persisted reconciliation and exception evidence.

If the configured AI provider is available and produces a valid response, the investigation additionally contains AI-generated analysis.

If AI is disabled, unavailable, or produces an invalid response, the API falls back to deterministic investigation.

The LLM is therefore not the source of truth for:

* Monetary totals
* Transaction matching
* Exception classification
* Database state
* Evidence identifiers
* Settlement existence
* Refund existence
* Fee calculations

---

## Investigation Response

Example AI-assisted response:

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

When deterministic fallback is used:

```json
{
  "exception_id": "EXC-001",
  "investigation_mode": "DETERMINISTIC_FALLBACK",
  "ai_provider_status": "UNAVAILABLE",
  "evidence_count": 2,
  "deterministic_analysis": {},
  "ai_analysis": null,
  "fallback_reason": "AI provider is unavailable."
}
```

### Investigation modes

| Mode                     | Meaning                                                            |
| ------------------------ | ------------------------------------------------------------------ |
| `AI_ASSISTED`            | Deterministic analysis was augmented with a validated AI response. |
| `DETERMINISTIC_FALLBACK` | Investigation completed without usable AI output.                  |

### AI provider states

| State              | Meaning                                              |
| ------------------ | ---------------------------------------------------- |
| `SUCCESS`          | Provider returned a valid response.                  |
| `UNAVAILABLE`      | Provider was disabled or unavailable.                |
| `INVALID_RESPONSE` | Provider returned a response that failed validation. |

Every investigation persists the deterministic analysis regardless of AI availability.

---

# Human Review

```http
POST /api/v1/exceptions/{exception_id}/review
```

Human review is available only while an exception is in the `OPEN` state.

Example request:

```http
POST /api/v1/exceptions/EXC-001/review
Content-Type: application/json

{
  "reviewer": "finance.analyst@example.com",
  "action": "APPROVE",
  "reason": "Settlement was confirmed in the processor portal."
}
```

The `reviewer` and `reason` fields must contain non-whitespace text.

The `action` value is case-insensitive and must be one of:

| Action     | Resulting exception state | Audit action          |
| ---------- | ------------------------- | --------------------- |
| `APPROVE`  | `RESOLVED`                | `EXCEPTION_RESOLVED`  |
| `REJECT`   | `ESCALATED`               | `EXCEPTION_REJECTED`  |
| `ESCALATE` | `ESCALATED`               | `EXCEPTION_ESCALATED` |

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

If the exception does not exist:

```text
404 Not Found
```

If the exception is no longer open:

```text
409 Conflict
```

Invalid request payloads result in FastAPI's standard:

```text
422 Unprocessable Entity
```

---

# Dashboard

| Method | Path                          | Description                                                                                     |
| ------ | ----------------------------- | ----------------------------------------------------------------------------------------------- |
| `GET`  | `/dashboard/summary`          | Returns transaction counts, match rate, financial totals, and exception status/severity counts. |
| `GET`  | `/dashboard/exception-trends` | Returns exception counts grouped by type, severity, and status.                                 |

---

## Dashboard Summary

```http
GET /api/v1/dashboard/summary
```

Example:

```json
{
  "transactions": {
    "total": 1928,
    "matched": 804,
    "amount_mismatch": 972,
    "missing_settlement": 152,
    "match_rate": 0.417
  },
  "financials": {
    "total_expected_amount": "97323820.00",
    "total_actual_settlement": "75533931.12",
    "total_difference": "21789888.88"
  },
  "exceptions": {
    "total": 1124,
    "open": 1121,
    "resolved": 2,
    "escalated": 1,
    "resolution_rate": 0.0018,
    "high_severity": 972,
    "critical_severity": 152
  }
}
```

Financial totals are represented as decimal strings rather than binary floating-point values.

---

# Reconciliation Statuses

The deterministic reconciliation engine currently identifies the following result states:

| Status               | Meaning                                                         |
| -------------------- | --------------------------------------------------------------- |
| `MATCHED`            | Payment and settlement reconcile successfully.                  |
| `AMOUNT_MISMATCH`    | A settlement exists but the expected and actual amounts differ. |
| `MISSING_SETTLEMENT` | No corresponding settlement exists.                             |

The reconciliation engine remains authoritative for these classifications.

AI investigation operates after exception generation and does not replace deterministic reconciliation.

---

# Error Handling

Application errors use a JSON `detail` field.

For domain-level errors, `detail` contains a stable error code, human-readable message, and relevant exception identifier where applicable.

Example:

```json
{
  "detail": {
    "error": "EXCEPTION_NOT_FOUND",
    "message": "Exception EXC-001 was not found.",
    "exception_id": "EXC-001"
  }
}
```

Invalid request bodies use FastAPI's standard validation response.

Example:

```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": [
        "body",
        "reviewer"
      ],
      "msg": "String should have at least 1 character",
      "input": ""
    }
  ]
}
```

---

# HTTP Status Codes

| Status                      | Meaning                                                                                         |
| --------------------------- | ----------------------------------------------------------------------------------------------- |
| `200 OK`                    | Successful request.                                                                             |
| `201 Created`               | Resource successfully created, where applicable.                                                |
| `400 Bad Request`           | Invalid application request.                                                                    |
| `404 Not Found`             | Requested resource does not exist.                                                              |
| `409 Conflict`              | Requested state transition conflicts with the current domain state.                             |
| `422 Unprocessable Entity`  | Request validation failed.                                                                      |
| `500 Internal Server Error` | Unexpected application failure or investigation result that could not be produced or validated. |

---

# API Design Principles

## Deterministic First

Financial reconciliation is deterministic.

The API therefore establishes:

```text
Financial Records
        ↓
Normalization
        ↓
Transaction Matching
        ↓
Deterministic Reconciliation
        ↓
Exception Detection
        ↓
Evidence Generation
        ↓
AI Investigation
```

AI is an investigation and explanation layer rather than the financial source of truth.

## Evidence-Based AI

AI investigations operate on persisted evidence and deterministic analysis.

The AI layer is not permitted to invent:

* Transactions
* Settlements
* Refunds
* Fees
* Adjustments
* Evidence records
* Monetary totals
* Database identifiers

## Graceful AI Failure

The API remains operational when an AI provider is unavailable.

In that case:

```text
AI unavailable
      ↓
Deterministic analysis
      ↓
Persist fallback investigation
      ↓
Return usable investigation response
```

This prevents an external LLM dependency from becoming a single point of failure for the reconciliation workflow.

## Auditability

Human decisions and important exception state transitions are recorded through audit records.

This provides an operational trail for:

* Who performed an action
* What action occurred
* Previous state
* New state
* Reason
* Confidence where applicable
* Timestamp

---

# OpenAPI

The FastAPI application automatically exposes the OpenAPI contract.

Interactive documentation:

```text
/docs
```

Raw schema:

```text
/openapi.json
```

The OpenAPI specification should be treated as the executable API contract and kept synchronized with implementation changes.

---

# Related Documentation

* `docs/reconciliation.md` — reconciliation engine and financial invariants
* `docs/ai-investigation.md` — deterministic and AI-assisted investigation architecture
* `docs/architecture.md` — system architecture and component responsibilities
* `docs/diagrams/system-architecture.md` — high-level architecture diagram
* `docs/diagrams/reconciliation-flow.md` — reconciliation workflow
* `docs/diagrams/ai-investigation-flow.md` — investigation workflow
* `docs/diagrams/database-er.md` — database entity relationships

---

# Summary

RazorRecon AI's API is designed around a deterministic financial core with AI-assisted investigation layered on top.

The core design principle is:

> **The reconciliation engine establishes the discrepancy. AI explains the discrepancy.**

This separation ensures that AI failures do not compromise financial correctness while still allowing investigators to receive richer explanations, evidence interpretation, root-cause analysis, risk assessment, and recommended actions.
