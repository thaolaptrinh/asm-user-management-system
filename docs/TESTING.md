# Testing Guide

## Overview

| Layer | Framework | Focus |
|-------|-----------|-------|
| Backend | Pytest + pytest-asyncio | API endpoints, services, CRUD, TOTP security |
| Frontend E2E | Playwright | Full user flows through the browser |

---

## Backend Tests

### Run All Backend Tests

```bash
make test-be
```

This command:
1. Spins up a clean test database container
2. Runs Alembic migrations
3. Seeds test data
4. Executes the full Pytest suite with coverage reporting
5. Tears down the test containers

### Run Specific Tests (Inside the Container)

```bash
# Open a shell in the backend container (requires services running)
make shell-be

# Run a specific test file
pytest tests/services/test_totp_service.py -v

# Run a specific test case
pytest tests/services/test_totp_service.py::test_verify_totp_replay_attack -v

# Run with coverage for a specific module
pytest tests/ -v --cov=app --cov-report=term-missing
```

### What the Backend Tests Verify

**API Tests** (`tests/api/`):
- `test_auth.py` — registration, login, logout, token validation
- `test_totp.py` — TOTP setup, verification, disable, recovery codes
- `test_users.py` — user listing, creation, deletion, authorization
- `test_deps.py` — authentication dependency checks

**Service Tests** (`tests/services/`):
- `test_totp_service.py` — secret generation, QR code creation, code verification, replay attack prevention, challenge/response flow, enrollment vs. login flows
- `test_user_service.py` — user creation, validation, updates

**CRUD / Repository Tests** (`tests/crud/`, `tests/repositories/`):
- Database operations, uniqueness constraints, TOTP secret persistence, counter updates

### Key Security Tests

The TOTP service tests include dedicated security scenarios:

- **Replay attack prevention**: Verifies that a TOTP counter already recorded in `last_used_counter` is rejected on reuse
- **Enrollment flow**: Confirms that completing enrollment marks the secret as verified
- **Challenge expiration**: Validates that expired or already-used challenges are rejected
- **Invalid codes**: Confirms that wrong 6-digit codes return an `UnauthorizedError`

---

## Frontend / E2E Tests

### Run Frontend Tests

```bash
# Playwright E2E tests (requires services running via make dev)
make test-fe

# E2E tests in CI mode (self-contained, builds its own containers)
make test-e2e-ci
```

### Seed Deterministic Test Data

E2E tests use pre-seeded users with known credentials and TOTP secrets:

```bash
make seed-e2e
```

### What the E2E Tests Verify

- `login.spec.ts` — credential validation, TOTP code entry, logout, protected route redirection
- `users.spec.ts` — user creation, user deletion, form validation
- `user-settings.spec.ts` — TOTP setup, QR code display, verification, recovery code regeneration
- `sign-up.spec.ts` — registration form validation, duplicate email prevention

---

## Test Coverage Targets

| Component | Target |
|-----------|--------|
| Backend API + Services | > 80% |
| E2E (critical user flows) | Login, TOTP, user management |

---

## Troubleshooting Tests

| Problem | Solution |
|---------|----------|
| Backend tests fail with DB errors | `make db-reset`, then `make test-be` |
| E2E tests fail intermittently | `make seed-e2e && make restart`, then retry |
| Playwright can't find elements | Ensure services are running: `make ps` |
