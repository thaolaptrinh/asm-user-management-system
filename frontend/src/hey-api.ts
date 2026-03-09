import type { CreateClientConfig } from "./client/client.gen"

export const createClientConfig: CreateClientConfig = (config) => ({
  ...config,
  baseUrl: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  // Cookies are sent automatically with every request (HttpOnly cookie auth)
  credentials: "include",
})
