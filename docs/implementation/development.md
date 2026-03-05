# Development Guide

Guide to running the development environment for the FastAPI + Next.js template.

## Requirements

- [Docker](https://www.docker.com/) and Docker Compose
- [uv](https://docs.astral.sh/uv/) (backend) and [Bun](https://bun.sh/) or Node.js 20+ (frontend)
- Make (optional, for using `make` commands)

## Quick start

1. Copy the env file and set environment variables:

   ```bash
   cp .env.example .env
   # Edit .env: SECRET_KEY, MYSQL_PASSWORD, FIRST_SUPERUSER_PASSWORD
   ```

2. Start infrastructure and app:

   ```bash
   make up      # DB, Adminer, Mailcatcher
   make migrate # Run Alembic migrations
   make seed    # Seed initial data
   make dev     # Run backend + frontend with watch
   ```

3. Open:

   - **Frontend:** http://localhost:3000  
   - **Backend API docs:** http://localhost:8000/docs  
   - **Adminer:** http://localhost:8080  

## Make commands (from repo root)

### Development

| Command | Description |
|--------|-------------|
| `make dev` | Run full stack with watch (frontend :3000, backend :8000) |
| `make dev-full` | Run with proxy (production-like, requires port 80) |
| `make dev-fe` | Frontend only |
| `make dev-be` | Backend only |
| `make up` | Infrastructure only (db, adminer, mailcatcher) |
| `make down` | Stop all |
| `make logs` | View logs (follow) |
| `make ps` | List containers |

### Database

| Command | Description |
|--------|-------------|
| `make migrate` | Run pending migrations |
| `make migrate-fresh` | Drop tables and re-run all migrations |
| `make migrate-rollback` | Rollback last migration |
| `make migrate-status` | Show current revision |
| `make migration <name>` | Create new migration (e.g. `make migration add_status_to_users`) |
| `make seed` | Seed database |
| `make db-reset` | Remove DB volume and re-run prestart |

### Tools

| Command | Description |
|--------|-------------|
| `make test` | Backend (pytest + coverage) + Frontend (unit + coverage) |
| `make test-e2e` | E2E (Playwright) |
| `make lint` | Lint backend + frontend |
| `make format` | Format backend (ruff) |
| `make help` | List all targets |

## Running backend without Docker

From the `backend/` directory:

```bash
uv sync
source .venv/bin/activate  # Linux/macOS
# .env is at repo root; backend reads env_file="../.env"
fastapi run --reload app/main.py
```

Backend runs at http://localhost:8000.

## Running frontend without Docker

From the `frontend/` directory:

```bash
bun install
bun run dev
```

Frontend runs at http://localhost:3000. Ensure `NEXT_PUBLIC_API_URL` points to the backend (default from root `.env`).

## Docker Compose override

`compose.override.yml` is used for local dev: port mapping, volume mounts, mailcatcher, watch. It does not affect production.

- Backend: `fastapi run --reload app/main.py`, syncs `./backend`.
- Frontend: syncs `./frontend`, rebuilds on `package.json` / `bun.lock` changes.

## Adding features

- **Backend:** Models in `backend/app/models.py`, API in `backend/app/api/`, CRUD in `backend/app/crud.py`. Create migration: `make migration <name>`.
- **Frontend:** App Router in `frontend/src/app/`, components in `frontend/src/components/`, hooks in `frontend/src/hooks/`. Regenerate API client: `bun run generate-client` (after backend OpenAPI changes).

See also [Backend README](../../backend/README.md) and [Frontend README](../../frontend/README.md).
