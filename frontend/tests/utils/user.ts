import * as crypto from "node:crypto"
import { expect, type APIRequestContext, type Page } from "@playwright/test"

// ---------------------------------------------------------------------------
// TOTP code generator (RFC 6238) — needed to complete enrollment for test users
// ---------------------------------------------------------------------------

function base32Decode(encoded: string): Buffer {
  const alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"
  const cleaned = encoded.toUpperCase().replace(/=+$/, "")
  let bits = 0
  let value = 0
  const bytes: number[] = []
  for (const char of cleaned) {
    const idx = alphabet.indexOf(char)
    if (idx === -1) continue
    value = (value << 5) | idx
    bits += 5
    if (bits >= 8) {
      bytes.push((value >> (bits - 8)) & 0xff)
      bits -= 8
    }
  }
  return Buffer.from(bytes)
}

export function generateTotp(base32Secret: string): string {
  const key = base32Decode(base32Secret)
  const counter = BigInt(Math.floor(Date.now() / 1000 / 30))
  const buf = Buffer.alloc(8)
  buf.writeBigUInt64BE(counter)
  const hmac = crypto.createHmac("sha1", key)
  hmac.update(buf)
  const digest = hmac.digest()
  const offset = digest[digest.length - 1] & 0xf
  const code =
    ((digest[offset] & 0x7f) << 24) |
    ((digest[offset + 1] & 0xff) << 16) |
    ((digest[offset + 2] & 0xff) << 8) |
    (digest[offset + 3] & 0xff)
  return (code % 1_000_000).toString().padStart(6, "0")
}

// ---------------------------------------------------------------------------
// createTestUser — create a user via API and complete full TOTP enrollment.
// Returns credentials + all recovery codes for use in logInUser.
// Each recovery code is one-time use — callers must use a fresh code per login.
// Uses playwright's APIRequestContext (available as `request` fixture in tests).
// ---------------------------------------------------------------------------

export async function createTestUser({
  request,
  email,
  password,
  fullName = "Test User",
}: {
  request: APIRequestContext
  email: string
  password: string
  fullName?: string
}): Promise<{ email: string; password: string; fullName: string; recoveryCodes: string[] }> {
  // Step 1: Register
  const regResp = await request.post("/api/v1/auth/register", {
    data: { email, password, full_name: fullName },
  })
  if (!regResp.ok()) {
    throw new Error(`createTestUser: register failed for ${email}: ${await regResp.text()}`)
  }

  // Step 2: Login → temp_token
  const loginResp = await request.post("/api/v1/auth/login", {
    form: { username: email, password },
  })
  const { temp_token } = await loginResp.json()

  const authHeader = { Authorization: `Bearer ${temp_token}` }

  // Step 3: Enroll TOTP → get secret
  const enrollResp = await request.post("/api/v1/auth/totp/enroll", {
    headers: authHeader,
  })
  const { secret } = await enrollResp.json()

  // Step 4: Create challenge → challenge_id
  const challengeResp = await request.post("/api/v1/auth/totp/challenge", {
    headers: authHeader,
  })
  const { challenge_id } = await challengeResp.json()

  // Step 5: Verify enrollment (Flow B) with a generated TOTP code
  const totpCode = generateTotp(secret)
  const verifyResp = await request.post("/api/v1/auth/totp/verify", {
    data: { challenge_id, totp_code: totpCode, temp_token },
  })
  if (!verifyResp.ok()) {
    throw new Error(`createTestUser: TOTP enrollment verify failed: ${await verifyResp.text()}`)
  }
  const { recovery_codes } = await verifyResp.json()

  return { email, password, fullName, recoveryCodes: recovery_codes as string[] }
}

// ---------------------------------------------------------------------------
// logInUser — navigate to /login, fill credentials, handle TOTP if needed.
// Pass `recoveryCode` for users with TOTP (all fully-enrolled users).
// ---------------------------------------------------------------------------

export async function logInUser(
  page: Page,
  email: string,
  password: string,
  recoveryCode?: string,
): Promise<void> {
  await page.goto("/login")
  await page.waitForSelector("[data-testid='email-input']", { state: "visible" })
  await page.getByTestId("email-input").fill(email)
  await page.getByTestId("password-input").fill(password)
  await page.getByRole("button", { name: "Log In" }).click()

  // Wait for either dashboard redirect or TOTP verification form
  const totpVisible = await page
    .getByTestId("totp-code-input")
    .waitFor({ state: "visible", timeout: 8000 })
    .then(() => true)
    .catch(() => false)

  if (totpVisible) {
    if (!recoveryCode) {
      throw new Error(`logInUser: TOTP required for ${email} — provide recoveryCode`)
    }
    await page.getByRole("button", { name: /use a recovery code instead/i }).click()
    await page.getByTestId("recovery-code-input").fill(recoveryCode)
    await page.getByRole("button", { name: "Use Recovery Code" }).click()
  }

  await page.waitForURL("/", { timeout: 15_000 })
  await expect(page.getByRole("heading", { name: /Welcome back/i })).toBeVisible()
}

// ---------------------------------------------------------------------------
// logOutUser — click user menu → Log out.
// ---------------------------------------------------------------------------

export async function logOutUser(page: Page): Promise<void> {
  await page.getByTestId("user-menu").click()
  await page.getByRole("menuitem", { name: "Log out" }).click()
  await page.waitForURL("/login")
}

// ---------------------------------------------------------------------------
// signUpNewUser — fill the public /signup form (used by sign-up.spec.ts).
// Note: new users will be directed to TOTP enrollment on first login.
// ---------------------------------------------------------------------------

export async function signUpNewUser(
  page: Page,
  fullName: string,
  email: string,
  password: string,
): Promise<void> {
  await page.goto("/signup")
  await page.getByTestId("full-name-input").fill(fullName)
  await page.getByTestId("email-input").fill(email)
  await page.getByTestId("password-input").fill(password)
  await page.getByTestId("confirm-password-input").fill(password)
  await page.getByRole("button", { name: "Sign Up" }).click()
}
