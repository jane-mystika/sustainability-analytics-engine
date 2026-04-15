# Sustainability Analytics API

FastAPI backend for metrics, scoring, forecasting, alerts, and admin workflows.

## Local run
1. `python -m venv .venv`
2. `.venv\Scripts\activate`
3. `pip install -r requirements.txt`
4. Copy `.env.example` to `.env`
5. `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`

## PaaS note (Render, etc.)
If your platform provides a dynamic port, run Uvicorn with the provided `PORT`:
- `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

## Important environment variables
- `ENVIRONMENT`: `development` or `production`
- `DATA_SOURCE`: `csv` or `mysql`
- `DATA_CSV_PATH`: CSV path relative to repo root. Default: `backend-python/data/sample_data.csv`
- `MYSQL_URL`: SQLAlchemy connection string when using MySQL
- `CORS_ORIGINS`: comma-separated allowed frontend origins
- `TRUSTED_HOSTS`: comma-separated allowed hostnames
- `SEED_DEMO_DATA`: `true` for local demo mode, `false` for production
- `ADMIN_*`: bootstrap admin account settings

## Operational endpoints
- `GET /`
- `GET /health`
- `GET /ready`
- `GET /docs`
