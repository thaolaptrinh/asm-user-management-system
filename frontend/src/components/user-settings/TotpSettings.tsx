"use client"

import { useState } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { ShieldCheck, ShieldOff, Copy, Check, Download, RefreshCw, ShieldAlert } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { LoadingButton } from "@/components/ui/loading-button"
import { Input } from "@/components/ui/input"
import { Separator } from "@/components/ui/separator"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  DialogClose,
} from "@/components/ui/dialog"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import useCustomToast from "@/hooks/useCustomToast"
import {
  useTotpStatus,
  useTotpEnroll,
  useTotpChallenge,
  useTotpVerifyEnroll,
  useRecoveryCodesStatus,
  useGenerateRecoveryCodes,
} from "@/hooks/useTotp"

const totpCodeSchema = z.object({
  code: z.string().min(6, "Enter your 6-digit code").max(8),
})

// ---------------------------------------------------------------------------
// Shared copy/download actions for recovery codes
// ---------------------------------------------------------------------------

function RecoveryCodeActions({ codes }: { codes: string[] }) {
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
    <div className="flex gap-2">
      <Button variant="outline" className="flex-1" onClick={handleCopy}>
        {copied ? (
          <Check className="mr-2 h-4 w-4" />
        ) : (
          <Copy className="mr-2 h-4 w-4" />
        )}
        {copied ? "Copied!" : "Copy All"}
      </Button>
      <Button variant="outline" className="flex-1" onClick={handleDownload}>
        <Download className="mr-2 h-4 w-4" />
        Download
      </Button>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Enrollment dialog
// ---------------------------------------------------------------------------

function EnrollDialog({
  open,
  onOpenChange,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
}) {
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const enrollMutation = useTotpEnroll()
  const challengeMutation = useTotpChallenge()
  const verifyMutation = useTotpVerifyEnroll()

  type EnrollStep =
    | { name: "idle" }
    | { name: "qr"; qrCode: string; secret: string }
    | { name: "verify"; challengeId: string }
    | { name: "done" }

  const [enrollStep, setEnrollStep] = useState<EnrollStep>({ name: "idle" })
  const [loadingEnroll, setLoadingEnroll] = useState(false)
  const [recoveryCodes, setRecoveryCodes] = useState<string[]>([])

  const form = useForm<z.infer<typeof totpCodeSchema>>({
    resolver: zodResolver(totpCodeSchema),
    defaultValues: { code: "" },
  })

  const startEnroll = async () => {
    setLoadingEnroll(true)
    try {
      const enrollData = await enrollMutation.mutateAsync()
      const challengeData = await challengeMutation.mutateAsync()
      setEnrollStep({
        name: "qr",
        qrCode: enrollData.qr_code,
        secret: enrollData.secret,
      })
      // Pre-fetch challenge and store it
      setEnrollStep({
        name: "qr",
        qrCode: enrollData.qr_code,
        secret: enrollData.secret,
      })
      // Store challengeId for verify step
      ;(window as any).__totp_challenge_id = String(challengeData.challenge_id)
    } catch (err) {
      showErrorToast(
        err instanceof Error ? err.message : "Failed to start enrollment",
      )
    } finally {
      setLoadingEnroll(false)
    }
  }

  const handleQrContinue = () => {
    const challengeId = (window as any).__totp_challenge_id as string
    setEnrollStep({ name: "verify", challengeId })
  }

  const onVerifySubmit = async (data: z.infer<typeof totpCodeSchema>) => {
    if (enrollStep.name !== "verify") return
    try {
      const result = await verifyMutation.mutateAsync({
        challengeId: enrollStep.challengeId,
        totpCode: data.code,
      })
      setRecoveryCodes(result.recovery_codes ?? [])
      setEnrollStep({ name: "done" })
      showSuccessToast("Two-factor authentication enabled!")
    } catch {
      showErrorToast("Invalid code. Please try again.")
      form.reset()
    }
  }

  const handleClose = () => {
    setEnrollStep({ name: "idle" })
    setRecoveryCodes([])
    form.reset()
    onOpenChange(false)
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Enable Two-Factor Authentication</DialogTitle>
          <DialogDescription>
            Use an authenticator app to generate codes for signing in.
          </DialogDescription>
        </DialogHeader>

        {enrollStep.name === "idle" && (
          <div className="flex flex-col gap-4 py-2">
            <p className="text-sm text-muted-foreground">
              You&apos;ll need an authenticator app such as Google Authenticator
              or Authy installed on your phone.
            </p>
            <DialogFooter>
              <DialogClose asChild>
                <Button variant="outline">Cancel</Button>
              </DialogClose>
              <LoadingButton onClick={startEnroll} loading={loadingEnroll}>
                Get Started
              </LoadingButton>
            </DialogFooter>
          </div>
        )}

        {enrollStep.name === "qr" && (
          <div className="flex flex-col gap-4 py-2">
            <p className="text-sm text-muted-foreground">
              Scan the QR code with your authenticator app.
            </p>
            <div className="flex justify-center">
              {/* qrCode is already a full data URI from the backend */}
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={enrollStep.qrCode}
                alt="QR code for TOTP setup"
                width={192}
                height={192}
                className="rounded border"
              />
            </div>
            <div className="rounded-md bg-muted px-4 py-3">
              <p className="text-xs text-muted-foreground mb-1">
                Manual entry key
              </p>
              <p className="font-mono text-sm break-all select-all">
                {enrollStep.secret}
              </p>
            </div>
            <DialogFooter>
              <Button onClick={handleQrContinue} className="w-full">
                I&apos;ve scanned the code
              </Button>
            </DialogFooter>
          </div>
        )}

        {enrollStep.name === "verify" && (
          <Form {...form}>
            <form
              onSubmit={form.handleSubmit(onVerifySubmit)}
              className="flex flex-col gap-4 py-2"
            >
              <p className="text-sm text-muted-foreground">
                Enter the 6-digit code from your authenticator app to confirm.
              </p>
              <FormField
                control={form.control}
                name="code"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Authentication Code</FormLabel>
                    <FormControl>
                      <Input
                        placeholder="000000"
                        maxLength={8}
                        autoComplete="one-time-code"
                        inputMode="numeric"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <DialogFooter>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() =>
                    setEnrollStep({
                      name: "qr",
                      qrCode: "",
                      secret: "",
                    })
                  }
                >
                  Back
                </Button>
                <LoadingButton type="submit" loading={verifyMutation.isPending}>
                  Activate 2FA
                </LoadingButton>
              </DialogFooter>
            </form>
          </Form>
        )}

        {enrollStep.name === "done" && (
          <div className="flex flex-col gap-4 py-2">
            <div className="flex items-center gap-3">
              <ShieldCheck className="h-8 w-8 text-green-500 shrink-0" />
              <p className="text-sm font-medium">
                Two-factor authentication is now active!
              </p>
            </div>
            {recoveryCodes.length > 0 && (
              <>
                <div className="rounded-md border border-amber-200 bg-amber-50 px-4 py-3 flex items-start gap-2 dark:bg-amber-950/20 dark:border-amber-800">
                  <ShieldAlert className="h-4 w-4 text-amber-600 shrink-0 mt-0.5" />
                  <p className="text-xs text-amber-800 dark:text-amber-400">
                    Save these recovery codes now — they won&apos;t be shown again.
                  </p>
                </div>
                <div className="rounded-md bg-muted p-4 grid grid-cols-2 gap-2">
                  {recoveryCodes.map((code) => (
                    <p key={code} className="font-mono text-sm">
                      {code}
                    </p>
                  ))}
                </div>
                <RecoveryCodeActions codes={recoveryCodes} />
              </>
            )}
            <Button onClick={handleClose} className="w-full">
              Done
            </Button>
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}

// ---------------------------------------------------------------------------
// Recovery codes dialog
// ---------------------------------------------------------------------------

function RecoveryCodesDialog({
  open,
  onOpenChange,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
}) {
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const generateMutation = useGenerateRecoveryCodes()
  const [codes, setCodes] = useState<string[]>([])

  const handleGenerate = async () => {
    try {
      const result = await generateMutation.mutateAsync()
      setCodes(result.codes)
      showSuccessToast("Recovery codes generated. Save them somewhere safe!")
    } catch {
      showErrorToast("Failed to generate recovery codes")
    }
  }

  const handleClose = () => {
    setCodes([])
    onOpenChange(false)
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Recovery Codes</DialogTitle>
          <DialogDescription>
            Use these codes to access your account if you lose your
            authenticator device. Each code can only be used once.
          </DialogDescription>
        </DialogHeader>

        {codes.length === 0 ? (
          <div className="flex flex-col gap-4 py-2">
            <p className="text-sm text-muted-foreground">
              Generating new codes will invalidate all existing ones.
            </p>
            <DialogFooter>
              <DialogClose asChild>
                <Button variant="outline">Cancel</Button>
              </DialogClose>
              <LoadingButton
                onClick={handleGenerate}
                loading={generateMutation.isPending}
              >
                Generate New Codes
              </LoadingButton>
            </DialogFooter>
          </div>
        ) : (
          <div className="flex flex-col gap-4 py-2">
            <div className="rounded-md bg-muted p-4 grid grid-cols-2 gap-2">
              {codes.map((code) => (
                <p key={code} className="font-mono text-sm">
                  {code}
                </p>
              ))}
            </div>
            <p className="text-xs text-muted-foreground">
              Store these codes in a safe place. They won&apos;t be shown again.
            </p>
            <RecoveryCodeActions codes={codes} />
            <Button onClick={handleClose}>Done</Button>
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}

// ---------------------------------------------------------------------------
// Main TotpSettings component
// ---------------------------------------------------------------------------

export default function TotpSettings() {
  const { data: statusData, isLoading: statusLoading } = useTotpStatus()
  const { data: recoveryData } = useRecoveryCodesStatus()
  const [enrollOpen, setEnrollOpen] = useState(false)
  const [recoveryOpen, setRecoveryOpen] = useState(false)

  const isEnabled = statusData?.is_enabled ?? false

  return (
    <div className="max-w-md">
      <h3 className="text-lg font-semibold py-4">Two-Factor Authentication</h3>

      <div className="flex flex-col gap-6">
        {/* Status */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {isEnabled ? (
              <ShieldCheck className="h-5 w-5 text-green-500" />
            ) : (
              <ShieldOff className="h-5 w-5 text-muted-foreground" />
            )}
            <div>
              <p className="font-medium">Authenticator App</p>
              <p className="text-sm text-muted-foreground">
                {isEnabled
                  ? "Your account is protected with 2FA."
                  : "Add an extra layer of security to your account."}
              </p>
            </div>
          </div>
          <Badge variant={isEnabled ? "default" : "secondary"}>
            {statusLoading ? "..." : isEnabled ? "Enabled" : "Disabled"}
          </Badge>
        </div>

        {!isEnabled && (
          <Button
            onClick={() => setEnrollOpen(true)}
            className="self-start"
          >
            Enable 2FA
          </Button>
        )}

        {/* Recovery codes (only shown when TOTP is enabled) */}
        {isEnabled && (
          <>
            <Separator />
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">Recovery Codes</p>
                <p className="text-sm text-muted-foreground">
                  {recoveryData !== undefined
                    ? `${recoveryData.remaining_count} unused codes remaining`
                    : "Backup codes for when your device is unavailable."}
                </p>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setRecoveryOpen(true)}
              >
                <RefreshCw className="mr-2 h-4 w-4" />
                Regenerate
              </Button>
            </div>
          </>
        )}
      </div>

      <EnrollDialog open={enrollOpen} onOpenChange={setEnrollOpen} />
      <RecoveryCodesDialog open={recoveryOpen} onOpenChange={setRecoveryOpen} />
    </div>
  )
}
