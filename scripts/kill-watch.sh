#!/usr/bin/env bash
# Release Docker Compose watch project lock (see docker/compose#11069).
# (1) Linux: kill watch process with cwd=this project.
# (2) macOS: run watch --no-up in background, parse "PID X is still running" or kill job after 2s.
set -e
cd "$(dirname "$0")/.."
project_cwd=$(pwd)

for pid in $(pgrep -f 'compose watch' 2>/dev/null || true); do
  if [ -d "/proc/$pid" ] 2>/dev/null; then
    cwd=$(readlink -f "/proc/$pid/cwd" 2>/dev/null || true)
    if [ "$cwd" = "$project_cwd" ]; then
      kill "$pid" 2>/dev/null || true
    fi
  fi
done

if [ ! -d /proc ]; then
  tmp=$(mktemp)
  ( docker compose watch --no-up 2>&1 | tee "$tmp"; exit 0 ) &
  sleep 2
  kill %1 2>/dev/null
  wait %1 2>/dev/null
  true
  pid=$(sed -n 's/.*process with PID \([0-9]*\) is still running.*/\1/p' "$tmp")
  rm -f "$tmp"
  if [ -n "$pid" ] && [ "$pid" -eq "$pid" ] 2>/dev/null; then
    kill "$pid" 2>/dev/null || true
  fi
fi

sleep 1
