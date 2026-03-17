import { describe, it, expect } from "vitest"
import { classifyTotpError } from "./totp-error"

describe("classifyTotpError", () => {
  it("returns 'expired' for expired temp_token error", () => {
    expect(classifyTotpError({ detail: "Invalid or expired token" })).toBe("expired")
  })

  it("returns 'invalid' for invalid TOTP code", () => {
    expect(classifyTotpError({ detail: "Invalid TOTP code" })).toBe("invalid")
  })

  it("returns 'invalid' for replay attack (code already used)", () => {
    expect(classifyTotpError({ detail: "TOTP code already used in current window" })).toBe("invalid")
  })

  it("returns 'unknown' for a generic Error object", () => {
    expect(classifyTotpError(new Error("network error"))).toBe("unknown")
  })

  it("returns 'unknown' for null", () => {
    expect(classifyTotpError(null)).toBe("unknown")
  })

  it("returns 'unknown' for an object without detail", () => {
    expect(classifyTotpError({ message: "something" })).toBe("unknown")
  })
})
