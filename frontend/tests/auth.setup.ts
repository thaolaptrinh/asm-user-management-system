import { test as setup } from "@playwright/test"

const authFile = "playwright/.auth/user.json"

/**
 * Authenticate via browser: go to /login, submit form, then save storage state.
 * Playwright best practice: log in via the browser (like a real user), not via API/curl.
 */
setup("authenticate", async ({ page }) => {
  const email = process.env.FIRST_SUPERUSER
  const password = process.env.FIRST_SUPERUSER_PASSWORD
  if (!email || !password) {
    throw new Error(
      "Set FIRST_SUPERUSER and FIRST_SUPERUSER_PASSWORD (e.g. in .env or compose env_file)",
    )
  }

  await page.goto("/login")
  await page.getByTestId("email-input").fill(email)
  await page.getByTestId("password-input").fill(password)
  await page.getByRole("button", { name: "Log In" }).click()
  await page.waitForURL("/")
  await page.getByRole("heading", { name: /Welcome back/ }).waitFor({ state: "visible" })

  await page.context().storageState({ path: authFile })
})
