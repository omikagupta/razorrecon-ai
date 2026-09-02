# RazorRecon AI — Reconciliation Data Flow

```mermaid id="3h5kq2"
flowchart TD

    A["Synthetic Financial Data"] --> B["Ingestion Service"]

    B --> C["Normalize Financial Records"]

    C --> D["Load Payment Records"]
    C --> E["Load Settlement Records"]

    D --> F["Transaction Matching"]
    E --> F

    F --> G{"Matching Settlement Found?"}

    G -->|Yes| H["Compare Expected vs Actual Amount"]

    G -->|No| I["Missing Settlement"]

    H --> J{"Amounts Match?"}

    J -->|Yes| K["MATCHED"]

    J -->|No| L["AMOUNT_MISMATCH"]

    I --> M["MISSING_SETTLEMENT"]

    K --> N["Persist Reconciliation Result"]
    L --> N
    M --> N

    L --> O["Create Exception"]
    M --> O

    O --> P["Collect Evidence"]

    P --> Q["Generate Deterministic Analysis"]

    Q --> R["Investigation"]

    R --> S{"AI Provider Available?"}

    S -->|Yes| T["AI-Assisted Investigation"]
    S -->|No| U["Deterministic Fallback"]

    T --> V["Validate Investigation"]
    V --> W{"Valid AI Response?"}

    W -->|Yes| X["Persist AI Investigation"]
    W -->|No| U

    U --> Y["Persist Fallback Investigation"]

    X --> Z["Human Review"]
    Y --> Z

    Z --> AA["Audit Log"]
```

## Financial Calculation Rule

For a reconciliation result with a settlement:

```text
difference = expected_amount - actual_amount
```

For a missing settlement:

```text
actual_amount = 0
difference = expected_amount
```

This ensures that missing settlements contribute their full expected amount to the financial exposure reported by the dashboard.

## Processing Responsibilities

| Stage                  | Responsibility                                    |
| ---------------------- | ------------------------------------------------- |
| Ingestion              | Load financial source data                        |
| Normalization          | Prepare records for comparison                    |
| Matching               | Identify corresponding payment/settlement records |
| Reconciliation         | Determine financial status                        |
| Exception Detection    | Create exceptions for discrepancies               |
| Evidence Collection    | Gather persisted supporting facts                 |
| Deterministic Analysis | Establish factual investigation context           |
| AI Investigation       | Interpret evidence and explain discrepancies      |
| Fallback               | Preserve investigation capability when AI fails   |
| Human Review           | Make the operational decision                     |
| Audit Log              | Record the review action                          |

## Critical Design Boundary

The LLM is **not** responsible for:

* matching transactions
* calculating monetary differences
* determining dashboard totals
* creating financial evidence
* inventing financial records
* deciding whether a payment actually settled

Those responsibilities remain within deterministic application logic and PostgreSQL-backed data.

The AI layer operates downstream of reconciliation and assists with interpretation.
