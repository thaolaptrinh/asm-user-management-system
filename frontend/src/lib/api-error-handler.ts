import type { QueryClient } from "@tanstack/react-query"
import { client } from "@/client/client.gen"
import { navigateToLogin } from "@/lib/router-instance"

let queryClientInstance: QueryClient | null = null
let isHandlerSetup = false

export function setQueryClient(queryClient: QueryClient) {
  queryClientInstance = queryClient
}

export function setupUnauthorizedHandler() {
  if (isHandlerSetup) return

  client.interceptors.error.use(async (error, response) => {
    if (response.status === 401) {
      if (queryClientInstance) {
        queryClientInstance.clear()
      }
      navigateToLogin()
    }
    throw error
  })

  isHandlerSetup = true
}
