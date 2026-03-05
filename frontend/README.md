# FastAPI + Next.js Template

Full-stack template with FastAPI backend and Next.js frontend.

## Features

- **Frontend:** Next.js 16, React 19, TypeScript, Tailwind CSS, shadcn/ui
- **Backend:** FastAPI, MySQL, SQLModel, Pydantic, JWT auth
- **Testing:** Vitest (unit), Playwright (E2E), 110 tests
- **Auth:** JWT-based authentication with refresh tokens
- **UI Components:** shadcn/ui with dark mode support

## Project Structure

```
.
├── backend/          # FastAPI application
│   ├── app/
│   │   ├── api/      # API routes
│   │   └── core/     # Core logic
│   └── tests/        # Backend tests
├── frontend/         # Next.js application
│   ├── src/
│   │   ├── app/      # Next.js app router
│   │   ├── components/
│   │   ├── hooks/    # Custom React hooks
│   │   ├── lib/      # Utilities
│   │   └── tests/    # Frontend tests
│   └── tests/        # E2E tests (Playwright)
└── docker-compose.yml
```

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Bun (recommended) or Node.js 20+

### Backend Setup

Backend uses [uv](https://docs.astral.sh/uv/). See [Backend README](../backend/README.md) for details.

```bash
cd backend
uv sync
source .venv/bin/activate   # Linux/macOS
fastapi run --reload app/main.py
```

Backend runs at http://localhost:8000. Or use Docker: from repo root run `make up` then `make dev-be`.

### Frontend Setup

```bash
cd frontend
bun install
bun run dev
```

Frontend runs on http://localhost:3000

### Using Docker Compose

```bash
docker-compose up -d
```

This starts both backend and frontend services.

## Testing

### Unit Tests (Vitest)

```bash
# Run all unit tests
bun run test

# Watch mode
bun run test:watch

# UI mode
bun run test:ui

# Coverage report
bun run test:coverage
```

**Coverage:** 10.16% (110 tests)
- proxy.ts: 100%
- useCustomToast: 100%
- useCopyToClipboard: 100%
- useMobile: 90.9%

### E2E Tests (Playwright)

```bash
# Run E2E tests
bun run test:e2e

# Run specific test file
bun run test:e2e tests/login.spec.ts

# Run in headed mode (show browser)
bun run test:e2e:headed
```

## Available Scripts

### Frontend

```bash
bun run dev          # Start dev server
bun run build        # Build for production
bun run start        # Start production server
bun run lint         # Run ESLint
bun run test         # Run unit tests
bun run test:watch   # Watch mode
bun run test:coverage # Coverage report
bun run test:e2e     # Run E2E tests
bun run test:e2e:headed # E2E with browser
```

### Backend (see [backend/README.md](../backend/README.md))

```bash
uv sync             # Install deps
fastapi run --reload app/main.py   # Dev server
# Tests: from repo root: ./scripts/run-backend-tests.sh cov
# Lint/format: from repo root: make lint / make format
```

### Makefile Commands (from repo root)

```bash
make dev            # Start all services with watch
make dev-be         # Backend only
make dev-fe         # Frontend only
make test           # Backend (pytest + cov) + Frontend unit (Vitest + cov)
make test-unit      # Frontend unit tests only
make test-e2e       # E2E (Playwright)
make lint           # Lint backend + frontend
make help           # List all targets
```

## Adding Tests

### Unit Tests

Create `.test.ts` files in `src/` directories:

```typescript
// src/lib/utils.test.ts
import { describe, expect, it } from "vitest"
import { cn } from "./utils"

describe("cn utility", () => {
  it("should merge class names", () => {
    expect(cn("px-2", "py-1")).toBe("px-2 py-1")
  })
})
```

### E2E Tests

Create `.spec.ts` files in `tests/` directory:

```typescript
// tests/login.spec.ts
import { test, expect } from "@playwright/test"

test("login flow", async ({ page }) => {
  await page.goto("http://localhost:3000/login")
  await page.fill('input[name="email"]', "user@example.com")
  await page.fill('input[name="password"]', "password")
  await page.click('button[type="submit"]')
  await expect(page).toHaveURL("http://localhost:3000/")
})
```

See [TESTING.md](./TESTING.md) for detailed testing guidelines.

## Environment Variables

Copy `.env.example` to `.env` and configure:

See repo root `.env.example` for full list. Main ones:

```bash
# Backend (from repo root .env)
MYSQL_DATABASE=app
MYSQL_USER=app_user
MYSQL_PASSWORD=...

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Deployment

### Vercel (Frontend)

```bash
cd frontend
bun run build
vercel --prod
```

### Backend (Render/Railway/etc)

Set environment variables and deploy.

### Docker

From repo root, use `compose.yml` (production-style). Create the `traefik-public` network if using Traefik.

```bash
docker compose up -d
```

## Troubleshooting

### Tests failing

```bash
# Clear cache
rm -rf node_modules/.vite
rm -rf .vitest-cache

# Reinstall dependencies
bun install
```

### Permission issues

```bash
# Fix node_modules ownership
sudo chown -R $USER:$USER node_modules
```

## Learn More

- [Next.js Documentation](https://nextjs.org/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Vitest Documentation](https://vitest.dev/)
- [Playwright Documentation](https://playwright.dev/)
