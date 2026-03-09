import path from 'node:path';
import { defineConfig, devices } from '@playwright/test';

/**
 * Read environment variables from file.
 * https://github.com/motdotla/dotenv
 */
// import dotenv from 'dotenv';
// dotenv.config({ path: path.resolve(__dirname, '.env') });

/**
 * See https://playwright.dev/docs/test-configuration.
 */
export default defineConfig({
  testDir: './tests',
  /* Run tests in files in parallel */
  fullyParallel: true,
  /* Timeout per test; increase if DB/API is slow */
  timeout: 30 * 1000,
  /* Fail the build on CI if you accidentally left test.only in the source code. */
  forbidOnly: !!process.env.CI,
  /* Retry on CI only */
  retries: process.env.CI ? 2 : 0,
  /* Opt out of parallel tests on CI. */
  workers: process.env.CI ? 1 : undefined,
  /* Local: stop on first failure (fail-fast). CI: run all to get full report. */
  maxFailures: process.env.CI ? 0 : 1,
  /* Reporter: CI = github. Local = list (each test name + pass/fail) + html (file). Fail-fast: maxFailures above. */
  reporter: process.env.CI
    ? 'github'
    : [
        ['list', { printSteps: true }],
        ['html', { open: 'never', outputFolder: path.join(__dirname, 'playwright-report') }],
      ],

  expect: {
    timeout: 15 * 1000,
  },

  /* Shared settings for all the projects below. See https://playwright.dev/docs/api/class-testoptions. */
  use: {
    /* Base URL of the app under test (frontend), not the API. */
    baseURL: process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:3000',

    trace: process.env.CI ? 'on' : 'retain-on-failure',
    video: process.env.CI ? 'retain-on-failure' : undefined,
  },

  /* Setup project: run auth once, then reuse storageState (https://playwright.dev/docs/auth). */
  projects: [
    { name: 'setup', testMatch: /.*\.setup\.ts/ },
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        storageState: 'playwright/.auth/user.json',
      },
      dependencies: ['setup'],
    },
    ...(process.env.CI
      ? [
          {
            name: 'firefox',
            use: {
              ...devices['Desktop Firefox'],
              storageState: 'playwright/.auth/user.json',
            },
            dependencies: ['setup'],
          },
          {
            name: 'webkit',
            use: {
              ...devices['Desktop Safari'],
              storageState: 'playwright/.auth/user.json',
            },
            dependencies: ['setup'],
          },
        ]
      : []),

    /* Test against mobile viewports. */
    // {
    //   name: 'Mobile Chrome',
    //   use: { ...devices['Pixel 5'] },
    // },
    // {
    //   name: 'Mobile Safari',
    //   use: { ...devices['iPhone 12'] },
    // },

    /* Test against branded browsers. */
    // {
    //   name: 'Microsoft Edge',
    //   use: { ...devices['Desktop Edge'], channel: 'msedge' },
    // },
    // {
    //   name: 'Google Chrome',
    //   use: { ...devices['Desktop Chrome'], channel: 'chrome' },
    // },
  ],

  /* E2E web server: use dev:e2e (next dev --webpack). Turbopack can panic in container under load
   * (turbo-persistence range index bug); Webpack is stable. Dev (make dev) still uses Turbopack.
   * Revisit when Next.js fixes the panic; then we can try `bun run dev` here again.
   *
   * SKIP in Docker: Frontend is already running in another container. */
  webServer: process.env.PLAYWRIGHT_SKIP_WEB_SERVER
    ? undefined
    : {
        command: 'bun run dev:e2e',
        url: 'http://localhost:3000',
        timeout: 120 * 1000,
        reuseExistingServer: true,
      },
});
