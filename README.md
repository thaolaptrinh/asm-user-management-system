# FastAPI + Next.js Template

Production-ready full-stack template with FastAPI backend and Next.js frontend.

## Quick Start

```bash
cp .env.example .env
make secrets          # Generate secret keys
make dev              # Start all services
```

- **Frontend:** http://localhost:3000
- **API Docs:** http://localhost:8000/api/v1/docs

---

## Commands

| Command | Description |
|---------|-------------|
| `make dev` | Start all services (hot reload) |
| `make dev-build` | Rebuild and restart |
| `make secrets` | Generate secret keys |
| `make migrate` | Run DB migrations |
| `make seed` | Seed DB with data |
| `make db-reset` | Fresh DB (migrate + seed) |
| `make generate-client` | Regenerate API client |
| `make test` | Backend + Frontend tests |
| `make test-be` | Backend tests (coverage) |
| `make test-fe` | Frontend tests |
| `make test-e2e` | E2E tests |
| `make lint` | Lint all code |
| `make typecheck` | Type-check all code |
| `make build` | Build Docker images |
| `make shell-be` | Backend container shell |
| `make shell-fe` | Frontend container shell |
| `make shell-db` | Database shell |
| `make logs-be` | Backend logs |
| `make logs-fe` | Frontend logs |
| `make ps` | Check container status |
| `make stop` | Stop all services |
| `make down` | Stop and remove containers |
| `make restart` | Restart all services |

Run `make help` for all commands.

---

## Architecture

**Backend:** Routes → Services → Repositories → DB

**Frontend:** Pages → API Client → React Query → Components

```
┌─────────────┐     ┌─────────────┐
│   Next.js   │────▶│   FastAPI   │
│  (Frontend) │     │  (Backend)  │
└─────────────┘     └──────┬──────┘
                           │
                      ┌────▼─────┐
                      │  MySQL/   │
                      │ Postgres │
                      └──────────┘
```

---

## Project Structure

```
├── backend/           # FastAPI app (Docker)
│   ├── app/
│   │   ├── api/v1/routes/   # Endpoints
│   │   ├── services/         # Business logic
│   │   ├── repositories/     # Data access
│   │   ├── models/           # ORM
│   │   └── schemas/          # Validation
│   ├── alembic/versions/     # Migrations
│   └── tests/                # Pytest
├── frontend/          # Next.js app (Docker)
│   ├── src/app/              # App Router
│   ├── src/client/           # API client
│   ├── src/components/       # Components
│   └── tests/                # Playwright
├── docker/            # Docker configs
└── Makefile          # All commands
```

---

## Features

**Backend:**
- Layered architecture (Services/Repositories)
- JWT auth with HttpOnly cookies
- MySQL/PostgreSQL support
- Alembic migrations
- Pydantic validation
- Rate limiting
- Seed data

**Frontend:**
- Next.js App Router
- Auto-generated API client
- shadcn/ui components
- Dark mode support
- React Query
- React Hook Form + Zod
- Playwright E2E tests

---

## Environment

Required in `.env` (generate with `make secrets`):

```bash
APP_KEY=
JWT_SECRET_KEY=
DB_PASSWORD=
DB_ROOT_PASSWORD=
FIRST_SUPERUSER_PASSWORD=
```

**Database switching:**

```bash
# MySQL
DB_CONNECTION=mysql
DB_HOST=db-mysql

# PostgreSQL
DB_CONNECTION=postgres
DB_HOST=db-postgres
```

**Frontend API URL:** Set `NEXT_PUBLIC_API_URL` in root `.env`

---

## Development Workflow

All development in Docker containers:

```bash
make dev              # Start all
make ps               # Check status
make shell-be         # Backend shell
make shell-fe         # Frontend shell
make logs-be          # Backend logs
make logs-fe          # Frontend logs
make dev-build        # Rebuild
make down && make dev  # Fresh start
```

---

## Deployment

**Local:** `make dev`

**Production:**

```bash
make build            # Build images
make up                # Start production stack
```

Set `APP_ENV=production` to disable docs and enable security.

---

## Documentation

- **[Backend](backend/README.md)** - Architecture, features
- **[Frontend](frontend/README.md)** - Components, API client
- **[Development](docs/implementation/development.md)** - Workflows
- **[Testing](docs/testing/README.md)** - Backend & frontend tests

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| **Can't connect to DB** | `make shell-db` → check DB status |
| **Tests failing** | `make db-reset` |
| **Import errors** | `make dev-build` |
| **Migration issues** | `make migrate-status` |
| **Container issues** | `make ps` → check, then `make down && make dev` |
| **Everything stuck** | `make down && make dev` |
