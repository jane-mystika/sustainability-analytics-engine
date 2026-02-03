# Semiconductor Sustainability Analytics Engine

This project delivers a multi-facility sustainability analytics engine for semiconductor/electronics manufacturing.

## Structure
- `frontend-streamlit/` Streamlit dashboard
- `backend-python/` FastAPI backend
- `database-mysql/` MySQL schema + sample CSV

## Quick Start (Local)
1. Backend
   - `cd backend-python`
   - `python -m venv .venv`
   - `.venv\\Scripts\\activate`
   - `pip install -r requirements.txt`
   - `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
2. Frontend
   - `cd ..\\frontend-streamlit`
   - `python -m venv .venv`
   - `.venv\\Scripts\\activate`
   - `pip install -r requirements.txt`
   - `streamlit run app.py`

## Sample Data
The app defaults to `database-mysql/seed/sample_data.csv`.  
You can also load it into MySQL using `database-mysql/schema.sql`.

## AWS Notes
See `docs/DEPLOY_AWS.md` for a deployment-ready outline.
