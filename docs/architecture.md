# Architecture

RazorRecon AI is a FastAPI service for loading payment data, reconciling
payments against settlements, and managing the resulting exceptions.

## Components

| Component | Responsibility |
| --- | --- |
| `backend/app/api` | HTTP API for health, dashboard, exception, investigation, and review operations. |
| `backend/app/services/ingestion` | Loads synthetic transaction CSV data into the financial tables. |
| `backend/app/services/reconciliation` | Matches payments to settlements, persists results, creates exceptions, evidence, and analytics. |
| `backend/app/ai` | Generates an AI-assisted investigation when configured; otherwise returns a deterministic fallback. |
| PostgreSQL | Stores financial records, reconciliation results, exceptions, evidence, human reviews, investigations, and audit logs. |

## Workflow

```text
CSV transactions
  -> ingestion
  -> payment and settlement records
  -> reconciliation run
  -> results and exceptions
  -> evidence + deterministic/AI investigation
  -> human review + audit log
```

The API is stateless. Every request opens a database session and closes it
after the response is produced. Review actions update the exception, create a
human-review row, and create an audit-log row in one database transaction.

See [API reference](api.md) for the HTTP contract and [the project README](../README.md)
for setup and the local workflow.
