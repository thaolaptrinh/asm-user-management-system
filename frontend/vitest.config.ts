import react from "@vitejs/plugin-react"
import { playwright } from "@vitest/browser-playwright"
import tsconfigPaths from "vite-tsconfig-paths"
import { defineConfig } from "vitest/config"

export default defineConfig({
  plugins: [react(), tsconfigPaths()],

  // Cache directory to avoid permission issues
  cacheDir: ".vitest-cache",

  test: {
    // Enable global APIs (describe, it, expect, vi)
    globals: true,

    // Setup file
    setupFiles: ["./vitest.setup.ts"],

    // Use istanbul: tests run with Bun (JSC), not Node (V8) — v8 coverage API is not available on Bun
    coverage: {
      provider: "istanbul",
      reporter: ["text", "json", "html", "lcov"],
      reportsDirectory: process.env.VITEST_COVERAGE_DIR ?? "coverage",
      include: ["src/**/*"],
      exclude: [
        "node_modules/",
        "vitest.setup.ts",
        "src/vite-env.d.ts",
        "*.config.{ts,js}",
        "tests/", // Playwright E2E tests
        "src/client/**", // OpenAPI-generated client (@hey-api/openapi-ts)
        "**/*.gen.ts", // Any generated *.gen.ts files
        "src/components/ui/**", // shadcn/ui primitives (not app logic)
      ],
      // Fail if coverage drops below threshold (raise as you add more tests)
      thresholds: {
        lines: 8,
        functions: 5,
        branches: 3,
        statements: 8,
      },
    },

    // Environment variables
    env: process.env,

    // Project-based configuration
    projects: [
      // Unit tests - Node environment
      {
        test: {
          name: "unit",
          include: ["src/**/*.test.{js,ts}"],
          exclude: ["src/**/*.test.tsx"],
          environment: "node",
        },
        resolve: {
          alias: {
            "@": "./src",
          },
        },
      },
      // UI tests - Real browser (disabled: @vitest/browser cannot resolve path aliases)
      {
        test: {
          name: "ui",
          include: ["**/*.test.tsx", "src/**/*.test.tsx"],
          browser: {
            enabled: true,
            headless: true,
            provider: playwright(),
            screenshotDirectory: "vitest-test-results",
            instances: [{ browser: "chromium" }],
          },
        },
        resolve: {
          alias: {
            "@": "./src",
          },
        },
      },
    ],

    // Reporters
    reporters: ["default"],
  },

  // Path aliases for Next.js
  resolve: {
    alias: {
      "@": "./src",
    },
  },
})
