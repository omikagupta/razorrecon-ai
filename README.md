# RazorRecon AI

RazorRecon AI reconciles payment and settlement data, turns mismatches into
actionable exceptions, and supports evidence-backed AI investigation and human
review.

## Quick start

Prerequisites: Python 3.11+, Docker (for PostgreSQL), and optionally a Gemini
API key for AI-assisted investigation.

```powershell
docker compose up -d
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
Copy-Item .env.example .env
```

Update `DATABASE_URL` in `.env` for your local PostgreSQL instance. The
included Docker Compose configuration uses:

```text
postgresql+psycopg2://razorrecon:razorrecon@localhost:5432/razorrecon
```

Initialize and populate the database, then run a reconciliation:

```powershell
python scripts/init_db.py
python scripts/ingest_transactions.py
python scripts/persist_reconciliation.py
python scripts/generate_evidence.py
```

Start the API from the project root:

```powershell
$env:PYTHONPATH = "backend"
uvicorn app.main:app --reload
```

Open <http://127.0.0.1:8000/docs> for the interactive API documentation.

## API

All routes are versioned under `/api/v1`. The main workflow is:

1. List exceptions with `GET /api/v1/exceptions`.
2. Inspect one exception with `GET /api/v1/exceptions/{exception_id}`.
3. Request an investigation with `POST /api/v1/exceptions/{exception_id}/investigate`.
4. Submit a decision with `POST /api/v1/exceptions/{exception_id}/review`.

The full endpoint and payload reference is in [docs/api.md](docs/api.md).

## AI configuration

AI investigation is optional. Set `LLM_PROVIDER=none` to use the deterministic
fallback only. To use Gemini, set `LLM_PROVIDER=gemini`, `LLM_MODEL`, and
`GEMINI_API_KEY` in `.env`. Do not commit your `.env` file.

## Tests

Run tests from the project root with the backend on the Python import path:

```powershell
$env:PYTHONPATH = "backend"
pytest
```

## Documentation

- [API reference](docs/api.md)
- [Architecture](docs/architecture.md)
