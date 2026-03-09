#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

DB_CONNECTION=$(grep "^DB_CONNECTION=" "$ROOT/.env" | cut -d= -f2 | cut -d'#' -f1 | tr -d '[:space:]')
DB_CONNECTION="${DB_CONNECTION:-mysql}"

DC="docker compose \
  --env-file $ROOT/.env \
  -f $ROOT/docker/compose.base.yml \
  -f $ROOT/docker/compose.dev.yml \
  --profile $DB_CONNECTION"

# Ensure backend container is running
if [ -z "$($DC ps -q backend)" ]; then
  echo "Backend is not running. Run: make dev"
  exit 1
fi

# Generate OpenAPI spec from running backend → writes to host (bind-mounted into frontend container)
$DC exec -T backend uv run python - <<'PY' > "$ROOT/frontend/openapi.json"
import json
from app.main import app
print(json.dumps(app.openapi(), indent=2))
PY

# Generate TypeScript client inside frontend container.
# src/client/ is bind-mounted → generated files appear on host automatically.
# chown fixes ownership from container root to the current host user.
$DC exec -T frontend sh -c "
  cd /app/frontend &&
  bun run generate-client &&
  chown -R $(id -u):$(id -g) src/client
"
