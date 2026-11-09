#!/usr/bin/env bash
set -euo pipefail

LLAMA_BIN="$HOME/llama.cpp/build/bin/llama-server"
if [ ! -x "$LLAMA_BIN" ]; then
  echo "Missing llama.cpp server: $LLAMA_BIN"
  exit 1
fi

export HF_HUB_OFFLINE=1
exec "$LLAMA_BIN" -hf nvidia/NVIDIA-Nemotron-3-Nano-4B-GGUF:Q4_K_M -c 4096 --port 8081
