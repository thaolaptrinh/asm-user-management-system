"use client"

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { totp, totpRecovery } from "@/client/sdk.gen"
import type { TotpVerifyFlowBResponse } from "@/client/types.gen"
import { useFinaliseLogin } from "@/hooks/useAuth"

// ---------------------------------------------------------------------------
// TOTP status
// ---------------------------------------------------------------------------

/** Check whether the user has TOTP enabled. Requires an access_token cookie. */
export function useTotpStatus() {
  return useQuery({
    queryKey: ["totp-status"],
    queryFn: async () => {
      const { data } = await totp.totpStatus()
      if (!data) throw new Error("Failed to fetch TOTP status")
      return data
    },
    staleTime: 60_000,
  })
}

// ---------------------------------------------------------------------------
// Enrollment flow (called from settings — user already has an access_token cookie)
// ---------------------------------------------------------------------------

/** Step 1: generate secret + QR code. */
export function useTotpEnroll() {
  return useMutation({
    mutationFn: async () => {
      const { data } = await totp.totpEnroll({ throwOnError: true })
      return data!
    },
  })
}

/** Step 2: create an in-memory challenge. */
export function useTotpChallenge() {
  return useMutation({
    mutationFn: async () => {
      const { data } = await totp.totpChallenge({ throwOnError: true })
      return data!
    },
  })
}

/** Step 3 (Flow B): verify TOTP code to complete enrollment. Returns recovery_codes. */
export function useTotpVerifyEnroll() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({
      challengeId,
      totpCode,
      tempToken,
    }: {
      challengeId: string
      totpCode: string
      /** Optional: pass during login enrollment to bind the challenge to the login session. */
      tempToken?: string
    }) => {
      const { data } = await totp.totpVerify({
        body: {
          challenge_id: challengeId as `${string}-${string}-${string}-${string}-${string}`,
          totp_code: totpCode,
          // Binding: include temp_token so the backend can verify the challenge
          // belongs to the same login session (prevents cross-session enrollment).
          ...(tempToken ? { temp_token: tempToken } : {}),
        },
        throwOnError: true,
      })
      return data! as TotpVerifyFlowBResponse
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["totp-status"] })
      queryClient.invalidateQueries({ queryKey: ["recovery-codes-status"] })
    },
  })
}

// ---------------------------------------------------------------------------
// Login flow — pass `auth: tempToken` so hey-api's security handler sets
// `Authorization: Bearer <tempToken>` on the request.
// ---------------------------------------------------------------------------

/** Check TOTP status during login using a temp_token. */
export async function checkTotpStatusWithTempToken(tempToken: string) {
  const { data } = await totp.totpStatus({ auth: tempToken, throwOnError: true })
  return data!
}

/** Step 1 of login enrollment: get QR code using temp_token. */
export async function enrollTotpWithTempToken(tempToken: string) {
  const { data } = await totp.totpEnroll({ auth: tempToken, throwOnError: true })
  return data!
}

/** Step 2 of login enrollment: get challenge using temp_token. */
export async function createChallengeWithTempToken(tempToken: string) {
  const { data } = await totp.totpChallenge({ auth: tempToken, throwOnError: true })
  return data!
}

// ---------------------------------------------------------------------------
// TOTP verify — Flow A (login): temp_token + totp_code → access_token cookie
// ---------------------------------------------------------------------------

export function useTotpVerifyLogin() {
  const finalise = useFinaliseLogin()

  return useMutation({
    mutationFn: async ({
      tempToken,
      totpCode,
    }: {
      tempToken: string
      totpCode: string
    }) => {
      const { data } = await totp.totpVerify({
        body: { temp_token: tempToken, totp_code: totpCode },
        throwOnError: true,
      })
      return data!
    },
    onSuccess: () => finalise.mutate(),
  })
}

// ---------------------------------------------------------------------------
// Recovery codes (settings — uses access_token cookie automatically)
// ---------------------------------------------------------------------------

export function useRecoveryCodesStatus() {
  return useQuery({
    queryKey: ["recovery-codes-status"],
    queryFn: async () => {
      const { data } = await totpRecovery.getRecoveryCodesStatus()
      if (!data) throw new Error("Failed to fetch recovery codes status")
      return data
    },
    staleTime: 30_000,
  })
}

export function useGenerateRecoveryCodes() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async () => {
      const { data } = await totpRecovery.generateRecoveryCodes({ throwOnError: true })
      return data!
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["recovery-codes-status"] })
    },
  })
}

// ---------------------------------------------------------------------------
// Recovery code login — uses temp_token as Bearer via `auth` option
// ---------------------------------------------------------------------------

export function useRecoveryLogin() {
  const finalise = useFinaliseLogin()

  return useMutation({
    mutationFn: async ({
      tempToken,
      code,
    }: {
      tempToken: string
      code: string
    }) => {
      // Backend returns 401 on invalid code (throwOnError: true will throw automatically).
      const { data } = await totpRecovery.verifyRecoveryCode({
        body: { temp_token: tempToken, code: code.toUpperCase() },
        throwOnError: true,
      })
      return data!
    },
    onSuccess: () => finalise.mutate(),
  })
}
