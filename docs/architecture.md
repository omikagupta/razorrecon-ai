# RazorRecon AI — Architecture

## 1. Overview

RazorRecon AI is a backend-driven financial reconciliation and exception-investigation platform.

The system compares payment records against settlement records, identifies reconciliation outcomes, creates structured exceptions for discrepancies, collects supporting evidence, and optionally uses an LLM to assist with investigation.

The architecture deliberately separates **deterministic financial computation** from **AI-assisted interpretation**.

```text
                    RazorRecon AI
                         │
             ┌───────────┴───────────┐
             │                       │
        React Frontend           FastAPI Backend
             │                       │
             │              ┌────────┴────────┐
             │              │                 │
             │        Reconciliation      Exception /
             │             Engine          Investigation
             │              │                 │
             │              └────────┬────────┘
             │                       │
             └──────────────► PostgreSQL
                                     │
                              Financial Records
                              Reconciliation Results
                              Exceptions
                              Evidence
                              Investigations
                              Human Reviews
                              Audit Logs
```

The production-oriented deployment runs the frontend, backend, and PostgreSQL as separate services using Docker Compose.

---

# 2. Architectural Principles

RazorRecon AI follows several core engineering principles.

### 2.1 Deterministic financial truth

Financial calculations are performed by application logic rather than an LLM.

The reconciliation engine is responsible for:

* transaction matching
* amount comparisons
* settlement detection
* reconciliation status
* monetary differences
* exception creation
* evidence generation
* financial aggregation

The AI layer does **not** determine monetary truth.

---

### 2.2 AI as an investigation assistant

The LLM is used only after deterministic reconciliation has established the underlying facts.

The AI can help with:

* interpreting evidence
* explaining discrepancies
* identifying likely root causes
* assessing operational risk
* generating investigation summaries
* recommending next actions

If the configured AI provider is unavailable or produces an invalid response, the system falls back to deterministic investigation.

---

### 2.3 Evidence before explanation

An investigation is constructed from persisted financial evidence.

The system does not allow the AI layer to invent:

* transaction IDs
* settlement IDs
* amounts
* fees
* refunds
* adjustment records
* database facts

This keeps the AI layer grounded in the reconciliation data.

---

### 2.4 Stateless API

The FastAPI application is stateless.

Application state is persisted in PostgreSQL rather than held inside individual API processes.

This allows backend instances to be restarted or scaled independently from the database.

---

### 2.5 Auditable operations

Human review operations produce persistent records.

A review action can update:

```text
Exception
    │
    ├── HumanReview
    │
    └── AuditLog
```

These records provide an operational history of how an exception was handled.

---

# 3. High-Level System Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│                        Client Layer                         │
│                                                             │
│              React + Vite + Tailwind CSS                   │
│                                                             │
│       Dashboard │ Exceptions │ Investigations │ Review     │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTP / JSON
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                       API Layer                             │
│                                                             │
│                         FastAPI                             │
│                                                             │
│  ┌─────────────┐ ┌────────────┐ ┌────────────────────────┐ │
│  │ Dashboard   │ │ Exceptions │ │ Reconciliation Runs    │ │
│  │ API         │ │ API        │ │ API                    │ │
│  └─────────────┘ └────────────┘ └────────────────────────┘ │
│                                                             │
│             Health │ Readiness │ Error Handling             │
│                         │                                   │
│                  Request Logging                             │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                     Service Layer                           │
│                                                             │
│  ┌───────────────────┐     ┌─────────────────────────────┐ │
│  │ Ingestion         │     │ Reconciliation              │ │
│  │ Service           │────►│ Service                     │ │
│  └───────────────────┘     └──────────────┬──────────────┘ │
│                                           │                 │
│                                           ▼                 │
│                               ┌───────────────────────────┐ │
│                               │ Exception Intelligence   │ │
│                               └─────────────┬─────────────┘ │
│                                             │               │
│                                             ▼               │
│                               ┌───────────────────────────┐ │
│                               │ Evidence + Investigation │ │
│                               └─────────────┬─────────────┘ │
└─────────────────────────────────────────────┼───────────────┘
                                              │
                          ┌───────────────────┴────────────────┐
                          │                                    │
                          ▼                                    ▼
                 ┌──────────────────┐                ┌─────────────────┐
                 │   AI Provider    │                │   PostgreSQL    │
                 │                  │                │                 │
                 │ Optional LLM     │                │ Financial data  │
                 │ Investigation    │                │ Reconciliation  │
                 │                  │                │ Exceptions      │
                 └──────────────────┘                │ Evidence        │
                                                     │ Investigations  │
                                                     │ Reviews         │
                                                     │ Audit logs      │
                                                     └─────────────────┘
```

---

# 4. Backend Architecture

The backend is organized into API, service, AI, persistence, database, configuration, and cross-cutting infrastructure layers.

```text
backend/app/
│
├── api/
│   └── v1/
│       ├── dashboard.py
│       ├── exceptions.py
│       └── reconciliation_runs.py
│
├── ai/
│   └── investigation/
│
├── core/
│   ├── config.py
│   ├── error_handlers.py
│   └── request_logging.py
│
├── db/
│   ├── base.py
│   └── session.py
│
├── models/
│   ├── financial.py
│   └── reconciliation.py
│
├── repositories/
│
├── schemas/
│
├── services/
│   ├── ingestion/
│   └── reconciliation/
│
└── main.py
```

### API Layer

Responsible for:

* HTTP routing
* request validation
* response serialization
* dependency management
* exposing application capabilities

The API layer does not contain the core reconciliation algorithm.

---

### Service Layer

The service layer contains the business logic.

Important responsibilities include:

* ingestion
* transaction matching
* reconciliation
* exception generation
* evidence creation
* investigation orchestration
* review processing

This separation keeps business rules independent from HTTP transport.

---

### Database Layer

SQLAlchemy is used for database access.

The database layer provides:

* engine configuration
* session management
* ORM models
* transaction boundaries

Alembic manages schema migrations.

---

### Core Infrastructure

Cross-cutting backend behavior includes:

* application configuration
* environment validation
* centralized exception handling
* request logging
* CORS configuration
* health endpoints

---

# 5. Reconciliation Architecture

The reconciliation engine is the financial core of RazorRecon AI.

The processing pipeline is:

```text
Input Financial Data
        │
        ▼
   Normalization
        │
        ▼
 Transaction Matching
        │
        ▼
 Deterministic Comparison
        │
        ├───────────────┐
        │               │
        ▼               ▼
    MATCHED      AMOUNT_MISMATCH
        │               │
        │               │
        └───────┬───────┘
                │
                ▼
       Missing Settlement?
                │
          ┌─────┴─────┐
          │           │
         No          Yes
          │           │
          ▼           ▼
     Reconciliation  MISSING_SETTLEMENT
        Result             │
                           ▼
                     Exception
```

The current reconciliation outcomes are:

| Status               | Meaning                                                                          |
| -------------------- | -------------------------------------------------------------------------------- |
| `MATCHED`            | Payment has a corresponding settlement with the expected financial relationship. |
| `AMOUNT_MISMATCH`    | A settlement exists but the expected and actual amounts differ.                  |
| `MISSING_SETTLEMENT` | No corresponding settlement was found.                                           |

---

# 6. Financial Invariants

Financial correctness is treated as a first-class requirement.

For reconciliation results:

```text
difference = expected_amount - actual_amount
```

For a missing settlement:

```text
actual_amount = 0
difference = expected_amount
```

This ensures missing settlements contribute correctly to aggregate financial exposure.

The dashboard therefore maintains the invariant:

```text
total_difference
=
total_expected_amount
-
total_actual_settlement
```

These calculations are performed deterministically and are not delegated to an LLM.

---

# 7. Exception Intelligence

Exceptions are generated from reconciliation results.

```text
Reconciliation Result
          │
          ▼
   Exception Detection
          │
          ▼
      Exception
          │
          ├──────────────┐
          │              │
          ▼              ▼
      Evidence      Investigation
          │              │
          │       ┌──────┴──────┐
          │       │             │
          │       ▼             ▼
          │   AI Assisted   Deterministic
          │                  Fallback
          │       │             │
          └───────┴──────┬──────┘
                         ▼
                  Investigation
                         │
                         ▼
                    Human Review
                         │
                         ▼
                     Audit Log
```

This architecture separates:

1. detection of a financial anomaly
2. collection of evidence
3. interpretation of evidence
4. human decision-making
5. auditability

---

# 8. AI Investigation Architecture

The AI subsystem is intentionally downstream of deterministic reconciliation.

```text
                    Exception
                        │
                        ▼
                 Evidence Builder
                        │
                        ▼
              Deterministic Analysis
                        │
                        ▼
               Investigation Context
                        │
                        ▼
                 AI Provider Check
                   /           \
                  /             \
            Available          Unavailable
                │                   │
                ▼                   ▼
          LLM Investigation    Deterministic
                │               Fallback
                │                   │
                └─────────┬─────────┘
                          ▼
                   Final Investigation
                          │
                          ▼
                    Persist Result
```

### AI success path

When the configured provider is available:

```text
Exception
   ↓
Evidence
   ↓
Prompt / Investigation Context
   ↓
LLM
   ↓
Structured AI Response
   ↓
Validation
   ↓
Persist Investigation
```

### Fallback path

If the provider is unavailable or the response cannot be validated:

```text
AI Failure
    ↓
Capture Fallback Reason
    ↓
Deterministic Analysis
    ↓
Persist Investigation
    ↓
investigation_mode = DETERMINISTIC_FALLBACK
```

This ensures AI availability does not determine whether the core reconciliation platform remains operational.

---

# 9. AI Responsibility Boundary

The following responsibilities remain deterministic:

| Responsibility       | Owner                  |
| -------------------- | ---------------------- |
| Transaction matching | Reconciliation engine  |
| Monetary arithmetic  | Reconciliation engine  |
| Financial totals     | Database/service layer |
| Exception creation   | Reconciliation engine  |
| Evidence creation    | Application logic      |
| Database truth       | PostgreSQL             |
| IDs and references   | Application/database   |
| Final human decision | Human reviewer         |

The AI layer is responsible for:

| Responsibility          | Owner |
| ----------------------- | ----- |
| Evidence interpretation | AI    |
| Discrepancy explanation | AI    |
| Root-cause hypothesis   | AI    |
| Risk interpretation     | AI    |
| Investigation summary   | AI    |
| Recommended next action | AI    |

This boundary reduces the risk of hallucinated financial facts.

---

# 10. Persistence Architecture

PostgreSQL is the system of record.

The major persistence domains are:

```text
Financial Domain
├── Merchant
├── Order
├── Payment
├── Settlement
├── Refund
├── Fee
└── Adjustment

Reconciliation Domain
├── ReconciliationRun
├── ReconciliationResult
├── ExceptionRecord
├── Evidence
├── Investigation
├── HumanReview
└── AuditLog
```

The database stores both the original financial records and the derived reconciliation/investigation state.

This makes the investigation reproducible from persisted evidence.

---

# 11. Investigation Persistence

An investigation contains deterministic and optional AI analysis.

Conceptually:

```text
Investigation
├── investigation_id
├── exception_id
├── investigation_mode
├── ai_provider_status
├── evidence_count
├── deterministic_analysis
├── ai_analysis
├── fallback_reason
└── created_at
```

Possible investigation modes include:

```text
AI_ASSISTED
DETERMINISTIC_FALLBACK
```

Possible provider states include:

```text
SUCCESS
UNAVAILABLE
INVALID_RESPONSE
```

---

# 12. Human Review and Auditability

AI does not directly resolve financial exceptions.

The operational workflow is:

```text
Exception
    │
    ▼
Investigation
    │
    ▼
Human Review
    │
    ├── Resolve
    ├── Escalate
    └── Keep Open
    │
    ▼
Audit Log
```

A review operation is persisted together with an audit record.

This provides traceability for:

* who performed the review
* what decision was made
* when the action occurred
* why the action occurred

---

# 13. API Architecture

The API is versioned under:

```text
/api/v1
```

Current API areas include:

```text
/api/v1
/api/v1/health
/api/v1/health/live
/api/v1/health/ready

Dashboard
Exceptions
Reconciliation Runs
Investigations
Human Review
```

The detailed HTTP contract is maintained separately in:

```text
docs/api.md
```

---

# 14. Health and Reliability Architecture

The backend exposes multiple health levels.

### Liveness

```text
GET /api/v1/health/live
```

Confirms that the application process is running.

### Readiness

```text
GET /api/v1/health/ready
```

Checks application readiness and database connectivity.

### Health

```text
GET /api/v1/health
```

Provides service and database health information.

This distinction is useful for container orchestration and production deployments.

---

# 15. Error Handling

FastAPI uses centralized exception handlers for:

* HTTP exceptions
* request validation errors
* unexpected application exceptions

The goal is to provide consistent API responses rather than exposing raw internal errors.

Conceptually:

```text
Request
   │
   ▼
FastAPI Router
   │
   ▼
Validation
   │
   ├── Invalid ──► Validation Handler
   │
   ▼
Business Logic
   │
   ├── HTTP Error ──► HTTP Handler
   │
   ├── Unexpected Error ──► Global Error Handler
   │
   ▼
Response
```

---

# 16. Request Observability

The backend includes request logging middleware.

The middleware provides visibility into API activity without coupling logging to individual route implementations.

The architecture is:

```text
HTTP Request
     │
     ▼
Request Logging Middleware
     │
     ▼
FastAPI Application
     │
     ▼
Endpoint
     │
     ▼
HTTP Response
     │
     ▼
Request Logging Middleware
```

This provides a foundation for future metrics, tracing, and centralized log aggregation.

---

# 17. Frontend Architecture

The frontend is a React/Vite application using Tailwind CSS.

Its primary responsibility is presentation and interaction.

```text
React Frontend
      │
      ├── Dashboard
      │
      ├── Exception Management
      │
      ├── Investigation View
      │
      └── Human Review
             │
             ▼
        FastAPI REST API
```

The frontend does not independently calculate financial truth.

Dashboard financial metrics originate from backend API responses.

---

# 18. Docker Architecture

The production-oriented local deployment uses three services:

```text
┌──────────────────────────────────────────┐
│              Docker Compose              │
│                                          │
│  ┌─────────────┐                         │
│  │ PostgreSQL  │                         │
│  │     :5432   │                         │
│  └──────┬──────┘                         │
│         │                                │
│         ▼                                │
│  ┌─────────────┐                         │
│  │   Backend   │                         │
│  │     :8000   │                         │
│  └──────┬──────┘                         │
│         │                                │
│         ▼                                │
│  ┌─────────────┐                         │
│  │  Frontend   │                         │
│  │     :80     │                         │
│  └─────────────┘                         │
│                                          │
└──────────────────────────────────────────┘
```

External development ports are currently:

```text
PostgreSQL → localhost:5432
Backend    → localhost:8000
Frontend   → localhost:5173
```

The frontend container serves the compiled React application through Nginx.

The backend container:

1. starts from a Python runtime image
2. installs backend dependencies
3. runs Alembic migrations
4. starts Uvicorn

---

# 19. Database Migration Architecture

Alembic manages schema evolution.

Startup flow:

```text
Backend Container
       │
       ▼
alembic upgrade head
       │
       ▼
Database Schema
       │
       ▼
Uvicorn
       │
       ▼
FastAPI
```

This ensures the database schema is brought to the expected migration head before the application begins serving requests.

Current migration history includes:

```text
f91af069443f
      │
      ▼
c451329fa386
      │
      ▼
HEAD
```

---

# 20. Configuration Architecture

Configuration is environment-driven.

The application reads settings such as:

```text
APP_ENV
DATABASE_URL
LLM_PROVIDER
LLM_MODEL
GEMINI_API_KEY
LOG_LEVEL
CORS_ORIGINS
```

Secrets are not committed to Git.

The repository provides:

```text
.env.example
```

while local secrets remain in:

```text
.env
```

The `.gitignore` configuration prevents local environment files from being committed.

---

# 21. Security Boundaries

The current architecture includes several baseline security controls:

* environment-based secret management
* `.env` exclusion from Git
* CORS configuration
* request validation through Pydantic/FastAPI
* centralized error handling
* database isolation through Docker
* non-hardcoded database configuration
* AI fallback when external AI services fail

Future production hardening can add:

* authentication and authorization
* role-based access control
* API rate limiting
* secret manager integration
* encryption at rest
* encryption in transit
* structured security auditing
* stronger database permissions

---

# 22. Testing Architecture

The project uses pytest for automated backend testing.

The test suite covers multiple layers, including:

```text
API Tests
    │
    ├── Health
    ├── Dashboard
    ├── Exceptions
    └── Reconciliation Runs

Service Tests
    │
    ├── Ingestion
    ├── Reconciliation
    └── Investigation

Persistence Tests
    │
    ├── Financial results
    ├── Exceptions
    └── Reviews

AI Tests
    │
    ├── Successful provider
    ├── Provider unavailable
    └── Invalid response / fallback
```

The current verified test suite contains **185 passing tests**.

---

# 23. Reliability Strategy

RazorRecon AI is designed so that individual subsystems can fail without corrupting the financial reconciliation process.

### AI provider failure

```text
AI unavailable
      ↓
Deterministic fallback
      ↓
Investigation still produced
```

### Database failure

```text
Database unavailable
      ↓
Health/readiness reports degraded
      ↓
Application does not report false database health
```

### Invalid API input

```text
Invalid request
      ↓
Pydantic/FastAPI validation
      ↓
Structured validation error
```

### Unexpected application failure

```text
Unexpected exception
      ↓
Centralized error handler
      ↓
Controlled API response
```

---

# 24. Deployment Topology

The current deployment topology is intentionally simple and reproducible.

```text
                         Developer / User
                                │
                                ▼
                       ┌─────────────────┐
                       │ React + Nginx   │
                       │ Frontend :5173  │
                       └────────┬────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │ FastAPI/Uvicorn │
                       │ Backend :8000   │
                       └────────┬────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   PostgreSQL    │
                       │      :5432      │
                       └─────────────────┘
```

Optional external dependency:

```text
FastAPI
   │
   ▼
LLM Provider
```

The LLM is not required for deterministic reconciliation.

---

# 25. Architectural Trade-offs

## PostgreSQL instead of a document database

Financial reconciliation requires:

* transactional consistency
* relational relationships
* aggregation
* constraints
* predictable querying

PostgreSQL is therefore a natural fit.

---

## Deterministic reconciliation before AI

A purely LLM-driven reconciliation system would introduce unnecessary uncertainty into financial calculations.

The selected architecture instead uses:

```text
Deterministic computation
          +
AI interpretation
```

This provides the benefits of AI while preserving financial correctness.

---

## Docker Compose instead of Kubernetes

The project is currently designed for a reproducible internship/demo deployment.

Docker Compose provides:

* service isolation
* reproducible startup
* database persistence
* environment configuration
* straightforward local deployment

Kubernetes can be introduced later when operational scale requires it.

---

# 26. Current Architecture Boundaries

The current system is a demonstration/portfolio platform using synthetic financial data.

It is **not connected to live payment-provider or banking infrastructure**.

Production deployment would require additional controls around:

* authentication
* authorization
* PCI/security requirements
* sensitive financial-data handling
* secret management
* observability
* high availability
* backup and disaster recovery
* distributed job processing
* rate limiting
* compliance requirements

These are intentionally treated as future production extensions rather than being falsely represented as already implemented.

---

# 27. Future Architecture Evolution

A production-scale version could evolve toward:

```text
                    API Gateway
                         │
              ┌──────────┴──────────┐
              │                     │
         Frontend               Auth Service
              │
              ▼
       Reconciliation API
              │
       ┌──────┴──────┐
       │             │
       ▼             ▼
 Reconciliation   Investigation
     Worker          Worker
       │             │
       └──────┬──────┘
              ▼
            Redis
              │
              ▼
          PostgreSQL
              │
              ▼
        Object Storage
```

Potential additions include:

* asynchronous reconciliation jobs
* Redis-backed task queues
* object storage for large evidence files
* vector search for historical investigations
* model evaluation pipelines
* distributed tracing
* metrics collection
* role-based access control
* Kubernetes deployment
* automated CI/CD

---

# 28. Summary

The RazorRecon AI architecture is built around one central principle:

> **Financial truth is deterministic; AI assists with investigation and interpretation.**

The complete logical flow is:

```text
Financial Data
      │
      ▼
   Ingestion
      │
      ▼
Normalization
      │
      ▼
Transaction Matching
      │
      ▼
Deterministic Reconciliation
      │
      ▼
Exception Detection
      │
      ▼
Evidence Collection
      │
      ▼
AI Investigation
      │
      ├── AI Success
      │
      └── Deterministic Fallback
      │
      ▼
Human Review
      │
      ▼
Audit Trail
      │
      ▼
Dashboard / Reporting
```

This separation provides a foundation for a reliable, explainable, auditable financial reconciliation system while still allowing AI to improve the investigation workflow.
