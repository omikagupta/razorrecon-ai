# Architecture

RazorRecon AI is a deterministic reconciliation system with an optional AI investigation layer. Financial truth is produced only by database records and deterministic rules; Gemini may explain an exception, but never changes an amount, match status, or workflow state.

## Data flow

```text
CSV / database records
        |
        v
Financial tables (payments, settlements, refunds, fees, adjustments)
        |
        v
Deterministic reconciliation engine
        |
        +--> reconciliation result + exception + evidence + audit log
        |
        v
Investigation service
        |
        +--> deterministic analysis (always available)
        |
        +--> optional Gemini analysis
                 |
                 +--> validated report OR deterministic fallback
```

The reconciliation engine reads `Payment` and `Settlement` records and emits a result for every payment. Persistence records the run, its immutable results, exceptions for non-matches, supporting evidence, and an audit trail. Dashboard and exception APIs read those persisted records.

## Deterministic boundary

`backend/app/services/reconciliation/` owns reconciliation semantics:

| Component | Responsibility |
| --- | --- |
| `matcher.py` | Payment-to-settlement lookup and status selection |
| `rules.py` | Exact monetary comparison rules |
| `engine.py` | Batch orchestration and result summaries |
| `persistence.py` | Atomic run/result/exception persistence |
| `intelligence.py` | Evidence-based, deterministic explanation |
| `evidence.py` | Collection of payment, settlement, refund, fee, and adjustment records |

Use `Decimal` and database `NUMERIC` values for all money. Never pass floats into a financial rule, and never rely on an LLM for arithmetic or record matching.

## AI investigation boundary

`investigate_exception` first computes deterministic intelligence and collects evidence. It then builds a constrained prompt, calls the configured provider, extracts JSON, and validates it with `AIInvestigationReport`.

| Provider outcome | Investigation mode | Provider status | Result |
| --- | --- | --- |
| Valid response | `AI_ASSISTED` | `SUCCESS` | Deterministic analysis plus validated AI report |
| Disabled/provider/runtime failure | `DETERMINISTIC_FALLBACK` | `UNAVAILABLE` | Deterministic analysis and reason |
| Empty, malformed, or schema-invalid JSON | `DETERMINISTIC_FALLBACK` | `INVALID_RESPONSE` | Deterministic analysis and reason |

The fallback is a successful investigation outcome, not a reconciliation failure. Persisting `investigation_mode`, `ai_provider_status`, and `fallback_reason` makes this behaviour observable and auditable.

## Operational invariants

- A result is derived from source records and is never edited by the AI layer.
- Every persisted run has a lifecycle (`CREATED`, `RUNNING`, `COMPLETED`, or `FAILED`); a failed run is retained for auditability.
- Reconciliation writes are atomic after the `RUNNING` state has been safely committed.
- Human review, investigation records, and audit logs are separate from financial source records.

## Production evolution

For high-volume and payment-provider integrations, add an explicit settlement policy/version, typed fee components, a settlement-window calendar, idempotent run keys, and batch-oriented queries. Those additions keep deterministic decisions reproducible when commercial terms or bank holidays change.
