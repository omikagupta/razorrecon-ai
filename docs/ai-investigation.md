# RazorRecon AI — Reconciliation Engine

## Overview

RazorRecon AI uses a deterministic reconciliation engine to compare financial payment records against settlement records and identify discrepancies.

The reconciliation engine is the financial source of truth for the platform.

AI is intentionally positioned **after deterministic reconciliation**. The LLM does not determine monetary truth, perform transaction matching, or calculate financial totals.

The core architecture is:

```text
Financial Records
       ↓
Normalization
       ↓
Payment / Settlement Matching
       ↓
Deterministic Reconciliation
       ↓
Exception Detection
       ↓
Evidence Generation
       ↓
AI / Deterministic Investigation
       ↓
Human Review
       ↓
Audit Trail
```

---

# Reconciliation Pipeline

The reconciliation process can be divided into several stages.

## 1. Financial Data Ingestion

The system begins with financial source data representing payments and settlements.

The financial domain contains:

* Merchants
* Orders
* Payments
* Settlements
* Refunds
* Fees
* Adjustments

The ingestion layer loads source records into PostgreSQL.

The reconciliation engine then operates on persisted financial records rather than directly trusting external input.

---

## 2. Normalization

Before matching, financial records are normalized into a consistent representation.

Important normalization concerns include:

* Transaction identifiers
* Payment identifiers
* Settlement identifiers
* Monetary amounts
* Currency
* Timestamps
* Status values

The goal is to ensure that logically equivalent records can be compared consistently.

---

# 3. Transaction Matching

The reconciliation engine attempts to associate payment transactions with corresponding settlement records.

Conceptually:

```text
Payment
   │
   │ payment_id
   ▼
Settlement
```

The current data model uses indexed business identifiers such as:

```text
payment_id
settlement_id
transaction_id
```

rather than database-enforced foreign-key relationships.

This allows the reconciliation service to control matching behavior explicitly.

---

# 4. Deterministic Reconciliation

Once a payment and settlement relationship has been identified, the engine compares the expected and actual amounts.

The fundamental financial invariant is:

```text
difference = expected_amount - actual_amount
```

For example:

```text
Expected payment:       ₹1,000.00
Actual settlement:       ₹980.00
                         ─────────
Difference:               ₹20.00
```

The result is persisted in `reconciliation_results`.

Important fields include:

* `expected_amount`
* `actual_amount`
* `difference`
* `status`
* `match_method`
* `match_confidence`

---

# Reconciliation Status

The reconciliation engine classifies transactions into deterministic states.

Current important states include:

```text
MATCHED
AMOUNT_MISMATCH
MISSING_SETTLEMENT
```

## MATCHED

A payment has a corresponding settlement and the financial values satisfy the matching rules.

```text
Payment
   ↓
Settlement found
   ↓
Amounts consistent
   ↓
MATCHED
```

---

## AMOUNT_MISMATCH

A settlement exists, but the actual settlement amount differs from the expected amount.

```text
Payment
   ↓
Settlement found
   ↓
Amount differs
   ↓
AMOUNT_MISMATCH
```

The monetary discrepancy is persisted explicitly.

Example:

```text
Expected: ₹5,000
Actual:   ₹4,850

Difference = ₹150
```

---

## MISSING_SETTLEMENT

A payment exists but a corresponding settlement cannot be found.

```text
Payment
   ↓
No settlement found
   ↓
MISSING_SETTLEMENT
```

This is a particularly important financial exception because the system must not silently treat the missing settlement as zero financial exposure.

The correct interpretation is:

```text
Expected amount = ₹5,000
Actual settlement = ₹0
Difference = ₹5,000
```

Therefore:

```text
difference = expected_amount
```

when the settlement is missing.

---

# Missing Settlement Financial Invariant

The persistence layer explicitly handles missing settlements.

Conceptually:

```text
if actual_amount is missing:

    difference = expected_amount

otherwise:

    difference = expected_amount - actual_amount
```

This ensures that missing settlement exposure contributes to financial reconciliation totals.

Without this rule, missing settlements could incorrectly produce:

```text
expected = ₹5,000
actual = NULL
difference = NULL
```

which would cause aggregation to understate the actual financial discrepancy.

The corrected representation is:

```text
expected = ₹5,000
actual = NULL
difference = ₹5,000
```

The `NULL` actual amount preserves the fact that no settlement record exists, while the difference represents the corresponding financial exposure.

---

# Reconciliation Result Model

Each transaction-level reconciliation result contains:

| Field              | Purpose                                         |
| ------------------ | ----------------------------------------------- |
| `run_id`           | Identifies the reconciliation execution         |
| `transaction_id`   | Identifies the transaction being evaluated      |
| `status`           | Deterministic reconciliation outcome            |
| `expected_amount`  | Amount expected from the payment/order side     |
| `actual_amount`    | Settlement amount when available                |
| `difference`       | Calculated monetary discrepancy                 |
| `match_method`     | Matching strategy used                          |
| `match_confidence` | Confidence associated with the matching process |
| `created_at`       | Result creation timestamp                       |

The result is the bridge between raw financial records and operational exception management.

---

# Reconciliation Runs

A reconciliation execution is represented by `ReconciliationRun`.

Each run tracks:

* `run_id`
* `status`
* `total_records`
* `matched_records`
* `exception_count`
* `started_at`
* `completed_at`

Conceptually:

```text
ReconciliationRun
        │
        ├── total records
        ├── matched records
        └── exceptions
                │
                ▼
     ReconciliationResult
```

This allows the system to reason about reconciliation both at:

1. **Run level**
2. **Transaction level**

---

# Exception Generation

A reconciliation result can produce an operational exception.

The relationship is:

```text
ReconciliationResult
        ↓
ExceptionRecord
```

The exception stores:

* `exception_id`
* `transaction_id`
* `exception_type`
* `severity`
* `status`
* `confidence`
* `description`
* `created_at`
* `resolved_at`

The reconciliation engine therefore separates:

```text
Financial calculation
        ↓
Operational exception
```

This is important because a financial discrepancy and the workflow used to resolve that discrepancy are different concerns.

---

# Exception Severity

Exception severity provides an operational prioritization layer.

The system can distinguish between discrepancies based on their financial and operational impact.

For example:

```text
Normal discrepancy
        ↓
High severity
        ↓
Critical exposure
```

Severity is not determined by an LLM.

It is derived from application-level reconciliation and exception logic.

This keeps financial prioritization deterministic and reproducible.

---

# Evidence Generation

Once an exception is created, the system can collect evidence related to the discrepancy.

The evidence model records:

* `exception_id`
* `evidence_type`
* `source_table`
* `source_record_id`
* `description`
* `created_at`

The important relationship is:

```text
Exception
    ↓
Evidence
    ↓
Source financial records
```

Evidence provides the factual context used by downstream investigation.

---

# Deterministic Analysis Before AI

RazorRecon AI follows a deterministic-first architecture.

The investigation pipeline is:

```text
Exception
    ↓
Evidence
    ↓
Deterministic Analysis
    ↓
AI Investigation
```

The deterministic layer establishes the factual baseline before an LLM is introduced.

For example, deterministic analysis can establish:

```text
Expected amount: ₹10,000
Actual amount: ₹9,500
Difference: ₹500
Settlement found: Yes
Exception type: AMOUNT_MISMATCH
```

The AI layer can then interpret those facts.

It should not replace them.

---

# Why Deterministic Reconciliation Comes First

Financial reconciliation is fundamentally a structured data problem.

The system already knows:

* payment identifiers
* settlement identifiers
* amounts
* currencies
* transaction states
* timestamps
* database records

These facts should be evaluated using deterministic application logic.

Using an LLM to perform the underlying financial comparison would introduce unnecessary uncertainty.

Therefore:

```text
Deterministic logic
        =
Financial truth

AI
        =
Investigation assistance
```

---

# AI Responsibility Boundary

The AI system is intentionally prevented from becoming the financial source of truth.

The LLM is **not responsible for**:

* Calculating monetary totals
* Performing authoritative payment/settlement matching
* Determining database truth
* Inventing transaction identifiers
* Inventing settlement records
* Inventing fees or refunds
* Creating financial evidence
* Replacing deterministic exception classification

The LLM **is responsible for assisting with**:

* Evidence interpretation
* Discrepancy explanation
* Potential root-cause reasoning
* Risk interpretation
* Investigation summaries
* Recommended operational actions

This boundary makes the AI component safer and easier to audit.

---

# Investigation Flow

The complete investigation architecture is:

```text
                 Exception
                    │
                    ▼
                 Evidence
                    │
                    ▼
          Deterministic Analysis
                    │
                    ▼
             Provider Check
               /          \
              /            \
        Available        Unavailable
            │                 │
            ▼                 ▼
       AI Analysis     Deterministic
                           Fallback
              \             /
               \           /
                ▼         ▼
                  Investigation
                       │
                       ▼
                  Human Review
                       │
                       ▼
                   Audit Log
```

This means an AI provider outage does not stop the reconciliation platform from producing a useful investigation.

---

# AI Fallback

AI is an optional enhancement rather than a hard dependency.

If the configured AI provider is:

* unavailable
* incorrectly configured
* returns an invalid response
* otherwise fails validation

the system can fall back to deterministic investigation.

The investigation records the provider state and fallback reason.

For example:

```text
investigation_mode = DETERMINISTIC_FALLBACK

ai_provider_status = UNAVAILABLE

fallback_reason = provider unavailable
```

This provides graceful degradation.

---

# Investigation Persistence

Investigation results are persisted in PostgreSQL.

The `investigations` table stores:

* `investigation_id`
* `exception_id`
* `investigation_mode`
* `ai_provider_status`
* `evidence_count`
* `deterministic_analysis`
* `ai_analysis`
* `fallback_reason`
* `created_at`

This means the result of an investigation is not transient.

It becomes part of the operational history of the exception.

---

# Confidence

The system distinguishes between different forms of confidence.

## Match confidence

Stored on reconciliation results:

```text
match_confidence
```

This represents confidence associated with transaction matching.

## Exception confidence

Stored on exceptions:

```text
confidence
```

This represents confidence associated with the generated exception.

## Investigation confidence

AI-generated confidence may be included inside the investigation analysis, but it is not treated as authoritative financial truth.

The system should therefore avoid interpreting:

```text
AI confidence = financial certainty
```

Those are different concepts.

---

# Human Review

Automated reconciliation and AI investigation do not necessarily represent the final operational decision.

The final workflow can involve a human reviewer:

```text
Reconciliation
      ↓
Exception
      ↓
Investigation
      ↓
Human Review
      ↓
Resolution
```

Human review records:

* `exception_id`
* `reviewer`
* `action`
* `reason`
* `created_at`

This creates an explicit human decision boundary.

---

# Auditability

Operational state changes are recorded through `AuditLog`.

An audit entry contains:

* `transaction_id`
* `actor`
* `action`
* `previous_state`
* `new_state`
* `reason`
* `confidence`
* `created_at`

The resulting lifecycle is:

```text
Financial fact
      ↓
Reconciliation result
      ↓
Exception
      ↓
Investigation
      ↓
Human action
      ↓
Audit record
```

This allows an investigator to understand not only **what happened**, but also how the final operational state was reached.

---

# Financial Invariants

The reconciliation engine relies on several important invariants.

## Invariant 1 — Difference calculation

For transactions with a settlement:

```text
difference = expected_amount - actual_amount
```

## Invariant 2 — Missing settlement

For transactions without a settlement:

```text
difference = expected_amount
```

while:

```text
actual_amount = NULL
```

preserves the distinction between:

```text
No settlement record
```

and:

```text
Settlement amount = 0
```

## Invariant 3 — Monetary precision

Financial amounts use:

```text
Numeric(18, 2)
```

rather than binary floating-point storage.

This is important for financial calculations.

---

# Example Reconciliation

Consider the following records:

```text
Payment
-------
payment_id = pay_123
amount     = ₹10,000
currency   = INR
```

Settlement:

```text
Settlement
----------
settlement_id = set_123
payment_id    = pay_123
amount        = ₹9,750
currency      = INR
```

The reconciliation engine calculates:

```text
Expected = ₹10,000
Actual   = ₹9,750
Difference = ₹250
```

Result:

```text
status = AMOUNT_MISMATCH
```

The system then creates an exception:

```text
Exception
---------
type = AMOUNT_MISMATCH
```

Evidence can reference the relevant payment and settlement records.

The investigation layer can then explain the discrepancy.

---

# Missing Settlement Example

Payment:

```text
payment_id = pay_456
amount     = ₹7,500
```

No settlement exists.

The result becomes:

```text
status = MISSING_SETTLEMENT

expected_amount = ₹7,500
actual_amount   = NULL
difference      = ₹7,500
```

This means the system correctly reports:

```text
₹7,500 of unresolved settlement exposure
```

rather than treating the discrepancy as unknown or zero.

---

# Operational Design Principle

The reconciliation engine follows:

```text
                    TRUSTED
                      │
                      ▼
              Financial Records
                      │
                      ▼
            Deterministic Matching
                      │
                      ▼
             Financial Calculation
                      │
                      ▼
               Exception Logic
                      │
                      ▼
                   Evidence
                      │
                      ▼
              AI Interpretation
                      │
                      ▼
                Human Review
                      │
                      ▼
                 Audit Trail
```

The closer a component is to financial truth, the more deterministic it should be.

The closer a component is to explanation and operational assistance, the more AI can be used safely.

---

# Engineering Rationale

The architecture deliberately separates three concerns:

### 1. Financial truth

Handled by:

* PostgreSQL
* deterministic matching
* deterministic calculations
* reconciliation rules

### 2. Investigation intelligence

Handled by:

* deterministic analysis
* evidence collection
* optional AI interpretation
* fallback investigation

### 3. Operational decision-making

Handled by:

* human review
* state transitions
* audit logging

This separation prevents AI from becoming a hidden source of financial truth.

---

# Current Limitations

The current implementation is intentionally focused on a strong internship-level prototype.

Known areas for future production evolution include:

* Explicit PostgreSQL foreign-key constraints
* More sophisticated matching strategies
* Idempotent ingestion guarantees
* Large-scale batch reconciliation
* Currency conversion and multi-currency reconciliation
* Settlement batch-level reconciliation
* Advanced fee/refund/adjustment reconciliation
* Rule configuration per merchant
* More granular financial controls
* Distributed job processing
* Immutable audit-log enforcement
* Role-based review permissions

These are future extensions rather than capabilities claimed by the current implementation.

---

# Summary

RazorRecon AI treats reconciliation as a **deterministic financial control system enhanced by AI**, rather than an AI system that happens to process financial data.

The core principle is:

```text
Financial Facts
      ↓
Deterministic Reconciliation
      ↓
Evidence
      ↓
AI-Assisted Investigation
      ↓
Human Decision
      ↓
Auditability
```

The result is an architecture where:

* financial calculations remain deterministic
* discrepancies are reproducible
* evidence is persisted
* AI failures degrade gracefully
* investigations are auditable
* humans retain operational control

> **AI explains the discrepancy. The reconciliation engine establishes the discrepancy.**
