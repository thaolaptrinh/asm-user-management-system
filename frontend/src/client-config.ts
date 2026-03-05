// Client configuration - NOT auto-generated
// This file persists after API client regeneration

import { client } from "@/client/client.gen"

// Set baseUrl from environment
const apiUrl =
  process.env.NEXT_PUBLIC_API_URL ||
  (typeof window !== "undefined"
    ? "http://localhost:8000"
    : "http://backend:8000")

client.setConfig({
  baseUrl: apiUrl,
  auth: () => {
    if (typeof window === "undefined") return undefined
    return localStorage.getItem("access_token") ?? undefined
  },
})

// Error interceptor - clear auth data on 401/404
// Note: Redirect is handled by React Query error handling in useAuth hook
// This ensures smooth SPA navigation without full page reload
client.interceptors.error.use((error: unknown, response: Response) => {
  if (
    typeof window !== "undefined" &&
    (response?.status === 401 || response?.status === 404)
  ) {
    // Clear all auth data
    localStorage.removeItem("access_token")
    document.cookie = "access_token=; path=/; max-age=0"
    // Let React Query handle the redirect via useAuth hook
  }
  return error
})

export { client }
