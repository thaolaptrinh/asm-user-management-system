# Deployment Guide

Guide to deploying the FastAPI + Next.js template to staging or production.

## Environment variables

Ensure all required variables are set in `.env` (or your platform’s env):

- **DOMAIN:** Primary domain (e.g. `example.com`) — used by Traefik and TLS.
- **NEXT_PUBLIC_API_URL:** Backend API URL used by the frontend (e.g. `https://api.example.com`).
- **FRONTEND_HOST:** Frontend URL (e.g. `https://dashboard.example.com`) — used by the backend for links in emails.
- **ENVIRONMENT:** `staging` or `production`.
- **SECRET_KEY, MYSQL_*, FIRST_SUPERUSER, FIRST_SUPERUSER_PASSWORD:** See [.env.example](../../.env.example). **Do not** use the default value `changethis` in production.
- **SENTRY_DSN:** (optional) Sentry for the backend.
- **DOCKER_IMAGE_BACKEND, DOCKER_IMAGE_FRONTEND:** Docker image names if using a custom registry.

## Docker Compose (production-style)

`compose.yml` is configured with:

- **db:** MySQL 8, persistent volume.
- **prestart:** Runs migrations + seed (once on deploy).
- **backend:** FastAPI, depends on db and prestart.
- **frontend:** Next.js standalone build.
- **adminer:** In the `tools` profile, can be enabled when needed.

Traefik labels are used when running behind Traefik (HTTPS, hosts `api.${DOMAIN}`, `dashboard.${DOMAIN}`, etc.).

### Running with Compose

1. Build and push images (if using a registry):

   ```bash
   docker compose build
   docker compose push
   ```

2. On the server, set env (DOMAIN, SECRET_KEY, MYSQL_PASSWORD, …) then:

   ```bash
   docker compose up -d
   ```

3. Adminer (optional): `docker compose --profile tools up -d` to enable adminer.

### Traefik network

`compose.yml` declares network `traefik-public: external: true`. Create the network before running:

```bash
docker network create traefik-public
```

If you are not using Traefik, adjust or simplify labels and network for your setup.

## Deploying Frontend / Backend separately

### Frontend (Vercel / static host)

- Build: `cd frontend && bun run build`.
- Set `NEXT_PUBLIC_API_URL` to your production backend URL.
- Vercel: deploy via Git or `vercel --prod`; configure env in the dashboard.

### Backend (Render, Railway, VM, …)

- Provide all required env (SECRET_KEY, MYSQL_*, FIRST_SUPERUSER*, CORS, FRONTEND_HOST, …).
- Run migrations on startup (e.g. prestart script or one-off job): `alembic upgrade head`.
- Run app: `fastapi run app/main.py` or via Gunicorn/Uvicorn (see Dockerfile CMD).

## Security

- Change all default secrets; use a secret manager or secure env.
- CORS: `BACKEND_CORS_ORIGINS` should only include your real frontend origin(s).
- In production use HTTPS (Traefik or another reverse proxy).

## See also

- [Development](development.md) — running locally.
- [Testing](../testing/README.md) — tests and coverage.
- [Backend README](../../backend/README.md) — migrations, backend tests.
