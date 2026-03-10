import type { NextRequest } from "next/server"
import { NextResponse } from "next/server"

/**
 * Proxy runs before routes (Next.js 16+). Handles auth redirects only;
 * token validity is checked by API client and useAuth hook.
 */
export function proxy(request: NextRequest) {
  const token = request.cookies.get("access_token")?.value
  const hasValidToken = Boolean(token?.trim())
  const { pathname } = request.nextUrl

  // Auth routes (where unauthenticated users go)
  const isAuthRoute =
    pathname === "/login" ||
    pathname === "/signup" ||
    pathname === "/recover-password" ||
    pathname === "/reset-password"

  // Protected routes (require authentication)
  const isProtectedRoute =
    pathname === "/" ||
    pathname.startsWith("/users") ||
    pathname.startsWith("/settings")

  // Redirect authenticated users away from auth routes
  if (isAuthRoute && hasValidToken) {
    const url = request.nextUrl.clone()
    url.pathname = "/"
    return NextResponse.redirect(url)
  }

  // Redirect unauthenticated users to login for protected routes
  if (isProtectedRoute && !hasValidToken) {
    const url = request.nextUrl.clone()
    url.pathname = "/login"
    return NextResponse.redirect(url)
  }

  return NextResponse.next()
}

export default proxy

export const config = {
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico).*)"],
}
