"use client"

import type { useRouter } from "next/navigation"

let routerInstance: ReturnType<typeof useRouter> | null = null

export function setRouterInstance(router: ReturnType<typeof useRouter>) {
  routerInstance = router
}

export function navigateToLogin() {
  if (typeof window === "undefined") return

  const currentPath = window.location.pathname
  if (currentPath === "/login") return

  if (routerInstance) {
    routerInstance.replace("/login")
  } else {
    window.location.replace("/login")
  }
}
