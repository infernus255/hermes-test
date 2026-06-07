#!/bin/bash
set -e

if [ -z "${TELEGRAM_BOT_TOKEN}" ]; then
  echo "ERROR: TELEGRAM_BOT_TOKEN is required"
  exit 1
fi

mkdir -p /root/.hermes
rm -f /root/.hermes/.env
cat > /root/.hermes/.env <<EOF
TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
GATEWAY_ALLOW_ALL_USERS=${GATEWAY_ALLOW_ALL_USERS:-false}
EOF

if [ -n "${GEMINI_API_KEY}" ]; then
  echo "GEMINI_API_KEY=${GEMINI_API_KEY}" >> /root/.hermes/.env
fi

if [ -n "${GOOGLE_API_KEY}" ]; then
  echo "GOOGLE_API_KEY=${GOOGLE_API_KEY}" >> /root/.hermes/.env
fi

if [ -n "${TELEGRAM_ALLOWED_USERS}" ]; then
  echo "TELEGRAM_ALLOWED_USERS=${TELEGRAM_ALLOWED_USERS}" >> /root/.hermes/.env
fi

chmod 600 /root/.hermes/.env

hermes config set model.provider gemini || true
hermes config set model.default gemini-3.5-flash || true
hermes config set model.base_url https://generativelanguage.googleapis.com/v1beta/openai || true

if [ "$#" -gt 0 ]; then
  exec "$@"
else
  exec hermes gateway run
fi
