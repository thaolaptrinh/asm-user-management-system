/**
 * Test helpers for JWT token generation
 */

export function createValidToken(expiryMinutes = 60): string {
  const header = btoa(JSON.stringify({ alg: "HS256", typ: "JWT" }))
  const payload = btoa(
    JSON.stringify({
      exp: Math.floor(Date.now() / 1000) + expiryMinutes * 60,
      iat: Math.floor(Date.now() / 1000),
    }),
  )
  const signature = "fake-signature"
  return `${header}.${payload}.${signature}`
}

export function createExpiredToken(): string {
  const header = btoa(JSON.stringify({ alg: "HS256", typ: "JWT" }))
  const payload = btoa(
    JSON.stringify({
      exp: Math.floor(Date.now() / 1000) - 3600, // Expired 1 hour ago
      iat: Math.floor(Date.now() / 1000) - 7200,
    }),
  )
  const signature = "fake-signature"
  return `${header}.${payload}.${signature}`
}
