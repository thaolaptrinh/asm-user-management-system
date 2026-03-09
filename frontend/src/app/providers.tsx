"use client"

import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { ReactQueryDevtools } from "@tanstack/react-query-devtools"
import { useRouter } from "next/navigation"
import { ThemeProvider } from "next-themes"
import { useEffect, useState } from "react"
import { Toaster } from "sonner"
import {
  setQueryClient,
  setupUnauthorizedHandler,
} from "@/lib/api-error-handler"
import { setRouterInstance } from "@/lib/router-instance"

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000,
          },
        },
      }),
  )
  const router = useRouter()

  useEffect(() => {
    setQueryClient(queryClient)
    setRouterInstance(router)
    setupUnauthorizedHandler()
  }, [queryClient, router])

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider
        attribute="class"
        defaultTheme="dark"
        enableSystem
        disableTransitionOnChange
      >
        {children}
        <Toaster richColors closeButton />
        <ReactQueryDevtools initialIsOpen={false} />
      </ThemeProvider>
    </QueryClientProvider>
  )
}
