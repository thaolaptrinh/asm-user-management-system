import type { Metadata } from "next"
import { Geist, Geist_Mono } from "next/font/google"
import "./globals.css"
import { ClientInit } from "@/components/client-init"
import { TooltipProvider } from "@/components/ui/tooltip"
import { Providers } from "./providers"

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
})

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
})

export const metadata: Metadata = {
  title: "User Management System with TOTP 2FA",
  description: "User Management System with Two-Factor Authentication (2FA) using TOTP (Time-based One-Time Password)",
  icons: {
    icon: "/assets/images/favicon.png",
  },
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
        suppressHydrationWarning
      >
        <Providers>
          <ClientInit />
          <TooltipProvider>{children}</TooltipProvider>
        </Providers>
      </body>
    </html>
  )
}
