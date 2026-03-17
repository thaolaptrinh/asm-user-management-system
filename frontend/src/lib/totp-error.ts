export type TotpErrorKind = "expired" | "invalid" | "unknown"

export function classifyTotpError(err: unknown): TotpErrorKind {
  const detail = (err as { detail?: string })?.detail
  if (!detail) return "unknown"
  if (detail === "Invalid or expired token") return "expired"
  return "invalid"
}
