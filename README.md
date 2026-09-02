# RazorRecon AI

### AI Finance Controller for Merchant Payment Reconciliation

RazorRecon AI is an AI-assisted financial reconciliation platform designed to help finance and operations teams identify, investigate, and resolve discrepancies between merchant payment records and settlement records.

The system combines **deterministic financial reconciliation**, **exception intelligence**, **evidence-based AI investigation**, **human review**, and **audit logging** into a single workflow.

> **Important:** All financial data used in this project is synthetic/demo data. RazorRecon AI is an engineering prototype and is not connected to live Razorpay or banking systems.

---

## Table of Contents

* [Overview](#overview)
* [Problem Statement](#problem-statement)
* [Solution](#solution)
* [Key Features](#key-features)
* [System Architecture](#system-architecture)
* [Reconciliation Pipeline](#reconciliation-pipeline)
* [AI Investigation Architecture](#ai-investigation-architecture)
* [Safety Boundaries for AI](#safety-boundaries-for-ai)
* [Exception Intelligence](#exception-intelligence)
* [Human Review and Auditability](#human-review-and-auditability)
* [Current Demo Dataset](#current-demo-dataset)
* [Technology Stack](#technology-stack)
* [Project Structure](#project-structure)
* [API Overview](#api-overview)
* [Database Architecture](#database-architecture)
* [Running Locally](#running-locally)
* [Running with Docker](#running-with-docker)
* [Environment Variables](#environment-variables)
* [Testing](#testing)
* [Reliability and Failure Handling](#reliability-and-failure-handling)
* [Security](#security)
* [Observability](#observability)
* [Engineering Decisions](#engineering-decisions)
* [Current Limitations](#current-limitations)
* [Future Improvements](#future-improvements)
* [Demo Workflow](#demo-workflow)
* [Project Status](#project-status)
* [License](#license)

---

# Overview

Financial reconciliation is the process of determining whether financial transactions recorded by different systems agree with each other.

For a payment platform, a single merchant transaction can involve multiple financial entities:

```text
Order
  ↓
Payment
  ↓
Fees / Taxes
  ↓
Refunds / Adjustments
  ↓
Expected Settlement
  ↓
Actual Settlement
```

When these records do not agree, finance teams need to determine:

1. Which records belong together?
2. Was the correct amount settled?
3. Why does a discrepancy exist?
4. Is the discrepancy legitimate?
5. What evidence supports the explanation?
6. Can the issue safely be resolved?
7. Does it require human review?

RazorRecon AI automates this workflow while keeping **financial calculations deterministic and auditable**.

---

# Problem Statement

Traditional reconciliation workflows often rely heavily on spreadsheets, manual investigation, and disconnected operational systems.

This becomes difficult when transaction volumes increase and discrepancies can originate from multiple sources:

* payment amount differences
* missing settlements
* processing fees
* refunds
* adjustments
* duplicate records
* settlement timing differences
* inconsistent transaction information

A reconciliation system therefore needs more than simple record matching.

It needs:

```text
Matching
   +
Financial calculation
   +
Exception classification
   +
Evidence
   +
Investigation
   +
Decision support
   +
Auditability
```

RazorRecon AI is designed around this complete workflow.

---

# Solution

RazorRecon AI processes financial records through a layered pipeline:

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
Evidence Collection
       ↓
AI Investigation
       ↓
Risk / Confidence Assessment
       ↓
Policy-Based Decision
       ↓
Human Review or Resolution
       ↓
Audit Trail
       ↓
Finance Dashboard
```

The architecture intentionally separates **financial correctness** from **AI reasoning**.

---

# Key Features

## 1. Deterministic Reconciliation

The reconciliation engine compares expected financial outcomes with actual settlement records.

Financial calculations use deterministic application logic rather than an LLM.

This ensures:

* reproducibility
* consistency
* auditability
* predictable behavior

---

## 2. Transaction Matching

The system identifies corresponding financial records and produces reconciliation results.

Supported outcomes include:

```text
MATCHED
AMOUNT_MISMATCH
MISSING_SETTLEMENT
```

---

## 3. Exception Intelligence

Discrepancies are converted into structured exceptions with information such as:

* exception ID
* transaction ID
* exception type
* severity
* status
* confidence
* description
* timestamps

Exceptions can be filtered by:

* status
* severity
* exception type

---

## 4. Evidence-Based Investigation

When an exception requires investigation, RazorRecon AI collects structured evidence related to the financial transaction.

The investigation layer can combine:

```text
Deterministic Analysis
        +
Financial Evidence
        +
Optional AI Reasoning
```

The result is returned in a structured format containing information such as:

* summary
* root cause
* risk level
* recommended action
* confidence
* key evidence
* unresolved questions

---

## 5. AI Fallback

AI is treated as an optional intelligence layer.

If the configured AI provider is unavailable or returns an invalid response, the system can fall back to deterministic analysis.

Therefore:

```text
AI failure
    ≠
Financial reconciliation failure
```

This is a deliberate reliability decision.

---

## 6. Human Review

Cases that should not be automatically resolved can be routed through a human review workflow.

Human decisions are represented explicitly rather than silently changing financial state.

---

## 7. Auditability

Important investigation and review actions are persisted so that the system can maintain an operational history of decisions.

---

## 8. Finance Dashboard

The frontend provides a finance-oriented dashboard for monitoring:

* transaction counts
* match rate
* reconciliation status
* financial differences
* exception counts
* exception severity
* resolution status

---

# System Architecture

```text
                    ┌───────────────────────┐
                    │      React UI         │
                    │  Finance Dashboard    │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │       FastAPI         │
                    │       REST API        │
                    └───────────┬───────────┘
                                │
              ┌─────────────────┼─────────────────┐
              │                 │                 │
              ▼                 ▼                 ▼
       ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
       │ Reconciliation│ │ Exception    │ │  Dashboard   │
       │    Engine    │ │ Intelligence │ │   Service    │
       └───────┬──────┘ └───────┬──────┘ └──────────────┘
               │                │
               ▼                ▼
       ┌──────────────┐ ┌──────────────┐
       │ Matching     │ │ Investigation│
       │ Logic        │ │ + Evidence   │
       └───────┬──────┘ └───────┬──────┘
               │                │
               └────────┬───────┘
                        ▼
              ┌─────────────────────┐
              │     PostgreSQL      │
              │                     │
              │ Financial Records   │
              │ Reconciliation      │
              │ Exceptions          │
              │ Evidence            │
              │ Investigations      │
              │ Human Reviews       │
              │ Audit Logs          │
              └─────────────────────┘
```

The application is containerized using Docker Compose.

---

# Reconciliation Pipeline

The reconciliation engine follows a deterministic workflow.

```text
Source Financial Records
          ↓
       Matching
          ↓
 Expected Amount
          ↓
 Actual Settlement
          ↓
     Comparison
          ↓
 ┌────────┼────────────┐
 ↓        ↓            ↓
MATCHED   MISMATCH     MISSING
                     SETTLEMENT
          ↓
      Exception
          ↓
 Evidence + Investigation
```

For missing settlements, the absence of an actual settlement represents a zero received amount for reconciliation purposes.

Therefore:

```text
difference = expected_amount
```

when an expected settlement exists but no actual settlement record exists.

This preserves the financial invariant:

```text
total_difference
=
total_expected_amount
-
total_actual_settlement
```

---

# AI Investigation Architecture

RazorRecon AI follows a **deterministic-first, AI-assisted** architecture.

```text
             Exception
                 │
                 ▼
       Deterministic Analysis
                 │
                 ├── Exception Type
                 ├── Amount Difference
                 ├── Transaction Context
                 └── Reconciliation Result
                 │
                 ▼
          Evidence Collection
                 │
                 ├── Payment
                 ├── Settlement
                 ├── Refund
                 ├── Fee
                 └── Adjustment
                 │
                 ▼
        Investigation Layer
                 │
          ┌──────┴──────┐
          ▼             ▼
       AI Success     AI Failure
          │             │
          ▼             ▼
     AI Analysis   Deterministic
                   Fallback
          │             │
          └──────┬──────┘
                 ▼
          Investigation
              Result
```

The API explicitly represents investigation modes such as:

```text
AI_ASSISTED
DETERMINISTIC_FALLBACK
```

and provider states such as:

```text
SUCCESS
UNAVAILABLE
INVALID_RESPONSE
```

This makes AI behavior observable instead of hiding it behind a generic response.

---

# Safety Boundaries for AI

A core architectural principle is:

> **The LLM should reason about financial evidence, not become the financial source of truth.**

## AI does NOT perform:

* monetary arithmetic
* settlement calculations
* financial totals
* transaction matching
* database truth determination
* creation of financial evidence
* invention of transaction IDs
* invention of fees
* invention of refunds
* invention of settlements

## AI MAY perform:

* evidence interpretation
* discrepancy explanation
* root-cause analysis
* risk interpretation
* investigation summarization
* recommended operational actions
* structured reasoning

This separation is especially important for financial systems where deterministic calculations need to remain reproducible.

---

# Exception Intelligence

Exceptions represent situations where reconciliation cannot be treated as a normal match.

Examples include:

```text
AMOUNT_MISMATCH
MISSING_SETTLEMENT
```

Each exception can contain:

```text
Exception ID
Transaction ID
Exception Type
Severity
Status
Confidence
Description
Created At
Resolved At
```

The dashboard uses these records to provide operational visibility into unresolved financial discrepancies.

---

# Human Review and Auditability

AI should not automatically make every operational decision.

The system therefore supports a human review layer for cases requiring additional judgment.

Conceptually:

```text
Exception
   ↓
Investigation
   ↓
Risk / Confidence
   ↓
Policy
   │
   ├── Safe → Resolution
   │
   └── Uncertain / Sensitive
              ↓
        Human Review
              ↓
        Final Decision
              ↓
         Audit Log
```

This provides a clear separation between:

* automated analysis
* AI recommendations
* human decisions
* recorded state changes

---

# Current Demo Dataset

The current running demonstration database contains synthetic reconciliation data.

Current observed dataset:

| Metric                  |          Value |
| ----------------------- | -------------: |
| Total transactions      |          1,928 |
| Matched                 |            804 |
| Amount mismatches       |            972 |
| Missing settlements     |            152 |
| Match rate              |          41.7% |
| Total expected amount   | ₹97,323,820.00 |
| Total actual settlement | ₹75,533,931.12 |
| Total difference        | ₹21,789,888.88 |
| Total exceptions        |          1,124 |
| Open exceptions         |          1,121 |
| Resolved exceptions     |              2 |
| Escalated exceptions    |              1 |

These numbers describe the current synthetic/demo database and should not be interpreted as production financial performance.

---

# Technology Stack

## Frontend

* React
* Vite
* Tailwind CSS
* JavaScript

## Backend

* Python
* FastAPI
* Pydantic
* SQLAlchemy

## Database

* PostgreSQL

## AI

* Optional LLM provider integration
* Structured investigation responses
* Deterministic fallback

## Infrastructure

* Docker
* Docker Compose
* Nginx

## Database Migrations

* Alembic

## Testing

* pytest

## Version Control

* Git
* GitHub

---

# Project Structure

```text
razorrecon-ai/
│
├── backend/
│   ├── alembic/
│   │   └── versions/
│   │
│   ├── app/
│   │   ├── ai/
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── repositories/
│   │   ├── schemas/
│   │   └── services/
│   │
│   ├── tests/
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   ├── public/
│   ├── Dockerfile
│   └── package.json
│
├── docker/
│   └── backend.Dockerfile
│
├── tests/
│
├── docs/
│
├── .env.example
├── .gitignore
├── docker-compose.yml
└── README.md
```

---

# API Overview

The backend exposes a versioned REST API under:

```text
/api/v1
```

Core system endpoints include:

```text
GET /api/v1
GET /api/v1/health
GET /api/v1/health/live
GET /api/v1/health/ready
```

Dashboard:

```text
GET /api/v1/dashboard/summary
```

Exception management includes endpoints for:

```text
GET  /api/v1/exceptions
GET  /api/v1/exceptions/{exception_id}
```

The exception API also exposes investigation and human-review functionality.

The complete API contract is documented separately in:

```text
docs/api.md
```

Interactive API documentation is available through FastAPI's generated documentation when the backend is running:

```text
http://localhost:8000/docs
```

---

# Database Architecture

The database separates financial entities from reconciliation and operational state.

Conceptually:

```text
Merchants
   │
   ├── Orders
   ├── Payments
   ├── Settlements
   ├── Refunds
   ├── Fees
   └── Adjustments

Reconciliation Runs
        │
        ▼
Reconciliation Results
        │
        ▼
Exceptions
   │       │
   │       └──────────► Investigations
   │
   ├──────────────► Evidence
   │
   └──────────────► Human Reviews
                         │
                         ▼
                     Audit Logs
```

PostgreSQL provides:

* relational integrity
* transactional consistency
* indexing
* structured financial data
* reliable persistence

Schema evolution is managed through Alembic migrations.

---

# Running Locally

## Prerequisites

Install:

* Python 3.12+
* Node.js
* npm
* PostgreSQL
* Git

---

## Backend

Create and activate a Python environment.

Then install dependencies:

```bash
pip install -r backend/requirements.txt
```

Configure the required environment variables.

Start the backend:

```bash
uvicorn app.main:app --reload
```

The API will be available at:

```text
http://localhost:8000
```

Swagger documentation:

```text
http://localhost:8000/docs
```

---

# Running with Docker

Docker Compose is the recommended way to run the complete stack.

Build the services:

```bash
docker compose build
```

Start the application:

```bash
docker compose up -d
```

Check service status:

```bash
docker compose ps
```

The stack contains:

```text
PostgreSQL
   ↓
FastAPI Backend
   ↓
React/Nginx Frontend
```

Expected services:

```text
razorrecon-postgres
razorrecon-backend
razorrecon-frontend
```

Backend:

```text
http://localhost:8000
```

Frontend:

```text
http://localhost:5173
```

Stop the stack:

```bash
docker compose down
```

---

# Environment Variables

Configuration is environment-driven.

Example:

```text
APP_ENV=development

DATABASE_URL=postgresql+psycopg2://razorrecon:change-me@postgres:5432/razorrecon

LLM_PROVIDER=gemini
LLM_MODEL=gemini-3.6-flash
GEMINI_API_KEY=your-gemini-api-key

LOG_LEVEL=INFO

CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

POSTGRES_DB=razorrecon
POSTGRES_USER=razorrecon
POSTGRES_PASSWORD=change-me
```

Secrets must be supplied through environment configuration.

Never commit:

```text
.env
API keys
passwords
credentials
```

Only `.env.example` should be committed.

---

# Testing

RazorRecon AI uses pytest for automated testing.

The current full test suite has been verified with:

```text
185 passed
```

Run the complete suite:

```bash
python -m pytest
```

Testing covers multiple layers of the system, including:

* reconciliation logic
* financial calculations
* matching
* exception handling
* persistence
* API behavior
* AI investigation behavior
* fallback behavior
* dashboard calculations
* validation
* error handling

The goal is not simply to test individual functions, but to verify important system workflows.

---

# Reliability and Failure Handling

A key design principle is that optional AI functionality must not become a single point of failure for reconciliation.

```text
                    Reconciliation
                         │
                         ▼
                    Exception
                         │
                         ▼
                  AI Investigation
                         │
              ┌──────────┴──────────┐
              │                     │
           Available             Unavailable
              │                     │
              ▼                     ▼
        AI-assisted          Deterministic
        investigation          fallback
              │                     │
              └──────────┬──────────┘
                         ▼
                   Safe Result
```

Other reliability mechanisms include:

* database health checks
* liveness endpoint
* readiness endpoint
* database connection verification
* centralized exception handling
* structured request logging
* container health dependencies
* database migrations

---

# Security

RazorRecon AI follows production-minded security principles appropriate for an engineering prototype.

## Secrets

Secrets are supplied through environment variables.

## Input Validation

API requests are validated using Pydantic models.

## SQL Safety

Database access uses SQLAlchemy rather than constructing raw SQL from untrusted request input.

## CORS

Allowed frontend origins are explicitly configurable.

## Error Handling

Application exceptions are handled centrally so internal implementation details are not unnecessarily exposed to API clients.

## Logging

Request logging is implemented while avoiding unnecessary exposure of sensitive application data.

## Synthetic Data

All financial records used in the project are synthetic.

---

# Observability

The application includes basic operational observability mechanisms.

## Health

```text
GET /api/v1/health
```

Checks application/database health.

## Liveness

```text
GET /api/v1/health/live
```

Confirms that the application process is alive.

## Readiness

```text
GET /api/v1/health/ready
```

Confirms that the application can reach the database.

## Request Logging

Backend requests are processed through request logging middleware.

This provides a foundation for extending the system with:

* metrics
* distributed tracing
* centralized log aggregation
* alerting

---

# Engineering Decisions

## Deterministic Financial Calculations

Financial calculations are kept outside the LLM.

**Reason:** financial arithmetic needs to be reproducible, testable, and auditable.

---

## AI After Reconciliation

The AI layer investigates exceptions rather than deciding the underlying financial arithmetic.

**Reason:** the LLM should explain evidence rather than become the source of financial truth.

---

## Deterministic Fallback

AI provider failures do not invalidate reconciliation.

**Reason:** optional intelligence should degrade gracefully.

---

## PostgreSQL

A relational database is used for the financial domain.

**Reason:** financial entities have structured relationships and require consistency and transactional behavior.

---

## Alembic

Database schema changes are version-controlled.

**Reason:** reproducible environments require explicit schema migration history.

---

## Docker Compose

The application can be reproduced as a multi-container stack.

**Reason:** it reduces environment-specific differences and simplifies reviewer setup.

---

# Current Limitations

RazorRecon AI is an internship-level engineering prototype rather than a production payment platform.

Current limitations include:

* financial data is synthetic
* no live payment-provider integration is claimed
* no live banking integration is claimed
* AI functionality depends on provider configuration
* the current deployment model is Docker Compose
* authentication and authorization require further expansion for production financial use
* large-scale distributed processing has not been presented as production-benchmarked
* advanced enterprise observability is not yet implemented

These limitations are intentional and documented rather than hidden.

---

# Future Improvements

Potential future development includes:

## Distributed Processing

```text
Event Stream
     ↓
Message Queue
     ↓
Reconciliation Workers
     ↓
Scalable Processing
```

## Enterprise Authentication

* role-based access control
* service-to-service authentication
* stronger authorization policies

## Advanced Observability

* Prometheus metrics
* Grafana dashboards
* distributed tracing
* centralized logging
* alerting

## Production AI Gateway

A dedicated AI gateway could provide:

* provider abstraction
* model routing
* rate limiting
* retries
* response validation
* cost monitoring
* prompt versioning

## External Integrations

Potential future integrations include:

* payment processors
* banking systems
* ERP systems
* accounting platforms

## Deployment

A future production architecture could use Kubernetes and managed infrastructure.

---

# Demo Workflow

A recommended demonstration follows this sequence:

```text
1. Start Docker Compose
        ↓
2. Open the finance dashboard
        ↓
3. Review reconciliation metrics
        ↓
4. Open the exception queue
        ↓
5. Filter exceptions
        ↓
6. Open an exception
        ↓
7. Inspect expected vs actual values
        ↓
8. Review supporting evidence
        ↓
9. Run/view investigation
        ↓
10. Show AI-assisted reasoning
        ↓
11. Demonstrate deterministic fallback
        ↓
12. Perform human review
        ↓
13. Inspect audit history
```

This demonstrates the complete financial investigation lifecycle rather than only showing a dashboard.

---

# Project Status

## Completed

* [x] Backend architecture
* [x] PostgreSQL persistence
* [x] Financial data models
* [x] Reconciliation engine
* [x] Transaction matching
* [x] Exception detection
* [x] Exception intelligence
* [x] Evidence-based investigation
* [x] AI-assisted investigation
* [x] Deterministic AI fallback
* [x] Human review workflow
* [x] Audit logging
* [x] Dashboard APIs
* [x] React dashboard
* [x] Centralized error handling
* [x] Request logging
* [x] Health/readiness endpoints
* [x] CORS configuration
* [x] Alembic migrations
* [x] Docker backend
* [x] Docker frontend
* [x] Docker Compose
* [x] Full-stack Docker verification
* [x] Automated testing
* [x] 185 passing tests
* [x] Git repository cleanup

## Current Phase

**Phase 9 — Documentation and Architecture**

Next deliverables:

* architecture documentation
* reconciliation documentation
* AI investigation documentation
* API documentation
* database documentation
* security documentation
* testing documentation
* engineering decision records
* demo guide
* architecture diagrams

---

# License

This project is intended as an educational and internship portfolio project.

All financial data used by the project is synthetic.
