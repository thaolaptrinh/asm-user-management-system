# FastAPI + Next.js Template

A production-ready full-stack template: **FastAPI** backend (MySQL, JWT auth) and **Next.js 16** frontend (React 19, TypeScript, shadcn/ui). Use as a starting point for new projects or reference implementation.

## Stack

| Layer     | Tech |
|----------|------|
| **Backend**  | FastAPI, MySQL, SQLModel, Pydantic, JWT, Alembic (uv) |
| **Frontend** | Next.js 16, React 19, TypeScript, Tailwind CSS, shadcn/ui (Bun) |
| **Testing**  | Pytest (backend), Vitest + Playwright (frontend) |
| **Infra**    | Docker Compose, Traefik (optional) |

## Prerequisites

- [Docker](https://www.docker.com/) and Docker Compose
- [Make](https://www.gnu.org/software/make/) (optional; you can run the underlying `docker compose` commands directly)

## Quick start

1. **Copy env and set required variables:**

   ```bash
   cp .env.example .env
   ```

   Edit `.env` and set at least: `SECRET_KEY`, `MYSQL_PASSWORD`, `MYSQL_ROOT_PASSWORD`, `FIRST_SUPERUSER_PASSWORD`.

2. **Start infrastructure and run migrations:**

   ```bash
   make up        # DB, Adminer, Mailcatcher
   make migrate   # Alembic migrations
   make seed      # Initial superuser
   ```

3. **Start the app (backend + frontend with hot reload):**

   ```bash
   make dev
   ```

4. **Open in browser:**

   | Service   | URL |
   |-----------|-----|
   | Frontend  | http://localhost:3000 |
   | API docs  | http://localhost:8000/docs |
   | Adminer   | http://localhost:8080 |

## Commands

| Command | Description |
|---------|-------------|
| `make help` | List all Make targets |
| `make up` | Start infrastructure (db, adminer, mailcatcher) |
| `make down` | Stop all services |
| `make dev` | Start backend + frontend with watch |
| `make dev-be` | Backend only |
| `make dev-fe` | Frontend only |
| `make migrate` | Run pending migrations |
| `make migration <name>` | Create a new migration (e.g. `make migration add_posts_table`) |
| `make seed` | Seed database |
| `make test` | Backend (pytest + coverage) + Frontend (Vitest + coverage) |
| `make test-e2e` | E2E tests (Playwright) |
| `make lint` | Lint frontend (Biome) + backend (Ruff) |
| `make format` | Format backend (Ruff) |

Run `make help` for the full list.

## Docs

- [Development](docs/implementation/development.md) — Running locally, Make commands, adding features
- [Testing](docs/testing/README.md) — Backend (Pytest), frontend (Vitest, Playwright)
- [Deployment](docs/implementation/deployment.md) — Docker Compose, env vars, security
- [Backend](backend/README.md) — API structure, migrations, uv
- [Frontend](frontend/README.md) — App Router, scripts, testing

## Project layout

```
├── backend/           # FastAPI app (app/, tests/, migrations/)
├── frontend/          # Next.js app (src/app/, components/, tests/)
├── scripts/           # run-backend-tests.sh, reset-test-db.sh, etc.
├── docs/              # implementation, testing
├── compose.yml        # Production-style Compose
├── compose.override.yml  # Local dev (ports, volumes, watch)
├── .env.example       # Env template (copy to .env)
└── Makefile           # Convenience targets
```

## Using this template

1. Clone the repo or use it as a GitHub template.
2. Copy `.env.example` to `.env` and set secrets.
3. Run `make up && make migrate && make seed && make dev`.
4. Customize backend models, API routes, and frontend pages to your needs.

For detailed workflows, see [Development](docs/implementation/development.md).
