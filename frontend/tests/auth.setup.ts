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

  // Log any console errors
  page.on("console", (msg) => {
    if (msg.type() === "error") {
      console.log(`Console error: ${msg.text()}`)
    }
  })

  await page.goto("/login")
  await page.getByTestId("email-input").fill(email)
  await page.getByTestId("password-input").fill(password)

  console.log(`Attempting login with: ${email}`)

  await page.getByRole("button", { name: "Log In" }).click()

  // Wait for URL change to "/" (redirect after successful login)
  console.log(`Waiting for redirect to /...`)
  await page.waitForURL("/", { timeout: 15000 })
  console.log(`Successfully redirected to: ${page.url()}`)

  // Verify we're on the right page
  await page
    .getByRole("heading", { name: /Welcome back/ })
    .waitFor({ state: "visible", timeout: 5000 })

  // Save auth state for other tests
  await page.context().storageState({ path: authFile })
  console.log(`Auth state saved to: ${authFile}`)
})
