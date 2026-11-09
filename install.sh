#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_NAME="Fuserio"
DESKTOP_DIR="$HOME/.local/share/applications"
DESKTOP_LINK="$HOME/Desktop/$APP_NAME.desktop"
DESKTOP_FILE="$DESKTOP_DIR/$APP_NAME.desktop"

mkdir -p "$DESKTOP_DIR" "$HOME/Desktop"

if [ ! -f "$SCRIPT_DIR/.venv/bin/python" ]; then
  python3 -m venv "$SCRIPT_DIR/.venv"
fi

"$SCRIPT_DIR/.venv/bin/python" -m pip install --upgrade pip >/dev/null 2>&1 || true
"$SCRIPT_DIR/.venv/bin/python" -m pip install -r "$SCRIPT_DIR/requirements.txt" >/dev/null 2>&1 || true

cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Fuserio
Comment=Offline local AI workspace
Exec=/bin/bash -lc '"$SCRIPT_DIR/fuserio.sh"'
Path=$SCRIPT_DIR
Icon=$SCRIPT_DIR/assets/fus-fuserio.png
Terminal=false
Categories=Development;Utility;
StartupNotify=true
EOF

cp "$DESKTOP_FILE" "$DESKTOP_LINK"
chmod +x "$DESKTOP_FILE" "$DESKTOP_LINK"

if command -v gio >/dev/null 2>&1; then
  gio set "$DESKTOP_FILE" metadata::trusted true || true
  gio set "$DESKTOP_LINK" metadata::trusted true || true
fi

if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "$DESKTOP_DIR" >/dev/null 2>&1 || true
fi

echo "Fuserio launcher installed."
echo "Desktop file: $DESKTOP_LINK"
echo "Application file: $DESKTOP_FILE"
echo "Run it by double-clicking the Desktop icon or using: $SCRIPT_DIR/fuserio.sh"
