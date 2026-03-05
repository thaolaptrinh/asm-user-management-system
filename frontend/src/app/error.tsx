"use client"

import Link from "next/link"

import { Button } from "@/components/ui/button"

export default function ErrorPage({
  error: _error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  return (
    <div
      className="flex min-h-screen flex-col items-center justify-center p-4"
      data-testid="error-component"
    >
      <div className="z-10 flex items-center">
        <div className="ml-4 flex flex-col items-center justify-center p-4">
          <span className="mb-4 text-6xl font-bold leading-none md:text-8xl">
            Error
          </span>
          <span className="mb-2 text-2xl font-bold">Oops!</span>
        </div>
      </div>

      <p className="z-10 mb-4 text-center text-lg text-muted-foreground">
        Something went wrong. Please try again.
      </p>
      <div className="z-10 flex flex-wrap items-center justify-center gap-2">
        <Button onClick={reset}>Try again</Button>
        <Link href="/items">
          <Button variant="outline">Go Home</Button>
        </Link>
      </div>
    </div>
  )
}
