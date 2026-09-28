# Development Guide

## Prerequisites

Python 3.12+ and Node 22+ are used in CI. Install backend packages with `pip install -r backend/requirements.txt pytest`; install frontend packages with `npm install --prefix frontend`.

## Run locally

```powershell
uvicorn backend.app.main:app --reload
npm run dev --prefix frontend
```

Set `VITE_API_BASE_URL=http://localhost:8000/api/v1` if the frontend is not using the default endpoint. Never commit `.env`, model weights, uploads, or reviewed decisions containing personal information.

## Data review workflow

Use `ml/data/review_sheets/` and `cleaned_manifest.csv`. Record reviewer, timestamp, and a decision in a decision CSV, then apply it through `scripts/apply_review_decisions.py`. Do not edit source images or mass-approve them programmatically.

## Quality conventions

Use type hints, strict TypeScript, modular boundaries, and pytest. API errors use safe messages; detailed server failures are logged without tokens or passwords. Run `python -m compileall -q backend ml scripts`, `python -m pytest -q`, and `npm run build --prefix frontend` before a handoff.
