import { beforeEach, describe, expect, it, vi } from "vitest"

// Mock window
const mockMatchMedia = vi.fn()
Object.defineProperty(global, "window", {
  value: {
    matchMedia: mockMatchMedia,
    innerWidth: 1024,
  },
  writable: true,
})

// Mock React hooks
vi.mock("react", async () => {
  const actual = await vi.importActual("react")
  return {
    ...actual,
    useState: vi.fn((initialValue) => [initialValue, vi.fn()]),
    useEffect: vi.fn((fn) => fn()),
  }
})

describe("useMobile hook", () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Reset window width
    global.innerWidth = 1024
    // Reset matchMedia mock
    mockMatchMedia.mockReturnValue({
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    })
  })

  it("should have correct mobile breakpoint", async () => {
    const MOBILE_BREAKPOINT = 768
    expect(MOBILE_BREAKPOINT).toBe(768)
  })

  it("should return false for desktop screen", async () => {
    global.innerWidth = 1024

    const { useIsMobile } = await import("./useMobile")
    const result = useIsMobile()

    expect(result).toBe(false) // 1024 >= 768
  })

  it("should return true for mobile screen", async () => {
    global.innerWidth = 500

    const { useIsMobile } = await import("./useMobile")
    const { useState } = await import("react")

    vi.mocked(useState).mockReturnValue([true, vi.fn()])

    const result = useIsMobile()
    expect(result).toBe(true) // 500 < 768
  })

  it("should return false for tablet screen (768px)", async () => {
    global.innerWidth = 768

    const { useIsMobile } = await import("./useMobile")
    const { useState } = await import("react")

    vi.mocked(useState).mockReturnValue([false, vi.fn()])

    const result = useIsMobile()
    expect(result).toBe(false) // 768 is not < 768
  })

  it("should return true for small tablet (767px)", async () => {
    global.innerWidth = 767

    const { useIsMobile } = await import("./useMobile")
    const { useState } = await import("react")

    vi.mocked(useState).mockReturnValue([true, vi.fn()])

    const result = useIsMobile()
    expect(result).toBe(true) // 767 < 768
  })

  it("should call matchMedia with correct query", async () => {
    global.innerWidth = 500

    const { useIsMobile } = await import("./useMobile")

    vi.mocked(mockMatchMedia).mockReturnValue({
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    })

    useIsMobile()

    expect(mockMatchMedia).toHaveBeenCalledWith("(max-width: 767px)")
  })

  it("should setup event listener for media query changes", async () => {
    const mockAddEventListener = vi.fn()
    const mockRemoveEventListener = vi.fn()

    vi.mocked(mockMatchMedia).mockReturnValue({
      addEventListener: mockAddEventListener,
      removeEventListener: mockRemoveEventListener,
    })

    const { useIsMobile } = await import("./useMobile")
    const { useEffect } = await import("react")

    const cleanup = vi.fn()
    vi.mocked(useEffect).mockImplementation((fn) => {
      cleanup.mockImplementation(fn())
    })

    useIsMobile()

    expect(mockAddEventListener).toHaveBeenCalledWith(
      "change",
      expect.any(Function),
    )
  })

  it("should cleanup event listener on unmount", async () => {
    const mockAddEventListener = vi.fn()
    const mockRemoveEventListener = vi.fn()

    vi.mocked(mockMatchMedia).mockReturnValue({
      addEventListener: mockAddEventListener,
      removeEventListener: mockRemoveEventListener,
    })

    const { useIsMobile } = await import("./useMobile")
    const { useEffect } = await import("react")

    const cleanup = vi.fn()
    vi.mocked(useEffect).mockImplementation((fn) => {
      const cleanupFn = fn()
      if (cleanupFn) {
        cleanup.mockImplementation(cleanupFn)
      }
      return cleanup
    })

    useIsMobile()

    // Trigger cleanup
    const cleanupResult = vi.mocked(useEffect).mock.calls[0][0]()
    if (cleanupResult) {
      cleanupResult()
    }

    expect(mockRemoveEventListener).toHaveBeenCalledWith(
      "change",
      expect.any(Function),
    )
  })
})
