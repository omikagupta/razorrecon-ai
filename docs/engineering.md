# RazorRecon AI — Security, Testing & Engineering Decisions

## Overview

RazorRecon AI is designed as a financial reconciliation and exception-investigation platform with a deterministic financial core and an optional AI reasoning layer.

Engineering priorities are:

1. Financial correctness
2. Deterministic behavior
3. Graceful AI failure
4. Auditability
5. Input validation
6. Reproducible deployments
7. Automated testing
8. Clear separation of responsibilities

The system deliberately avoids making an external LLM responsible for financial truth.

---

# Security

## Secret Management

Secrets and environment-specific configuration are not committed to source control.

The repository uses:

```text
.env
```

for local configuration and:

```text
.env.example
```

as the safe configuration template.

The `.gitignore` excludes:

```text
.env
.env.*
!.env.example
```

This prevents local credentials and provider keys from being accidentally committed while keeping the expected configuration structure documented.

AI provider credentials are supplied through environment variables rather than hard-coded in application source code.

---

## Environment Configuration

Application configuration is centralized through the settings layer.

Important configuration categories include:

* Application environment
* Database connection
* LLM provider
* LLM model
* AI provider credentials
* Log level
* CORS origins

The application validates environment-sensitive values before startup.

Supported application environments are:

```text
development
testing
production
```

Supported log levels are:

```text
DEBUG
INFO
WARNING
ERROR
CRITICAL
```

Invalid configuration values fail validation instead of silently falling back to unsafe behavior.

---

# CORS

Cross-Origin Resource Sharing is configured through environment-based allowed origins.

The default development configuration allows:

```text
http://localhost:5173
http://127.0.0.1:5173
```

The API does not rely on a wildcard origin configuration for the normal application setup.

Production deployments should provide an explicit frontend origin.

---

# Input Validation

FastAPI and Pydantic provide request validation at the API boundary.

Invalid request bodies result in the standard:

```text
422 Unprocessable Entity
```

Domain-level validation is additionally performed where business rules require it.

For example, human review requires:

* A non-empty reviewer
* A non-empty reason
* A supported review action
* An exception that is still in the `OPEN` state

This creates two validation layers:

```text
Request Schema Validation
          ↓
Domain Validation
          ↓
Business Operation
```

---

# State Transition Protection

Exception reviews are state-aware.

A human review can only be performed while an exception is `OPEN`.

If another operation has already changed the exception state, the API returns:

```text
409 Conflict
```

This prevents invalid state transitions such as attempting to approve an already resolved exception.

---

# Error Handling

The API uses centralized exception handling for:

* HTTP exceptions
* Request validation errors
* Unexpected application exceptions

Application errors expose structured information rather than raw internal stack traces.

Domain errors use stable error codes together with human-readable messages.

This provides clients with predictable error handling while avoiding unnecessary internal implementation details.

---

# Database Security

The application uses PostgreSQL through SQLAlchemy.

Database credentials are supplied through environment configuration rather than source code.

The Docker deployment uses a dedicated application database user instead of relying on an arbitrary default database identity.

Production deployments should additionally use:

* Strong database credentials
* Restricted database network access
* TLS where required
* Least-privilege database permissions
* Managed secret storage

---

# AI Security Boundary

The AI layer is intentionally constrained.

The LLM is not authoritative for:

* Monetary totals
* Transaction matching
* Settlement existence
* Refund existence
* Fee calculations
* Adjustment calculations
* Exception classification
* Database identifiers
* Evidence identifiers

Instead, deterministic application logic establishes financial truth before AI analysis occurs.

The architecture is:

```text
Financial Records
       ↓
Deterministic Reconciliation
       ↓
Exception + Evidence
       ↓
AI Investigation
```

This reduces the impact of hallucinated or incorrect model output.

---

# AI Output Validation

AI output is validated before being treated as a successful investigation result.

A provider response that cannot be validated is represented as:

```text
ai_provider_status = INVALID_RESPONSE
```

The system can then fall back to deterministic investigation.

This prevents malformed model responses from silently entering the operational workflow.

---

# AI Availability and Failure Isolation

AI is an optional dependency.

When an AI provider is unavailable:

```text
AI Provider
     X
     ↓
Deterministic Investigation
     ↓
Persist Investigation
     ↓
Return Usable Result
```

The reconciliation system therefore does not become unavailable merely because an external LLM provider is unavailable.

This is a deliberate reliability boundary.

---

# Testing Strategy

The project uses `pytest` for automated backend testing.

The test suite currently contains:

```text
185 tests
```

The full suite has been verified successfully.

Latest recorded result:

```text
185 passed
```

Testing covers multiple architectural layers rather than only endpoint happy paths.

---

# Test Categories

## API Tests

API tests verify:

* HTTP status codes
* Response structure
* Validation behavior
* Not-found behavior
* Conflict behavior
* Dashboard responses
* Exception endpoints
* Investigation endpoints
* Human review endpoints

---

## Reconciliation Tests

The reconciliation engine is tested for:

* Successful matches
* Amount mismatches
* Missing settlements
* Match confidence
* Result persistence
* Exception creation
* Evidence generation

The deterministic reconciliation layer is particularly important because it establishes the financial state consumed by downstream AI functionality.

---

# Financial Invariant Tests

Financial invariants are explicitly tested.

For normal reconciliation:

```text
difference = expected_amount - actual_amount
```

For a missing settlement:

```text
actual_amount = NULL
difference = expected_amount
```

Example:

```text
expected_amount = 100.00
actual_amount   = NULL
difference      = 100.00
```

The test suite verifies this behavior rather than treating a missing settlement as an ordinary zero-valued settlement.

This protects dashboard financial exposure calculations from silently under-reporting discrepancies.

---

# AI Investigation Tests

AI investigation tests verify:

* Deterministic analysis is always available
* AI-assisted mode works when a valid provider response exists
* AI output is validated
* AI failures do not break investigation
* Deterministic fallback is returned when required
* Investigation state is persisted
* Provider status is correctly recorded
* Fallback reasons are retained

The AI tests therefore verify both the successful path and the failure path.

---

# Human Review Tests

Human review tests verify:

* Valid approvals
* Valid rejections
* Valid escalations
* Case-insensitive actions
* Empty reviewer rejection
* Empty reason rejection
* Unknown exception handling
* Closed exception conflict handling
* Exception state transitions
* Audit-log creation

This ensures that human decisions cannot bypass domain state rules.

---

# Database and Migration Testing

Database behavior is tested against PostgreSQL rather than relying exclusively on mocked persistence.

Alembic migrations are part of the deployment path.

The current migration head is:

```text
c451329fa386
```

The migration chain currently includes:

```text
f91af069443f
        ↓
c451329fa386
```

The backend container executes:

```text
alembic upgrade head
```

before starting Uvicorn.

This keeps application startup aligned with the expected schema version.

---

# Testing Environment

Testing uses a dedicated application environment:

```text
APP_ENV=testing
```

The test database configuration uses PostgreSQL.

The AI provider is disabled for deterministic test execution:

```text
LLM_PROVIDER=none
```

This ensures the test suite does not depend on:

* Internet connectivity
* External AI provider availability
* AI provider latency
* AI provider quotas
* Provider response nondeterminism

---

# Test Reproducibility

The intended test command is:

```powershell
$env:DATABASE_URL="postgresql+psycopg2://razorrecon:razorrecon@localhost:5433/razorrecon"
$env:APP_ENV="testing"
$env:LLM_PROVIDER="none"
python -m pytest
```

The test environment therefore uses deterministic configuration and a controlled database.

---

# Regression Testing

Regression tests are especially important for financial invariants.

A previously identified persistence issue caused missing settlements to retain:

```text
difference = NULL
```

even though the expected amount was known.

The correct behavior is:

```text
difference = expected_amount
```

when:

```text
actual_amount = NULL
```

The regression test was strengthened to explicitly assert:

```text
expected_amount = 100
actual_amount = NULL
difference = 100
```

This prevents the same financial exposure bug from returning unnoticed.

---

# Reliability

## Deterministic Financial Core

The financial reconciliation engine does not depend on AI.

This means:

```text
LLM unavailable
       ↓
Reconciliation still works
```

---

## Health Checks

The API provides separate operational endpoints:

```text
/health
/health/live
/health/ready
```

The distinction allows infrastructure to distinguish between:

* Process liveness
* Application/database readiness
* Overall health state

---

## Docker Health

PostgreSQL includes a Docker health check.

The backend waits for PostgreSQL readiness before starting.

The frontend depends on backend startup.

This establishes the intended startup sequence:

```text
PostgreSQL
    ↓
Backend
    ↓
Frontend
```

---

# Observability

The backend includes request logging middleware.

Operational logging records request-level information while centralized exception handling prevents unexpected failures from becoming silent errors.

Important operational signals include:

* Request method
* Request path
* Response status
* Request processing
* Application exceptions
* Database health
* AI provider state
* Investigation mode

The architecture intentionally exposes AI provider state and investigation mode so operators can distinguish successful AI augmentation from deterministic fallback.

---

# Engineering Decisions

## Why FastAPI?

FastAPI was selected because it provides:

* Typed request and response models
* Automatic OpenAPI documentation
* Strong validation
* Async-compatible architecture
* Clear API routing
* Good integration with Python data and AI tooling

It also makes the API contract visible through `/docs` and `/openapi.json`.

---

## Why PostgreSQL?

PostgreSQL was selected because the project requires:

* Transactional persistence
* Exact decimal financial values
* Structured relational data
* Reliable querying
* Production-grade durability
* Migration support

Financial amounts are stored using `NUMERIC(18,2)`.

---

## Why SQLAlchemy?

SQLAlchemy provides:

* Typed ORM models
* Database abstraction
* Explicit persistence logic
* PostgreSQL compatibility
* Integration with Alembic

It separates database representation from business-service logic.

---

## Why Alembic?

Database schema changes need to be reproducible.

Alembic provides:

* Version-controlled migrations
* Upgrade paths
* Deployment-time schema management
* Migration history

This is preferable to manually modifying production databases.

---

## Why React + Vite?

The frontend requires a responsive operational dashboard with API-driven data.

React provides component-based UI architecture while Vite provides a fast development and production build workflow.

---

## Why Docker?

Docker provides reproducible environments across development and deployment.

The stack can be represented as:

```text
Frontend
   │
   ▼
Backend
   │
   ▼
PostgreSQL
```

Docker Compose provides local orchestration of these services.

---

# Architecture Decision: Deterministic First

This is the most important engineering decision in the project.

A naive architecture could be:

```text
Transaction
    ↓
LLM
    ↓
"Is this suspicious?"
```

RazorRecon AI instead uses:

```text
Transaction
    ↓
Deterministic Reconciliation
    ↓
Exception
    ↓
Evidence
    ↓
Deterministic Analysis
    ↓
Optional AI Investigation
    ↓
Human Review
```

The advantage is that financial correctness does not depend on probabilistic model behavior.

---

# Architecture Decision: AI as an Investigator

AI is treated as an investigator rather than an accountant.

The deterministic layer answers:

> What discrepancy occurred?

The AI layer helps answer:

> Why might this discrepancy have occurred?

and:

> What should an investigator examine next?

This separation makes the system easier to test, reason about, and audit.

---

# Architecture Decision: Persist Investigation History

Investigations are stored as separate records rather than replacing previous analysis.

This supports:

* Investigation history
* Repeated investigation
* AI-provider comparison
* Fallback tracking
* Future model evaluation

An exception can therefore have multiple investigation records.

---

# Architecture Decision: Application-Level Relationships

The current SQLAlchemy models use application-level identifier relationships rather than explicit SQLAlchemy `ForeignKey` constraints.

This is useful for the current reconciliation model because the system works with financial identifiers originating from external systems.

The trade-off is that referential integrity must be maintained by application logic.

A future production implementation could introduce stronger database-level constraints where appropriate.

---

# Architecture Decision: Decimal Financial Types

Floating-point arithmetic is inappropriate for financial totals.

The system therefore uses:

```text
NUMERIC(18,2)
```

for monetary values.

This makes persisted financial calculations exact to the required precision.

---

# Engineering Trade-offs

The current implementation prioritizes correctness, explainability, and a strong deterministic foundation within a focused project scope.

Some production-scale capabilities remain future work.

These include:

* Full authentication and authorization
* Role-based access control
* Rate limiting
* Idempotency keys
* Distributed job processing
* Large-scale asynchronous reconciliation
* Stronger database constraints
* Source-system lineage
* Encryption/key-management integration
* Advanced observability
* Metrics and tracing infrastructure
* Production secret-management integration
* Expanded AI evaluation and model governance

These limitations are explicit rather than hidden.

---

# Security and Reliability Checklist

| Area                           | Current State |
| ------------------------------ | ------------- |
| Secrets outside source control | ✅             |
| `.env.example` provided        | ✅             |
| Environment validation         | ✅             |
| Explicit CORS origins          | ✅             |
| Request validation             | ✅             |
| Centralized error handling     | ✅             |
| Database health checks         | ✅             |
| Liveness endpoint              | ✅             |
| Readiness endpoint             | ✅             |
| AI fallback                    | ✅             |
| AI output validation           | ✅             |
| Deterministic reconciliation   | ✅             |
| Financial invariant tests      | ✅             |
| Human-review state protection  | ✅             |
| Audit logging                  | ✅             |
| PostgreSQL persistence         | ✅             |
| Alembic migrations             | ✅             |
| Dockerized deployment          | ✅             |
| Automated test suite           | ✅             |

---

# Current Verification Baseline

The current project verification baseline is:

```text
Backend tests:       185 passed
Database:            PostgreSQL
Migration head:      c451329fa386
AI test mode:        Disabled / deterministic
Containerization:    Docker Compose
Frontend build:      Production build verified
Git working tree:    Expected to remain clean after committed changes
```

---

# Engineering Principle

The system is built around a simple reliability hierarchy:

```text
                    Human Review
                         ▲
                         │
                   AI Investigation
                         ▲
                         │
                    Evidence
                         ▲
                         │
                   Exception
                         ▲
                         │
             Deterministic Reconciliation
                         ▲
                         │
                  Financial Records
```

Each higher layer consumes information established by the layer below it.

The AI layer therefore cannot silently redefine financial truth.

---

# Summary

RazorRecon AI prioritizes deterministic financial correctness, graceful AI failure, testability, auditability, and operational reliability.

The central engineering principle is:

> **Financial truth must remain deterministic, explainable, testable, and independent of probabilistic AI output.**

AI adds investigative value without becoming a single point of failure for the reconciliation system.
