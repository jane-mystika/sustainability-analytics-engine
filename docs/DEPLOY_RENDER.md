# Render Deployment Guide

This repo is designed for Docker + a reverse proxy (Caddy), but you can also deploy it on Render by running the backend and frontend as two separate services.

## Create 2 services

### 1) Backend (FastAPI)
- Create a **Web Service** from `mini/backend-python`
- Start command (non-Docker): `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Or use the provided `mini/backend-python/Dockerfile` and set the service port to `8000`

**Environment variables (backend)**
- `ENVIRONMENT=production`
- `CORS_ORIGINS=https://<your-frontend-onrender-domain>`
- `TRUSTED_HOSTS=<your-backend-onrender-domain>`
- `SEED_DEMO_DATA=false` (recommended)
- `ADMIN_USER_ID=admin`
- `ADMIN_PASSWORD=<set-a-strong-password>`

Health checks:
- `/health`
- `/ready`

### 2) Frontend (Streamlit)
- Create a **Web Service** from `mini/frontend-streamlit`
- Start command (non-Docker): `streamlit run app.py --server.address=0.0.0.0 --server.port $PORT`
- Or use the provided `mini/frontend-streamlit/Dockerfile` and set the service port to `8501`

**Environment variables (frontend)**
- `API_URL=https://<your-backend-onrender-domain>`
- `ADMIN_USER_ID=admin`
- `ADMIN_PASSWORD=<same-as-backend>`

## Verify
- Open the frontend URL and confirm the sidebar shows `API: https://...`
- Visit the backend URL `/docs` and `/health` to confirm the API is reachable

## Common issue: "Backend not reachable"
If you see a message like "Backend not reachable", it almost always means the frontend `API_URL` env var is still pointing at `http://localhost:8000` (the local dev default).
