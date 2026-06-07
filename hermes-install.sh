#!/bin/bash
set -e

# Script de instalación reproducible para Ubuntu/Codespaces.
# No incluye credenciales en el repositorio.

sudo apt update
sudo apt install -y curl git python3 python3-venv python3-pip npm xz-utils ca-certificates

curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash

cat <<'EOF'
Hermes Agent instalado. Para completar la configuración:
  1) Copia hermes.env.example a hermes.env
  2) Rellena TELEGRAM_BOT_TOKEN y GEMINI_API_KEY
  3) Ejecuta docker compose up --build -d
EOF
