# Domain Deployment Guide

Use this when you want the app to feel like a real website with your own domain.

## What you need
- A Linux server with Docker installed
- A domain name you control
- Ports `80` and `443` open on the server firewall

## Steps
1. Copy `.env.production.example` to `.env.production`
2. Set `DOMAIN` to something like `analytics.yourdomain.com`
3. Change the admin email and password
4. Point the domain's DNS A record to the server IP
5. Run:
   - `docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build`

## What happens
- Caddy receives public traffic
- Caddy automatically provisions TLS certificates
- Requests for `/` go to the Streamlit dashboard
- Requests for `/api/*`, `/docs`, `/health`, and `/ready` go to the FastAPI backend

## Important limitation
This repo is deployment-ready, but I cannot register a domain or update DNS from inside your local workspace. After you choose a real domain and point it to the server, the included setup will handle the app serving and HTTPS layer.
