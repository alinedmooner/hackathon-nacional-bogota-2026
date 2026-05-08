#!/bin/sh
set -e

ENV_JS_PATH="/usr/share/nginx/html/assets/env.js"

if [ -n "$BACKEND_URL" ]; then
  envsubst '$BACKEND_URL' < "$ENV_JS_PATH" > "${ENV_JS_PATH}.tmp"
  mv "${ENV_JS_PATH}.tmp" "$ENV_JS_PATH"
fi

exec "$@"
