"use client"

import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { ReactQueryDevtools } from "@tanstack/react-query-devtools"
import { useRouter } from "next/navigation"
import { ThemeProvider } from "next-themes"
import { useEffect, useState } from "react"
import { Toaster } from "sonner"
import { auth } from "@/client/sdk.gen"
import { setRouterInstance, navigateToLogin } from "@/lib/router-instance"
import { setupUnauthorizedInterceptor, setQueryClient as setAuthQueryClient } from "@/lib/unauthorized-interceptor"

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
    setAuthQueryClient(queryClient)
    setRouterInstance(router)

    const logout = () => auth.logout({ throwOnError: false })
    setupUnauthorizedInterceptor({
      queryClient,
      logout,
      redirect: () => navigateToLogin("session_expired"),
    })
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
