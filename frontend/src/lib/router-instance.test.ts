import { describe, it, expect, vi, beforeEach, afterEach } from "vitest"

describe("navigateToLogin", () => {
  let replaceSpy: ReturnType<typeof vi.fn>

  beforeEach(async () => {
    vi.resetModules()
    replaceSpy = vi.fn()
    vi.stubGlobal("window", {
      location: { pathname: "/dashboard", replace: replaceSpy },
    })
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it("navigates to /login with no reason", async () => {
    const { navigateToLogin } = await import("./router-instance")
    navigateToLogin()
    expect(replaceSpy).toHaveBeenCalledWith("/login")
  })

  it("navigates to /login?reason=session_expired when reason provided", async () => {
    const { navigateToLogin } = await import("./router-instance")
    navigateToLogin("session_expired")
    expect(replaceSpy).toHaveBeenCalledWith("/login?reason=session_expired")
  })

  it("does nothing when already on /login", async () => {
    vi.stubGlobal("window", {
      location: { pathname: "/login", replace: replaceSpy },
    })
    const { navigateToLogin } = await import("./router-instance")
    navigateToLogin()
    expect(replaceSpy).not.toHaveBeenCalled()
  })

  it("does nothing when already on /login even with reason", async () => {
    vi.stubGlobal("window", {
      location: { pathname: "/login", replace: replaceSpy },
    })
    const { navigateToLogin } = await import("./router-instance")
    navigateToLogin("session_expired")
    expect(replaceSpy).not.toHaveBeenCalled()
  })
})
