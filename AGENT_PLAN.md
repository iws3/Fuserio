# Build Your Private Offline AI Desktop App



```text
Follow the plan in AGENT_PLAN.md in this folder. Read the whole file first, including the rules in section 3. Then work through the milestones in order, one at a time. After each milestone, run the Done when checks and show me the real output. Stop and ask me if a check fails twice, if a step needs sudo, or if a download is larger than 50 MB. If something in the plan does not match what you find on this machine, say so and propose a fix instead of guessing.
```

## 1. What we are building

A personal chat app for Ubuntu called LocalChat (rename it whenever you like). You double-click an icon on the desktop, a window opens, a local language model loads, and you chat with it. Nothing leaves the computer: no internet, no accounts, no cloud services. The model runs through llama.cpp, which you already built. The app is a Python program that starts llama.cpp, talks to it on the local machine, and stores your chats on your own disk. It should be easy to customize: models, personas (a system prompt plus settings), generation settings and colour themes, all changeable from the app or by editing small files.

One phrase in the request was ambiguous: click on the desktop to download. This plan reads it as click on the desktop to launch the app. If you wanted a single installable file you can share, milestone 11 covers that as an optional extra.

Out of scope: cloud APIs, sign-in, telemetry, multi-user access, anything reachable from other computers, and model training.

## 2. Facts about this machine

- Ubuntu Linux with apt, user `gita`, a Dell Latitude 5590 laptop with 15 GB of RAM. Inference runs on the CPU. The GeForce MX130 GPU has only 2 GB of VRAM, so GPU offload is an optional setting that defaults to zero layers.
- llama.cpp is built in `~/llama.cpp`, and the server binary should be `~/llama.cpp/build/bin/llama-server`. Milestone 0 confirms this.
- Models are GGUF files, for example Qwen2.5-3B-Instruct at Q4\_K\_M and an NVIDIA Nemotron model, probably under `~/.cache/llama.cpp` or `~/models`. Find the real file names and do not assume them.
- The internet connection is slow (about 120 kB/s) and drops often. For any download over 50 MB, fetch the file with `wget -c`, which resumes after a break, then install it from disk with `pip install --no-deps <file>`. Ask before starting big downloads.
- The owner teaches AI engineering, so write simple, readable, well-commented code that could be shown in a class. Write all text (README, comments, button labels) in plain, direct English and avoid em dashes.

## 3. Rules for the agent

1. **Offline always.** After installation, the app may only connect to 127.0.0.1. No telemetry, update checks, remote fonts, remote icons or model downloads at runtime. Never use the `-hf` flag. Start the server with `HF_HUB_OFFLINE=1` in its environment.
2. **Work in small steps** and run the code after every step. Make a git commit at the end of each milestone with a clear message.
3. **Never block the interface.** Anything slow, such as loading the model, streaming a reply or counting tokens, runs in a worker thread, and the window must stay responsive.
4. **Stay in your lane.** Write only inside the project folder, `~/.config/localchat`, `~/.local/share/localchat`, `~/.local/share/applications` and the single launcher file on `~/Desktop`. Ask before touching anything else, and never delete user files.
5. **No sudo without asking.** List the apt packages you need, explain why, and wait for approval.
6. **Keep dependencies minimal:** `PySide6-Essentials`, `requests`, and `pytest` for development. Use the standard library for everything else.
7. **Show evidence.** Paste real command output for every Done when check. Do not say something works without proof.
8. **If a step fails twice, stop and report** what you tried instead of silently working around it.

## 4. Design decisions

- **Language and interface:** Python 3 with PySide6 (Qt). Install `PySide6-Essentials` instead of the full `PySide6` package to keep the download smaller.
- **Model engine:** `llama-server` from llama.cpp, started and stopped by the app as a child process on 127.0.0.1, on a free port chosen at startup, protected by a random API key generated for each session.
- **Talking to the model:** the OpenAI-compatible endpoint `/v1/chat/completions` with streaming, using `requests`.
- **Storage:** SQLite (standard library) in `~/.local/share/localchat/chats.db`. Settings in `~/.config/localchat/config.json`. Logs in `~/.local/share/localchat/logs/`.
- **Customization by files:** personas are small JSON files in a `presets` folder, and themes are small JSON files of colour tokens in a `themes` folder. Dropping a new file into either folder adds a new option.
- **Environment:** a project-local virtual environment in `.venv`, separate from your conda environments, so the app stays small and independent.

## 5. Project layout

```text
localchat/
  AGENT_PLAN.md   README.md   CHANGELOG.md   requirements.txt
  run.sh   install.sh   uninstall.sh
  assets/icon.png
  presets/    general.json  tutor.json  code-helper.json  summarizer.json
  themes/     light.json  dark.json  navy-gold.json
  docs/environment.md
  localchat/
    __main__.py     starts the app
    app.py          main window
    server.py       starts, watches and stops llama-server
    client.py       streaming chat client
    storage.py      SQLite chats and messages
    settings.py     config file, personas, themes
    widgets.py      sidebar, chat view, settings dialog
  tests/
```

And the main window:

```text
+------------------------------------------------------------------------+
| LocalChat       [Model: Qwen2.5-3B v]  [Persona: Tutor v]        [Gear] |
+----------------+-------------------------------------------------------+
| [+ New chat]   |  You:        Explain a KV cache simply.               |
| [Search...]    |  Assistant:  A KV cache stores ... (streams in)       |
| Chat about GPU |                                                       |
| Chat about ... +-------------------------------------------------------+
|                | [ Type a message ......................... ] [Send]   |
+----------------+-------------------------------------------------------+
| Model ready  |  8.2 tokens/s  |  RAM 6.1 GB used                      |
+------------------------------------------------------------------------+
```

## 6. Milestones

### Milestone 0: Inspect the machine (read only)

1. Record `python3 --version`, `git --version`, and the OS version.
2. Confirm `~/llama.cpp/build/bin/llama-server` exists. Run it with `--version` and `--help` and note which of these flags exist: `--host`, `--port`, `--api-key`, `-m`, `-c`, `-t`, `-ngl`, `--jinja`, `--reasoning-format`, `--no-webui`.
3. Find models with `find ~ -name '*.gguf' -size +50M 2>/dev/null` and record each path and size.
4. Record `free -h`, `nproc` and the physical core count from `lscpu`.
5. Write everything to `docs/environment.md`.

**Done when:** `docs/environment.md` lists the server path, the confirmed flags, every model with its size, the RAM and the core counts.

### Milestone 1: Skeleton and environment

1. Run `git init` and create the layout from section 5 with empty files.
2. Create the virtual environment with `python3 -m venv .venv`, then install `PySide6-Essentials`, `requests` and `pytest` into it. Write the versions to `requirements.txt`. If a download stalls, use the resume method from section 2.
3. If Qt cannot load its xcb plugin, ask to install `libxcb-cursor0` with apt, and any other package the error names.
4. Make `python -m localchat` open an empty window titled LocalChat.

**Done when:** the window opens and closes cleanly, and `git log` shows the first commit.

### Milestone 2: Server manager (no interface yet)

1. In `server.py`, write a `LlamaServer` class with `start(model_path, ctx, threads, gpu_layers)` and `stop()`.
2. `start` picks a free port, makes a random API key, and launches llama-server with `--host 127.0.0.1`, the port, the key, `-m`, `-c`, `-t` and `-ngl`, with its output sent to a log file. Default threads to the physical core count, context to 4096 and GPU layers to 0.
3. Poll `GET /health` until it returns 200. A 503 means the model is still loading. Give up with a clear error after 120 seconds. The health endpoint does not need the key.
4. `stop` sends terminate, waits five seconds, then kills. Also register cleanup so the child process dies when the app exits or crashes.
5. Add `python -m localchat.server --model PATH`, which starts the server, waits until it is ready, sends one short prompt, prints the answer and shuts down.

**Done when:** the command prints a real answer from your model, and afterwards `pgrep llama-server` prints nothing.

### Milestone 3: Streaming client

1. In `client.py`, write a generator `stream_chat(base_url, api_key, messages, **params)` that yields `(reasoning, content)` pieces from the server's streaming reply (see section 7).
2. Support cancelling in the middle by closing the response, and return the timing data from the final chunk, which includes tokens per second.
3. Write pytest tests against a small fake server built with `http.server` that sends canned streaming lines. Test normal replies, reasoning pieces, cancellation, a server error and an empty choices list.

**Done when:** `pytest` passes with no model and no network.

### Milestone 4: The chat window

1. Build the layout from section 5: sidebar, chat view, message box and status bar.
2. On startup, load the saved model in a background thread. Show Loading model in the status bar and keep Send disabled until `/health` returns 200.
3. Sending runs `stream_chat` in a worker thread and appends text live through Qt signals. While streaming, Send becomes Stop. Enter sends, and Shift+Enter adds a new line.
4. Render the conversation with `QTextBrowser.setMarkdown`, throttled to about 20 updates per second, so code blocks and lists look right.
5. If the server sends reasoning text (Nemotron may), show it in a collapsed section labelled Thinking above the answer.
6. Closing the window stops the server.

**Done when:** you chat with Qwen 3B, the text appears as it is generated, Stop works, the window never freezes, and `pgrep llama-server` is empty after you close the app.

### Milestone 5: Saving chats

1. In `storage.py`, create the tables `chats(id, title, created, updated, preset)` and `messages(id, chat_id, role, content, reasoning, created, tokens, tps)`.
2. The sidebar lists chats newest first. Support new chat, rename, delete (with a confirmation) and a search box that searches message text.
3. Name a new chat from the first 40 characters of its first message. Do not call the model for titles.
4. Export a chat to a Markdown file from a menu.
5. Count tokens with the server's `/tokenize` endpoint. When a conversation passes 85 percent of the context size, drop the oldest messages (never the system prompt) and show a notice in the chat.

**Done when:** after restarting the app the old chats are there, search finds a word from an old message, an exported file reads well, and a very long chat trims itself with a visible notice.

### Milestone 6: Customization

1. Add a settings dialog with: model (a list from scanned folders plus a Browse button), context size, threads, GPU layers, temperature, top\_p, max tokens, font size, theme and persona.
2. Personas are JSON files with `name`, `system_prompt`, `temperature`, `top_p` and `max_tokens`. Ship General, Tutor, Code helper and Summarizer in `presets/`. User-made ones live in `~/.config/localchat/presets/`. Let the user save the current settings as a new persona, duplicate one, or delete their own.
3. Themes are JSON files of colour tokens (background, panel, text, accent, font family). Build the Qt stylesheet from them. Ship Light, Dark and Navy and Gold, with navy backgrounds and gold accents.
4. Apply changes live when possible. Restart the server only when the model, context size, threads or GPU layers change, and show progress while it reloads.
5. Before loading a model, warn if its file size is above 70 percent of the available RAM.

**Done when:** you can switch persona and theme without restarting, a new theme file dropped into the themes folder appears after a restart, the settings survive a restart, and changing the model reloads the server with a visible progress message.

### Milestone 7: Everyday comforts

1. Add Regenerate for the last answer, Copy on each message, and editing the last user message and resending it.
2. The status bar shows tokens per second from the last reply and the current RAM use.
3. Add shortcuts: Ctrl+N for a new chat, Ctrl+comma for settings, Esc to stop.
4. Let the user drag a text file into the message box. Read it as UTF-8 text with a 100 KB limit and a clear message above the limit.
5. Show friendly errors for a missing model file and for a server crash, with a Show log button and a Restart button.

**Done when:** each feature works, and killing the server by hand with `pkill llama-server` shows the friendly error, and the Restart button brings the model back.

### Milestone 8: Prove it is offline

1. Add `tests/test_no_external_urls.py`, which scans the source files and fails if it finds an http or https address that is not 127.0.0.1 or localhost.
2. Turn the network off (unplug the cable and run `nmcli radio wifi off`), launch the app and chat.
3. While chatting, run `ss -tnp | grep -E 'python|llama'` and confirm that every connection is to 127.0.0.1.
4. Turn the network back on afterwards.

**Done when:** the test passes, the chat works with the network off, and the `ss` output shows only local connections.

### Milestone 9: Desktop icon and installer

1. Make an icon with a short script that uses `QPainter` and write it to `assets/icon.png` at 256 by 256 pixels. No downloads.
2. Write `run.sh`, which changes to the project folder and runs `.venv/bin/python -m localchat`.
3. Write `install.sh`, which is safe to run twice. It creates the venv if missing, installs from `requirements.txt`, writes the launcher from section 8 with the real home directory paths into `~/.local/share/applications/` and `~/Desktop/`, makes it executable, marks it trusted with `gio set`, and runs `update-desktop-database`.
4. Write `uninstall.sh`, which removes the launchers and keeps the chats unless run with `--purge`.
5. Explain in the README that if the desktop icon shows a warning, the user should right-click it and choose Allow Launching.

**Done when:** you double-click the icon on the desktop, the window appears within a few seconds, the model loads, you chat with the network off, and closing the window leaves no `llama-server` running.

### Milestone 10: Documentation

1. Write `README.md` with: how to run the app, how to add a model, how to add a theme or persona, where the data lives, how to back it up, troubleshooting, and what to do after rebuilding llama.cpp.
2. Add `CHANGELOG.md` and make the final commit.

**Done when:** following only the README from a clean copy of the folder gets the app running.

### Milestone 11 (optional): A shareable package

Only if the owner asks. Build an AppImage or a `.deb` so the app installs on another Ubuntu machine. This needs large extra tools, so ask before downloading anything.

## 7. Key code patterns

Starting the server with a random key and port:

```python
import secrets, socket, subprocess, os

def free_port():
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]

class LlamaServer:
    def start(self, model_path, ctx=4096, threads=4, gpu_layers=0):
        self.port = free_port()
        self.key = secrets.token_hex(16)
        cmd = [LLAMA_SERVER, '-m', model_path, '-c', str(ctx), '-t', str(threads),
               '-ngl', str(gpu_layers), '--host', '127.0.0.1',
               '--port', str(self.port), '--api-key', self.key]
        env = dict(os.environ, HF_HUB_OFFLINE='1')
        self.proc = subprocess.Popen(cmd, env=env, stdout=self.log_file,
                                     stderr=subprocess.STDOUT)
```

Streaming a reply:

```python
import json, requests

def stream_chat(base_url, api_key, messages, **params):
    r = requests.post(base_url + '/v1/chat/completions',
                      headers={'Authorization': 'Bearer ' + api_key},
                      json={'messages': messages, 'stream': True, **params},
                      stream=True, timeout=(5, 300))
    r.raise_for_status()
    for line in r.iter_lines(decode_unicode=True):
        if not line or not line.startswith('data: '):
            continue
        data = line[6:]
        if data == '[DONE]':
            break
        chunk = json.loads(data)
        if not chunk.get('choices'):
            continue
        delta = chunk['choices'][0]['delta']
        yield delta.get('reasoning_content'), delta.get('content')
```

These are starting points. Check the real server output on this machine, including how reasoning text arrives for the Nemotron model, and adapt the code.

## 8. The desktop launcher

Template for `localchat.desktop`, with the real paths filled in by `install.sh`:

```ini
[Desktop Entry]
Type=Application
Name=LocalChat
Comment=Private offline AI assistant
Exec=/home/gita/apps/localchat/run.sh
Icon=/home/gita/apps/localchat/assets/icon.png
Terminal=false
Categories=Utility;
StartupWMClass=localchat
```

Make the file executable, mark it trusted so the desktop allows launching, and refresh the application database:

```bash
chmod +x ~/Desktop/localchat.desktop
gio set ~/Desktop/localchat.desktop metadata::trusted true
update-desktop-database ~/.local/share/applications
```

## 9. Final acceptance checklist

1. Double-clicking the desktop icon opens the app and loads a model.
2. A chat works with Wi-Fi off and the cable unplugged.
3. Every network connection made by the app and the server is to 127.0.0.1.
4. Replies stream live, Stop works, and the window never freezes.
5. Chats survive a restart, and search and export work.
6. Persona, theme, model and generation settings can be changed in the app.
7. A new theme or persona file dropped into its folder shows up as an option.
8. Closing the app leaves no `llama-server` process running.
9. All tests pass, and the README is accurate.

## 10. Ideas for later

After the core is solid, good next features include answering questions from your own documents (using the server's embedding support), voice input with whisper.cpp, a system tray icon, a prompt library, comparing two models side by side, and a Show token probabilities panel that displays the top candidate tokens for each word the model writes, which would make a strong teaching tool for your students.
