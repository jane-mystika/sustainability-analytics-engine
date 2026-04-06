# Sustainability Analytics Dashboard

Streamlit frontend for sustainability scoring, alerts, forecasting, and admin operations.

## Local run
1. `python -m venv .venv`
2. `.venv\Scripts\activate`
3. `pip install -r requirements.txt`
4. Copy `.env.example` to `.env`
5. `streamlit run app.py`

## Important environment variables
- `APP_TITLE`: dashboard title shown in the UI
- `ENVIRONMENT`: `development` or `production`
- `API_URL`: backend base URL
- `DATA_CSV_PATH`: local fallback dataset path
- `REQUEST_TIMEOUT`: API request timeout in seconds

## Deployment note
In the production compose stack, this app talks to the backend over the internal Docker network while Caddy serves the public domain and HTTPS.
