import { expect, type Page } from "@playwright/test"
import { Users } from "../../src/client"
import { client as httpClient } from "../../src/client/client.gen"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://backend:8000"
httpClient.setConfig({ baseUrl: API_URL })

/** Create a user via public sign-up (no auth). */
export async function createUser({
  email,
  password,
}: {
  email: string
  password: string
}) {
  return Users.registerUser({
    body: { email, password, full_name: "Test User" },
  })
}

export async function signUpNewUser(
  page: Page,
  name: string,
  email: string,
  password: string,
) {
  await page.goto("/signup")

  await page.getByTestId("full-name-input").fill(name)
  await page.getByTestId("email-input").fill(email)
  await page.getByTestId("password-input").fill(password)
  await page.getByTestId("confirm-password-input").fill(password)
  await page.getByRole("button", { name: "Sign Up" }).click()
  await page.goto("/login")
}

export async function logInUser(page: Page, email: string, password: string) {
  await page.goto("/login")

  await page.getByTestId("email-input").fill(email)
  await page.getByTestId("password-input").fill(password)
  await page.getByRole("button", { name: "Log In" }).click()
  await page.waitForURL("/")
  await expect(page.getByRole("heading", { name: /Welcome back/ })).toBeVisible()
}

export async function logOutUser(page: Page) {
  await page.getByTestId("user-menu").click()
  await page.getByRole("menuitem", { name: "Log out" }).click()
  await page.goto("/login")
}
