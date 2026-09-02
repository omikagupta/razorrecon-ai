# RazorRecon AI — Database Design

## Overview

RazorRecon AI uses PostgreSQL as its primary persistence layer.

The database stores:

* Merchant and payment-domain records
* Reconciliation executions
* Reconciliation results
* Financial exceptions
* Evidence supporting exceptions
* AI-assisted investigations
* Human review decisions
* Audit history

SQLAlchemy is used as the application ORM and Alembic manages schema migrations.

The database is designed around a deterministic financial reconciliation workflow with AI-assisted investigation layered on top.

---

# Database Architecture

The primary data flow is:

```text
Merchant
   │
   ├── Order
   │      │
   │      └── Payment
   │             │
   │             ├── Settlement
   │             ├── Refund
   │             ├── Fee
   │             └── Adjustment
   │
   └── Payment

Payment / Settlement
        │
        ▼
ReconciliationRun
        │
        ▼
ReconciliationResult
        │
        ▼
ExceptionRecord
        │
        ├── Evidence
        ├── Investigation
        └── HumanReview

Transaction
    │
    ▼
AuditLog
```

The relationships shown above represent the application's logical data model.

---

# Financial Domain Tables

## merchants

Stores merchant-level information.

| Column        | Type         | Constraints               |
| ------------- | ------------ | ------------------------- |
| `id`          | Integer      | Primary key               |
| `merchant_id` | VARCHAR(50)  | Unique, not null, indexed |
| `name`        | VARCHAR(255) | Not null                  |
| `created_at`  | DATETIME     | Not null                  |

`merchant_id` is the stable application-level merchant identifier.

---

## orders

Stores merchant orders.

| Column        | Type          | Constraints               |
| ------------- | ------------- | ------------------------- |
| `id`          | Integer       | Primary key               |
| `order_id`    | VARCHAR(50)   | Unique, not null, indexed |
| `merchant_id` | VARCHAR(50)   | Not null, indexed         |
| `amount`      | NUMERIC(18,2) | Not null                  |
| `currency`    | VARCHAR(3)    | Not null, default `INR`   |
| `status`      | VARCHAR(30)   | Not null                  |
| `created_at`  | DATETIME      | Not null                  |

Logical relationship:

```text
merchants.merchant_id
        │
        ▼
orders.merchant_id
```

---

## payments

Stores payment transactions associated with orders and merchants.

| Column              | Type          | Constraints               |
| ------------------- | ------------- | ------------------------- |
| `id`                | Integer       | Primary key               |
| `payment_id`        | VARCHAR(50)   | Unique, not null, indexed |
| `order_id`          | VARCHAR(50)   | Not null, indexed         |
| `merchant_id`       | VARCHAR(50)   | Not null, indexed         |
| `amount`            | NUMERIC(18,2) | Not null                  |
| `currency`          | VARCHAR(3)    | Not null, default `INR`   |
| `status`            | VARCHAR(30)   | Not null                  |
| `payment_timestamp` | DATETIME      | Not null                  |

Logical relationships:

```text
orders.order_id
      │
      ▼
payments.order_id

merchants.merchant_id
      │
      ▼
payments.merchant_id
```

---

## settlements

Stores settlement records associated with payments.

| Column                 | Type          | Constraints               |
| ---------------------- | ------------- | ------------------------- |
| `id`                   | Integer       | Primary key               |
| `settlement_id`        | VARCHAR(50)   | Unique, not null, indexed |
| `payment_id`           | VARCHAR(50)   | Not null, indexed         |
| `merchant_id`          | VARCHAR(50)   | Not null, indexed         |
| `amount`               | NUMERIC(18,2) | Not null                  |
| `currency`             | VARCHAR(3)    | Not null, default `INR`   |
| `settlement_timestamp` | DATETIME      | Not null                  |

Logical relationships:

```text
payments.payment_id
        │
        ▼
settlements.payment_id

merchants.merchant_id
        │
        ▼
settlements.merchant_id
```

---

## refunds

Stores refunds associated with payments and orders.

| Column             | Type          | Constraints               |
| ------------------ | ------------- | ------------------------- |
| `id`               | Integer       | Primary key               |
| `refund_id`        | VARCHAR(50)   | Unique, not null, indexed |
| `payment_id`       | VARCHAR(50)   | Not null, indexed         |
| `order_id`         | VARCHAR(50)   | Not null, indexed         |
| `amount`           | NUMERIC(18,2) | Not null                  |
| `status`           | VARCHAR(30)   | Not null                  |
| `refund_timestamp` | DATETIME      | Not null                  |

Logical relationships:

```text
payments.payment_id
        │
        ▼
refunds.payment_id

orders.order_id
      │
      ▼
refunds.order_id
```

---

## fees

Stores fees associated with payments.

| Column       | Type          | Constraints               |
| ------------ | ------------- | ------------------------- |
| `id`         | Integer       | Primary key               |
| `fee_id`     | VARCHAR(50)   | Unique, not null, indexed |
| `payment_id` | VARCHAR(50)   | Not null, indexed         |
| `fee_type`   | VARCHAR(50)   | Not null                  |
| `amount`     | NUMERIC(18,2) | Not null                  |
| `created_at` | DATETIME      | Not null                  |

Logical relationship:

```text
payments.payment_id
        │
        ▼
fees.payment_id
```

---

## adjustments

Stores payment-level financial adjustments.

| Column            | Type          | Constraints               |
| ----------------- | ------------- | ------------------------- |
| `id`              | Integer       | Primary key               |
| `adjustment_id`   | VARCHAR(50)   | Unique, not null, indexed |
| `payment_id`      | VARCHAR(50)   | Not null, indexed         |
| `adjustment_type` | VARCHAR(50)   | Not null                  |
| `amount`          | NUMERIC(18,2) | Not null                  |
| `created_at`      | DATETIME      | Not null                  |

Logical relationship:

```text
payments.payment_id
        │
        ▼
adjustments.payment_id
```

---

# Reconciliation Tables

## reconciliation_runs

Represents one execution of the reconciliation engine.

| Column            | Type         | Constraints               |
| ----------------- | ------------ | ------------------------- |
| `id`              | Integer      | Primary key               |
| `run_id`          | VARCHAR(100) | Unique, not null, indexed |
| `status`          | VARCHAR(30)  | Not null                  |
| `total_records`   | Integer      | Default `0`               |
| `matched_records` | Integer      | Default `0`               |
| `exception_count` | Integer      | Default `0`               |
| `started_at`      | DATETIME     | Not null                  |
| `completed_at`    | DATETIME     | Nullable                  |

Logical relationship:

```text
reconciliation_runs.run_id
            │
            ▼
reconciliation_results.run_id
```

A run provides aggregate execution-level information while individual results contain transaction-level reconciliation outcomes.

---

## reconciliation_results

Stores the deterministic result of reconciling a transaction.

| Column             | Type          | Constraints       |
| ------------------ | ------------- | ----------------- |
| `id`               | Integer       | Primary key       |
| `run_id`           | VARCHAR(100)  | Not null, indexed |
| `transaction_id`   | VARCHAR(100)  | Not null, indexed |
| `status`           | VARCHAR(50)   | Not null          |
| `expected_amount`  | NUMERIC(18,2) | Nullable          |
| `actual_amount`    | NUMERIC(18,2) | Nullable          |
| `difference`       | NUMERIC(18,2) | Nullable          |
| `match_method`     | VARCHAR(50)   | Nullable          |
| `match_confidence` | NUMERIC(5,4)  | Nullable          |
| `created_at`       | DATETIME      | Not null          |

The result records the deterministic reconciliation decision.

Current statuses include:

* `MATCHED`
* `AMOUNT_MISMATCH`
* `MISSING_SETTLEMENT`

---

# Financial Precision

Monetary fields use:

```text
NUMERIC(18,2)
```

rather than floating-point types.

This prevents binary floating-point representation from introducing rounding errors into financial calculations.

For example:

```text
expected_amount = 100.00
actual_amount   = 99.99
difference      = 0.01
```

The database therefore preserves exact two-decimal monetary values.

Confidence values use:

```text
NUMERIC(5,4)
```

allowing values such as:

```text
0.8600
```

---

# Missing Settlement Representation

A missing settlement is represented explicitly rather than pretending that a settlement exists with zero value.

For a missing settlement:

```text
expected_amount = expected financial amount
actual_amount   = NULL
difference      = expected_amount
```

For example:

```text
expected_amount = 500.00
actual_amount   = NULL
difference      = 500.00
```

This preserves the distinction between:

```text
No settlement exists
```

and:

```text
A settlement exists with amount 0.00
```

The distinction is important for financial investigation and dashboard exposure calculations.

---

# Exception Intelligence Tables

## exceptions

Stores reconciliation exceptions generated from deterministic reconciliation results.

| Column           | Type         | Constraints               |
| ---------------- | ------------ | ------------------------- |
| `id`             | Integer      | Primary key               |
| `exception_id`   | VARCHAR(100) | Unique, not null, indexed |
| `transaction_id` | VARCHAR(100) | Not null, indexed         |
| `exception_type` | VARCHAR(100) | Not null, indexed         |
| `severity`       | VARCHAR(30)  | Not null                  |
| `status`         | VARCHAR(30)  | Not null                  |
| `confidence`     | NUMERIC(5,4) | Nullable                  |
| `description`    | TEXT         | Nullable                  |
| `created_at`     | DATETIME     | Not null                  |
| `resolved_at`    | DATETIME     | Nullable                  |

Exception identifiers are stable application-level identifiers.

Current exception types are:

* `AMOUNT_MISMATCH`
* `MISSING_SETTLEMENT`

A matched transaction does not generate an exception.

---

## evidence

Stores evidence associated with an exception.

| Column             | Type         | Constraints       |
| ------------------ | ------------ | ----------------- |
| `id`               | Integer      | Primary key       |
| `exception_id`     | VARCHAR(100) | Not null, indexed |
| `evidence_type`    | VARCHAR(50)  | Not null          |
| `source_table`     | VARCHAR(100) | Not null          |
| `source_record_id` | VARCHAR(100) | Not null          |
| `description`      | TEXT         | Nullable          |
| `created_at`       | DATETIME     | Not null          |

Evidence identifies the source table and source record supporting an investigation.

Important implementation detail:

`Evidence` does not contain a separate `evidence_id` field. Its database primary key is `id`.

Logical relationship:

```text
exceptions.exception_id
        │
        ▼
evidence.exception_id
```

---

# Investigation Persistence

## investigations

Stores persisted AI-assisted or deterministic investigation results.

| Column                   | Type         | Constraints               |
| ------------------------ | ------------ | ------------------------- |
| `id`                     | Integer      | Primary key               |
| `investigation_id`       | VARCHAR(100) | Unique, not null, indexed |
| `exception_id`           | VARCHAR(100) | Not null, indexed         |
| `investigation_mode`     | VARCHAR(50)  | Not null                  |
| `ai_provider_status`     | VARCHAR(50)  | Not null                  |
| `evidence_count`         | Integer      | Not null, default `0`     |
| `deterministic_analysis` | JSON         | Not null                  |
| `ai_analysis`            | JSON         | Nullable                  |
| `fallback_reason`        | TEXT         | Nullable                  |
| `created_at`             | DATETIME     | Not null                  |

Logical relationship:

```text
exceptions.exception_id
        │
        ▼
investigations.exception_id
```

Multiple investigations may exist for one exception.

This intentionally preserves investigation history rather than overwriting previous analysis.

---

## Investigation Modes

The application currently supports:

| Mode                     | Meaning                                                        |
| ------------------------ | -------------------------------------------------------------- |
| `AI_ASSISTED`            | Deterministic analysis augmented with a validated AI response. |
| `DETERMINISTIC_FALLBACK` | Investigation completed without usable AI output.              |

The deterministic analysis is always persisted.

AI output is optional and stored separately in `ai_analysis`.

---

## AI Provider Status

Current provider states include:

| Status             | Meaning                                  |
| ------------------ | ---------------------------------------- |
| `SUCCESS`          | AI provider returned a valid response.   |
| `UNAVAILABLE`      | AI provider was disabled or unavailable. |
| `INVALID_RESPONSE` | Provider output failed validation.       |

This separation allows downstream consumers to distinguish between successful AI augmentation and deterministic fallback.

---

# Human Review

## human_reviews

Stores human decisions made against exceptions.

| Column         | Type         | Constraints       |
| -------------- | ------------ | ----------------- |
| `id`           | Integer      | Primary key       |
| `exception_id` | VARCHAR(100) | Not null, indexed |
| `reviewer`     | VARCHAR(100) | Not null          |
| `action`       | VARCHAR(50)  | Not null          |
| `reason`       | TEXT         | Nullable          |
| `created_at`   | DATETIME     | Not null          |

Logical relationship:

```text
exceptions.exception_id
        │
        ▼
human_reviews.exception_id
```

Supported review actions include:

* `APPROVE`
* `REJECT`
* `ESCALATE`

Human review creates a durable record of the operational decision.

---

# Audit Logging

## audit_logs

Stores transaction-level audit history.

| Column           | Type         | Constraints       |
| ---------------- | ------------ | ----------------- |
| `id`             | Integer      | Primary key       |
| `transaction_id` | VARCHAR(100) | Not null, indexed |
| `actor`          | VARCHAR(100) | Not null          |
| `action`         | VARCHAR(100) | Not null          |
| `previous_state` | VARCHAR(50)  | Nullable          |
| `new_state`      | VARCHAR(50)  | Nullable          |
| `reason`         | TEXT         | Nullable          |
| `confidence`     | NUMERIC(5,4) | Nullable          |
| `created_at`     | DATETIME     | Not null          |

Audit records capture:

* Actor
* Action
* Previous state
* New state
* Reason
* Confidence where applicable
* Timestamp

The audit model is transaction-oriented.

Therefore `AuditLog` uses `transaction_id` rather than `exception_id`.

Logical relationship:

```text
transaction
    │
    ▼
audit_logs.transaction_id
```

---

# Logical Relationships vs Database Foreign Keys

The current SQLAlchemy models use application-level identifier relationships rather than explicit SQLAlchemy `ForeignKey` constraints.

For example:

```text
orders.merchant_id
        │
        ▼
merchants.merchant_id
```

and:

```text
settlements.payment_id
        │
        ▼
payments.payment_id
```

These relationships are enforced by application logic rather than database-level foreign-key constraints.

This is an intentional characteristic of the current implementation.

It allows the reconciliation engine to work with imported financial records and external identifiers without requiring every source system identifier to exist as a strict relational foreign key.

The trade-off is that referential integrity must be carefully maintained by the application and validation layer.

---

# Identifier Strategy

The system uses two identifier categories.

## Database IDs

Every table has an integer:

```text
id
```

used as the database primary key.

## Domain/Application IDs

Financial and operational entities additionally expose stable string identifiers such as:

```text
merchant_id
order_id
payment_id
settlement_id
refund_id
fee_id
adjustment_id
run_id
exception_id
investigation_id
```

These identifiers are indexed and, where appropriate, unique.

The separation provides a stable application-level identity without exposing database implementation details as the primary business identifier.

---

# Indexing Strategy

The schema indexes identifiers used frequently in lookup and reconciliation operations.

Important indexed fields include:

```text
merchant_id
order_id
payment_id
settlement_id
refund_id
fee_id
adjustment_id
run_id
transaction_id
exception_id
exception_type
investigation_id
```

These indexes support common operations such as:

* Finding a payment by payment identifier
* Locating settlements
* Matching orders and payments
* Finding reconciliation results for a run
* Looking up exceptions
* Retrieving investigation history
* Retrieving evidence
* Finding audit history for a transaction

---

# Reconciliation Data Model

The reconciliation layer connects execution-level and transaction-level state.

```text
ReconciliationRun
        │
        │ run_id
        ▼
ReconciliationResult
        │
        │ transaction_id
        ▼
ExceptionRecord
```

The run answers:

> What happened during this reconciliation execution?

The result answers:

> What happened to this specific transaction?

The exception answers:

> Which transactions require investigation or human action?

---

# Exception Investigation Model

The exception investigation model is intentionally append-oriented.

```text
Exception
   │
   ├──────── Evidence
   │
   ├──────── Investigation
   │             │
   │             ├── deterministic_analysis
   │             └── ai_analysis
   │
   └──────── HumanReview
```

This allows the system to retain:

* Supporting evidence
* Deterministic reasoning
* AI reasoning
* AI fallback state
* Human decisions

without replacing earlier records.

---

# Auditability Model

The system maintains multiple levels of traceability.

### Reconciliation level

```text
run_id
```

identifies a reconciliation execution.

### Transaction level

```text
transaction_id
```

identifies the financial transaction involved in reconciliation.

### Exception level

```text
exception_id
```

identifies an investigation-worthy discrepancy.

### Investigation level

```text
investigation_id
```

identifies one persisted investigation attempt.

### Audit level

```text
transaction_id + actor + action + timestamp
```

provides the transaction-level operational history.

---

# Database Migrations

Alembic manages schema evolution.

Current migration history:

```text
f91af069443f
    ↓
c451329fa386
```

## Initial Financial Schema

Revision:

```text
f91af069443f
```

Creates the initial financial and reconciliation schema.

## Investigation Schema

Revision:

```text
c451329fa386
```

Adds the persisted `investigations` table.

The current database migration head is:

```text
c451329fa386
```

---

# Migration Safety

The backend container runs migrations before starting the API:

```text
alembic upgrade head
        ↓
uvicorn
```

This ensures that a newly deployed environment attempts to bring its schema to the current migration head before serving application traffic.

Migration execution should remain version-controlled and reproducible.

---

# Data Integrity Principles

## Monetary Values

Financial amounts use exact decimal database types.

```text
NUMERIC(18,2)
```

## Explicit Missing Values

A missing settlement uses:

```text
actual_amount = NULL
```

rather than silently converting the missing record into a zero-valued settlement.

## Deterministic Source of Truth

Reconciliation results are produced by deterministic application logic.

AI-generated analysis is persisted separately and does not replace deterministic financial state.

## Append-Oriented Investigation History

Multiple investigations can be retained for the same exception.

## Human Accountability

Human reviews persist:

* Reviewer
* Action
* Reason
* Timestamp

## Operational Auditability

Important transaction actions are represented in `audit_logs`.

---

# Current Limitations

The current database design intentionally has several areas that can be strengthened in a future production iteration.

### Explicit Foreign Keys

The current schema relies on application-level relationships rather than SQL foreign-key constraints.

A production implementation could introduce explicit foreign keys where external-system identifier semantics allow it.

### Stronger Database-Level Constraints

Some domain states are currently represented through application-level validation.

Future versions could add database constraints for:

* Allowed statuses
* Allowed review actions
* Non-negative financial values where appropriate
* Confidence ranges
* State-transition rules

### Source-System Metadata

A production ingestion layer could additionally track:

* Source system
* Import batch
* File identifier
* Ingestion timestamp
* Source checksum
* Schema version

This would strengthen lineage and reproducibility.

---

# Design Rationale

The database is designed to support a financial-control workflow rather than a generic CRUD application.

The core principle is:

```text
Financial records
       ↓
Deterministic reconciliation
       ↓
Persisted discrepancy
       ↓
Evidence
       ↓
Investigation
       ↓
Human decision
       ↓
Audit trail
```

Every stage leaves enough persisted information for the next stage to operate without requiring an LLM to reconstruct financial truth.

---

# Summary

RazorRecon AI's PostgreSQL schema separates financial records, reconciliation state, exception intelligence, investigation state, human decisions, and audit history.

The key architectural principle is:

> **The database stores financial truth and operational evidence; AI provides an additional reasoning layer over that evidence.**

This allows reconciliation correctness, investigation reliability, and auditability to remain independent of external AI-provider availability.
