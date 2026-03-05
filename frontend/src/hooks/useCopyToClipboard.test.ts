import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

// Mock navigator.clipboard
const mockWriteText = vi.fn()
Object.defineProperty(global, "navigator", {
  value: {
    clipboard: {
      writeText: mockWriteText,
    },
  },
  writable: true,
})

// Mock React hooks
vi.mock("react", async () => {
  const actual = await vi.importActual("react")
  return {
    ...actual,
    useState: vi.fn((initialValue) => [initialValue, vi.fn()]),
    useCallback: vi.fn((fn) => fn),
  }
})

describe("useCopyToClipboard hook", () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it("should return copiedText and copy function", async () => {
    const { useCopyToClipboard } = await import("./useCopyToClipboard")
    const [copiedText, copy] = useCopyToClipboard()

    expect(copiedText).toBeNull()
    expect(typeof copy).toBe("function")
  })

  it("should copy text successfully", async () => {
    mockWriteText.mockResolvedValue(undefined)

    const { useCopyToClipboard } = await import("./useCopyToClipboard")
    const { useState } = await import("react")
    const { useCallback } = await import("react")

    const setStateMock = vi.fn()
    vi.mocked(useState).mockReturnValue([null, setStateMock])
    vi.mocked(useCallback).mockImplementation((fn) => fn)

    const [, copy] = useCopyToClipboard()
    const result = await copy("test text")

    expect(mockWriteText).toHaveBeenCalledWith("test text")
    expect(setStateMock).toHaveBeenCalledWith("test text")
    expect(result).toBe(true)
  })

  it("should clear copied text after 2 seconds", async () => {
    mockWriteText.mockResolvedValue(undefined)

    const { useCopyToClipboard } = await import("./useCopyToClipboard")
    const { useState } = await import("react")

    const setStateMock = vi.fn()
    vi.mocked(useState).mockReturnValue([null, setStateMock])

    const [, copy] = useCopyToClipboard()
    await copy("test text")

    // Fast-forward 2 seconds
    vi.advanceTimersByTime(2000)

    expect(setStateMock).toHaveBeenCalledWith(null)
  })

  it("should handle clipboard not supported", async () => {
    // Mock navigator without clipboard
    Object.defineProperty(global, "navigator", {
      value: {},
      writable: true,
    })

    const { useCopyToClipboard } = await import("./useCopyToClipboard")

    const [, copy] = useCopyToClipboard()
    const result = await copy("test text")

    expect(result).toBe(false)

    // Restore clipboard
    Object.defineProperty(global, "navigator", {
      value: {
        clipboard: {
          writeText: mockWriteText,
        },
      },
      writable: true,
    })
  })

  it("should handle clipboard write error", async () => {
    const consoleWarnSpy = vi
      .spyOn(console, "warn")
      .mockImplementation(() => {})
    mockWriteText.mockRejectedValue(new Error("Copy failed"))

    const { useCopyToClipboard } = await import("./useCopyToClipboard")
    const { useState } = await import("react")

    const setStateMock = vi.fn()
    vi.mocked(useState).mockReturnValue(["some-text", setStateMock])

    const [, copy] = useCopyToClipboard()
    const result = await copy("test text")

    expect(result).toBe(false)
    expect(setStateMock).toHaveBeenCalledWith(null)
    expect(consoleWarnSpy).toHaveBeenCalledWith(
      "Copy failed",
      expect.any(Error),
    )

    consoleWarnSpy.mockRestore()
  })

  it("should handle empty string", async () => {
    mockWriteText.mockResolvedValue(undefined)

    const { useCopyToClipboard } = await import("./useCopyToClipboard")
    const { useState } = await import("react")

    const setStateMock = vi.fn()
    vi.mocked(useState).mockReturnValue([null, setStateMock])

    const [, copy] = useCopyToClipboard()
    const result = await copy("")

    expect(mockWriteText).toHaveBeenCalledWith("")
    expect(setStateMock).toHaveBeenCalledWith("")
    expect(result).toBe(true)
  })

  it("should handle long text", async () => {
    const longText = "A".repeat(10000)
    mockWriteText.mockResolvedValue(undefined)

    const { useCopyToClipboard } = await import("./useCopyToClipboard")
    const { useState } = await import("react")

    const setStateMock = vi.fn()
    vi.mocked(useState).mockReturnValue([null, setStateMock])

    const [, copy] = useCopyToClipboard()
    const result = await copy(longText)

    expect(mockWriteText).toHaveBeenCalledWith(longText)
    expect(result).toBe(true)
  })

  it("should handle special characters", async () => {
    const specialText = "Test with emoji 🎉 and special chars <>&\"'"
    mockWriteText.mockResolvedValue(undefined)

    const { useCopyToClipboard } = await import("./useCopyToClipboard")
    const { useState } = await import("react")

    const setStateMock = vi.fn()
    vi.mocked(useState).mockReturnValue([null, setStateMock])

    const [, copy] = useCopyToClipboard()
    const result = await copy(specialText)

    expect(mockWriteText).toHaveBeenCalledWith(specialText)
    expect(result).toBe(true)
  })

  it("should handle multiple rapid copies", async () => {
    mockWriteText.mockResolvedValue(undefined)

    const { useCopyToClipboard } = await import("./useCopyToClipboard")
    const { useState } = await import("react")

    const setStateMock = vi.fn()
    vi.mocked(useState).mockReturnValue([null, setStateMock])

    const [, copy] = useCopyToClipboard()

    await copy("first")
    await copy("second")
    await copy("third")

    expect(mockWriteText).toHaveBeenCalledTimes(3)
    expect(setStateMock).toHaveBeenLastCalledWith("third")
  })

  it("should return correct CopiedValue type", async () => {
    const { useCopyToClipboard } = await import("./useCopyToClipboard")
    const [copiedText] = useCopyToClipboard()

    // Initial state is null
    expect(copiedText).toBeNull()

    // After copy, should be string
    const { useState } = await import("react")
    vi.mocked(useState).mockReturnValue(["test-text", vi.fn()])

    const [copiedText2] = useCopyToClipboard()
    expect(copiedText2).toBe("test-text")
  })
})
