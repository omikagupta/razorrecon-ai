# Demo guide

This walkthrough uses only the repository's synthetic data. Do not enter live payment data or a production Gemini key into the demo environment.

## 1. Start the stack

From the repository root, start the containers:

```powershell
docker compose up --build
```

Wait until PostgreSQL is healthy and the backend starts. In a second terminal, verify it:

```powershell
Invoke-RestMethod http://localhost:8000/api/v1/health | ConvertTo-Json
```

Expected result: `status` and `database` are `healthy`.

## 2. Open the application

Open the frontend at `http://localhost:5173` and the interactive backend API at `http://localhost:8000/docs`. Explain that the frontend is a view over persisted reconciliation results, not a calculation engine.

## 3. Run reconciliation

If the database has already been populated with synthetic records, create a reconciliation run:

```powershell
Invoke-RestMethod -Method Post http://localhost:8000/api/v1/reconciliation-runs | ConvertTo-Json -Depth 8
```

Point out the generated `run_id`, totals, match count, and exception count. If the database has not been seeded, use the project's initialization and ingestion scripts from an environment that can reach the Compose database, then repeat this request.

## 4. Show financial results

Request the dashboard summary:

```powershell
Invoke-RestMethod http://localhost:8000/api/v1/dashboard/summary | ConvertTo-Json -Depth 8
```

Explain that totals come from `ReconciliationResult` records. `total_difference` is exposure (absolute differences); a missing settlement is persisted as the full expected amount less zero.

## 5. Inspect an exception

List open exceptions and copy an `exception_id`:

```powershell
Invoke-RestMethod 'http://localhost:8000/api/v1/exceptions?status=OPEN&page_size=10' | ConvertTo-Json -Depth 8
```

Then replace `<exception_id>` below:

```powershell
Invoke-RestMethod 'http://localhost:8000/api/v1/exceptions/<exception_id>' | ConvertTo-Json -Depth 10
```

Walk through the deterministic classification and the evidence entries for the payment, settlement, refund, fee, and adjustment records.

## 6. Demonstrate investigation and fallback

Run an investigation:

```powershell
Invoke-RestMethod -Method Post 'http://localhost:8000/api/v1/exceptions/<exception_id>/investigate' | ConvertTo-Json -Depth 10
```

With no Gemini provider configured, the expected outcome is `DETERMINISTIC_FALLBACK` with `UNAVAILABLE`; that is intentional graceful degradation. With a configured provider, show `AI_ASSISTED` only when its JSON passes schema validation. In either case, emphasize that the deterministic analysis remains the financial source of truth.

## 7. Show auditability

Submit a human review only for an `OPEN` exception:

```powershell
$body = @{ reviewer = 'demo-operator'; action = 'ESCALATE'; reason = 'Requires settlement file confirmation.' } | ConvertTo-Json
Invoke-RestMethod -Method Post -ContentType 'application/json' -Body $body 'http://localhost:8000/api/v1/exceptions/<exception_id>/review' | ConvertTo-Json
```

Reload the exception details and investigation history to show the review and audit trail. Do not use this action on a shared demo database unless the state change is desired.

## 8. Stop the demo

Press `Ctrl+C` in the Compose terminal, then remove containers when finished:

```powershell
docker compose down
```

The named PostgreSQL volume is preserved. Use `docker compose down -v` only when deliberately discarding the local synthetic database.
