# Sustainability Analytics Cloud

Production-ready starter for a sustainability analytics platform focused on semiconductor and electronics manufacturing.

## What changed
- Centralized backend configuration with safer production defaults
- Startup lifecycle for predictable seeding and health checks
- Trusted host and CORS configuration from environment variables
- Streamlit dashboard with environment-aware API status and polished theme
- Dockerfiles for backend and frontend
- `docker-compose.prod.yml` plus Caddy reverse proxy for HTTPS and custom domains

## Project structure
- `backend-python/` FastAPI API
- `frontend-streamlit/` Streamlit dashboard
- `database-mysql/` schema and sample data
- `deploy/` reverse proxy configuration

For deployment, the backend also includes its own CSV at `backend-python/data/sample_data.csv` so it can run without depending on files outside the backend service root.

## Local development
1. Backend
   - `cd backend-python`
   - `python -m venv .venv`
   - `.venv\Scripts\activate`
   - `pip install -r requirements.txt`
   - Copy `.env.example` to `.env`
   - `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
2. Frontend
   - `cd ..\frontend-streamlit`
   - `python -m venv .venv`
   - `.venv\Scripts\activate`
   - `pip install -r requirements.txt`
   - Copy `.env.example` to `.env`
   - `streamlit run app.py`

## Production deployment
1. Copy `.env.production.example` to `.env.production`
2. Replace `DOMAIN`, admin credentials, and any data source settings
3. Point your domain's DNS A record to your server IP
4. On the server run:
   - `docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build`
5. Visit `https://your-domain`

Caddy will provision HTTPS automatically once the domain points to the server and ports `80/443` are open.

## Render deployment (two services)
If you're deploying on Render (or any PaaS that doesn't run `docker compose`), deploy the backend and frontend as separate services and set the frontend `API_URL` to the backend URL. See `docs/DEPLOY_RENDER.md`.

## Useful endpoints
- Website: `/`
- API docs: `/docs`
- Health: `/health`
- Readiness: `/ready`
- API through proxy: `/api/...`

## Notes
- In production, demo seeding should stay disabled with `SEED_DEMO_DATA=false`
- The repo still uses in-memory operational stores for users, alerts, assignments, and notifications; for a larger rollout, move those into a database next
- I can also scaffold Terraform, AWS deployment files, or CI/CD if you want to take this the rest of the way
