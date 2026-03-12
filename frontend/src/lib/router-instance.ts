"use client"

import type { useRouter } from "next/navigation"
import { LOGIN_PATH } from "@/constants/auth"

let routerInstance: ReturnType<typeof useRouter> | null = null

export function setRouterInstance(router: ReturnType<typeof useRouter>) {
  routerInstance = router
}

export function navigateToLogin() {
  if (typeof window === "undefined") return

  const currentPath = window.location.pathname
  if (currentPath === LOGIN_PATH) return

  if (routerInstance) {
    routerInstance.replace(LOGIN_PATH)
  } else {
    window.location.replace(LOGIN_PATH)
  }
}
