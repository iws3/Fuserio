#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

export QT_QPA_PLATFORM=${QT_QPA_PLATFORM:-xcb}

if [ ! -f "$SCRIPT_DIR/.venv/bin/python" ]; then
  python3 -m venv "$SCRIPT_DIR/.venv"
fi

. "$SCRIPT_DIR/.venv/bin/activate"
python -m pip install -r "$SCRIPT_DIR/requirements.txt" >/dev/null 2>&1 || true

exec python -m localchat
