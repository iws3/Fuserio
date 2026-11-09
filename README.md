# Fuserio

A small offline desktop app interface for a local AI workflow. This project focuses on the polished desktop experience for a developer-focused local assistant.

## Run from the terminal

```bash
cd /home/gita/Desktop/desktop-app
. .venv/bin/activate
python -m localchat
```

## Run from the desktop launcher

```bash
cd /home/gita/Desktop/desktop-app
chmod +x fuserio.sh
./fuserio.sh
```

## Model launch commands for this machine

Nemotron:

```bash
cd ~/llama.cpp
./build/bin/llama-server -hf nvidia/NVIDIA-Nemotron-3-Nano-4B-GGUF:Q4_K_M -c 4096 --port 8081
```

Qwen:

```bash
cd ~/llama.cpp
./build/bin/llama-server -hf bartowski/Qwen2.5-3B-Instruct-GGUF:Q4_K_M --port 8081
```

## Requirements

This project uses PySide6, requests, and pytest.

## Branding

- `fus.png` is the supplied source logo.
- `assets/fus-fuserio.png` is the Fuserio green and teal version used by the app window and desktop launcher.
- Run `./install.sh` after a fresh checkout to install the desktop shortcut with the branded icon.

## Notes

- The interface is intentionally styled like a developer-focused hacker console.
- It keeps everything local and does not require a cloud account.
- The app can be launched directly from a desktop shortcut once the Qt xcb dependency is installed.
