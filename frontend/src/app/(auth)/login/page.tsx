"use client"

import { zodResolver } from "@hookform/resolvers/zod"
import Link from "next/link"
import { useSearchParams } from "next/navigation"
import { Suspense, useEffect, useState } from "react"
import { useForm } from "react-hook-form"
import { z } from "zod"

import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { LoadingButton } from "@/components/ui/loading-button"
import { PasswordInput } from "@/components/ui/password-input"
import { Button } from "@/components/ui/button"

import { Copy, Check, Download } from "lucide-react"
import { classifyTotpError } from "@/lib/totp-error"
import { useLogin } from "@/hooks/useAuth"
import {
  checkTotpStatusWithTempToken,
  enrollTotpWithTempToken,
  createChallengeWithTempToken,
  useTotpVerifyLogin,
  useTotpVerifyEnroll,
  useRecoveryLogin,
} from "@/hooks/useTotp"

// ---------------------------------------------------------------------------
// Schemas
// ---------------------------------------------------------------------------

const credentialsSchema = z.object({
  username: z.string().email(),
  password: z
    .string()
    .min(8, { message: "Password must be at least 8 characters" }),
})

const totpCodeSchema = z.object({
  code: z
    .string()
    .min(6, { message: "Enter your 6-digit code" })
    .max(8),
})

const recoveryCodeSchema = z.object({
  code: z
    .string()
    .regex(/^[A-Za-z0-9]{4}-[A-Za-z0-9]{4}$/, {
      message: "Format: XXXX-XXXX",
    }),
})

// ---------------------------------------------------------------------------
// Step types
// ---------------------------------------------------------------------------

type Step =
  | { name: "credentials" }
  | { name: "totp"; tempToken: string }
  | { name: "recovery"; tempToken: string }
  | { name: "enroll"; tempToken: string; qrCode: string; secret: string }
  | { name: "enroll-verify"; tempToken: string; challengeId: string; qrCode: string; secret: string }
  | { name: "enroll-codes"; tempToken: string; codes: string[] }
  | { name: "enroll-login"; tempToken: string }

// ---------------------------------------------------------------------------
// Sub-forms
// ---------------------------------------------------------------------------

function CredentialsForm({
  onDone,
  externalError,
  isNavigating,
}: {
  onDone: (tempToken: string) => void
  externalError?: string | null
  isNavigating?: boolean
}) {
  const loginMutation = useLogin()
  const [error, setError] = useState<string | null>(null)

  const form = useForm<z.infer<typeof credentialsSchema>>({
    resolver: zodResolver(credentialsSchema),
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: { username: "", password: "" },
  })

  const onSubmit = async (data: z.infer<typeof credentialsSchema>) => {
    setError(null)
    try {
      const result = await loginMutation.mutateAsync({
        email: data.username,
        password: data.password,
      })
      onDone(result?.temp_token ?? "")
    } catch(err: unknown) {
      const detail = (err as { detail?: string })?.detail
      setError(detail ?? "Something went wrong. Please try again.")
    }
  }

  return (
    <>
      <div className="flex flex-col items-center gap-2 text-center">
        <h1 className="text-2xl font-bold">Login to your account</h1>
      </div>

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="grid gap-4">
          <FormField
            control={form.control}
            name="username"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Email</FormLabel>
                <FormControl>
                  <Input
                    data-testid="email-input"
                    placeholder="user@example.com"
                    type="email"
                    {...field}
                  />
                </FormControl>
                <FormMessage className="text-xs" />
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name="password"
            render={({ field }) => (
              <FormItem>
                <div className="flex items-center">
                  <FormLabel>Password</FormLabel>
                  <Link
                    href="/recover-password"
                    className="ml-auto text-sm underline-offset-4 hover:underline"
                  >
                    Forgot your password?
                  </Link>
                </div>
                <FormControl>
                  <PasswordInput
                    data-testid="password-input"
                    placeholder="Password"
                    {...field}
                  />
                </FormControl>
                <FormMessage className="text-xs" />
              </FormItem>
            )}
          />
          {(error || externalError) && (
            <p className="text-sm text-destructive text-center">
              {error ?? externalError}
            </p>
          )}
          <LoadingButton type="submit" loading={loginMutation.isPending || isNavigating}>
            Log In
          </LoadingButton>
        </form>
      </Form>

      <div className="text-center text-sm">
        Don&apos;t have an account yet?{" "}
        <Link href="/signup" className="underline underline-offset-4">
          Sign up
        </Link>
      </div>
    </>
  )
}

function TotpVerifyForm({
  tempToken,
  onUseRecovery,
  onCancel,
  onExpiredToken,
}: {
  tempToken: string
  onUseRecovery: () => void
  onCancel: () => void
  onExpiredToken: (message: string) => void
}) {
  const verifyMutation = useTotpVerifyLogin()
  const [error, setError] = useState<string | null>(null)

  const form = useForm<z.infer<typeof totpCodeSchema>>({
    resolver: zodResolver(totpCodeSchema),
    defaultValues: { code: "" },
  })

  const onSubmit = async (data: z.infer<typeof totpCodeSchema>) => {
    setError(null)
    try {
      await verifyMutation.mutateAsync({ tempToken, totpCode: data.code })
    } catch (err) {
      const kind = classifyTotpError(err)
      if (kind === "expired") {
        onExpiredToken("Session expired. Please log in again.")
      } else {
        setError("Invalid OTP code. Please try again.")
        form.reset()
      }
    }
  }

  return (
    <>
      <div className="flex flex-col items-center gap-2 text-center">
        <h1 className="text-2xl font-bold">Two-Factor Authentication</h1>
        <p className="text-sm text-muted-foreground">
          Enter the 6-digit code from your authenticator app.
        </p>
      </div>

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="grid gap-4">
          <FormField
            control={form.control}
            name="code"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Authentication Code</FormLabel>
                <FormControl>
                  <Input
                    data-testid="totp-code-input"
                    placeholder="000000"
                    maxLength={8}
                    autoComplete="one-time-code"
                    inputMode="numeric"
                    {...field}
                  />
                </FormControl>
                <FormMessage className="text-xs" />
              </FormItem>
            )}
          />
          {error && (
            <p className="text-sm text-destructive text-center">{error}</p>
          )}
          <LoadingButton type="submit" loading={verifyMutation.isPending}>
            Verify
          </LoadingButton>
        </form>
      </Form>

      <Button
        variant="ghost"
        className="w-full text-sm"
        onClick={onUseRecovery}
      >
        Use a recovery code instead
      </Button>

      <Button
        variant="ghost"
        className="w-full text-sm"
        onClick={onCancel}
      >
        Cancel
      </Button>
    </>
  )
}

function RecoveryCodeForm({
  tempToken,
  onBack,
  onCancel,
}: {
  tempToken: string
  onBack: () => void
  onCancel: () => void
}) {
  const recoveryMutation = useRecoveryLogin()
  const [error, setError] = useState<string | null>(null)

  const form = useForm<z.infer<typeof recoveryCodeSchema>>({
    resolver: zodResolver(recoveryCodeSchema),
    defaultValues: { code: "" },
  })

  const onSubmit = async (data: z.infer<typeof recoveryCodeSchema>) => {
    setError(null)
    try {
      await recoveryMutation.mutateAsync({
        tempToken,
        code: data.code.toUpperCase(),
      })
    } catch (err) {
      setError(err instanceof Error ? err.message : "Invalid recovery code")
      form.reset()
    }
  }

  return (
    <>
      <div className="flex flex-col items-center gap-2 text-center">
        <h1 className="text-2xl font-bold">Recovery Code</h1>
        <p className="text-sm text-muted-foreground">
          Enter one of your 8-character recovery codes (format: XXXX-XXXX).
        </p>
      </div>

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="grid gap-4">
          <FormField
            control={form.control}
            name="code"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Recovery Code</FormLabel>
                <FormControl>
                  <Input
                    data-testid="recovery-code-input"
                    placeholder="XXXX-XXXX"
                    autoComplete="off"
                    {...field}
                  />
                </FormControl>
                <FormMessage className="text-xs" />
              </FormItem>
            )}
          />
          {error && (
            <p className="text-sm text-destructive text-center">{error}</p>
          )}
          <LoadingButton type="submit" loading={recoveryMutation.isPending}>
            Use Recovery Code
          </LoadingButton>
        </form>
      </Form>

      <Button variant="ghost" className="w-full text-sm" onClick={onBack}>
        Back to authenticator code
      </Button>

      <Button variant="ghost" className="w-full text-sm" onClick={onCancel}>
        Cancel
      </Button>
    </>
  )
}

function EnrollForm({
  tempToken,
  qrCode,
  secret,
  onDone,
  onCancel,
}: {
  tempToken: string
  qrCode: string
  secret: string
  onDone: (challengeId: string) => void
  onCancel: () => void
}) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)

  const handleContinue = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await createChallengeWithTempToken(tempToken)
      onDone(data.challenge_id)
    } catch {
      setError("Failed to create challenge. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  const handleCopy = () => {
    navigator.clipboard.writeText(secret)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <>
      <div className="flex flex-col items-center gap-2 text-center">
        <h1 className="text-2xl font-bold">Set Up Two-Factor Authentication</h1>
        <p className="text-sm text-muted-foreground">
          Scan the QR code with your authenticator app (e.g. Google Authenticator, Authy).
        </p>
      </div>

      {qrCode && (
        <div className="flex justify-center">
          {/* qrCode is already a full data URI from the backend */}
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={qrCode}
            alt="QR code for TOTP enrollment"
            width={192}
            height={192}
            className="rounded border"
          />
        </div>
      )}

      <div className="rounded-md bg-muted px-4 py-3">
        <p className="text-xs text-muted-foreground mb-2">Manual entry key</p>
        <div className="flex items-center gap-2">
          <p className="font-mono text-sm break-all select-all flex-1">{secret}</p>
          <Button
            variant="ghost"
            size="sm"
            className="h-8 w-8 p-0 shrink-0"
            onClick={handleCopy}
          >
            {copied ? (
              <Check className="h-4 w-4" />
            ) : (
              <Copy className="h-4 w-4" />
            )}
          </Button>
        </div>
      </div>

      {error && (
        <p className="text-sm text-destructive text-center">{error}</p>
      )}

      <LoadingButton onClick={handleContinue} loading={loading} className="w-full">
        I&apos;ve scanned the code
      </LoadingButton>

      <Button variant="ghost" className="w-full text-sm" onClick={onCancel}>
        Cancel
      </Button>
    </>
  )
}

const CHALLENGE_TTL_SECONDS = 60

function EnrollVerifyForm({
  tempToken,
  challengeId,
  onCodesGenerated,
  onRetry,
  onCancel,
}: {
  tempToken: string
  challengeId: string
  onCodesGenerated: (codes: string[]) => void
  onRetry: () => void
  onCancel: () => void
}) {
  const verifyEnrollMutation = useTotpVerifyEnroll()
  const [error, setError] = useState<string | null>(null)
  const [secondsLeft, setSecondsLeft] = useState(CHALLENGE_TTL_SECONDS)

  useEffect(() => {
    if (secondsLeft <= 0) return
    const timer = setTimeout(() => setSecondsLeft((s) => s - 1), 1000)
    return () => clearTimeout(timer)
  }, [secondsLeft])

  const form = useForm<z.infer<typeof totpCodeSchema>>({
    resolver: zodResolver(totpCodeSchema),
    defaultValues: { code: "" },
  })

  const onSubmit = async (data: z.infer<typeof totpCodeSchema>) => {
    setError(null)
    try {
      const result = await verifyEnrollMutation.mutateAsync({
        challengeId,
        totpCode: data.code,
        tempToken,
      })
      onCodesGenerated(result.recovery_codes ?? [])
    } catch {
      setError("Invalid or expired code. Try again.")
      form.reset()
    }
  }

  return (
    <>
      <div className="flex flex-col items-center gap-2 text-center">
        <h1 className="text-2xl font-bold">Confirm Your Code</h1>
        <p className="text-sm text-muted-foreground">
          Enter the 6-digit code from your authenticator app to activate 2FA.
        </p>
      </div>

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="grid gap-4">
          <FormField
            control={form.control}
            name="code"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Authentication Code</FormLabel>
                <FormControl>
                  <Input
                    data-testid="totp-enroll-code-input"
                    placeholder="000000"
                    maxLength={8}
                    autoComplete="one-time-code"
                    inputMode="numeric"
                    {...field}
                  />
                </FormControl>
                <FormMessage className="text-xs" />
              </FormItem>
            )}
          />
          {secondsLeft > 0 && (
            <p className="text-xs text-muted-foreground text-center">
              Session expires in {secondsLeft}s
            </p>
          )}
          {error && (
            <p className="text-sm text-destructive text-center">{error}</p>
          )}
          <LoadingButton
            type="submit"
            loading={verifyEnrollMutation.isPending}
            disabled={secondsLeft <= 0}
          >
            Activate 2FA
          </LoadingButton>
        </form>
      </Form>

      {secondsLeft <= 0 && (
        <Button variant="outline" className="w-full" onClick={onRetry}>
          Session expired — try again
        </Button>
      )}

      <Button variant="ghost" className="w-full text-sm" onClick={onCancel}>
        Cancel
      </Button>
    </>
  )
}

function EnrollCodesForm({
  codes,
  onDone,
  onCancel,
}: {
  codes: string[]
  onDone: () => void
  onCancel: () => void
}) {
  const [copied, setCopied] = useState(false)

  const handleCopy = () => {
    navigator.clipboard.writeText(codes.join("\n"))
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleDownload = () => {
    const content = [
      "Recovery Codes",
      "==============",
      "Keep these codes safe. Each code can only be used once.",
      "",
      ...codes,
    ].join("\n")
    const blob = new Blob([content], { type: "text/plain" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = "recovery-codes.txt"
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <>
      <div className="flex flex-col items-center gap-2 text-center">
        <h1 className="text-2xl font-bold">Save Your Recovery Codes</h1>
        <p className="text-sm text-muted-foreground">
          Store these codes somewhere safe. They won&apos;t be shown again.
        </p>
      </div>

      <div className="rounded-md bg-muted p-4 grid grid-cols-2 gap-2">
        {codes.map((code) => (
          <p key={code} className="font-mono text-sm">
            {code}
          </p>
        ))}
      </div>

      <div className="flex gap-2">
        <Button variant="outline" className="flex-1" onClick={handleCopy}>
          {copied ? (
            <Check className="mr-2 h-4 w-4" />
          ) : (
            <Copy className="mr-2 h-4 w-4" />
          )}
          {copied ? "Copied!" : "Copy"}
        </Button>
        <Button variant="outline" className="flex-1" onClick={handleDownload}>
          <Download className="mr-2 h-4 w-4" />
          Download
        </Button>
      </div>

      <LoadingButton onClick={onDone} className="w-full">
        I&apos;ve saved my codes — Continue
      </LoadingButton>

      <Button variant="ghost" className="w-full text-sm" onClick={onCancel}>
        Cancel
      </Button>
    </>
  )
}

function EnrollLoginForm({
  tempToken,
  onCancel,
}: {
  tempToken: string
  onCancel: () => void
}) {
  const verifyLoginMutation = useTotpVerifyLogin()
  const [error, setError] = useState<string | null>(null)

  const form = useForm<z.infer<typeof totpCodeSchema>>({
    resolver: zodResolver(totpCodeSchema),
    defaultValues: { code: "" },
  })

  const onSubmit = async (data: z.infer<typeof totpCodeSchema>) => {
    setError(null)
    try {
      await verifyLoginMutation.mutateAsync({ tempToken, totpCode: data.code })
    } catch {
      setError("Invalid or expired code. Try again.")
      form.reset()
    }
  }

  return (
    <>
      <div className="flex flex-col items-center gap-2 text-center">
        <h1 className="text-2xl font-bold">2FA Enabled!</h1>
        <p className="text-sm text-muted-foreground">
          Enter the 6-digit code from your authenticator app to complete login.
        </p>
      </div>

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="grid gap-4">
          <FormField
            control={form.control}
            name="code"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Authentication Code</FormLabel>
                <FormControl>
                  <Input
                    data-testid="totp-login-after-enroll-input"
                    placeholder="000000"
                    maxLength={8}
                    autoComplete="one-time-code"
                    inputMode="numeric"
                    {...field}
                  />
                </FormControl>
                <FormMessage className="text-xs" />
              </FormItem>
            )}
          />
          {error && (
            <p className="text-sm text-destructive text-center">{error}</p>
          )}
          <LoadingButton type="submit" loading={verifyLoginMutation.isPending}>
            Log In
          </LoadingButton>
        </form>
      </Form>

      <Button variant="ghost" className="w-full text-sm" onClick={onCancel}>
        Cancel
      </Button>
    </>
  )
}

// ---------------------------------------------------------------------------
// Registered banner — isolated to satisfy Next.js Suspense requirement
// ---------------------------------------------------------------------------

function RegisteredBanner() {
  const searchParams = useSearchParams()
  if (searchParams.get("registered") !== "true") return null
  return (
    <div className="rounded-md border border-blue-200 bg-blue-50 px-4 py-3 text-sm text-blue-800 dark:border-blue-800 dark:bg-blue-950 dark:text-blue-200">
      Account created! Log in below to set up two-factor authentication.
    </div>
  )
}

function SessionExpiredBanner() {
  const searchParams = useSearchParams()
  if (searchParams.get("reason") !== "session_expired") return null
  return (
    <div className="rounded-md border border-yellow-200 bg-yellow-50 px-4 py-3 text-sm text-yellow-800 dark:border-yellow-800 dark:bg-yellow-950 dark:text-yellow-200">
      Session expired. Please log in again.
    </div>
  )
}

// ---------------------------------------------------------------------------
// Main page — orchestrates multi-step flow
// ---------------------------------------------------------------------------

export default function LoginPage() {
  const [step, setStep] = useState<Step>({ name: "credentials" })
  const [postLoginError, setPostLoginError] = useState<string | null>(null)
  const [isNavigating, setIsNavigating] = useState(false)

  const handleCredentialsDone = async (tempToken: string) => {
    setPostLoginError(null)
    setIsNavigating(true)
    try {
      const status = await checkTotpStatusWithTempToken(tempToken)
      if (status.is_enabled) {
        setStep({ name: "totp", tempToken })
      } else {
        const enrollData = await enrollTotpWithTempToken(tempToken)
        setStep({
          name: "enroll",
          tempToken,
          qrCode: enrollData.qr_code,
          secret: enrollData.secret,
        })
      }
    } catch {
      setPostLoginError("Login failed. Please try again.")
      setStep({ name: "credentials" })
    } finally {
      setIsNavigating(false)
    }
  }

  return (
    <div className="flex flex-col gap-6">
      {step.name === "credentials" && (
        <>
          <Suspense>
            <RegisteredBanner />
            <SessionExpiredBanner />
          </Suspense>
          <CredentialsForm
            onDone={handleCredentialsDone}
            externalError={postLoginError}
            isNavigating={isNavigating}
          />
        </>
      )}

      {step.name === "totp" && (
        <TotpVerifyForm
          tempToken={step.tempToken}
          onUseRecovery={() =>
            setStep({ name: "recovery", tempToken: step.tempToken })
          }
          onCancel={() => setStep({ name: "credentials" })}
          onExpiredToken={(message) => {
            setPostLoginError(message)
            setStep({ name: "credentials" })
          }}
        />
      )}

      {step.name === "recovery" && (
        <RecoveryCodeForm
          tempToken={step.tempToken}
          onBack={() =>
            setStep({ name: "totp", tempToken: step.tempToken })
          }
          onCancel={() => setStep({ name: "credentials" })}
        />
      )}

      {step.name === "enroll" && (
        <EnrollForm
          tempToken={step.tempToken}
          qrCode={step.qrCode}
          secret={step.secret}
          onDone={(challengeId) =>
            setStep({
              name: "enroll-verify",
              tempToken: step.tempToken,
              challengeId,
              qrCode: step.qrCode,
              secret: step.secret,
            })
          }
          onCancel={() => setStep({ name: "credentials" })}
        />
      )}

      {step.name === "enroll-verify" && (
        <EnrollVerifyForm
          tempToken={step.tempToken}
          challengeId={step.challengeId}
          onCodesGenerated={(codes) =>
            setStep({ name: "enroll-codes", tempToken: step.tempToken, codes })
          }
          onRetry={() =>
            setStep({
              name: "enroll",
              tempToken: step.tempToken,
              qrCode: step.qrCode,
              secret: step.secret,
            })
          }
          onCancel={() => setStep({ name: "credentials" })}
        />
      )}

      {step.name === "enroll-codes" && (
        <EnrollCodesForm
          codes={step.codes}
          onDone={() =>
            setStep({ name: "enroll-login", tempToken: step.tempToken })
          }
          onCancel={() => setStep({ name: "credentials" })}
        />
      )}

      {step.name === "enroll-login" && (
        <EnrollLoginForm
          tempToken={step.tempToken}
          onCancel={() => setStep({ name: "credentials" })}
        />
      )}
    </div>
  )
}
