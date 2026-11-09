#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
. .venv/bin/activate
QT_QPA_PLATFORM=offscreen exec python -m localchat
