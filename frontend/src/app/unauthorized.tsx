import Link from "next/link"

import { Button } from "@/components/ui/button"

export default function UnauthorizedPage() {
  return (
    <div
      className="flex min-h-screen flex-col items-center justify-center p-4"
      data-testid="unauthorized-component"
    >
      <div className="z-10 flex items-center">
        <div className="ml-4 flex flex-col items-center justify-center p-4">
          <span className="mb-4 text-6xl font-bold leading-none md:text-8xl">
            401
          </span>
          <span className="mb-2 text-2xl font-bold">Unauthorized</span>
        </div>
      </div>

      <p className="z-10 mb-4 text-center text-lg text-muted-foreground">
        You need to log in to access this resource.
      </p>
      <div className="z-10 flex flex-wrap items-center justify-center gap-2">
        <Link href="/login">
          <Button>Go to Login</Button>
        </Link>
        <Link href="/">
          <Button variant="outline">Go Home</Button>
        </Link>
      </div>
    </div>
  )
}
