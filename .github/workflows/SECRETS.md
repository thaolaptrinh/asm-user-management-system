# GitHub Actions Secrets Required

This document lists all required GitHub Secrets for CI/CD workflows to function properly.

## 🔧 Required Secrets

### **Workflow: deploy-staging.yml**

Deploy application to staging environment.

| Secret | Description | Example | Required |
|--------|-------------|---------|----------|
| `DOMAIN_STAGING` | Staging domain | `staging.example.com` | ✅ Yes |
| `STACK_NAME_STAGING` | Docker stack name | `app-staging` | ✅ Yes |
| `SECRET_KEY` | APP_KEY from .env | `base64:...` | ✅ Yes |
| `FIRST_SUPERUSER` | Admin email | `admin@example.com` | ✅ Yes |
| `FIRST_SUPERUSER_PASSWORD` | Admin password | `min 8 chars` | ✅ Yes |
| `SMTP_HOST` | Mail server | `smtp.example.com` | ✅ Yes |
| `SMTP_USER` | SMTP username | `user@example.com` | ✅ Yes |
| `SMTP_PASSWORD` | SMTP password | `password` | ✅ Yes |
| `EMAILS_FROM_EMAIL` | From email | `noreply@example.com` | ✅ Yes |
| `MYSQL_PASSWORD` | DB password | `min 16 chars` | ✅ Yes |
| `SENTRY_DSN` | Sentry DSN | `https://...` | Optional |

**Setup:**
```bash
# Generate APP_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate passwords
make secrets
```

---

### **Workflow: deploy-production.yml**

Deploy application to production environment.

| Secret | Description | Example | Required |
|--------|-------------|---------|----------|
| `DOMAIN_PRODUCTION` | Production domain | `example.com` | ✅ Yes |
| `STACK_NAME_PRODUCTION` | Docker stack name | `app` | ✅ Yes |
| `SECRET_KEY` | APP_KEY from .env | `base64:...` | ✅ Yes |
| `FIRST_SUPERUSER` | Admin email | `admin@example.com` | ✅ Yes |
| `FIRST_SUPERUSER_PASSWORD` | Admin password | `min 8 chars` | ✅ Yes |
| `SMTP_HOST` | Mail server | `smtp.example.com` | ✅ Yes |
| `SMTP_USER` | SMTP username | `user@example.com` | ✅ Yes |
| `SMTP_PASSWORD` | SMTP password | `password` | ✅ Yes |
| `EMAILS_FROM_EMAIL` | From email | `noreply@example.com` | ✅ Yes |
| `MYSQL_PASSWORD` | DB password | `min 16 chars` | ✅ Yes |
| `SENTRY_DSN` | Sentry DSN | `https://...` | Optional |

---

### **Workflow: smokeshow.yml**

Upload test coverage reports as GitHub comments.

| Secret | Description | Example | Required |
|--------|-------------|---------|----------|
| `SMOKESHOW_AUTH_KEY` | Smokeshow API key | `ss_...` | ✅ Yes |

**Setup:**
```bash
# Get auth key from https://smokeshow.help
npm install -g smokeshow
smokeshow auth
```

---

### **Workflow: pre-commit.yml**

Run pre-commit on PRs and auto-fix code style issues.

| Secret | Description | Example | Required |
|--------|-------------|---------|----------|
| `PRE_COMMIT` | GitHub PAT with repo permissions | `ghp_...` | ✅ Yes |

**Setup:**
1. Go to https://github.com/settings/tokens
2. Generate new PAT with `repo` scope
3. Add to repo secrets: Settings → Secrets and variables → Actions → New repository secret

**Why needed:** Allows pre-commit to push fixes to PR branches

---

## ✅ Workflows WITHOUT Required Secrets

These workflows work out-of-the-box, no secrets needed:

| Workflow | Description |
|----------|-------------|
| `test-backend.yml` | Auto-fills .env.example for CI ✅ |
| `test-docker-compose.yml` | Uses docker compose defaults ✅ |
| `playwright.yml` | Uses docker compose defaults ✅ |
| `detect-conflicts.yml` | No secrets needed ✅ |
| `labeler.yml` | No secrets needed ✅ |

---

## 🚀 Quick Setup Guide

### **For Development/Forks (No Deployment)**

If you're just running tests and NOT deploying:

✅ **Optional:**
- `PRE_COMMIT` - for auto-formatting on PRs

❌ **NOT Needed:**
- deploy-staging.yml secrets
- deploy-production.yml secrets
- smokeshow secrets

**Workflow will fail but won't block you:**
- deploy-staging/production will skip (checks `github.repository_owner != 'fastapi'`)

---

### **For Production Deployment**

If deploying to staging/production:

**1. Add Repository Secrets:**
```bash
# Navigate to:
https://github.com/YOUR_USERNAME/YOUR_REPO/settings/secrets/actions

# Add these secrets:
DOMAIN_STAGING
STACK_NAME_STAGING
SECRET_KEY
FIRST_SUPERUSER
FIRST_SUPERUSER_PASSWORD
SMTP_HOST
SMTP_USER
SMTP_PASSWORD
EMAILS_FROM_EMAIL
MYSQL_PASSWORD
SENTRY_DSN (optional)
```

**2. Generate Secure Values:**
```bash
# APP_KEY / SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Strong passwords
openssl rand -base64 24
```

**3. Configure Self-Hosted Runners (for deployment):**
- GitHub Settings → Actions → Runners → New self-hosted runner
- Labels: `staging`, `production`

---

## 🔍 Troubleshooting

### **Error: "Required secret not found"**

**Solution:** Add missing secret via repo settings.

---

### **Error: "Do not deploy in the main repository"**

**Reason:** deploy-staging/production check `github.repository_owner != 'fastapi'`

**Solution:** This is intentional. Forks can deploy, main template repo won't.

---

### **Error: "Permission denied" (pre-commit)**

**Reason:** `PRE_COMMIT` secret missing or has wrong permissions.

**Solution:**
- Generate PAT with `repo` scope
- Add to secrets as `PRE_COMMIT`

---

## 📚 Additional Resources

- [GitHub Actions Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [GitHub PATs](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)
- [Smokeshow](https://smokeshow.help)
