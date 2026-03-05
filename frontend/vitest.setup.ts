/// <reference types="vitest/globals" />

// Extend Vitest's expect with jest-dom matchers
import * as matchers from "@testing-library/jest-dom/matchers"
import { cleanup } from "@testing-library/react"
import { afterEach, beforeAll } from "vitest"

expect.extend(matchers)

// Cleanup after each test
afterEach(() => {
  cleanup()
})

// Setup localStorage for all environments
beforeAll(() => {
  // Define localStorage if not available (for browser mode)
  if (typeof localStorage === "undefined") {
    const localStorageMock = (() => {
      let store: Record<string, string> = {}

      return {
        getItem: (key: string) => store[key] ?? null,
        setItem: (key: string, value: string) => {
          store[key] = String(value)
        },
        removeItem: (key: string) => {
          delete store[key]
        },
        clear: () => {
          store = {}
        },
        get length() {
          return Object.keys(store).length
        },
        key: (index: number) => {
          return Object.keys(store)[index] || null
        },
      }
    })()

    Object.defineProperty(global, "localStorage", {
      value: localStorageMock,
      writable: true,
    })
  }

  // Define sessionStorage too (often used with localStorage)
  if (typeof sessionStorage === "undefined") {
    const sessionStorageMock = (() => {
      let store: Record<string, string> = {}

      return {
        getItem: (key: string) => store[key] ?? null,
        setItem: (key: string, value: string) => {
          store[key] = String(value)
        },
        removeItem: (key: string) => {
          delete store[key]
        },
        clear: () => {
          store = {}
        },
      }
    })()

    Object.defineProperty(global, "sessionStorage", {
      value: sessionStorageMock,
      writable: true,
    })
  }
})

// Mock Next.js App Router (next/navigation)
vi.mock("next/navigation", () => ({
  useRouter() {
    return {
      push: vi.fn(),
      replace: vi.fn(),
      prefetch: vi.fn(),
      back: vi.fn(),
    }
  },
  usePathname() {
    return ""
  },
  useSearchParams() {
    return new URLSearchParams()
  },
}))

// Mock next-themes
vi.mock("next-themes", () => ({
  useTheme() {
    return {
      theme: "light",
      setTheme: vi.fn(),
    }
  },
}))

// Mock window.matchMedia for responsive hooks
Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})

// Mock sonner toast
vi.mock("sonner", () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
    info: vi.fn(),
    warning: vi.fn(),
    promise: vi.fn(),
  },
}))
