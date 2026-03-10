import { test as setup } from "@playwright/test"
import { testUsers } from "./fixtures/test-users"

const authFile = "playwright/.auth/user.json"

/**
 * Authenticate as admin (superuser) before all tests.
 *
 * Uses adminUser so that tests relying on stored auth can access admin pages.
 * TOTP is handled via recovery code ADMN-1111 (first of 10 seeded codes).
 * Remaining codes are reserved for tests that perform manual logins.
 */
setup("authenticate", async ({ page }) => {
  const { email, password, recoveryCodes } = testUsers.adminUser
  const recoveryCode = recoveryCodes[0] // ADMN-1111

  await page.goto("/login", { waitUntil: "networkidle" })
  await page.waitForSelector("[data-testid='email-input']", { state: "visible" })

  await page.getByTestId("email-input").fill(email)
  await page.getByTestId("password-input").fill(password)
  await page.getByRole("button", { name: "Log In" }).click()

  // Wait for TOTP verification step
  await page.getByTestId("totp-code-input").waitFor({ state: "visible", timeout: 10_000 })

  // Switch to recovery code flow
  await page.getByRole("button", { name: /use a recovery code instead/i }).click()
  await page.getByTestId("recovery-code-input").fill(recoveryCode)
  await page.getByRole("button", { name: "Use Recovery Code" }).click()

  // Verify dashboard reached
  await page.waitForURL("/", { timeout: 15_000 })
  await page.getByRole("heading", { name: /Welcome back/i }).waitFor({ state: "visible" })

  await page.context().storageState({ path: authFile })
})
