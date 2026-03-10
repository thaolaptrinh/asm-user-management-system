# Deployment Guide

This guide covers how to run the User Management System locally using Docker Compose and the provided Makefile.

## Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Docker | 20.10+ | https://docs.docker.com/get-docker/ |
| Docker Compose | v2.x | Included with Docker Desktop; Linux: https://docs.docker.com/compose/install/ |
| GNU Make | 4.x+ | Pre-installed on Linux/macOS; Windows: use WSL |
| Git | any | https://git-scm.com/downloads |

```bash
# Verify
docker --version
docker compose version
make --version
```

## 1. Clone the Repository

```bash
git clone https://github.com/thaolaptrinh/asm-user-management-system.git
cd asm-user-management-system
```

## 2. Environment Setup

```bash
# Copy environment template
make init

# Generate all required secrets (APP_KEY, DB passwords, JWT_SECRET_KEY, admin password)
make secrets
```

This creates a `.env` file with secure values. Review and adjust variables if needed (e.g., change `DB_FORWARD_PORT` if 3306 is already in use on your machine).

Key variables to be aware of:

```bash
APP_ENV=local
DB_CONNECTION=mysql
DB_FORWARD_PORT=3306          # Change if port conflict
FRONTEND_URL=http://localhost:3000
FIRST_SUPERUSER=admin@example.com
```

> To inspect or override the underlying `docker compose` commands, open the `Makefile`.

## 3. Start the System

```bash
make dev
```

This starts three containers (frontend, backend, database) with hot-reload enabled. The command runs in the foreground.

Wait until you see the services report as ready in the logs, then proceed to step 4.

## 4. Access the Application

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |

### Default Admin Account

```
Email:    admin@example.com
Password: see FIRST_SUPERUSER_PASSWORD in .env
```

Change this password after first login.

## 5. Verify the Deployment

```bash
# Check container status
make ps

# Stream logs
make logs
```

Open http://localhost:8000/docs in your browser to confirm the backend API is reachable.

## Stopping the System

```bash
make stop    # Stop containers (preserves data)
make down    # Stop and remove containers
make clean   # Remove containers + volumes (deletes all data)
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Port already in use | Change `DB_FORWARD_PORT` in `.env`; run `make down && make dev` |
| Database connection error | `make logs-db` to inspect; `make restart` or `make db-reset` |
| Container fails to start | `make logs` to inspect; `make dev-build` to rebuild images |
| TOTP codes rejected | Ensure system clock is synchronized (TOTP is time-sensitive) |
| Permission errors | Run `make dev-build` — the Makefile auto-maps `HOST_UID/GID` |
| Need a clean slate | `make clean && make secrets && make dev` (destroys all data) |
