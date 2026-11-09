import html
import os
import re
import secrets
import socket
import threading

import requests

from PySide6.QtCore import QProcess, QProcessEnvironment, Qt, QThread, QTimer, Signal
from PySide6.QtGui import QIcon, QKeySequence, QPixmap, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QTextBrowser,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from localchat.client import stream_chat


MODEL_OPTIONS = (
    ("Nemotron 3 Nano 4B", "nvidia/NVIDIA-Nemotron-3-Nano-4B-GGUF:Q4_K_M"),
    ("Qwen 2.5 Instruct 3B", "bartowski/Qwen2.5-3B-Instruct-GGUF:Q4_K_M"),
)


def build_stylesheet() -> str:
    return """
    QWidget {
        background: #031b18;
        color: #dcfff6;
        font-family: "JetBrains Mono", "Fira Code", "SFMono-Regular", monospace;
        border: none;
    }

    QMainWindow {
        background: #031b18;
    }

    #root {
        background: #021611;
        border: 1px solid rgba(64, 208, 176, 0.35);
        border-radius: 18px;
    }

    #sidebar {
        background: rgba(4, 23, 20, 0.95);
        border: 1px solid rgba(55, 191, 164, 0.35);
        border-radius: 16px 0 0 16px;
    }

    #chatPanel {
        background: rgba(2, 20, 17, 0.98);
        border: 1px solid rgba(55, 191, 164, 0.35);
        border-radius: 0 16px 16px 0;
    }

    #headerBar {
        background: rgba(5, 24, 21, 0.92);
        border: 1px solid rgba(64, 208, 176, 0.3);
        border-radius: 12px;
        padding: 12px 16px;
    }

    #brand {
        color: #7ef3d0;
        font-size: 28px;
        font-weight: 800;
        letter-spacing: 0.18em;
        text-transform: uppercase;
    }

    #statPill {
        color: #7ef3d0;
        border: 1px solid rgba(126, 243, 208, 0.45);
        background: rgba(12, 44, 39, 0.7);
        border-radius: 999px;
        padding: 7px 12px;
        font-size: 10px;
        letter-spacing: 0.18em;
        text-transform: uppercase;
    }

    #modelInfo {
        color: #bfeee3;
        font-size: 11px;
        letter-spacing: 0.10em;
        text-transform: uppercase;
    }

    #searchBox {
        background: rgba(7, 29, 25, 0.9);
        border: 1px solid rgba(81, 204, 175, 0.38);
        border-radius: 10px;
        padding: 9px 12px;
        color: #d8fff4;
        font-size: 12px;
    }

    #newChatButton {
        background: rgba(12, 52, 45, 0.92);
        border: 1px solid rgba(92, 240, 199, 0.6);
        border-radius: 10px;
        color: #aefee0;
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        padding: 12px 14px;
    }

    #newChatButton:hover {
        background: rgba(16, 68, 59, 0.95);
    }

    QListWidget {
        background: transparent;
        border: none;
        outline: none;
        padding: 4px 0;
    }

    QListWidget::item {
        background: rgba(11, 31, 27, 0.85);
        border: 1px solid rgba(75, 170, 150, 0.32);
        border-radius: 10px;
        padding: 12px 10px;
        margin: 6px 2px;
        color: #dffff6;
        font-size: 12px;
    }

    QListWidget::item:selected {
        background: rgba(15, 57, 49, 0.98);
        border-color: rgba(118, 245, 203, 0.72);
        color: #f1fff9;
    }

    #chatView {
        background: rgba(2, 17, 15, 0.98);
        border: 1px solid rgba(53, 170, 149, 0.18);
        border-radius: 12px;
        padding: 18px 22px;
        color: #e0fff7;
        font-size: 14px;
        line-height: 1.55;
    }

    #composer {
        background: rgba(7, 23, 20, 0.9);
        border: 1px solid rgba(83, 200, 171, 0.38);
        border-radius: 12px;
        color: #ebfff8;
        padding: 14px 16px;
        font-size: 14px;
    }

    QComboBox {
        background: rgba(7, 29, 25, 0.9);
        border: 1px solid rgba(81, 204, 175, 0.45);
        border-radius: 10px;
        color: #d8fff4;
        padding: 12px 30px 12px 12px;
        min-width: 190px;
    }

    QComboBox::drop-down {
        border: none;
        width: 26px;
    }

    QComboBox QAbstractItemView {
        background: #06231e;
        color: #e6fff6;
        selection-background-color: #0b6551;
        border: 1px solid #287d69;
    }

    #sendButton {
        background: linear-gradient(180deg, #0ca57d 0%, #0a8d6c 100%);
        border: 1px solid rgba(125, 255, 214, 0.72);
        color: #e9fff9;
        border-radius: 12px;
        padding: 14px 20px;
        font-size: 12px;
        font-weight: 800;
        letter-spacing: 0.16em;
        text-transform: uppercase;
    }

    #sendButton:hover {
        background: linear-gradient(180deg, #11b68a 0%, #0d9d74 100%);
    }

    #attachButton {
        background: rgba(12, 40, 35, 0.9);
        border: 1px solid rgba(91, 198, 170, 0.38);
        color: #dffef7;
        border-radius: 12px;
        padding: 12px 16px;
        font-size: 11px;
        letter-spacing: 0.12em;
        text-transform: uppercase;
    }

    QStatusBar {
        background: rgba(3, 20, 17, 0.95);
        color: #9ef5d2;
        border-top: 1px solid rgba(55, 191, 164, 0.24);
    }

    QStatusBar::item {
        border: none;
    }
    """


class InputField(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("Enter a prompt for the local model...")
        self.setFixedHeight(72)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter) and not event.modifiers() & Qt.ShiftModifier:
            self.window().send_message()
            return
        super().keyPressEvent(event)


class ExistingServerProbe(QThread):
    found = Signal(str, str)
    failed = Signal()

    def __init__(self, base_url: str):
        super().__init__()
        self.base_url = base_url
        self.cancelled = threading.Event()

    def cancel(self):
        self.cancelled.set()

    def run(self):
        for _ in range(12):
            if self.cancelled.is_set():
                return
            try:
                health = requests.get(f"{self.base_url}/health", timeout=1)
                if health.status_code == 200:
                    model_response = requests.get(f"{self.base_url}/v1/models", timeout=2)
                    model_response.raise_for_status()
                    result = model_response.json()
                    models = result.get("models") or result.get("data") or []
                    model_id = ""
                    if models:
                        model_id = models[0].get("id") or models[0].get("name") or ""
                    self.found.emit(self.base_url, model_id)
                    return
            except requests.RequestException:
                pass
            if self.cancelled.wait(0.25):
                return
        if not self.cancelled.is_set():
            self.failed.emit()


class ServerReadyProbe(QThread):
    ready = Signal(int, str, str, str)
    failed = Signal(int, str)

    def __init__(self, generation: int, base_url: str, api_key: str, model_id: str):
        super().__init__()
        self.generation = generation
        self.base_url = base_url
        self.api_key = api_key
        self.model_id = model_id
        self.cancelled = threading.Event()

    def cancel(self):
        self.cancelled.set()

    def run(self):
        for _ in range(180):
            if self.cancelled.is_set():
                return
            try:
                response = requests.get(f"{self.base_url}/health", timeout=2)
                if response.status_code == 200:
                    self.ready.emit(self.generation, self.base_url, self.api_key, self.model_id)
                    return
            except requests.RequestException:
                pass
            self.cancelled.wait(1)
        if not self.cancelled.is_set():
            self.failed.emit(self.generation, "The model did not become ready within three minutes.")


class ChatWorker(QThread):
    chunk = Signal(str, str)
    error = Signal(str)

    def __init__(self, base_url: str, api_key: str, messages: list[dict[str, str]]):
        super().__init__()
        self.base_url = base_url
        self.api_key = api_key
        self.messages = messages
        self.cancelled = threading.Event()
        self._response = None
        self._response_lock = threading.Lock()

    def cancel(self):
        self.cancelled.set()
        with self._response_lock:
            if self._response is not None:
                self._response.close()

    def _set_response(self, response):
        with self._response_lock:
            self._response = response
            if self.cancelled.is_set():
                response.close()

    def run(self):
        try:
            for reasoning, content in stream_chat(
                self.base_url,
                self.messages,
                api_key=self.api_key,
                cancel_event=self.cancelled,
                response_callback=self._set_response,
            ):
                if self.cancelled.is_set():
                    break
                self.chunk.emit(reasoning, content)
        except Exception as error:
            if not self.cancelled.is_set():
                self.error.emit(str(error))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fuserio")
        self.resize(1440, 900)
        self.setStyleSheet(build_stylesheet())
        self.logo_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "assets",
            "fus-fuserio.png",
        )
        self.setWindowIcon(QIcon(self.logo_path))
        self.messages: list[dict[str, str]] = []
        self.base_url = ""
        self.api_key = ""
        self.active_model = ""
        self.external_server: tuple[str, str] | None = None
        self.server_process: QProcess | None = None
        self.server_probe: ServerReadyProbe | None = None
        self.chat_worker: ChatWorker | None = None
        self.generation = 0
        self.pending_model_start = ""
        self.server_output = ""
        self._build_ui()
        self._load_demo_data()
        self.existing_server_probe = ExistingServerProbe("http://127.0.0.1:8081")
        self.existing_server_probe.found.connect(self._existing_server_found)
        self.existing_server_probe.failed.connect(self._existing_server_missing)
        self.existing_server_probe.start()
        self._load_demo_data()

    def _build_ui(self):
        root = QWidget()
        root.setObjectName("root")
        outer = QHBoxLayout(root)
        outer.setContentsMargins(18, 18, 18, 18)
        outer.setSpacing(18)

        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(18, 18, 18, 18)
        side_layout.setSpacing(12)

        new_chat = QPushButton("+ New chat")
        new_chat.setObjectName("newChatButton")
        side_layout.addWidget(new_chat)

        search = QTextEdit()
        search.setObjectName("searchBox")
        search.setFixedHeight(40)
        search.setPlaceholderText("Search chats")
        search.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        search.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        side_layout.addWidget(search)

        self.chat_list = QListWidget()
        self.chat_list.setAlternatingRowColors(False)
        side_layout.addWidget(self.chat_list, 1)

        main_panel = QWidget()
        main_panel.setObjectName("chatPanel")
        main_layout = QVBoxLayout(main_panel)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(14)

        header = QWidget()
        header.setObjectName("headerBar")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 10, 16, 10)
        header_layout.setSpacing(18)

        brand = QLabel("Fuserio")
        brand.setObjectName("brand")
        brand_logo = QLabel()
        brand_logo.setObjectName("brandLogo")
        brand_logo.setFixedSize(44, 44)
        brand_logo.setPixmap(
            QPixmap(self.logo_path).scaled(
                44,
                44,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
        )
        header_layout.addWidget(brand_logo)
        header_layout.addWidget(brand)
        header_layout.addStretch()

        self.model_info = QLabel("Select a local model below")
        self.model_info.setObjectName("modelInfo")
        header_layout.addWidget(self.model_info)

        self.connection_status = QLabel("CONNECTING")
        self.connection_status.setObjectName("statPill")
        header_layout.addWidget(self.connection_status)

        main_layout.addWidget(header)

        self.chat_view = QTextBrowser()
        self.chat_view.setObjectName("chatView")
        self.chat_view.setReadOnly(True)
        self.chat_view.setOpenExternalLinks(False)
        main_layout.addWidget(self.chat_view, 1)

        composer = QWidget()
        composer_layout = QHBoxLayout(composer)
        composer_layout.setContentsMargins(0, 0, 0, 0)
        composer_layout.setSpacing(12)

        self.input = InputField()
        self.input.setObjectName("composer")
        composer_layout.addWidget(self.input, 1)

        self.model_selector = QComboBox()
        self.model_selector.setObjectName("modelSelector")
        for label, model_id in MODEL_OPTIONS:
            self.model_selector.addItem(label, model_id)
        composer_layout.addWidget(self.model_selector)

        main_layout.addWidget(composer)

        outer.addWidget(sidebar, 1)
        outer.addWidget(main_panel, 5)

        self.setCentralWidget(root)
        self.statusBar().showMessage("Connecting to local model...")

        self.send_button = QPushButton("Send")
        self.send_button.setObjectName("sendButton")
        self.send_button.setEnabled(False)
        composer_layout.addWidget(self.send_button)
        self.send_button.clicked.connect(self._send_or_stop)
        self.model_selector.currentIndexChanged.connect(self._model_selected)
        new_chat.clicked.connect(self.new_chat)
        QShortcut(QKeySequence("Ctrl+N"), self, self.new_chat)
        QShortcut(QKeySequence("Ctrl+Comma"), self, self.show_status)
        QShortcut(QKeySequence("Escape"), self, self.stop_streaming)

    def _load_demo_data(self):
        chats = [
            ("GPU triage", "three hidden bottlenecks in the render pass"),
            ("LLM notes", "prototype memory-safe attention paths"),
            ("Server logs", "watching llama.cpp begin a clean startup"),
        ]

        for title, preview in chats:
            item = QListWidgetItem(title)
            item.setToolTip(preview)
            self.chat_list.addItem(item)

        self._render_messages()

    def new_chat(self):
        if self.chat_worker and self.chat_worker.isRunning():
            self.stop_streaming()
        self.messages.clear()
        self.chat_view.clear()
        self.input.clear()
        self._render_messages()
        self.statusBar().showMessage("Fresh session started")

    def stop_streaming(self):
        if self.chat_worker and self.chat_worker.isRunning():
            self.chat_worker.cancel()
            self.send_button.setEnabled(False)
            self.send_button.setText("Stopping")
            self.statusBar().showMessage("Stopping response...")

    def show_status(self):
        self.statusBar().showMessage("Settings panel pending")

    def send_message(self):
        if not self.base_url or (self.chat_worker and self.chat_worker.isRunning()):
            return
        message = self.input.toPlainText().strip()
        if not message:
            return

        self.input.clear()
        self.messages.append({"role": "user", "content": message})
        self.messages.append({"role": "assistant", "content": "", "reasoning": ""})
        self._render_messages()
        self.send_button.setText("Stop")
        self.send_button.setEnabled(True)
        self.statusBar().showMessage("Generating locally...")
        api_messages = [
            {"role": item["role"], "content": item["content"]}
            for item in self.messages[:-1]
        ]
        self.chat_worker = ChatWorker(self.base_url, self.api_key, api_messages)
        self.chat_worker.chunk.connect(self._append_stream_chunk)
        self.chat_worker.error.connect(self._chat_error)
        self.chat_worker.finished.connect(self._chat_finished)
        self.chat_worker.start()

    def _send_or_stop(self):
        if self.chat_worker and self.chat_worker.isRunning():
            self.stop_streaming()
        else:
            self.send_message()

    def _model_selected(self):
        self.generation += 1
        model_id = self.model_selector.currentData()
        self.base_url = ""
        self.api_key = ""
        self.active_model = ""
        self.send_button.setEnabled(False)
        self.connection_status.setText("LOADING")
        self.model_info.setText(f"Model: {self.model_selector.currentText()}")
        self.statusBar().showMessage("Loading selected local model...")
        if self.chat_worker and self.chat_worker.isRunning():
            self.pending_model_start = model_id
            self.stop_streaming()
            return
        self._prepare_model(model_id, self.generation)

    def _existing_server_found(self, base_url: str, model_id: str):
        self.external_server = (base_url, model_id)
        matched_index = next(
            (index for index in range(self.model_selector.count())
             if self.model_selector.itemData(index).lower() == model_id.lower()),
            -1,
        )
        if matched_index >= 0 and self.generation == 0:
            self.model_selector.blockSignals(True)
            self.model_selector.setCurrentIndex(matched_index)
            self.model_selector.blockSignals(False)
            self._connect_model(base_url, "", model_id, self.generation)
        elif self.model_selector.currentData() == model_id:
            self._connect_model(base_url, "", model_id, self.generation)
        elif self.generation == 0:
            self._start_model(self.model_selector.currentData(), self.generation)

    def _existing_server_missing(self):
        if self.generation == 0:
            self._start_model(self.model_selector.currentData(), self.generation)

    def _prepare_model(self, model_id: str, generation: int):
        if self.external_server and self.external_server[1].lower() == model_id.lower():
            self._connect_model(self.external_server[0], "", model_id, generation)
            return
        self._start_model(model_id, generation)

    def _start_model(self, model_id: str, generation: int):
        if self.server_process and self.server_process.state() != QProcess.NotRunning:
            self.pending_model_start = model_id
            if self.server_probe:
                self.server_probe.cancel()
            self.server_process.terminate()
            QTimer.singleShot(2500, self._kill_server_if_needed)
            self.connection_status.setText("STOPPING")
            return

        server_path = os.path.expanduser("~/llama.cpp/build/bin/llama-server")
        if not os.path.isfile(server_path) or not os.access(server_path, os.X_OK):
            self._model_error(generation, f"llama-server is missing or not executable: {server_path}")
            return

        with socket.socket() as server_socket:
            server_socket.bind(("127.0.0.1", 0))
            port = server_socket.getsockname()[1]
        api_key = secrets.token_hex(24)
        base_url = f"http://127.0.0.1:{port}"
        process = QProcess(self)
        process.setProcessChannelMode(QProcess.MergedChannels)
        process.setProgram(server_path)
        process.setArguments([
            "-hf", model_id, "-c", "4096", "--host", "127.0.0.1",
            "--port", str(port), "--api-key", api_key, "--no-webui",
        ])
        environment = QProcessEnvironment.systemEnvironment()
        environment.insert("HF_HUB_OFFLINE", "1")
        process.setProcessEnvironment(environment)
        process.readyReadStandardOutput.connect(self._read_server_output)
        process.finished.connect(
            lambda code, _status, item=process, token=generation:
            self._server_finished(item, code, token)
        )
        process.errorOccurred.connect(
            lambda _error, token=generation:
            self._model_error(token, "Could not start llama-server.")
        )
        self.server_process = process
        self.base_url = base_url
        self.api_key = api_key
        self.active_model = model_id
        self.pending_model_start = ""
        self.server_output = ""
        self.connection_status.setText("LOADING")
        self.statusBar().showMessage("Loading model offline. The window remains responsive.")
        process.start()

        self.server_probe = ServerReadyProbe(generation, base_url, api_key, model_id)
        self.server_probe.ready.connect(self._server_ready)
        self.server_probe.failed.connect(self._model_error)
        self.server_probe.start()

    def _kill_server_if_needed(self):
        if self.server_process and self.server_process.state() != QProcess.NotRunning:
            self.server_process.kill()

    def _read_server_output(self):
        if self.server_process:
            output = bytes(self.server_process.readAllStandardOutput()).decode("utf-8", errors="replace")
            self.server_output = (self.server_output + output)[-8000:]

    def _server_finished(self, process: QProcess, code: int, generation: int):
        if process == self.server_process:
            self.server_process = None
        if self.server_probe and generation == self.generation:
            self.server_probe.cancel()
        next_model = self.pending_model_start
        self.pending_model_start = ""
        if next_model:
            self._start_model(next_model, self.generation)
        elif generation == self.generation and not self.base_url:
            self._model_error(generation, f"llama-server exited with code {code}. {self.server_output[-1200:]}")
        elif generation == self.generation and self.active_model:
            self.base_url = ""
            self.send_button.setEnabled(False)
            self.connection_status.setText("OFFLINE")
            self.statusBar().showMessage("The model server stopped.")

    def _server_ready(self, generation: int, base_url: str, api_key: str, model_id: str):
        self._connect_model(base_url, api_key, model_id, generation)

    def _connect_model(self, base_url: str, api_key: str, model_id: str, generation: int):
        if generation != self.generation:
            return
        self.base_url = base_url
        self.api_key = api_key
        self.active_model = model_id
        label = next(
            (name for name, value in MODEL_OPTIONS if value.lower() == model_id.lower()),
            model_id,
        )
        self.model_info.setText(f"Model: {label}")
        self.connection_status.setText("READY")
        self.send_button.setEnabled(True)
        self.statusBar().showMessage("Local model ready. Your messages stay on this computer.")

    def _model_error(self, generation: int, message: str):
        if generation != self.generation:
            return
        detail = self.server_output[-1200:].strip()
        self.base_url = ""
        self.connection_status.setText("ERROR")
        self.send_button.setEnabled(False)
        self.statusBar().showMessage(message + (f" Check llama-server output: {detail}" if detail else ""))

    def _append_stream_chunk(self, reasoning: str, content: str):
        if not self.messages:
            return
        self.messages[-1]["reasoning"] += reasoning
        self.messages[-1]["content"] += content
        self._render_messages()

    def _chat_error(self, message: str):
        if self.messages and self.messages[-1]["role"] == "assistant":
            self.messages[-1]["content"] += f"\n\n[Chat error: {message}]"
            self._render_messages()
        self.statusBar().showMessage(f"Chat failed: {message}")

    def _chat_finished(self):
        self.chat_worker = None
        self.send_button.setText("Send")
        self.send_button.setEnabled(bool(self.base_url))
        if self.pending_model_start:
            model_id = self.pending_model_start
            self.pending_model_start = ""
            self._prepare_model(model_id, self.generation)
        elif self.base_url:
            self.statusBar().showMessage("Response complete.")

    def _render_messages(self):
        document = [
            '<html><body style="background-color:#050d0c;color:#e8f4ef;'
            'font-family:monospace;font-size:13px;margin:12px;">',
            '<table width="100%" cellspacing="0" cellpadding="0"><tr>',
            '<td style="color:#61efba;font-size:10px;">FUSERIO <span style="color:#57756b;">/</span> ',
            'PRIVATE INFERENCE SESSION</td>',
            '<td align="right" style="color:#648078;font-size:10px;">',
            '<span style="color:#55e7ae;">●</span> LOOPBACK ONLY</td>',
            '</tr></table>',
            '<hr color="#17332c" size="1">',
        ]

        if not self.messages:
            document.append(
                '<table width="100%" height="360" cellspacing="0" cellpadding="0">'
                '<tr><td align="center" valign="middle">'
                '<table cellspacing="0" cellpadding="18" bgcolor="#091713" '
                'border="1" bordercolor="#1d493a"><tr><td>'
                '<div style="color:#5ce8ad;font-size:10px;">[ CHANNEL READY ]</div><br>'
                '<div style="color:#effff7;font-size:24px;font-weight:bold;">Ready to build.</div><br>'
                '<div style="color:#91aa9e;">Send a prompt to begin a private local session.</div>'
                '</td></tr></table></td></tr></table>'
            )

        for turn_number, message in enumerate(self.messages, start=1):
            role = message["role"]
            content = self._format_message_content(message.get("content", ""))
            turn_label = f"TURN {turn_number:03d}"

            if role == "user":
                document.append(
                    '<table width="100%" cellspacing="0" cellpadding="0"><tr><td align="right">'
                    '<table width="78%" cellspacing="0" cellpadding="0" bgcolor="#111b18" '
                    'border="1" bordercolor="#59432b"><tr>'
                    '<td width="4" bgcolor="#f2ad62"></td>'
                    '<td style="padding:14px 18px;">'
                    '<table width="100%" cellspacing="0" cellpadding="0"><tr>'
                    '<td><span style="color:#ffcb8c;font-weight:bold;">YOU</span> '
                    '<span style="color:#6b6251;">/ OPERATOR</span></td>'
                    f'<td align="right" style="color:#8e765a;font-size:10px;">{turn_label} · OUTBOUND</td>'
                    '</tr></table><br>'
                    f'<div style="color:#f4efe4;line-height:1.55;">{content}</div>'
                    '</td></tr></table></td></tr></table><br>'
                )
                continue

            reasoning = self._format_message_content(message.get("reasoning", ""))
            if reasoning:
                reasoning_panel = (
                    '<table width="100%" cellspacing="0" cellpadding="0" bgcolor="#071513" '
                    'border="1" bordercolor="#17423a"><tr>'
                    '<td width="3" bgcolor="#45c8c0"></td>'
                    '<td style="padding:10px 14px;">'
                    '<div style="color:#62d8d0;font-size:10px;font-weight:bold;">'
                    'THINK TRACE <span style="color:#507873;">/ INTERNAL REASONING</span></div><br>'
                    f'<div style="color:#a1c9c1;line-height:1.5;">{reasoning}</div>'
                    '</td></tr></table><br>'
                )
            else:
                reasoning_panel = ""

            if not content:
                content = '<span style="color:#65efb9;">▋</span> '
                '<span style="color:#719087;">WAITING FOR MODEL TOKENS</span>'

            document.append(
                '<table width="100%" cellspacing="0" cellpadding="0"><tr><td>'
                '<table width="100%" cellspacing="0" cellpadding="0" bgcolor="#0a1714" '
                'border="1" bordercolor="#1c4537"><tr>'
                '<td width="4" bgcolor="#59edaa"></td>'
                '<td style="padding:15px 19px;">'
                '<table width="100%" cellspacing="0" cellpadding="0"><tr>'
                '<td><span style="color:#70f2b7;font-weight:bold;">FUSERIO</span> '
                '<span style="color:#5c8375;">/ LOCAL INTELLIGENCE</span></td>'
                f'<td align="right" style="color:#5e8878;font-size:10px;">{turn_label} · INBOUND</td>'
                f'</tr></table><br>{reasoning_panel}'
                f'<div style="color:#e5f5ec;line-height:1.6;">{content}</div>'
                '</td></tr></table></td></tr></table><br>'
            )

        document.append('</body></html>')
        self.chat_view.setHtml("".join(document))
        scrollbar = self.chat_view.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    @staticmethod
    def _format_message_content(content: str) -> str:
        pieces = content.split("```")
        rendered = []
        for index, piece in enumerate(pieces):
            if index % 2:
                code_lines = piece.split("\n", 1)
                language = code_lines[0].strip()
                code = code_lines[1] if len(code_lines) > 1 else code_lines[0]
                language_label = html.escape(language.upper() or "CODE")
                rendered.append(
                    '<table width="100%" cellspacing="0" cellpadding="0" bgcolor="#050d0c" '
                    'border="1" bordercolor="#254239"><tr><td style="padding:8px 12px;">'
                    f'<div style="color:#69d9a8;font-size:9px;">{language_label} / CODE BLOCK</div>'
                    f'<pre style="color:#d8eee3;font-family:monospace;white-space:pre-wrap;">'
                    f'{html.escape(code)}</pre></td></tr></table>'
                )
                continue

            escaped = html.escape(piece).replace("\n", "<br>")
            escaped = re.sub(
                r"`([^`]+)`",
                r'<span style="color:#9ee7bf;background-color:#13261f;">\1</span>',
                escaped,
            )
            rendered.append(escaped)
        return "".join(rendered)

    def closeEvent(self, event):
        if self.chat_worker and self.chat_worker.isRunning():
            self.chat_worker.cancel()
            self.chat_worker.wait(2000)
        if self.server_probe:
            self.server_probe.cancel()
            if self.server_probe.isRunning():
                self.server_probe.wait(3000)
        if self.existing_server_probe.isRunning():
            self.existing_server_probe.cancel()
            self.existing_server_probe.wait(1500)
        if self.server_process and self.server_process.state() != QProcess.NotRunning:
            self.server_process.terminate()
            if not self.server_process.waitForFinished(3000):
                self.server_process.kill()
                self.server_process.waitForFinished(1000)
        event.accept()


def main() -> None:
    app = QApplication([])
    app.setApplicationName("Fuserio")
    app.setApplicationDisplayName("Fuserio")
    app.setStyle("Fusion")
    app.setQuitOnLastWindowClosed(True)

    window = MainWindow()
    window.show()
    app.exec()
