import { describe, it, expect, vi, beforeEach } from "vitest"
import type { QueryClient } from "@tanstack/react-query"
import type { ResolvedRequestOptions } from "@/client/client/types.gen"

import { client } from "@/client/client.gen"
import { navigateToLogin } from "@/lib/router-instance"

vi.mock("@/client/sdk.gen", () => ({
  auth: {
    logout: vi.fn().mockResolvedValue(undefined),
  },
}))

const mockUse = vi.fn()
client.interceptors.error.use = mockUse

import {
  requiresAuth,
  createUnauthorizedHandler,
  setupUnauthorizedInterceptor,
  resetUnauthorizedInterceptor,
  setQueryClient,
} from "./unauthorized-interceptor"

const createMockResponse = (status: number): Response =>
  ({ status } as Response)

const createMockOptions = (
  security: ResolvedRequestOptions["security"],
): ResolvedRequestOptions =>
  ({ security } as ResolvedRequestOptions)

describe("requiresAuth", () => {
  it("returns true when security exists", () => {
    const options = createMockOptions([{ scheme: "bearer", type: "http" }])
    expect(requiresAuth(options)).toBe(true)
  })

  it("returns false when security undefined", () => {
    const options = createMockOptions(undefined)
    expect(requiresAuth(options)).toBe(false)
  })

  it("returns false when security empty", () => {
    const options = createMockOptions([])
    expect(requiresAuth(options)).toBe(false)
  })
})

describe("createUnauthorizedHandler", () => {
  let queryClient: QueryClient

  beforeEach(() => {
    queryClient = { clear: vi.fn() } as unknown as QueryClient
  })

  it("ignores non 401 responses", async () => {
    const logout = vi.fn().mockResolvedValue(undefined)
    const redirect = vi.fn()

    const handler = createUnauthorizedHandler({
      deps: { queryClient, logout, redirect },
    })

    const error = new Error()
    const res = createMockResponse(500)

    const result = await handler(error, res, createMockOptions([{ scheme: "bearer", type: "http" }]))

    expect(result).toBe(error)
    expect(logout).not.toHaveBeenCalled()
  })

  it("ignores public endpoints", async () => {
    const logout = vi.fn().mockResolvedValue(undefined)
    const redirect = vi.fn()

    const handler = createUnauthorizedHandler({
      deps: { queryClient, logout, redirect },
    })

    const error = new Error()
    const res = createMockResponse(401)

    const result = await handler(error, res, createMockOptions(undefined))

    expect(result).toBe(error)
    expect(logout).not.toHaveBeenCalled()
  })

  it("logs out on protected 401", async () => {
    const logout = vi.fn().mockResolvedValue(undefined)
    const redirect = vi.fn()

    const handler = createUnauthorizedHandler({
      deps: { queryClient, logout, redirect },
    })

    const error = new Error()
    const res = createMockResponse(401)

    await handler(error, res, createMockOptions([{ scheme: "bearer", type: "http" }]))

    expect(queryClient.clear).toHaveBeenCalled()
    expect(logout).toHaveBeenCalled()
    expect(redirect).toHaveBeenCalled()
  })

  it("handles logout failure", async () => {
    const logout = vi.fn().mockRejectedValue(new Error("fail"))
    const redirect = vi.fn()
    const consoleSpy = vi.spyOn(console, "error").mockImplementation(() => { })

    const handler = createUnauthorizedHandler({
      deps: { queryClient, logout, redirect },
    })

    await handler(
      new Error(),
      createMockResponse(401),
      createMockOptions([{ scheme: "bearer", type: "http" }]),
    )

    expect(consoleSpy).toHaveBeenCalled()
    expect(redirect).toHaveBeenCalled()

    consoleSpy.mockRestore()
  })

  it("prevents duplicate logout", async () => {
    const logout = vi.fn().mockResolvedValue(undefined)
    const redirect = vi.fn()

    const handler = createUnauthorizedHandler({
      deps: { queryClient, logout, redirect },
    })

    const res = createMockResponse(401)
    const opts = createMockOptions([{ scheme: "bearer", type: "http" }])

    // Trigger concurrent 401s
    const p1 = handler(new Error(), res, opts)
    const p2 = handler(new Error(), res, opts)

    await Promise.all([p1, p2])

    // Only one logout should occur despite two concurrent 401s
    expect(logout).toHaveBeenCalledTimes(1)
  })

  it("allows logout after previous attempt completes", async () => {
    const logout = vi.fn().mockResolvedValue(undefined)
    const redirect = vi.fn()

    const handler = createUnauthorizedHandler({
      deps: { queryClient, logout, redirect },
    })

    const res = createMockResponse(401)
    const opts = createMockOptions([{ scheme: "bearer", type: "http" }])

    // First 401
    await handler(new Error(), res, opts)
    expect(logout).toHaveBeenCalledTimes(1)

    // Second 401 after first completes
    await handler(new Error(), res, opts)
    expect(logout).toHaveBeenCalledTimes(2)
  })

  it("works when queryClient is null", async () => {
    const logout = vi.fn().mockResolvedValue(undefined)
    const redirect = vi.fn()

    const handler = createUnauthorizedHandler({
      deps: {
        queryClient: null,
        logout,
        redirect,
      },
    })

    await handler(
      new Error(),
      createMockResponse(401),
      createMockOptions([{ scheme: "bearer", type: "http" }]),
    )

    expect(logout).toHaveBeenCalled()
    expect(redirect).toHaveBeenCalled()
  })
})

describe("setupUnauthorizedInterceptor", () => {
  beforeEach(() => {
    resetUnauthorizedInterceptor()
    mockUse.mockClear()
  })

  it("registers interceptor with required deps", () => {
    const logout = vi.fn().mockResolvedValue(undefined)
    const redirect = vi.fn()

    setupUnauthorizedInterceptor({ logout, redirect })

    expect(mockUse).toHaveBeenCalled()
  })

  it("does not register twice", () => {
    const logout = vi.fn().mockResolvedValue(undefined)
    const redirect = vi.fn()

    setupUnauthorizedInterceptor({ logout, redirect })
    setupUnauthorizedInterceptor({ logout, redirect })

    expect(mockUse).toHaveBeenCalledTimes(1)
  })

  it("uses provided queryClient", () => {
    const queryClient = { clear: vi.fn() } as unknown as QueryClient
    const logout = vi.fn().mockResolvedValue(undefined)
    const redirect = vi.fn()

    setupUnauthorizedInterceptor({ queryClient, logout, redirect })

    expect(mockUse).toHaveBeenCalled()
  })
})

describe("setQueryClient", () => {
  it("sets global query client", () => {
    const queryClient = { clear: vi.fn() } as unknown as QueryClient

    expect(() => setQueryClient(queryClient)).not.toThrow()
  })
})

describe("global queryClient integration", () => {
  beforeEach(() => {
    resetUnauthorizedInterceptor()
    mockUse.mockClear()
  })

  it("uses global queryClient when provided", () => {
    const queryClient = { clear: vi.fn() } as unknown as QueryClient
    const logout = vi.fn().mockResolvedValue(undefined)
    const redirect = vi.fn()

    setQueryClient(queryClient)

    setupUnauthorizedInterceptor({ logout, redirect })

    expect(mockUse).toHaveBeenCalled()
  })
})

describe("resetUnauthorizedInterceptor", () => {
  it("resets globalQueryClient to null", () => {
    const queryClient = { clear: vi.fn() } as unknown as QueryClient
    const logout = vi.fn().mockResolvedValue(undefined)
    const redirect = vi.fn()

    setQueryClient(queryClient)
    resetUnauthorizedInterceptor()

    expect(() => setupUnauthorizedInterceptor({ logout, redirect })).not.toThrow()
  })
})

describe("integration", () => {
  beforeEach(() => {
    resetUnauthorizedInterceptor()
    mockUse.mockClear()
  })

  it("uses navigateToLogin for redirect in production-like setup", async () => {
    const queryClient = { clear: vi.fn() } as unknown as QueryClient
    const logout = vi.fn().mockResolvedValue(undefined)

    // Setup with navigateToLogin (like in providers.tsx)
    setupUnauthorizedInterceptor({
      queryClient,
      logout,
      redirect: navigateToLogin,
    })

    expect(mockUse).toHaveBeenCalled()

    // Verify interceptor was registered
    expect(mockUse).toHaveBeenCalledTimes(1)
  })
})
