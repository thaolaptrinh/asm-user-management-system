"use client"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useRouter } from "next/navigation"
import { useCallback, useEffect } from "react"
import { toast } from "sonner"

import { Login, type Token, Users } from "@/client"
import { handleError } from "@/lib/utils"
import useCustomToast from "./useCustomToast"

const ACCESS_TOKEN_KEY = "access_token"
const COOKIE_MAX_AGE_DAYS = 8

function setAccessTokenCookie(token: string) {
  if (typeof document === "undefined") return
  document.cookie = `${ACCESS_TOKEN_KEY}=${encodeURIComponent(token)}; path=/; max-age=${60 * 60 * 24 * COOKIE_MAX_AGE_DAYS}; SameSite=Lax`
}

function clearAccessTokenCookie() {
  if (typeof document === "undefined") return
  document.cookie = `${ACCESS_TOKEN_KEY}=; path=/; max-age=0`
}

const isLoggedIn = () => {
  if (typeof window === "undefined") return false
  return localStorage.getItem(ACCESS_TOKEN_KEY) !== null
}

const useAuth = () => {
  const router = useRouter()
  const queryClient = useQueryClient()
  const { showErrorToast } = useCustomToast()

  const logout = useCallback(() => {
    localStorage.removeItem(ACCESS_TOKEN_KEY)
    clearAccessTokenCookie()
    queryClient.clear()
    router.push("/login")
    toast.success("Logged out successfully")
  }, [queryClient, router])

  const { data: user, error } = useQuery({
    queryKey: ["currentUser"],
    queryFn: () => Users.readUserMe({ throwOnError: true }).then((r) => r.data),
    enabled: isLoggedIn(),
    retry: false,
  })

  // Auto-logout on auth errors (401/404)
  // Error interceptor in client-config.ts clears auth data
  // This hook handles the redirect using useEffect to avoid render-phase side effects
  useEffect(() => {
    if (error) {
      logout()
    }
  }, [error, logout])

  const signUpMutation = useMutation({
    mutationFn: (opts: {
      body: Parameters<typeof Users.registerUser>[0]["body"]
    }) =>
      Users.registerUser({ ...opts, throwOnError: true }).then((r) => r.data),
    onSuccess: () => {
      router.push("/login")
      toast.success("Account created successfully")
    },
    onError: handleError.bind(showErrorToast),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] })
    },
  })

  const loginMutation = useMutation({
    mutationFn: (opts: {
      body: Parameters<typeof Login.loginAccessToken>[0]["body"]
    }) =>
      Login.loginAccessToken({ ...opts, throwOnError: true }).then(
        (r) => r.data,
      ),
    onSuccess: (data: Token) => {
      localStorage.setItem(ACCESS_TOKEN_KEY, data.access_token)
      setAccessTokenCookie(data.access_token)
      toast.success("Logged in successfully")
      router.push("/")
    },
    onError: handleError.bind(showErrorToast),
  })

  return {
    signUpMutation,
    loginMutation,
    logout,
    user,
  }
}

export { isLoggedIn }
export default useAuth
