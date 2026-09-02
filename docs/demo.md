# RazorRecon AI — Demo Guide

## 1. Purpose

This guide provides a short, repeatable demonstration workflow for RazorRecon AI.

The goal of the demo is to show the complete financial-control workflow:

```text
Financial Data
      ↓
Reconciliation
      ↓
Exception Detection
      ↓
Evidence Collection
      ↓
AI Investigation
      ↓
Risk / Confidence
      ↓
Human Review
      ↓
Audit Trail
      ↓
Dashboard
```

The recommended demo can be completed in approximately **5–10 minutes**.

---

# 2. Demo Environment

RazorRecon AI can be demonstrated using the Docker Compose environment.

### Services

| Service    | Address                      | Purpose                |
| ---------- | ---------------------------- | ---------------------- |
| Frontend   | `http://localhost:5173`      | Dashboard UI           |
| Backend    | `http://localhost:8000`      | FastAPI API            |
| API Docs   | `http://localhost:8000/docs` | Interactive OpenAPI UI |
| PostgreSQL | `localhost:5432`             | Persistent database    |

The project uses synthetic/demo financial data and is not connected to live payment processor or banking systems.

---

# 3. Start the Application

From the project root:

```powershell
docker compose up --build -d
```

Verify the containers:

```powershell
docker compose ps
```

Expected services:

```text
razorrecon-postgres
razorrecon-backend
razorrecon-frontend
```

PostgreSQL should report a healthy state.

---

# 4. Verify Backend Health

Open:

```text
http://localhost:8000/api/v1/health
```

Expected response:

```json
{
  "status": "healthy",
  "service": "RazorRecon AI",
  "database": "healthy"
}
```

Also verify liveness:

```text
http://localhost:8000/api/v1/health/live
```

Expected:

```json
{
  "status": "alive",
  "service": "RazorRecon AI"
}
```

And readiness:

```text
http://localhost:8000/api/v1/health/ready
```

Expected:

```json
{
  "status": "ready",
  "service": "RazorRecon AI",
  "database": "healthy"
}
```

These endpoints demonstrate that the application distinguishes between:

* application process availability
* database readiness
* overall service health

---

# 5. Open the Dashboard

Open:

```text
http://localhost:5173
```

The dashboard should display the reconciliation overview.

The current demonstration dataset contains:

| Metric                   |          Value |
| ------------------------ | -------------: |
| Total transactions       |          1,928 |
| Matched                  |            804 |
| Amount mismatches        |            972 |
| Missing settlements      |            152 |
| Match rate               |          41.7% |
| Expected amount          | ₹97,323,820.00 |
| Actual settlement amount | ₹75,533,931.12 |
| Total difference         | ₹21,789,888.88 |
| Total exceptions         |          1,124 |
| Open exceptions          |          1,121 |
| Resolved                 |              2 |
| Escalated                |              1 |

The dashboard provides the high-level financial-control view.

---

# 6. Explain the Reconciliation Result

The central financial invariant is:

```text
difference = expected_amount - actual_amount
```

For the demonstration dataset:

```text
₹97,323,820.00
-₹75,533,931.12
----------------
₹21,789,888.88
```

Therefore:

```text
Expected - Actual = Difference
```

The reconciliation engine calculates this deterministically.

The AI layer does **not** determine the financial amount.

---

# 7. Demonstrate an Exception

Navigate to the exceptions section of the dashboard.

The main exception categories are:

```text
MATCHED
AMOUNT_MISMATCH
MISSING_SETTLEMENT
```

For the demo, an `AMOUNT_MISMATCH` or `MISSING_SETTLEMENT` exception is ideal because it clearly demonstrates the investigation workflow.

Select an exception to view its details.

The exception detail should expose information such as:

* Exception ID
* Transaction ID
* Exception type
* Severity
* Status
* Confidence
* Description
* Evidence
* Previous investigations
* Human reviews
* Transaction audit history

---

# 8. Demonstrate Evidence Collection

An investigation is evidence-driven rather than purely AI-generated.

Evidence can originate from financial records such as:

```text
Payment
Settlement
Refund
Fee
Adjustment
Reconciliation Result
```

The evidence model records:

* evidence type
* source table
* source record ID
* description
* creation timestamp

This provides traceability between an exception and the financial records supporting the investigation.

---

# 9. Run an AI Investigation

From the exception detail view, trigger:

```text
Investigate
```

The backend performs the investigation workflow.

The conceptual flow is:

```text
Exception
   ↓
Evidence Collection
   ↓
Deterministic Analysis
   ↓
AI Investigation
   ↓
Validation
   ↓
Investigation Record
```

The investigation response includes:

* investigation ID
* investigation mode
* AI provider status
* evidence count
* deterministic analysis
* AI analysis when available
* fallback reason when applicable

---

# 10. Demonstrate the AI Safety Boundary

RazorRecon AI follows a deterministic-first architecture.

The AI is responsible for:

* explaining discrepancies
* interpreting evidence
* identifying possible root causes
* summarizing investigation findings
* providing risk interpretation
* recommending next actions

The AI is **not** responsible for:

* calculating settlement totals
* deciding the financial truth
* inventing transactions
* inventing evidence
* modifying financial records
* determining database state

The core principle is:

> Financial truth must remain deterministic, explainable, testable, and independent of probabilistic AI output.

---

# 11. Demonstrate Deterministic Fallback

For a reproducible local test environment, the LLM provider can be disabled.

Example:

```env
LLM_PROVIDER=none
```

When the external AI provider is unavailable, the system does not fail the entire investigation.

Instead, it uses:

```text
DETERMINISTIC_FALLBACK
```

The investigation records the provider state and fallback reason.

This demonstrates graceful degradation.

The system therefore supports:

```text
AI available
     ↓
AI-assisted investigation

AI unavailable
     ↓
Deterministic fallback
```

The investigation remains auditable in both cases.

---

# 12. Demonstrate Human Review

After investigation, submit a human review.

Example request:

```http
POST /api/v1/exceptions/{exception_id}/review
Content-Type: application/json
```

Example body:

```json
{
  "reviewer": "finance.analyst@example.com",
  "action": "APPROVE",
  "reason": "Settlement was confirmed in the processor portal."
}
```

The review records:

* reviewer
* action
* reason
* timestamp

Only valid open exceptions can be reviewed.

Attempts to review an exception that is no longer open are rejected.

This protects the exception state machine.

---

# 13. Demonstrate Auditability

The system records important investigation and review activity.

The audit trail allows a reviewer to understand:

```text
What happened?
      ↓
What was the previous state?
      ↓
What action was performed?
      ↓
Who performed it?
      ↓
Why was it performed?
      ↓
What is the new state?
```

Audit records include information such as:

* actor
* action
* previous state
* new state
* reason
* confidence
* timestamp
* transaction ID

This is important for financial-control workflows where explainability and traceability matter.

---

# 14. API Demonstration

The interactive API documentation is available at:

```text
http://localhost:8000/docs
```

Recommended endpoints to demonstrate:

### Health

```http
GET /api/v1/health
```

### Dashboard

```http
GET /api/v1/dashboard/summary
```

### Exception list

```http
GET /api/v1/exceptions
```

### Exception details

```http
GET /api/v1/exceptions/{exception_id}
```

### Exception analytics

```http
GET /api/v1/exceptions/analytics/summary
```

### AI investigation

```http
POST /api/v1/exceptions/{exception_id}/investigate
```

### Human review

```http
POST /api/v1/exceptions/{exception_id}/review
```

The Swagger UI can be used to execute these requests directly.

---

# 15. Recommended 5-Minute Demo Script

## Minute 1 — Architecture

Briefly explain:

```text
React frontend
      ↓
FastAPI backend
      ↓
PostgreSQL
      ↓
Deterministic reconciliation
      ↓
AI investigation
```

Highlight that AI is an investigation layer rather than the source of financial truth.

---

## Minute 2 — Dashboard

Open the dashboard and show:

* transaction volume
* match rate
* exception counts
* expected amount
* actual settlement amount
* total financial difference

Explain that the financial totals come from deterministic reconciliation.

---

## Minute 3 — Exception Investigation

Open an exception.

Show:

* exception type
* severity
* transaction
* evidence
* deterministic analysis

Then trigger the investigation.

Show:

* investigation ID
* investigation mode
* provider status
* evidence count
* analysis

---

## Minute 4 — Human Decision

Submit a review.

Explain:

```text
Detection
   ↓
Investigation
   ↓
Human decision
   ↓
Audit trail
```

Show that the system prevents invalid state transitions.

---

## Minute 5 — Engineering Quality

Open the API documentation and briefly demonstrate:

```text
/health
/health/live
/health/ready
/docs
```

Then mention:

* 185 automated tests
* PostgreSQL persistence
* Alembic migrations
* Docker Compose
* deterministic AI fallback
* centralized error handling
* request logging
* environment-based configuration
* Git/GitHub version control

Finish with the key principle:

> AI explains the discrepancy. The reconciliation engine establishes the discrepancy.

---

# 16. Screenshot Checklist

The following screenshots are recommended for the GitHub repository and internship review.

## Screenshot 1 — Dashboard

Capture:

* dashboard title
* transaction metrics
* financial metrics
* exception metrics
* charts/trends if visible

Suggested filename:

```text
docs/screenshots/dashboard.png
```

---

## Screenshot 2 — Exception Detail

Capture:

* exception ID
* transaction ID
* exception type
* severity
* status
* evidence

Suggested filename:

```text
docs/screenshots/exception-detail.png
```

---

## Screenshot 3 — AI Investigation

Capture:

* investigation mode
* provider status
* evidence count
* deterministic analysis
* AI analysis or fallback information

Suggested filename:

```text
docs/screenshots/ai-investigation.png
```

---

## Screenshot 4 — Human Review

Capture:

* review action
* reviewer
* reason
* resulting exception state

Suggested filename:

```text
docs/screenshots/human-review.png
```

---

## Screenshot 5 — API Documentation

Capture the Swagger/OpenAPI interface showing the available API endpoints.

Suggested filename:

```text
docs/screenshots/api-docs.png
```

---

## Screenshot 6 — Docker Stack

Capture:

```powershell
docker compose ps
```

showing the PostgreSQL, backend, and frontend services.

Suggested filename:

```text
docs/screenshots/docker-stack.png
```

---

## Screenshot 7 — Test Suite

Capture:

```powershell
python -m pytest
```

showing:

```text
185 passed
```

Suggested filename:

```text
docs/screenshots/test-suite.png
```

---

# 17. Screenshot Directory

Create the directory:

```powershell
mkdir docs\screenshots
```

Recommended final structure:

```text
docs/
├── ai-investigation.md
├── api.md
├── architecture.md
├── database.md
├── demo.md
├── engineering.md
├── reconciliation.md
├── diagrams/
│   ├── ai-investigation-flow.md
│   ├── database-er.md
│   ├── reconciliation-flow.md
│   └── system-architecture.md
└── screenshots/
    ├── dashboard.png
    ├── exception-detail.png
    ├── ai-investigation.png
    ├── human-review.png
    ├── api-docs.png
    ├── docker-stack.png
    └── test-suite.png
```

Screenshots are optional documentation assets; the application itself does not depend on them.

---

# 18. Demo Troubleshooting

## Backend unavailable

Check:

```powershell
docker compose ps
```

Then:

```powershell
docker compose logs backend
```

---

## Database unavailable

Check:

```powershell
docker compose logs postgres
```

The PostgreSQL container should report a healthy status.

---

## Frontend unavailable

Check:

```powershell
docker compose logs frontend
```

Then verify:

```text
http://localhost:5173
```

---

## API returns degraded/not-ready

Check the backend database connection and PostgreSQL health.

The application intentionally exposes health and readiness information instead of hiding database failures.

---

## AI investigation unavailable

Check the configured:

```env
LLM_PROVIDER
```

For deterministic local testing:

```env
LLM_PROVIDER=none
```

The system should use deterministic fallback behavior rather than treating AI unavailability as a reconciliation failure.

---

# 19. Final Demo Checklist

Before presenting the project:

* [ ] Docker Compose starts successfully
* [ ] PostgreSQL is healthy
* [ ] Backend is healthy
* [ ] Frontend loads
* [ ] Dashboard metrics load
* [ ] Exception list loads
* [ ] Exception details load
* [ ] Evidence is displayed
* [ ] Investigation can be triggered
* [ ] AI/fallback mode is visible
* [ ] Human review works
* [ ] Audit information is visible
* [ ] `/docs` loads
* [ ] `/health` works
* [ ] `/health/live` works
* [ ] `/health/ready` works
* [ ] Test suite passes
* [ ] Git working tree is clean
* [ ] Latest commit is pushed to GitHub

---

# 20. Reviewer-Focused Project Story

The simplest way to explain RazorRecon AI is:

**RazorRecon AI is a financial reconciliation and exception investigation platform designed around deterministic financial correctness and controlled AI assistance.**

The reconciliation engine compares expected payment records against settlement records and identifies discrepancies.

Those discrepancies become structured exceptions.

The system then collects evidence and performs deterministic analysis before optionally using an LLM to explain the discrepancy and suggest investigation insights.

If the AI provider is unavailable, the system falls back to deterministic investigation rather than failing.

A human reviewer can then make the final operational decision, with the workflow recorded through investigation history, reviews, and audit information.

The result is a system where:

```text
Deterministic logic
        ↓
establishes financial truth

Evidence
        ↓
supports the investigation

AI
        ↓
helps explain the discrepancy

Human review
        ↓
makes the operational decision

Audit trail
        ↓
preserves accountability
```

This separation is the central architectural principle of RazorRecon AI.

---

# 21. Final Engineering Principle

RazorRecon AI is intentionally designed so that probabilistic AI does not become a source of financial truth.

```text
Financial truth
      ≠
LLM output
```

Instead:

```text
Financial records
      ↓
Deterministic reconciliation
      ↓
Exception
      ↓
Evidence
      ↓
AI-assisted explanation
      ↓
Human review
      ↓
Auditable outcome
```

**AI explains the discrepancy. The reconciliation engine establishes the discrepancy.**
