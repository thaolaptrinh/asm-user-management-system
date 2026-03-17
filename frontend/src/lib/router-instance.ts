"use client"

import type { useRouter } from "next/navigation"
import { LOGIN_PATH } from "@/constants/auth"

let routerInstance: ReturnType<typeof useRouter> | null = null

export function setRouterInstance(router: ReturnType<typeof useRouter>) {
  routerInstance = router
}

export function navigateToLogin(reason?: string) {
  if (typeof window === "undefined") return

  const currentPath = window.location.pathname
  if (currentPath === LOGIN_PATH) return

  const target = reason ? `${LOGIN_PATH}?reason=${reason}` : LOGIN_PATH

  if (routerInstance) {
    routerInstance.replace(target)
  } else {
    window.location.replace(target)
  }
}
