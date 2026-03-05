import { beforeEach, describe, expect, it, vi } from "vitest"

// Create a shared store for localStorage
const store: Record<string, string> = {}

const localStorageMock = {
  getItem: (key: string) => store[key] ?? null,
  setItem: (key: string, value: string) => {
    store[key] = String(value)
  },
  removeItem: (key: string) => {
    delete store[key]
  },
  clear: () => {
    for (const key of Object.keys(store)) delete store[key]
  },
  get length() {
    return Object.keys(store).length
  },
  key: (index: number) => {
    return Object.keys(store)[index] || null
  },
}

// Mock window and localStorage before importing auth
vi.stubGlobal("window", {})
vi.stubGlobal("localStorage", localStorageMock)

// Import after setting up mocks
import { isLoggedIn } from "./auth"

describe("auth utilities", () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    for (const key of Object.keys(store)) delete store[key]
  })

  describe("isLoggedIn", () => {
    it("should return false when token is not in localStorage", () => {
      expect(isLoggedIn()).toBe(false)
    })

    it("should return true when token is in localStorage", () => {
      localStorage.setItem("access_token", "fake-token")
      expect(isLoggedIn()).toBe(true)
    })

    it("should return false when window is undefined (SSR)", () => {
      const originalWindow = global.window
      // @ts-expect-error
      delete global.window
      expect(isLoggedIn()).toBe(false)
      global.window = originalWindow
    })

    it("should handle empty token", () => {
      localStorage.setItem("access_token", "")
      // Empty string is still truthy for existence check
      expect(isLoggedIn()).toBe(true)
    })
  })

  describe("token management", () => {
    it("should store token in localStorage", () => {
      const token = "test-access-token"
      localStorage.setItem("access_token", token)
      expect(localStorage.getItem("access_token")).toBe(token)
    })

    it("should remove token from localStorage", () => {
      localStorage.setItem("access_token", "test-token")
      localStorage.removeItem("access_token")
      expect(localStorage.getItem("access_token")).toBeNull()
    })

    it("should clear all data from localStorage", () => {
      localStorage.setItem("access_token", "test-token")
      localStorage.setItem("other_key", "other-value")
      localStorage.clear()
      expect(localStorage.getItem("access_token")).toBeNull()
      expect(localStorage.getItem("other_key")).toBeNull()
    })
  })

  describe("edge cases", () => {
    it("should handle empty localStorage", () => {
      expect(localStorage.length).toBe(0)
      expect(isLoggedIn()).toBe(false)
    })

    it("should handle multiple items in localStorage", () => {
      localStorage.setItem("access_token", "token1")
      localStorage.setItem("user_id", "123")
      localStorage.setItem("theme", "dark")
      expect(localStorage.length).toBe(3)
      expect(isLoggedIn()).toBe(true)
    })

    it("should handle getting keys by index", () => {
      localStorage.setItem("key1", "value1")
      localStorage.setItem("key2", "value2")
      expect(localStorage.key(0)).toBe("key1")
      expect(localStorage.key(1)).toBe("key2")
      expect(localStorage.key(2)).toBeNull()
    })

    it("should update existing token", () => {
      localStorage.setItem("access_token", "old-token")
      expect(localStorage.getItem("access_token")).toBe("old-token")
      localStorage.setItem("access_token", "new-token")
      expect(localStorage.getItem("access_token")).toBe("new-token")
    })
  })
})
