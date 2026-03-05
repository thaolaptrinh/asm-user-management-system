#!/usr/bin/env bash
# Drop + recreate test DB (name = MYSQL_DATABASE from .env + _test suffix). Run from repo root.
# Used by run-backend-tests.sh; can be run manually: ./scripts/reset-test-db.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

# Test DB = app DB + _test (or MYSQL_TEST_DATABASE if already set)
if [ -z "${MYSQL_TEST_DATABASE:-}" ] && [ -f .env ]; then
  set -a
  # shellcheck source=/dev/null
  source .env 2>/dev/null || true
  set +a
fi
MYSQL_TEST_DATABASE="${MYSQL_TEST_DATABASE:-${MYSQL_DATABASE:-app}_test}"

# Use root to drop/create test DB and grant app user access (MYSQL_ROOT_PASSWORD and MYSQL_USER from db container env)
docker compose exec -T db sh -c 'f=/tmp/.my.cnf.$$; printf "[client]\npassword=%s\n" "$MYSQL_ROOT_PASSWORD" > "$f"; chmod 600 "$f"; mysql --defaults-extra-file="$f" -u root -e "DROP DATABASE IF EXISTS '"$MYSQL_TEST_DATABASE"'; CREATE DATABASE '"$MYSQL_TEST_DATABASE"'; GRANT ALL PRIVILEGES ON '"$MYSQL_TEST_DATABASE"'.* TO \"$MYSQL_USER\"@\"%\"; FLUSH PRIVILEGES;"; rm -f "$f"'
