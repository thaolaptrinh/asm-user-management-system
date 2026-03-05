"use client"

export default function GlobalError({
  error: _error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  return (
    <html lang="en">
      <body>
        <div
          className="flex min-h-screen flex-col items-center justify-center p-4"
          data-testid="global-error"
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
          <div className="z-10 flex gap-2">
            <button
              type="button"
              onClick={reset}
              className="inline-flex shrink-0 items-center justify-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
            >
              Try again
            </button>
            <a
              href="/"
              className="inline-flex shrink-0 items-center justify-center gap-2 rounded-md border bg-background px-4 py-2 text-sm font-medium shadow-xs hover:bg-accent hover:text-accent-foreground"
            >
              Go Home
            </a>
          </div>
        </div>
      </body>
    </html>
  )
}
