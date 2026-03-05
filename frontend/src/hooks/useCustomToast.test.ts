import { toast } from "sonner"
import { beforeEach, describe, expect, it, vi } from "vitest"
import useCustomToast from "./useCustomToast"

// Mock sonner toast
vi.mock("sonner", () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}))

describe("useCustomToast", () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe("showSuccessToast", () => {
    it("should call toast.success with correct title and description", () => {
      const { showSuccessToast } = useCustomToast()

      showSuccessToast("Operation completed successfully")

      expect(toast.success).toHaveBeenCalledWith("Success!", {
        description: "Operation completed successfully",
      })
    })

    it("should handle empty description", () => {
      const { showSuccessToast } = useCustomToast()
      showSuccessToast("")

      expect(toast.success).toHaveBeenCalledWith("Success!", {
        description: "",
      })
    })

    it("should handle special characters in description", () => {
      const { showSuccessToast } = useCustomToast()
      const specialMessage = 'Test with <special> & "characters"'
      showSuccessToast(specialMessage)

      expect(toast.success).toHaveBeenCalledWith("Success!", {
        description: specialMessage,
      })
    })

    it("should handle long descriptions", () => {
      const { showSuccessToast } = useCustomToast()
      const longMessage = "A".repeat(1000)
      showSuccessToast(longMessage)

      expect(toast.success).toHaveBeenCalledWith("Success!", {
        description: longMessage,
      })
    })
  })

  describe("showErrorToast", () => {
    it("should call toast.error with correct title and description", () => {
      const { showErrorToast } = useCustomToast()
      showErrorToast("Invalid credentials")

      expect(toast.error).toHaveBeenCalledWith("Something went wrong!", {
        description: "Invalid credentials",
      })
    })

    it("should handle empty description", () => {
      const { showErrorToast } = useCustomToast()
      showErrorToast("")

      expect(toast.error).toHaveBeenCalledWith("Something went wrong!", {
        description: "",
      })
    })

    it("should handle error messages with special characters", () => {
      const { showErrorToast } = useCustomToast()
      const errorMessage = "Error: Field 'email' is required & must be valid"
      showErrorToast(errorMessage)

      expect(toast.error).toHaveBeenCalledWith("Something went wrong!", {
        description: errorMessage,
      })
    })

    it("should handle network error messages", () => {
      const { showErrorToast } = useCustomToast()
      showErrorToast("Network error: Unable to reach server")

      expect(toast.error).toHaveBeenCalledWith("Something went wrong!", {
        description: "Network error: Unable to reach server",
      })
    })
  })

  describe("integration scenarios", () => {
    it("should handle multiple toast calls", () => {
      const { showSuccessToast, showErrorToast } = useCustomToast()

      showSuccessToast("First success")
      showErrorToast("First error")
      showSuccessToast("Second success")

      expect(toast.success).toHaveBeenCalledTimes(2)
      expect(toast.error).toHaveBeenCalledTimes(1)
      expect(toast.success).toHaveBeenNthCalledWith(1, "Success!", {
        description: "First success",
      })
      expect(toast.error).toHaveBeenCalledWith("Something went wrong!", {
        description: "First error",
      })
      expect(toast.success).toHaveBeenNthCalledWith(2, "Success!", {
        description: "Second success",
      })
    })

    it("should return consistent function references", () => {
      const { showSuccessToast, showErrorToast } = useCustomToast()
      const { showSuccessToast: success2, showErrorToast: error2 } =
        useCustomToast()

      expect(typeof showSuccessToast).toBe("function")
      expect(typeof showErrorToast).toBe("function")
      expect(typeof success2).toBe("function")
      expect(typeof error2).toBe("function")
    })
  })
})
