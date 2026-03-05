const EMAIL = "FIRST_SUPERUSER"
const PASSWORD = "FIRST_SUPERUSER_PASSWORD"

export function getTestUser(): { email: string; password: string } {
  const email = process.env[EMAIL]
  const password = process.env[PASSWORD]
  if (!email || !password) {
    throw new Error(
      `Set FIRST_SUPERUSER and FIRST_SUPERUSER_PASSWORD (via env_file in compose or -e)`,
    )
  }
  return { email, password }
}
