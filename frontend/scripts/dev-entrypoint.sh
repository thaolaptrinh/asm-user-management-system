#!/usr/bin/env bash
set -e
# Fix bind-mount permissions: chown /app/frontend to host user (UID/GID from env),
# then run the app as that user so lockfile and .next are writable.
if [ -n "${UID}" ] && [ -n "${GID}" ]; then
  chown -R "${UID}:${GID}" /app/frontend
fi
exec gosu "${UID:-1000}:${GID:-1000}" "$@"
