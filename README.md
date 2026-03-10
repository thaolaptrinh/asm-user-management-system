# User Management System with TOTP Authentication

A web-based user management system with two-factor authentication (2FA) using TOTP. Users authenticate with email/password and a time-based one-time code from an authenticator app such as Google Authenticator.

**Repository**: https://github.com/thaolaptrinh/asm-user-management-system

---

## Features

- User registration and login/logout
- Two-factor authentication (TOTP) with QR code setup
- Recovery codes for account recovery
- Replay attack prevention (used codes are blocked)
- User listing, creation, and deletion
- All protected operations require valid authentication

## System Architecture

```
┌─────────────┐    HTTP    ┌─────────────┐    SQL    ┌─────────────┐
│  Frontend   │──────────▶│   Backend   │──────────▶│   Database  │
│  (Next.js)  │           │  (FastAPI)  │           │   (MySQL)   │
│   :3000     │           │   :8000     │           │   :3306     │
└─────────────┘           └─────────────┘           └─────────────┘
    Docker                    Docker                    Docker
```

All services are containerized and orchestrated with Docker Compose.

## Technology Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 16, TypeScript 5, React 19, Tailwind CSS 4, shadcn/ui |
| Forms | React Hook Form + Zod |
| Backend | FastAPI 0.115+, Python 3.12 |
| ORM | SQLAlchemy 2.0 (async) + Alembic 1.14 |
| Auth | PyJWT + bcrypt + PyOTP 2.9 |
| Database | MySQL 8.0 |
| Infrastructure | Docker, Docker Compose v2, GNU Make |
| Testing | Pytest (backend), Playwright (E2E) |

## Repository Structure

```
asm-user-management-system/
├── backend/
│   ├── app/
│   │   ├── api/v1/routes/      # API endpoints (auth, users, totp)
│   │   ├── core/               # Config, security, dependencies
│   │   ├── models/             # SQLAlchemy ORM models
│   │   ├── schemas/            # Pydantic request/response schemas
│   │   └── services/           # Business logic
│   ├── tests/                  # Pytest test suite
│   ├── alembic/                # Database migrations
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/                # Next.js App Router pages
│   │   ├── components/         # React components
│   │   └── lib/                # API client, utilities
│   └── Dockerfile
├── docker/
│   ├── compose.base.yml
│   ├── compose.dev.yml
│   ├── compose.test.yml
│   └── compose.prod.yml
├── Makefile                    # Development command wrappers
└── .env.example                # Environment variable template
```

## Setup Requirements

### Prerequisites

| Tool | Version | Notes |
|------|---------|-------|
| Docker | 20.10+ | https://docs.docker.com/get-docker/ |
| Docker Compose | v2.x | Included with Docker Desktop |
| GNU Make | 4.x+ | Pre-installed on Linux/macOS |
| Git | any | For cloning the repository |

Verify your installation:

```bash
docker --version
docker compose version
make --version
```

### Ports Required

Ensure ports **3000** (frontend), **8000** (backend), and **3306** (database) are available.

## Environment Variables

Copy `.env.example` to `.env` and populate with your values.

```bash
make init      # creates .env from .env.example
make secrets   # auto-generates all required secrets
```

Key variables:

| Variable | Description |
|----------|-------------|
| `APP_ENV` | Environment: `local` / `staging` / `production` |
| `APP_KEY` | Application encryption key (auto-generated) |
| `DB_CONNECTION` | Database type: `mysql` or `postgres` |
| `DB_PASSWORD` | Database password (min 16 chars, auto-generated) |
| `JWT_SECRET_KEY` | JWT signing secret (auto-generated) |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime (default: 15) |
| `FIRST_SUPERUSER` | Initial admin email (default: `admin@example.com`) |
| `FIRST_SUPERUSER_PASSWORD` | Initial admin password (auto-generated) |
| `FRONTEND_URL` | Frontend origin for CORS (default: `http://localhost:3000`) |

> See `.env.example` for the full list with descriptions.

## Run the System

```bash
# 1. Clone the repository
git clone https://github.com/thaolaptrinh/asm-user-management-system.git
cd asm-user-management-system

# 2. Initialize environment
make init
make secrets

# 3. Start all services with hot-reload
make dev
```

> `make dev` builds and starts all containers (frontend, backend, database) with file watching enabled. It runs in the foreground — press `Ctrl+C` to stop.

### Access the Application

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |

### Default Admin Account

After first startup, a superuser is created automatically:

```
Email:    admin@example.com
Password: check FIRST_SUPERUSER_PASSWORD in .env
```

### Common Commands

```bash
make help          # List all available commands
make ps            # Show running containers
make logs          # Stream all logs
make logs-be       # Backend logs only
make logs-fe       # Frontend logs only
make restart       # Restart all services
make stop          # Stop services
make down          # Stop and remove containers
make clean         # Remove containers + volumes (destructive)
make shell-fe      # Open shell in frontend container
make shell-be      # Open shell in backend container
make shell-db      # Open database shell
```

> To inspect the underlying `docker compose` commands for any Makefile target, open the `Makefile` directly.

## Running Commands Inside Containers

All application commands (package managers, scripts, migrations, debugging tools) must be run **inside the service container**, not on the host.

Enter the container shell first:

```bash
make shell-fe   # frontend container
make shell-be   # backend container
```

Then run commands as needed, for example:

```bash
# Frontend
bun add <package>          # install a package
bun run build              # build the app

# Backend
uv add <package>           # install a Python package
alembic upgrade head       # apply database migrations
python -m pytest           # run tests manually
```

## API Documentation

FastAPI generates interactive documentation automatically:

- **Swagger UI**: http://localhost:8000/docs — explore and test endpoints in-browser
- **ReDoc**: http://localhost:8000/redoc — reference-style documentation

### Endpoint Summary

**Auth** (`/api/v1/auth/`)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/register` | Register a new user |
| POST | `/login` | Login (returns `temp_token`) |
| POST | `/logout` | Logout |

**TOTP** (`/api/v1/auth/totp/`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/status` | Check whether TOTP is enabled |
| POST | `/enroll` | Generate TOTP secret + QR code (Step 1) |
| POST | `/challenge` | Create enrollment challenge (Step 2) |
| POST | `/verify` | Verify TOTP code — login (Flow A) or enroll (Flow B) |

**TOTP Recovery** (`/api/v1/auth/totp/recovery/`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Get recovery codes status |
| POST | `/` | Generate new recovery codes |
| POST | `/verify` | Login using a recovery code |

**Users** (`/api/v1/users/`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/me` | Get current user info |
| PATCH | `/me` | Update current user |
| PUT | `/me/password` | Change password |

**User Management** (`/api/v1/users/`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | List all users |
| POST | `/` | Create a user |
| GET | `/{id}` | Get user by ID |
| PATCH | `/{id}` | Update user |
| DELETE | `/{id}` | Delete user |

## Running Tests

### Backend Tests

```bash
make test-be
```

Runs Pytest inside a dedicated test container with a clean database. Covers API endpoints, service logic, TOTP security (replay attack prevention, enrollment flow, challenge/response), and database operations.

### Frontend / E2E Tests

```bash
make test-fe      # Frontend unit tests
make test-e2e     # Playwright E2E tests (requires running services)
```

See [TESTING.md](docs/TESTING.md) for detailed test documentation.

## Demo

For screenshots and feature walkthroughs, see [DEMO.md](docs/DEMO.md).

**Quick Preview**:

| Section | Description |
|---------|-------------|
| [Authentication Flow](docs/DEMO.md#1-authentication-flow) | Login, registration, TOTP setup (3 steps), recovery codes |
| [Dashboard](docs/DEMO.md#2-dashboard) | User and admin dashboard views |
| [User Management](docs/DEMO.md#3-user-management-admin) | List, create, delete users |
| [Settings](docs/DEMO.md#4-user-settings) | Profile, password change, TOTP management |
| [API Documentation](docs/DEMO.md#6-api-documentation) | Swagger UI for all endpoints |

## License

MIT — see [LICENSE](LICENSE).
