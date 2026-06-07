#!/usr/bin/env bash
set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MEMORY_FILE="$REPO_ROOT/memory.md"

if [ $# -lt 1 ]; then
  echo "Uso: $0 \"Texto de aprendizaje\""
  exit 1
fi

TIMESTAMP="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
ENTRY="$1"

mkdir -p "$(dirname "$MEMORY_FILE")"
cat >> "$MEMORY_FILE" <<EOF

### $TIMESTAMP
- $ENTRY
EOF

echo "Entrada agregada a $MEMORY_FILE"
