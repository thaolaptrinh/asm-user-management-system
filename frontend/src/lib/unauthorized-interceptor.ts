import { client } from "@/client/client.gen"
import type { QueryClient } from "@tanstack/react-query"
import type { ResolvedRequestOptions } from "@/client/client/types.gen"

export interface UnauthorizedHandlerDeps {
  queryClient: QueryClient | null
  logout: () => Promise<unknown>
  redirect: () => void
}

/**
 * Checks if a request requires authentication
 * @param options - The request options to check
 * @returns true if the request has security requirements
 */
export function requiresAuth(options: ResolvedRequestOptions): boolean {
  return options.security !== undefined && options.security.length > 0
}

export interface CreateUnauthorizedHandlerOptions {
  deps: UnauthorizedHandlerDeps
}

/**
 * Creates an error handler for 401 unauthorized responses
 *
 * On 401 responses for protected endpoints:
 * - Clears the query client cache
 * - Attempts to logout
 * - Redirects to login page
 * - Prevents duplicate logout attempts
 *
 * @param options - Handler options with required dependencies
 * @returns An error interceptor function
 */
export function createUnauthorizedHandler(options: CreateUnauthorizedHandlerOptions) {
  const { queryClient, logout, redirect } = options.deps
  let isLoggingOut = false

  return async (
    error: unknown,
    response: Response,
    requestOptions: ResolvedRequestOptions,
  ) => {
    if (response.status !== 401) {
      return error
    }

    if (!requiresAuth(requestOptions)) {
      return error
    }

    if (isLoggingOut) {
      return error
    }

    isLoggingOut = true

    queryClient?.clear()

    try {
      await logout()
    } catch (err) {
      console.error("[Auth] Logout failed:", err)
    } finally {
      redirect()
      isLoggingOut = false
    }

    return error
  }
}

export interface SetupUnauthorizedInterceptorOptions {
  queryClient?: QueryClient
  logout: () => Promise<unknown>
  redirect: () => void
}

let globalQueryClient: QueryClient | null = null
let isSetup = false

/**
 * Sets the global query client for the unauthorized interceptor
 * Must be called before setupUnauthorizedInterceptor if not providing queryClient in options
 * @param queryClient - The React Query client instance
 */
export function setQueryClient(queryClient: QueryClient) {
  globalQueryClient = queryClient
}

/**
 * Sets up the global unauthorized interceptor for handling 401 responses
 *
 * This function can only be called once per app lifecycle. Subsequent calls will be ignored.
 * The interceptor automatically:
 * - Detects 401 responses from protected endpoints
 * - Clears query cache
 * - Attempts logout
 * - Redirects to login
 *
 * @param options - Required dependencies for the interceptor
 */
export function setupUnauthorizedInterceptor(options: SetupUnauthorizedInterceptorOptions) {
  if (isSetup) return
  isSetup = true

  const queryClient = options.queryClient ?? globalQueryClient ?? null

  const handler = createUnauthorizedHandler({
    deps: {
      queryClient,
      logout: options.logout,
      redirect: options.redirect,
    },
  })

  client.interceptors.error.use(handler)
}

/**
 * Resets the unauthorized interceptor state
 *
 * WARNING: This is primarily intended for testing purposes.
 * Calling this in production will allow setupUnauthorizedInterceptor to be called again.
 */
export function resetUnauthorizedInterceptor() {
  isSetup = false
  globalQueryClient = null
}
