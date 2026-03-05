import { NextResponse } from "next/server"
import { beforeEach, describe, expect, it, vi } from "vitest"

vi.mock("next/server", () => ({
  NextResponse: {
    redirect: vi.fn(),
    next: vi.fn(),
  },
}))

import { proxy } from "./proxy"

describe("proxy", () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  const createMockRequest = (pathname: string, cookie?: string) => {
    return {
      nextUrl: {
        pathname,
        clone: () => ({
          pathname: "",
        }),
      },
      cookies: {
        get: vi.fn((key: string) => ({
          value: key === "access_token" ? cookie : null,
        })),
      },
    } as any
  }

  describe("protected routes without token", () => {
    it("should redirect to /login when accessing / without token", () => {
      const mockRequest = createMockRequest("/")
      const redirectSpy = vi.spyOn(NextResponse, "redirect")

      proxy(mockRequest)

      expect(redirectSpy).toHaveBeenCalled()
    })

    it("should redirect to /login when accessing /admin without token", () => {
      const mockRequest = createMockRequest("/admin")
      const redirectSpy = vi.spyOn(NextResponse, "redirect")

      proxy(mockRequest)

      expect(redirectSpy).toHaveBeenCalled()
    })

    it("should redirect to /login when accessing /items without token", () => {
      const mockRequest = createMockRequest("/items")
      const redirectSpy = vi.spyOn(NextResponse, "redirect")

      proxy(mockRequest)

      expect(redirectSpy).toHaveBeenCalled()
    })

    it("should redirect to /login when accessing /settings without token", () => {
      const mockRequest = createMockRequest("/settings")
      const redirectSpy = vi.spyOn(NextResponse, "redirect")

      proxy(mockRequest)

      expect(redirectSpy).toHaveBeenCalled()
    })
  })

  describe("protected routes with token", () => {
    it("should allow access to / with token", () => {
      const mockRequest = createMockRequest("/", "valid-token")
      const nextSpy = vi.spyOn(NextResponse, "next")
      const redirectSpy = vi.spyOn(NextResponse, "redirect")

      proxy(mockRequest)

      expect(nextSpy).toHaveBeenCalled()
      expect(redirectSpy).not.toHaveBeenCalled()
    })

    it("should allow access to /admin with token", () => {
      const mockRequest = createMockRequest("/admin", "valid-token")
      const nextSpy = vi.spyOn(NextResponse, "next")
      const redirectSpy = vi.spyOn(NextResponse, "redirect")

      proxy(mockRequest)

      expect(nextSpy).toHaveBeenCalled()
      expect(redirectSpy).not.toHaveBeenCalled()
    })

    it("should allow access to /items with token", () => {
      const mockRequest = createMockRequest("/items", "valid-token")
      const nextSpy = vi.spyOn(NextResponse, "next")
      const redirectSpy = vi.spyOn(NextResponse, "redirect")

      proxy(mockRequest)

      expect(nextSpy).toHaveBeenCalled()
      expect(redirectSpy).not.toHaveBeenCalled()
    })

    it("should allow access to /settings with token", () => {
      const mockRequest = createMockRequest("/settings", "valid-token")
      const nextSpy = vi.spyOn(NextResponse, "next")
      const redirectSpy = vi.spyOn(NextResponse, "redirect")

      proxy(mockRequest)

      expect(nextSpy).toHaveBeenCalled()
      expect(redirectSpy).not.toHaveBeenCalled()
    })
  })

  describe("auth routes without token", () => {
    it("should allow access to /login without token", () => {
      const mockRequest = createMockRequest("/login")
      const nextSpy = vi.spyOn(NextResponse, "next")
      const redirectSpy = vi.spyOn(NextResponse, "redirect")

      proxy(mockRequest)

      expect(nextSpy).toHaveBeenCalled()
      expect(redirectSpy).not.toHaveBeenCalled()
    })

    it("should allow access to /signup without token", () => {
      const mockRequest = createMockRequest("/signup")
      const nextSpy = vi.spyOn(NextResponse, "next")
      const redirectSpy = vi.spyOn(NextResponse, "redirect")

      proxy(mockRequest)

      expect(nextSpy).toHaveBeenCalled()
      expect(redirectSpy).not.toHaveBeenCalled()
    })

    it("should allow access to /recover-password without token", () => {
      const mockRequest = createMockRequest("/recover-password")
      const nextSpy = vi.spyOn(NextResponse, "next")
      const redirectSpy = vi.spyOn(NextResponse, "redirect")

      proxy(mockRequest)

      expect(nextSpy).toHaveBeenCalled()
      expect(redirectSpy).not.toHaveBeenCalled()
    })

    it("should allow access to /reset-password without token", () => {
      const mockRequest = createMockRequest("/reset-password")
      const nextSpy = vi.spyOn(NextResponse, "next")
      const redirectSpy = vi.spyOn(NextResponse, "redirect")

      proxy(mockRequest)

      expect(nextSpy).toHaveBeenCalled()
      expect(redirectSpy).not.toHaveBeenCalled()
    })
  })

  describe("auth routes with token", () => {
    it("should redirect to / when accessing /login with token", () => {
      const mockRequest = createMockRequest("/login", "valid-token")
      const redirectSpy = vi.spyOn(NextResponse, "redirect")
      const nextSpy = vi.spyOn(NextResponse, "next")

      proxy(mockRequest)

      expect(redirectSpy).toHaveBeenCalled()
      expect(nextSpy).not.toHaveBeenCalled()
    })

    it("should redirect to / when accessing /signup with token", () => {
      const mockRequest = createMockRequest("/signup", "valid-token")
      const redirectSpy = vi.spyOn(NextResponse, "redirect")
      const nextSpy = vi.spyOn(NextResponse, "next")

      proxy(mockRequest)

      expect(redirectSpy).toHaveBeenCalled()
      expect(nextSpy).not.toHaveBeenCalled()
    })

    it("should redirect to / when accessing /recover-password with token", () => {
      const mockRequest = createMockRequest("/recover-password", "valid-token")
      const redirectSpy = vi.spyOn(NextResponse, "redirect")
      const nextSpy = vi.spyOn(NextResponse, "next")

      proxy(mockRequest)

      expect(redirectSpy).toHaveBeenCalled()
      expect(nextSpy).not.toHaveBeenCalled()
    })

    it("should redirect to / when accessing /reset-password with token", () => {
      const mockRequest = createMockRequest("/reset-password", "valid-token")
      const redirectSpy = vi.spyOn(NextResponse, "redirect")
      const nextSpy = vi.spyOn(NextResponse, "next")

      proxy(mockRequest)

      expect(redirectSpy).toHaveBeenCalled()
      expect(nextSpy).not.toHaveBeenCalled()
    })
  })

  describe("public routes", () => {
    it("should allow access to /api routes", () => {
      const mockRequest = createMockRequest("/api/v1/login")
      const nextSpy = vi.spyOn(NextResponse, "next")
      const redirectSpy = vi.spyOn(NextResponse, "redirect")

      proxy(mockRequest)

      expect(nextSpy).toHaveBeenCalled()
      expect(redirectSpy).not.toHaveBeenCalled()
    })

    it("should allow access to /_next/static", () => {
      const mockRequest = createMockRequest("/_next/static/chunks/main.js")
      const nextSpy = vi.spyOn(NextResponse, "next")
      const redirectSpy = vi.spyOn(NextResponse, "redirect")

      proxy(mockRequest)

      expect(nextSpy).toHaveBeenCalled()
      expect(redirectSpy).not.toHaveBeenCalled()
    })

    it("should allow access to /favicon.ico", () => {
      const mockRequest = createMockRequest("/favicon.ico")
      const nextSpy = vi.spyOn(NextResponse, "next")
      const redirectSpy = vi.spyOn(NextResponse, "redirect")

      proxy(mockRequest)

      expect(nextSpy).toHaveBeenCalled()
      expect(redirectSpy).not.toHaveBeenCalled()
    })
  })

  describe("edge cases", () => {
    it("should handle empty token string", () => {
      const mockRequest = createMockRequest("/", "")
      const redirectSpy = vi.spyOn(NextResponse, "redirect")

      proxy(mockRequest)

      expect(redirectSpy).toHaveBeenCalled()
    })

    it("should handle undefined cookie value", () => {
      const mockRequest = createMockRequest("/")
      mockRequest.cookies.get = vi.fn(() => undefined)
      const redirectSpy = vi.spyOn(NextResponse, "redirect")

      proxy(mockRequest)

      expect(redirectSpy).toHaveBeenCalled()
    })

    it("should allow access to nested protected routes with token", () => {
      const mockRequest = createMockRequest("/admin/users", "valid-token")
      const nextSpy = vi.spyOn(NextResponse, "next")
      const redirectSpy = vi.spyOn(NextResponse, "redirect")

      proxy(mockRequest)

      expect(nextSpy).toHaveBeenCalled()
      expect(redirectSpy).not.toHaveBeenCalled()
    })

    it("should redirect on nested protected routes without token", () => {
      const mockRequest = createMockRequest("/admin/users")
      const redirectSpy = vi.spyOn(NextResponse, "redirect")

      proxy(mockRequest)

      expect(redirectSpy).toHaveBeenCalled()
    })

    it("should allow access to nested auth routes without token", () => {
      const mockRequest = createMockRequest("/reset-password/some-token")
      const nextSpy = vi.spyOn(NextResponse, "next")
      const redirectSpy = vi.spyOn(NextResponse, "redirect")

      proxy(mockRequest)

      expect(nextSpy).toHaveBeenCalled()
      expect(redirectSpy).not.toHaveBeenCalled()
    })
  })
})
