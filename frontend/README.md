# Frontend

Next.js frontend with React, TypeScript, shadcn/ui.

## Quick Start

```bash
make dev              # Start all services with Docker
make shell-fe         # Open shell in frontend container
```

**Frontend:** http://localhost:3000

---

## Structure

```
src/
├── app/                    # Next.js App Router
│   ├── (auth)/            # Auth routes
│   ├── (dashboard)/       # Protected routes
│   └── layout.tsx
├── client/                 # Auto-generated API client
├── components/
│   ├── admin/             # User management
│   ├── dashboard/         # Sidebar, nav
│   ├── items/             # Item CRUD
│   ├── ui/                # shadcn/ui
│   └── user-settings/     # Profile, password
├── hooks/                  # useAuth, useCustomToast
├── lib/                    # Queries, utils
└── tests/                  # Vitest tests
```

---

## API Client

Auto-generated from backend OpenAPI spec:

```typescript
import { items } from "@/client/sdk.gen"

const { data } = await items.listItems({})
await items.createItem({ body: { title: "Test" } })
```

**Regenerate** (from repo root):

```bash
make generate-client
```

---

## Authentication

```typescript
const { user, login, logout } = useAuth()
```

- JWT in HttpOnly cookie
- Protected routes check `/api/v1/users/me`
- No client-side token storage

---

## Components

- **Feature:** `admin/`, `items/`, `user-settings/`
- **UI:** `ui/` (shadcn/ui)
- **Common:** `dashboard/sidebar/`, `common/`

---

## Adding a Page

```typescript
// src/app/(dashboard)/feature/page.tsx
export default function FeaturePage() {
  return <div>...</div>
}
```

Add navigation in `components/dashboard/sidebar/AppSidebar.tsx`

---

## Tests

```bash
make test-fe            # Frontend tests (Vitest)
make test-e2e          # E2E tests (Playwright)
```

---

## Container Commands

```bash
make shell-fe         # Frontend shell
make logs-fe          # Frontend logs
make logs-fe -f       # Follow logs
```

**Inside container:**

```bash
bun run dev          # Start dev server
bun run test         # Run tests
bun --version        # Check version
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| **API errors** | `make shell-be` → `curl http://localhost:8000/health` |
| **Type errors** | `make typecheck` |
| **Tests fail** | `make test-fe` |
| **Build issues** | `make dev-build` |
| **Stale client** | `make generate-client` (from repo root) |
| **Container stuck** | `make down && make dev` |
