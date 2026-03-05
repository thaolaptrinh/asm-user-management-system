# Testing Guide

Guide to running tests for the FastAPI + Next.js template.

## Overview

- **Backend:** Pytest, runs against a MySQL test DB (name: `MYSQL_DATABASE` from .env + `_test`, e.g. `app_test`). Each run can reset the DB (clean slate).
- **Frontend unit:** Vitest, with coverage (Istanbul).
- **Frontend E2E:** Playwright, runs in a container or locally.

## Commands from repo root

| Command | Description |
|--------|-------------|
| `make test` | Backend (pytest + coverage) then frontend unit (Vitest + coverage) |
| `make test-cov` | Backend only with coverage |
| `make test-cov-100` | Backend coverage, fail if < 100% |
| `make test-unit` | Frontend unit tests only with coverage |
| `make test-unit-ui` | Frontend unit tests (Vitest UI) |
| `make test-e2e` | E2E (Playwright), requires backend to be running |

## Backend (Pytest)

- **Run (recommended):** With stack up (`docker compose up -d`), from repo root:

  ```bash
  ./scripts/run-backend-tests.sh       # reset test DB + pytest
  ./scripts/run-backend-tests.sh cov   # with coverage
  ./scripts/run-backend-tests.sh -v   # verbose
  ```

- Test DB name = `MYSQL_DATABASE` + `_test`. Scripts may drop/recreate the DB before running.
- Coverage report is in `backend/htmlcov/` (open `htmlcov/index.html`).
- Add or edit tests in `backend/tests/` (structure mirrors `app/`).

## Frontend unit (Vitest)

From `frontend/`:

```bash
bun run test           # run once
bun run test:watch     # watch
bun run test:ui        # Vitest UI
bun run test:coverage  # coverage
```

Tests live next to source (e.g. `*.test.ts`) or in test directories. Coverage can be written to the configured directory (e.g. `coverage/`).

## Frontend E2E (Playwright)

- **Via Make (recommended):** Backend and mailcatcher are started if needed; Playwright runs in a container:

  ```bash
  make test-e2e
  ```

- **Local:** With backend running (e.g. `make dev-be`), from `frontend/`:

  ```bash
  bun run test:e2e
  bun run test:e2e:headed  # open browser
  bun run test:e2e tests/login.spec.ts  # single file
  ```

E2E uses `NEXT_PUBLIC_API_URL` to reach the backend (in container: `http://backend:8000`). Config in `frontend/playwright.config.ts`.

## CI

Sample workflow in `.github/workflows/` can run backend and frontend tests (unit or E2E) in Docker/VM. Ensure env (MYSQL_*, FIRST_SUPERUSER*) is set for CI.

## See also

- [Backend README](../../backend/README.md) — backend tests, migrations.
- [Frontend README](../../frontend/README.md) — frontend test scripts.
- [Development](../implementation/development.md) — how to run the stack for testing.
