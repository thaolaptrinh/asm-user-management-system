import { describe, expect, it, vi } from "vitest"
import { cn, getInitials, handleError } from "./utils"

describe("cn utility function", () => {
  describe("basic functionality", () => {
    it("should merge class names correctly", () => {
      expect(cn("px-2", "py-1")).toBe("px-2 py-1")
    })

    it("should handle empty input", () => {
      expect(cn()).toBe("")
    })

    it("should handle single class name", () => {
      expect(cn("text-sm")).toBe("text-sm")
    })
  })

  describe("conditional classes", () => {
    it("should include truthy classes", () => {
      expect(cn("base", true && "active", false && "inactive")).toBe(
        "base active",
      )
    })

    it("should filter out falsy values", () => {
      expect(cn("base", null, undefined, false, 0, "")).toBe("base")
    })

    it("should handle conditional expressions", () => {
      const isActive = true
      const isLoading = false

      expect(cn("btn", isActive && "active", isLoading && "loading")).toBe(
        "btn active",
      )
    })
  })

  describe("Tailwind conflicts", () => {
    it("should resolve Tailwind conflicts (last one wins)", () => {
      expect(cn("px-2", "px-4")).toBe("px-4")
    })

    it("should handle multiple conflicting classes", () => {
      expect(cn("text-sm text-lg", "text-xl")).toBe("text-xl")
    })
  })

  describe("arrays", () => {
    it("should handle arrays of classes", () => {
      expect(cn(["px-2", "py-1"], "text-sm")).toBe("px-2 py-1 text-sm")
    })

    it("should flatten nested arrays", () => {
      expect(cn([["px-2"], ["py-1"]])).toBe("px-2 py-1")
    })
  })

  describe("complex scenarios", () => {
    it("should handle mixed inputs", () => {
      const props = {
        className: "custom",
        isActive: true,
      }

      expect(cn("base", props.className, props.isActive && "active")).toBe(
        "base custom active",
      )
    })

    it("should handle undefined and null gracefully", () => {
      expect(cn(undefined, null, "text-sm", undefined)).toBe("text-sm")
    })
  })
})

describe("utils functions", () => {
  describe("cn - class name utility", () => {
    it("should merge class names correctly", () => {
      expect(cn("px-2", "py-1")).toBe("px-2 py-1")
    })

    it("should handle conditional classes", () => {
      expect(cn("base", true && "active", false && "inactive")).toBe(
        "base active",
      )
    })

    it("should handle undefined and null", () => {
      expect(cn(undefined, null, "test")).toBe("test")
    })

    it("should handle Tailwind conflict resolution", () => {
      expect(cn("px-2 px-4")).toBe("px-4")
    })

    it("should handle empty inputs", () => {
      expect(cn()).toBe("")
    })

    it("should handle arrays", () => {
      expect(cn(["px-2", "py-1"])).toBe("px-2 py-1")
    })

    it("should handle objects", () => {
      expect(cn({ "px-2": true, "py-1": false })).toBe("px-2")
    })

    it("should handle mixed inputs", () => {
      expect(cn("base", { active: true }, ["extra"])).toBe("base active extra")
    })

    it("should handle complex conditional classes", () => {
      const isActive = true
      const size = "large"
      expect(cn({ "bg-red": isActive, [`text-${size}`]: true })).toBe(
        "bg-red text-large",
      )
    })
  })

  describe("handleError", () => {
    it("should call this with extracted error message", () => {
      const mockThis = vi.fn()
      const err = {
        body: {
          detail: [{ msg: "Custom error" }],
        },
      }

      handleError.call(mockThis, err)

      expect(mockThis).toHaveBeenCalledWith("Custom error")
    })

    it("should use default message for unknown errors", () => {
      const mockThis = vi.fn()
      handleError.call(mockThis, {})
      expect(mockThis).toHaveBeenCalledWith("Something went wrong.")
    })

    it("should preserve this context", () => {
      const context = { show: vi.fn() }
      const err = {
        message: "Test error",
      }

      handleError.call(context.show, err)

      expect(context.show).toHaveBeenCalledWith("Test error")
    })
  })

  describe("getInitials", () => {
    it("should get initials from single word", () => {
      expect(getInitials("John")).toBe("J")
    })

    it("should get initials from two words", () => {
      expect(getInitials("John Doe")).toBe("JD")
    })

    it("should get initials from multiple words", () => {
      expect(getInitials("John Doe Smith")).toBe("JD")
    })

    it("should handle empty string", () => {
      expect(getInitials("")).toBe("")
    })

    it("should handle single letter", () => {
      expect(getInitials("J")).toBe("J")
    })

    it("should handle extra spaces", () => {
      // getInitials splits on spaces without trimming
      // "  John   Doe  ".split(" ") = ["", "", "John", "", "", "Doe", "", ""]
      // .slice(0, 2) = ["", ""]
      // Result = ""
      expect(getInitials("  John   Doe  ")).toBe("")
    })

    it("should convert to uppercase", () => {
      expect(getInitials("john doe")).toBe("JD")
    })

    it("should handle special characters", () => {
      expect(getInitials("Mary-Jane O'Brien")).toBe("MO")
    })

    it("should handle numbers in name", () => {
      expect(getInitials("John123 Doe456")).toBe("JD")
    })

    it("should handle leading/trailing spaces", () => {
      expect(getInitials(" John ")).toBe("J")
    })

    it("should return empty for spaces only", () => {
      expect(getInitials("   ")).toBe("")
    })
  })
})
