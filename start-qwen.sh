#!/usr/bin/env bash
set -euo pipefail

LLAMA_BIN="$HOME/llama.cpp/build/bin/llama-server"
if [ ! -x "$LLAMA_BIN" ]; then
  echo "Missing llama.cpp server: $LLAMA_BIN"
  exit 1
fi

export HF_HUB_OFFLINE=1
exec "$LLAMA_BIN" -hf bartowski/Qwen2.5-3B-Instruct-GGUF:Q4_K_M --port 8081
