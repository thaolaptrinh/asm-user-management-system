# Testing Guide

This project uses a **modern, advanced testing setup** inspired by [Next-js-Boilerplate](https://github.com/ixartz/Next-js-Boilerplate).

**Priority:** E2E tests first, then unit tests. Component tests are not used (use E2E instead).  
**`make test`** (from repo root) runs frontend **unit tests with coverage**; the run **fails if coverage is below the threshold** in `vitest.config.ts` (so you must add tests when coverage drops).

## 🧪 Testing Stack

### **Unit Tests (Vitest)**
- **Runner:** Vitest 4.x
- **Environment:** Node.js for utilities, Browser for components
- **Coverage:** V8 provider
- **Speed:** ⚡ Blazing fast (40-100ms)

### **Component Tests (Vitest + Browser Mode)**
- **Runner:** Vitest with `@vitest/browser-playwright`
- **Environment:** Real Chromium browser
- **Accuracy:** 🎯 100% real browser behavior

### **E2E Tests (Playwright)**
- **Runner:** Playwright
- **Browsers:** Chromium, Firefox, WebKit
- **Purpose:** Critical user flows

---

## Running Commands

All test commands must be run **inside the frontend container**. Enter the shell first:

```bash
make shell-fe   # from the repo root
```

Then run any of the commands below.

## 📋 Commands

### **Unit Tests**

```bash
# Run once (CI mode)
bun test

# Watch mode (development)
bun test:watch

# UI mode (beautiful interface)
bun test:ui

# Coverage report
bun test:coverage

# Run specific project
bun test --project=unit
```

### **Component Tests (Browser Mode)**

**⚠️ Status:** Currently **blocked** by technical limitation

**Issue:** `@vitest/browser` + `vite-tsconfig-paths` + path aliases conflict  
**Error:** Cannot resolve `@/client` imports in browser environment

**Alternative:** Use **E2E tests** (recommended) or see section below

---

### **🚫 Browser Mode Limitations**

**What doesn't work:**
```bash
# These commands DON'T work:
bun test --project=ui              # ❌ Path alias errors
bun test src/hooks/useAuth.test.tsx # ❌ Cannot resolve @/client
```

**Why:** `@vitest/browser` cannot resolve TypeScript path aliases (`@/client`, `@/hooks`) when running in real Chromium browser.

**Workarounds:**
1. **Use E2E tests instead** (recommended - better coverage)
2. **Use relative imports** in source code (degrades code quality)
3. **Wait for upstream fix** in @vitest/browser

**See:** [Component Tests Section](#-component-tests-best-practices) below

### **E2E Tests (Playwright)**

```bash
# Run E2E tests
bun test:e2e

# Run with UI
bun test:e2e:ui

# Run with visible browser
bun test:e2e:headed
```

---

## 🏗️ Project Structure

```
frontend/
├── src/
│   ├── lib/
│   │   └── utils.test.ts          ✅ Unit tests (Node environment)
│   ├── hooks/
│   │   └── useAuth.test.ts        ✅ Hook tests (Node environment)
│   └── components/
│       └── Button.test.tsx        ✅ Component tests (Browser environment)
├── tests/
│   ├── login.spec.ts              ✅ E2E tests (Playwright)
│   └── items.spec.ts
├── vitest.config.ts               ✅ Vitest configuration
├── vitest.setup.ts                ✅ Test setup & mocks
└── playwright.config.ts           ✅ Playwright configuration
```

---

## ⚙️ Configuration

### **vitest.config.ts**

Advanced setup with **project-based testing**:

```typescript
{
  projects: [
    {
      name: 'unit',
      include: ['src/**/*.test.{js,ts}'],
      environment: 'node'
    },
    {
      name: 'ui',
      include: ['**/*.test.tsx'],
      browser: {
        enabled: true,
        provider: playwright()
      }
    }
  ]
}
```

**Benefits:**
- ✅ Unit tests run in Node (fast)
- ✅ Component tests run in real browser (accurate)
- ✅ Separate configurations for each type

---

## 🎯 When to Use What

### **Unit Tests** (`*.test.ts`)

**Purpose:** Test pure functions, utilities, hooks

**Examples:**
- ✅ Utility functions (`lib/utils.ts`)
- ✅ Custom hooks (`hooks/useAuth.ts`)
- � Validators, formatters
- ✅ Business logic

**Environment:** Node.js  
**Speed:** ⚡ 40-100ms

```typescript
// src/lib/utils.test.ts
import { describe, expect, it } from "vitest"
import { cn } from "./utils"

describe("cn utility", () => {
  it("merges classes correctly", () => {
    expect(cn("px-2", "py-1")).toBe("px-2 py-1")
  })
})
```

### **Component Tests** (`*.test.tsx`)

**Purpose:** Test React components in REAL browser

**Examples:**
- ✅ Form validation
- ✅ User interactions
- ✅ Component state
- ✅ Event handlers
- ✅ UI behavior

**Environment:** Real Chromium browser  
**Speed:** 🐢 1-3s (but 100% accurate)

```typescript
// src/components/Button.test.tsx
import { describe, expect, it } from "vitest"
import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { Button } from "./Button"

describe("Button", () => {
  it("renders correctly", async () => {
    render(<Button>Click me</Button>)
    
    const button = screen.getByRole("button", { name: "Click me" })
    await userEvent.click(button)
    
    expect(button).toBeInTheDocument()
  })
})
```

**Why Real Browser?**
- ✅ Real DOM behavior
- ✅ Real CSS rendering
- ✅ Real event handling
- ✅ No jsdom limitations

### **E2E Tests** (`tests/**/*.spec.ts`)

**Purpose:** Test critical user flows

**Examples:**
- ✅ Login → Dashboard → Logout
- ✅ CRUD operations
- ✅ Multi-page workflows

**Environment:** Playwright browsers  
**Speed:** 🐢 2-5 min

---

## 🚀 Quick Start

### 1. Add a Unit Test

```typescript
// src/lib/format.test.ts
import { describe, expect, it } from "vitest"
import { formatDate } from "./format"

describe("formatDate", () => {
  it("formats date correctly", () => {
    const date = new Date("2024-01-01")
    expect(formatDate(date)).toBe("2024-01-01")
  })
})
```

### 2. Add a Component Test

```typescript
// src/components/UserMenu.test.tsx
import { describe, expect, it } from "vitest"
import { render, screen } from "@testing-library/react"
import { UserMenu } from "./UserMenu"

describe("UserMenu", () => {
  it("shows user email", () => {
    render(<UserMenu email="test@example.com" />)
    expect(screen.getByText("test@example.com")).toBeInTheDocument()
  })
})
```

### 3. Run Tests

```bash
# Watch mode during dev
bun test:watch

# Run all tests (unit only; browser/component tests currently disabled)
bun test
```

---

## 💡 Best Practices

### **1. Test Structure**

Follow this pattern:

```typescript
describe("FeatureName", () => {
  describe("functionName", () => {
    it("should do X when Y", () => {
      // Arrange
      const input = { ... }
      
      // Act
      const result = functionName(input)
      
      // Assert
      expect(result).toBe(...)
    })
  })
})
```

### **2. Test Isolation**

Each test should be independent:

```typescript
beforeEach(() => {
  vi.clearAllMocks()
})
```

### **3. Descriptive Names**

```typescript
// ❌ Bad
it("works")

// ✅ Good
it("should merge class names correctly")
```

### **4. Test Behavior, Not Implementation**

```typescript
// ❌ Bad
it("sets isLoading to true")

// ✅ Good
it("shows loading spinner while fetching")
```

---

## 🔧 Advanced Features

### **Project-Based Testing**

Different test types run in different environments:

| Project | Files | Environment | Purpose |
|---------|-------|-------------|---------|
| `unit` | `*.test.ts` | Node.js | Fast logic testing ✅ |
| `ui` | `*.test.tsx` | Chromium | Real browser (⚠️ disabled: path alias issue) |

### **Browser Mode**

Component tests run in **real Chromium**, not jsdom:

```typescript
// vitest.config.ts
{
  browser: {
    enabled: true,
    headless: true,
    provider: playwright()
  }
}
```

**Benefits:**
- ✅ Real DOM
- ✅ Real CSS
- ✅ Real events
- ✅ No jsdom quirks

### **Coverage Reports**

```bash
bun test:coverage
```

Generates:
- Terminal output
- HTML report (`coverage/index.html`)
- LCov report (`coverage/lcov.info`)

---

## 🐛 Debugging

### **Vitest UI Mode**

```bash
bun test:ui
```

Opens beautiful UI at `http://localhost:51204/__vitest__/`

### **Browser Mode Debugging**

**⚠️ Not Available** - See [Browser Mode Limitations](#-component-tests-browser-mode)

**Alternative:** Use Playwright E2E tests with UI mode:
```bash
bun test:e2e:ui
bun test:e2e:headed --debug
```

### **Verbose Output**

```bash
bun test --reporter=verbose
```

---

## 📊 Testing Pyramid

```
        /\
       /  \      Playwright E2E (7 tests)
      /----\     - Slow (2-5 min)
     /      \    - Critical flows
    /--------\
   /          \   Vitest Component (*.test.tsx)
  /____________\  - Medium speed (1-3s)
                    - Real browser
   /____________\
  /              \ Vitest Unit (*.test.ts)
 /________________\ - Fast (40-100ms)
                     - Node environment
```

**Ideal Ratio:**
- 70% Unit tests (Node)
- 20% Component tests (Browser)
- 10% E2E tests (Playwright)

---

## 📚 Resources

- [Vitest Docs](https://vitest.dev/)
- [@vitest/browser](https://vitest.dev/guide/browser/)
- [Testing Library](https://testing-library.com/)
- [Playwright Docs](https://playwright.dev/)
- [Next-js-Boilerplate](https://github.com/ixartz/Next-js-Boilerplate) (Inspiration)
