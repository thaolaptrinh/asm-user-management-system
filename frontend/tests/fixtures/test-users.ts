/**
 * E2E Test User Fixtures
 *
 * These credentials match the seeded test users from seed_e2e_test_data.py
 * All credentials are deterministic for reproducible tests.
 *
 * Recovery code assignment (each login must use a unique code due to TOTP replay protection):
 *   adminUser.recoveryCodes[0]  ADMN-1111  → auth.setup.ts (stored auth)
 *   adminUser.recoveryCodes[1]  ADMN-2222  → users.spec.ts "Superuser can access users page"
 *   adminUser.recoveryCodes[2]  ADMN-3333  → user-settings.spec.ts theme re-login
 *
 *   standardUser.recoveryCodes[0]  ABCD-1234  → login.spec.ts "Log in with valid email and password"
 *   standardUser.recoveryCodes[1]  EFGH-5678  → login.spec.ts "Successful log out"
 *   standardUser.recoveryCodes[2]  IJKL-9012  → login.spec.ts "Logged-out user cannot access protected routes"
 */

export const testUsers = {
  /**
   * Standard test user with TOTP enabled
   * Used for login flow tests
   */
  standardUser: {
    email: "test-user@example.com",
    password: "TestPassword123!",
    fullName: "E2E Test User",
    totpSecret: "JBSWY3DPEHPK3PXP",
    recoveryCodes: [
      "ABCD-1234", "EFGH-5678", "IJKL-9012", "MNOP-3456", "QRST-7890",
      "UVWX-2345", "YZAB-6789", "CDEF-0123", "GHIJ-4567", "KLMN-8901",
    ],
  },

  /**
   * Admin user with TOTP enabled
   * Used for admin-specific features and as the stored auth state user
   */
  adminUser: {
    email: "admin@example.com",
    password: "TestPassword123!",
    fullName: "E2E Admin User",
    totpSecret: "JBSWY3DPEHPK3PXP",
    recoveryCodes: [
      "ADMN-1111", "ADMN-2222", "ADMN-3333", "ADMN-4444", "ADMN-5555",
      "ADMN-6666", "ADMN-7777", "ADMN-8888", "ADMN-9999", "ADMN-0000",
    ],
  },

  /**
   * User without TOTP
   * Used for signup and TOTP enrollment flow tests
   */
  userWithoutTotp: {
    email: "test-user-no-totp@example.com",
    password: "TestPassword123!",
    fullName: "E2E Test User (No TOTP)",
  },
}

export type TestUser = typeof testUsers.standardUser | typeof testUsers.adminUser
