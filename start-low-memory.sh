#!/usr/bin/env bash
set -euo pipefail

LLAMA_BIN="$HOME/llama.cpp/build/bin/llama-server"
MODEL="bartowski/DeepSeek-R1-Distill-Qwen-1.5B-GGUF:Q4_K_M"

if [[ ! -x "$LLAMA_BIN" ]]; then
  echo "Missing llama.cpp server: $LLAMA_BIN"
  exit 1
fi

export HF_HUB_OFFLINE=1
exec "$LLAMA_BIN" \
  -hf "$MODEL" \
  -c 2048 \
  -ngl 0 \
  -b 128 \
  -ub 64 \
  --parallel 1 \
  --host 127.0.0.1 \
  --port 8081