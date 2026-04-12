#!/bin/sh
set -eu

LOCK_FILE="/app/package-lock.json"
STAMP_FILE="/app/node_modules/.package-lock.sha256"

if [ ! -f "$LOCK_FILE" ]; then
  echo "[internal_console] package-lock.json not found."
  exit 1
fi

CURRENT_HASH="$(sha256sum "$LOCK_FILE" | awk '{print $1}')"
INSTALLED_HASH=""

if [ -f "$STAMP_FILE" ]; then
  INSTALLED_HASH="$(cat "$STAMP_FILE" 2>/dev/null || true)"
fi

if [ ! -d "/app/node_modules/.bin" ] || [ "$CURRENT_HASH" != "$INSTALLED_HASH" ]; then
  echo "[internal_console] Installing npm dependencies (first run or lockfile changed)..."
  npm ci
  echo "$CURRENT_HASH" > "$STAMP_FILE"
else
  echo "[internal_console] Dependencies up to date, skip npm ci."
fi

echo "[internal_console] Building frontend assets..."
npm run build

echo "[internal_console] Starting preview server on 0.0.0.0:5173 ..."
exec npm run preview -- --host 0.0.0.0 --port 5173
