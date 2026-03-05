#!/usr/bin/env bash
set -e
# Ensure report/output dirs exist; chown so host can read playwright-report and test-results
mkdir -p /app/frontend/playwright-report /app/frontend/test-results
if [ -n "${UID}" ] && [ -n "${GID}" ]; then
  chown -R "${UID}:${GID}" /app/frontend
fi
# Remove stale Next.js dev lock so "next dev" (webServer) can start (volume may persist from previous run).
rm -f /app/frontend/.next/dev/lock 2>/dev/null || true
if [ -n "${UID}" ] && [ -n "${GID}" ]; then
  exec gosu "${UID}:${GID}" env PATH="/opt/bun/bin:${PATH:-/usr/local/bin:/usr/bin:/bin}" "$@"
fi
exec env PATH="/opt/bun/bin:${PATH:-/usr/local/bin:/usr/bin:/bin}" "$@"
