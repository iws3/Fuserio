# LocalChat

A small offline desktop app interface for a local AI workflow. This project focuses on the polished desktop experience for a developer-oriented local assistant and follows the same offline-first design principles as the broader LocalChat plan.

## Run

```bash
cd /home/gita/Desktop/desktop-app
. .venv/bin/activate
python -m localchat
```

## Requirements

This project uses PySide6, `requests`, and `pytest`.

## Notes

- The interface is intentionally styled like a terminal-driven hacker dashboard.
- It keeps everything local and does not require a cloud account.
- Real model loading and llama.cpp integration can be added on top of this interface shell.
