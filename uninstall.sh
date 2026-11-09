#!/usr/bin/env bash
set -euo pipefail

APP_NAME="Fuserio"
DESKTOP_DIR="$HOME/.local/share/applications"
DESKTOP_LINK="$HOME/Desktop/$APP_NAME.desktop"
DESKTOP_FILE="$DESKTOP_DIR/$APP_NAME.desktop"

rm -f "$DESKTOP_FILE" "$DESKTOP_LINK"

if [ "${1:-}" = "--purge" ]; then
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  rm -rf "$SCRIPT_DIR/.venv"
  echo "Removed the local virtual environment."
fi

echo "Fuserio launcher removed."
