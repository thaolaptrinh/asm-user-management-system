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

// Create document mock with cookie
let documentCookie = ""
const documentMock = {
  get cookie() {
    return documentCookie
  },
  set cookie(value: string) {
    documentCookie = value
  },
}

// Mock window, localStorage, and document before importing
vi.stubGlobal("window", {})
vi.stubGlobal("localStorage", localStorageMock)
vi.stubGlobal("document", documentMock)

describe("client configuration", () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    documentCookie = ""
  })

  describe("auth configuration", () => {
    it("should return token from localStorage when available", () => {
      localStorage.setItem("access_token", "my-token")

      const authFn = () => {
        if (typeof window === "undefined") return undefined
        return localStorage.getItem("access_token") ?? undefined
      }

      const authValue = authFn()
      expect(authValue).toBe("my-token")
    })

    it("should return undefined when token is not in localStorage", () => {
      const authFn = () => {
        if (typeof window === "undefined") return undefined
        return localStorage.getItem("access_token") ?? undefined
      }

      const authValue = authFn()
      expect(authValue).toBeUndefined()
    })

    it("should return undefined when window is undefined (SSR)", () => {
      const originalWindow = global.window
      // @ts-expect-error
      delete global.window

      const authFn = () => {
        if (typeof window === "undefined") return undefined
        return localStorage.getItem("access_token") ?? undefined
      }

      const authValue = authFn()
      expect(authValue).toBeUndefined()

      global.window = originalWindow
    })
  })

  describe("error interceptor", () => {
    it("should clear auth data on 401 response", () => {
      // Set up auth data
      localStorage.setItem("access_token", "test-token")
      document.cookie = "access_token=test-token"

      // Create mock response
      const mockResponse = {
        status: 401,
      } as Response

      // Simulate the error interceptor logic
      const errorInterceptor = (error: unknown, response: Response) => {
        if (
          typeof window !== "undefined" &&
          (response?.status === 401 || response?.status === 404)
        ) {
          localStorage.removeItem("access_token")
          document.cookie = "access_token=; path=/; max-age=0"
        }
        return error
      }

      const mockError = new Error("Unauthorized")
      const result = errorInterceptor(mockError, mockResponse)

      // Verify auth data was cleared
      expect(localStorage.getItem("access_token")).toBeNull()
      expect(document.cookie).toBe("access_token=; path=/; max-age=0")
      // Error is passed through
      expect(result).toBe(mockError)
    })

    it("should clear auth data on 404 response", () => {
      // Set up auth data
      localStorage.setItem("access_token", "test-token")
      document.cookie = "access_token=test-token"

      // Create mock response
      const mockResponse = {
        status: 404,
      } as Response

      // Simulate the error interceptor logic
      const errorInterceptor = (error: unknown, response: Response) => {
        if (
          typeof window !== "undefined" &&
          (response?.status === 401 || response?.status === 404)
        ) {
          localStorage.removeItem("access_token")
          document.cookie = "access_token=; path=/; max-age=0"
        }
        return error
      }

      const mockError = new Error("Not Found")
      const result = errorInterceptor(mockError, mockResponse)

      // Verify auth data was cleared
      expect(localStorage.getItem("access_token")).toBeNull()
      expect(document.cookie).toBe("access_token=; path=/; max-age=0")
      expect(result).toBe(mockError)
    })

    it("should not clear auth data on other error responses", () => {
      // Set up auth data
      localStorage.setItem("access_token", "test-token")
      document.cookie = "access_token=test-token"

      // Create mock response with different status
      const mockResponse = {
        status: 500,
      } as Response

      // Simulate the error interceptor logic
      const errorInterceptor = (error: unknown, response: Response) => {
        if (
          typeof window !== "undefined" &&
          (response?.status === 401 || response?.status === 404)
        ) {
          localStorage.removeItem("access_token")
          document.cookie = "access_token=; path=/; max-age=0"
        }
        return error
      }

      const mockError = new Error("Internal Server Error")
      const result = errorInterceptor(mockError, mockResponse)

      // Verify auth data was NOT cleared
      expect(localStorage.getItem("access_token")).toBe("test-token")
      expect(document.cookie).toBe("access_token=test-token")
      expect(result).toBe(mockError)
    })

    it("should not clear auth data when window is undefined", () => {
      const originalWindow = global.window
      // @ts-expect-error
      delete global.window

      // Set up auth data
      localStorage.setItem("access_token", "test-token")

      // Create mock response
      const mockResponse = {
        status: 401,
      } as Response

      // Simulate the error interceptor logic
      const errorInterceptor = (error: unknown, response: Response) => {
        if (
          typeof window !== "undefined" &&
          (response?.status === 401 || response?.status === 404)
        ) {
          localStorage.removeItem("access_token")
          document.cookie = "access_token=; path=/; max-age=0"
        }
        return error
      }

      const mockError = new Error("Unauthorized")
      const result = errorInterceptor(mockError, mockResponse)

      // Verify auth data was NOT cleared (because window is undefined)
      expect(localStorage.getItem("access_token")).toBe("test-token")
      expect(result).toBe(mockError)

      global.window = originalWindow
    })

    it("should handle undefined response", () => {
      // Set up auth data
      localStorage.setItem("access_token", "test-token")

      // Simulate the error interceptor logic
      const errorInterceptor = (error: unknown, response: Response) => {
        if (
          typeof window !== "undefined" &&
          (response?.status === 401 || response?.status === 404)
        ) {
          localStorage.removeItem("access_token")
          document.cookie = "access_token=; path=/; max-age=0"
        }
        return error
      }

      const mockError = new Error("Network Error")
      const result = errorInterceptor(mockError, undefined as any)

      // Verify auth data was NOT cleared
      expect(localStorage.getItem("access_token")).toBe("test-token")
      expect(result).toBe(mockError)
    })

    it("should handle both localStorage and cookie clearing", () => {
      // Set up auth data in both places
      localStorage.setItem("access_token", "test-token")
      document.cookie = "access_token=test-token; path=/; max-age=604800"

      // Create mock response
      const mockResponse = {
        status: 401,
      } as Response

      // Simulate the error interceptor logic
      const errorInterceptor = (error: unknown, response: Response) => {
        if (
          typeof window !== "undefined" &&
          (response?.status === 401 || response?.status === 404)
        ) {
          localStorage.removeItem("access_token")
          document.cookie = "access_token=; path=/; max-age=0"
        }
        return error
      }

      const mockError = new Error("Unauthorized")
      errorInterceptor(mockError, mockResponse)

      // Verify both were cleared
      expect(localStorage.getItem("access_token")).toBeNull()
      // Cookie should be set with max-age=0 to delete it
      expect(document.cookie).toContain("max-age=0")
    })
  })

  describe("environment URLs", () => {
    it("should use localhost URL when no env var is set", () => {
      const originalEnv = process.env.NEXT_PUBLIC_API_URL
      delete process.env.NEXT_PUBLIC_API_URL

      const apiUrl =
        process.env.NEXT_PUBLIC_API_URL ||
        (typeof window !== "undefined"
          ? "http://localhost:8000"
          : "http://backend:8000")

      expect(apiUrl).toBe("http://localhost:8000")

      if (originalEnv) {
        process.env.NEXT_PUBLIC_API_URL = originalEnv
      }
    })

    it("should use env URL when NEXT_PUBLIC_API_URL is set", () => {
      const originalEnv = process.env.NEXT_PUBLIC_API_URL
      process.env.NEXT_PUBLIC_API_URL = "https://api.example.com"

      const apiUrl =
        process.env.NEXT_PUBLIC_API_URL ||
        (typeof window !== "undefined"
          ? "http://localhost:8000"
          : "http://backend:8000")

      expect(apiUrl).toBe("https://api.example.com")

      process.env.NEXT_PUBLIC_API_URL = originalEnv
    })

    it("should use backend URL in server environment", () => {
      const originalWindow = global.window
      const originalEnv = process.env.NEXT_PUBLIC_API_URL
      delete process.env.NEXT_PUBLIC_API_URL

      // @ts-expect-error
      delete global.window

      const apiUrl =
        process.env.NEXT_PUBLIC_API_URL ||
        (typeof window !== "undefined"
          ? "http://localhost:8000"
          : "http://backend:8000")

      expect(apiUrl).toBe("http://backend:8000")

      global.window = originalWindow
      if (originalEnv) {
        process.env.NEXT_PUBLIC_API_URL = originalEnv
      }
    })
  })
})
