#!/bin/sh
set -e

ENV_JS_PATH="/app/src/assets/env.js"

if [ -n "$BACKEND_URL" ]; then
  sed -i "s|__BACKEND_URL__|$BACKEND_URL|g" "$ENV_JS_PATH"
fi

exec "$@"
