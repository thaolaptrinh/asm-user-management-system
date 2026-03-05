"use client"
import Image from "next/image"
import Link from "next/link"
import { useTheme } from "next-themes"
import { useSyncExternalStore } from "react"
import { cn } from "@/lib/utils"

const subscribe = () => () => {}
const getSnapshot = () => true
const getServerSnapshot = () => false

function useMounted() {
  return useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot)
}

interface LogoProps {
  variant?: "full" | "icon" | "responsive"
  className?: string
  asLink?: boolean
}

export function Logo({
  variant = "full",
  className,
  asLink = true,
}: LogoProps) {
  const { resolvedTheme } = useTheme()
  const mounted = useMounted()
  const isDark = resolvedTheme === "dark"

  const fullLogo = isDark
    ? "/assets/images/fastapi-logo-light.svg"
    : "/assets/images/fastapi-logo.svg"
  const iconLogo = isDark
    ? "/assets/images/fastapi-icon-light.svg"
    : "/assets/images/fastapi-icon.svg"

  const content =
    variant === "responsive" ? (
      <>
        <Image
          src={mounted ? fullLogo : "/assets/images/fastapi-logo.svg"}
          alt="FastAPI"
          width={120}
          height={24}
          unoptimized
          suppressHydrationWarning
          className={cn(
            "h-6 w-auto group-data-[collapsible=icon]:hidden",
            className,
          )}
        />
        <Image
          src={mounted ? iconLogo : "/assets/images/fastapi-icon.svg"}
          alt="FastAPI"
          width={20}
          height={20}
          unoptimized
          suppressHydrationWarning
          className={cn(
            "size-5 hidden group-data-[collapsible=icon]:block",
            className,
          )}
        />
      </>
    ) : (
      <Image
        src={
          mounted
            ? variant === "full"
              ? fullLogo
              : iconLogo
            : "/assets/images/fastapi-logo.svg"
        }
        alt="FastAPI"
        width={variant === "full" ? 120 : 20}
        height={variant === "full" ? 24 : 20}
        unoptimized
        suppressHydrationWarning
        className={cn(variant === "full" ? "h-6 w-auto" : "size-5", className)}
      />
    )

  if (!asLink) {
    return content
  }

  return <Link href="/">{content}</Link>
}
