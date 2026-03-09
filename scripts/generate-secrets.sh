#!/usr/bin/env bash
# Generate secure secrets for .env

echo "# Application"
echo "APP_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
echo ""
echo "# Database"
echo "DB_PASSWORD=$(python3 -c 'import secrets; print(secrets.token_urlsafe(20))')"
echo "DB_ROOT_PASSWORD=$(python3 -c 'import secrets; print(secrets.token_urlsafe(20))')"
echo ""
echo "# Authentication"
echo "JWT_SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
echo ""
echo "# Superuser"
echo "FIRST_SUPERUSER_PASSWORD=$(python3 -c 'import secrets; print(secrets.token_urlsafe(16))')"
