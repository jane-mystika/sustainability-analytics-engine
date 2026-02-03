# Sustainability Analytics API

FastAPI backend for metrics, scoring, forecasting, and alerts.

## Run (local)
1. Create a virtual environment and install dependencies:
   - `python -m venv .venv`
   - `.venv\\Scripts\\activate`
   - `pip install -r requirements.txt`
2. Copy `.env.example` to `.env` and adjust as needed.
   - For CSV: keep `DATA_SOURCE=csv`.
   - For MySQL: set `DATA_SOURCE=mysql` and `MYSQL_URL`.
3. Start the API:
   - `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`

## Endpoints
- `GET /health`
- `GET /facilities`
- `GET /metrics`
- `GET /score`
- `GET /forecast`
- `GET /alerts`
