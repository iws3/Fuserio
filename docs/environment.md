# LocalChat Environment

Inspected on 2026-11-09.

## Operating system and tools

- OS: Ubuntu 22.04.5 LTS (Jammy Jellyfish)
- Python: 3.14.7
- Git: 2.34.1
- `rg` is not installed; standard `grep` is available.

## llama.cpp

- Server path: `/home/gita/llama.cpp/build/bin/llama-server`
- Version: `0.7.0-dev` (build 11840, commit `36e36e63a`)
- Confirmed options: `--host`, `--port`, `--api-key`, `-m` / `--model`, `-c` / `--ctx-size`, `-t` / `--threads`, `-ngl` / `--gpu-layers`, `--jinja`, `--reasoning-format`, and `--no-webui`.

## Models

The requested scan (`find ~ -name '*.gguf' -size +50M`) found no GGUF model files over 50 MB under `/home/gita`.

## Memory and CPUs

- RAM: 15 GiB total, 8.6 GiB available at inspection time
- Swap: 2.0 GiB
- Logical CPUs (`nproc`): 8
- Physical cores (`lscpu`): 4 (1 socket, 2 threads per core)
- CPU: Intel Core i7-8650U