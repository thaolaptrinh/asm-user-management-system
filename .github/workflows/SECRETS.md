# GitHub Actions Secrets Required

This document lists all required GitHub Secrets for CI/CD workflows to function properly.

## 🔧 Required Secrets

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
| `playwright.yml` | Uses docker compose defaults ✅ |
| `detect-conflicts.yml` | No secrets needed ✅ |
| `labeler.yml` | No secrets needed ✅ |

---

## 🚀 Quick Setup Guide

### **For Development/Forks**

✅ **Optional:**
- `PRE_COMMIT` - for auto-formatting on PRs

---

## 🔍 Troubleshooting

### **Error: "Required secret not found"**

**Solution:** Add missing secret via repo settings.

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
