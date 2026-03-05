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

  const isAuthRoute =
    pathname.startsWith("/login") ||
    pathname.startsWith("/signup") ||
    pathname.startsWith("/recover-password") ||
    pathname.startsWith("/reset-password")

  const isProtectedRoute =
    pathname === "/" ||
    pathname.startsWith("/admin") ||
    pathname.startsWith("/items") ||
    pathname.startsWith("/settings")

  if (isProtectedRoute && !hasValidToken) {
    const url = request.nextUrl.clone()
    url.pathname = "/login"
    return NextResponse.redirect(url)
  }

  if (isAuthRoute && hasValidToken) {
    const url = request.nextUrl.clone()
    url.pathname = "/"
    return NextResponse.redirect(url)
  }

  return NextResponse.next()
}

export default proxy

export const config = {
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico).*)"],
}
