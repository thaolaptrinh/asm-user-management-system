"use client"

/**
 * Auth API: single source of truth in @/hooks/useAuth.
 * This file re-exports for backward compatibility (e.g. auth pages importing from @/lib/auth).
 */
export { isLoggedIn, default as useAuth } from "@/hooks/useAuth"
