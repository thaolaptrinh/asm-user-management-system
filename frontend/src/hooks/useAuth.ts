"use client"

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { auth, users } from "@/client/sdk.gen"

/**
 * Login — POSTs credentials to the backend.
 * The backend sets an HttpOnly `access_token` cookie; no token handling needed here.
 */
export function useLogin() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (credentials: { email: string; password: string }) => {
      const response = await auth.login({
        body: {
          username: credentials.email,
          password: credentials.password,
        },
        throwOnError: true,
      })
      // Cookie is set automatically. Refetch user to update auth state.
      await queryClient.invalidateQueries({ queryKey: ["me"] })
      const data = await queryClient.fetchQuery({
        queryKey: ["me"],
        queryFn: async () => {
          const { data } = await users.getMe()
          if (!data) throw new Error("Failed to fetch user")
          return data
        },
      })
      return response.data
    },
  })
}

/**
 * Logout — calls the backend to clear the HttpOnly cookie server-side.
 */
export function useLogout() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async () => {
      await auth.logout({ throwOnError: true })
    },
    onSuccess: () => {
      queryClient.clear()
      window.location.href = "/login"
    },
    onError: () => {
      // Clear local state even if the logout request fails
      queryClient.clear()
      window.location.href = "/login"
    },
  })
}

/**
 * Fetch current user — relies on the HttpOnly cookie being sent automatically.
 * Returns undefined when not authenticated (401 → query error).
 */
export function useMe() {
  return useQuery({
    queryKey: ["me"],
    queryFn: async () => {
      const { data } = await users.getMe()
      if (!data) throw new Error("Failed to fetch user")
      return data
    },
    retry: false,
    staleTime: 5 * 60 * 1000,
  })
}

/**
 * Composite auth hook — the single source of truth for client-side auth state.
 */
export function useAuth() {
  const { data: user, isPending, isError } = useMe()
  const logoutMutation = useLogout()

  return {
    isAuthenticated: !!user && !isError,
    isLoading: isPending,
    user: user ?? null,
    logout: () => logoutMutation.mutate(),
  }
}
