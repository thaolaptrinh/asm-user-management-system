#!/usr/bin/env bash
# Run from repo root. Each run: drop + recreate test DB (name = app DB + _test), then pytest.
# Usage:
#   ./scripts/run-backend-tests.sh           # pytest tests/
#   ./scripts/run-backend-tests.sh -v        # pytest with extra args
#   ./scripts/run-backend-tests.sh cov       # coverage report
#   ./scripts/run-backend-tests.sh cov-100   # coverage, fail if < 100%

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

# 1. Drop + recreate test DB (clean slate). reset-test-db.sh reads .env → MYSQL_DATABASE + _test
"$SCRIPT_DIR/reset-test-db.sh"

# 2. Use same test DB name (re-read .env; reset-test-db.sh runs in subshell)
if [ -z "${MYSQL_TEST_DATABASE:-}" ] && [ -f .env ]; then
  set -a
  # shellcheck source=/dev/null
  source .env 2>/dev/null || true
  set +a
fi
MYSQL_TEST_DATABASE="${MYSQL_TEST_DATABASE:-${MYSQL_DATABASE:-app}_test}"
MYSQL_DATABASE="$MYSQL_TEST_DATABASE"

# 3. Run migrations on test DB so tables exist (we use Alembic only; init_db no longer create_all)
docker compose exec -T -e MYSQL_DATABASE="$MYSQL_DATABASE" backend alembic upgrade head

# Coverage file in /tmp (writable in container; /app/backend may be read-only)
case "${1:-}" in
  cov)
    docker compose exec -T -e MYSQL_DATABASE="$MYSQL_DATABASE" -e COVERAGE_FILE=/tmp/.coverage backend coverage run -m pytest tests/
    docker compose exec -T -e MYSQL_DATABASE="$MYSQL_DATABASE" -e COVERAGE_FILE=/tmp/.coverage backend coverage report
    ;;
  cov-100)
    docker compose exec -T -e MYSQL_DATABASE="$MYSQL_DATABASE" -e COVERAGE_FILE=/tmp/.coverage backend coverage run -m pytest tests/
    docker compose exec -T -e MYSQL_DATABASE="$MYSQL_DATABASE" -e COVERAGE_FILE=/tmp/.coverage backend coverage report --fail-under=100
    ;;
  *)
    docker compose exec -T -e MYSQL_DATABASE="$MYSQL_DATABASE" backend pytest tests/ "$@"
    ;;
esac
