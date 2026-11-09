import os
import textwrap

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
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


def build_stylesheet() -> str:
    return """
    QWidget {
        background: #07130f;
        color: #dffcf5;
        border: none;
        font-family: "JetBrains Mono", "Fira Code", "SFMono-Regular", monospace;
    }

    QMainWindow {
        background: #07130f;
    }

    #root {
        background: #081b18;
        border: 1px solid #16352d;
        border-radius: 16px;
    }

    #sidebar {
        background: rgba(13, 29, 24, 0.95);
        border: 1px solid #1d4d43;
        border-radius: 16px 0 0 16px;
    }

    #chatPanel {
        background: rgba(5, 22, 19, 0.96);
        border: 1px solid #1d4d43;
        border-radius: 0 16px 16px 0;
    }

    #topBar {
        background: rgba(6, 26, 22, 0.9);
        border: 1px solid #1d4d43;
        border-radius: 12px;
        padding: 10px 14px;
    }

    QLabel {
        color: #eafaf5;
    }

    #brand {
        font-size: 20px;
        font-weight: 700;
        letter-spacing: 0.08em;
        color: #76f7d1;
        text-transform: uppercase;
    }

    #statusPill {
        color: #9ef7d1;
        border: 1px solid #2cd3a3;
        border-radius: 999px;
        background: rgba(29, 77, 67, 0.35);
        padding: 5px 12px;
        font-size: 11px;
        letter-spacing: 0.12em;
        text-transform: uppercase;
    }

    .panelButton {
        background: rgba(26, 48, 44, 0.8);
        color: #dffcf5;
        border: 1px solid #285b51;
        border-radius: 10px;
        padding: 10px 12px;
        font-size: 12px;
        font-weight: 600;
    }

    .panelButton:hover {
        border-color: #5ef5c7;
        background: rgba(31, 62, 55, 0.9);
    }

    #searchBox {
        background: rgba(9, 20, 18, 0.8);
        border: 1px solid #285b51;
        border-radius: 10px;
        padding: 8px 10px;
        color: #d8fff1;
    }

    QListWidget {
        background: transparent;
        border: none;
        outline: none;
        padding: 6px;
    }

    QListWidget::item {
        background: rgba(12, 30, 25, 0.8);
        border: 1px solid rgba(40, 91, 81, 0.8);
        border-radius: 10px;
        padding: 12px 10px;
        margin: 6px 2px;
        color: #d8fff1;
    }

    QListWidget::item:selected {
        background: rgba(20, 54, 48, 0.95);
        border-color: #5ef5c7;
    }

    #chatView {
        background: transparent;
        border: none;
        color: #ebfff9;
        padding: 18px;
        font-size: 14px;
        line-height: 1.5;
    }

    .msg {
        margin: 8px 0;
        border-radius: 14px;
        padding: 10px 12px;
        border: 1px solid rgba(93, 240, 196, 0.15);
    }

    .user {
        background: rgba(13, 45, 42, 0.8);
        margin-left: 80px;
    }

    .assistant {
        background: rgba(9, 22, 24, 0.9);
        margin-right: 80px;
    }

    .meta {
        font-size: 10px;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: #7ee7c8;
        margin-bottom: 6px;
    }

    .bubble {
        color: #ebfff9;
        white-space: normal;
    }

    #composer {
        background: rgba(8, 19, 17, 0.92);
        border: 1px solid #285b51;
        border-radius: 12px;
        padding: 10px 12px;
        color: #ebfff9;
        font-size: 14px;
    }

    #sendButton {
        background: #0d8b6d;
        border: 1px solid #39d4a3;
        color: #eafff6;
        border-radius: 10px;
        padding: 11px 20px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }

    #sendButton:hover {
        background: #11a57d;
    }

    #auxButton {
        background: rgba(22, 44, 37, 0.85);
        border: 1px solid #285b51;
        color: #dffcf5;
        border-radius: 10px;
        padding: 10px 12px;
        font-size: 12px;
    }

    QStatusBar {
        background: rgba(8, 19, 17, 0.95);
        color: #9ef7d1;
        border-top: 1px solid #1d4d43;
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
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter) and not event.modifiers() & Qt.ShiftModifier:
            self.parent().send_message()
            return
        super().keyPressEvent(event)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LocalChat")
        self.resize(1280, 820)
        self.setStyleSheet(build_stylesheet())
        self._build_ui()
        self._load_demo_data()

    def _build_ui(self):
        main_widget = QWidget()
        main_widget.setObjectName("root")
        root_layout = QHBoxLayout(main_widget)
        root_layout.setContentsMargins(18, 18, 18, 18)
        root_layout.setSpacing(18)

        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(16, 16, 16, 16)
        sidebar_layout.setSpacing(12)

        new_chat = QPushButton("+ New chat")
        new_chat.setObjectName("newChat")
        new_chat.setProperty("class", "panelButton")
        new_chat.setStyleSheet("QPushButton { background: rgba(14, 58, 52, 0.7); border: 1px solid #2cd3a3; }")
        sidebar_layout.addWidget(new_chat)

        search = QTextEdit()
        search.setObjectName("searchBox")
        search.setFixedHeight(38)
        search.setPlaceholderText("Search chats")
        search.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        search.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        sidebar_layout.addWidget(search)

        self.chat_list = QListWidget()
        sidebar_layout.addWidget(self.chat_list)
        self.chat_list.setAlternatingRowColors(False)

        main_panel = QWidget()
        main_panel.setObjectName("chatPanel")
        main_panel_layout = QVBoxLayout(main_panel)
        main_panel_layout.setContentsMargins(16, 16, 16, 16)
        main_panel_layout.setSpacing(14)

        top_bar = QWidget()
        top_bar.setObjectName("topBar")
        top_bar_layout = QHBoxLayout(top_bar)
        top_bar_layout.setContentsMargins(12, 8, 12, 8)

        brand = QLabel("LocalChat")
        brand.setObjectName("brand")
        top_bar_layout.addWidget(brand)
        top_bar_layout.addStretch()

        model_label = QLabel("Model: Qwen2.5-3B")
        model_label.setStyleSheet("color: #b7fff0; font-size: 12px; letter-spacing: 0.08em;")
        top_bar_layout.addWidget(model_label)

        persona_label = QLabel("Persona: general")
        persona_label.setStyleSheet("color: #b7fff0; font-size: 12px; letter-spacing: 0.08em;")
        top_bar_layout.addWidget(persona_label)

        status_pill = QLabel("offline")
        status_pill.setObjectName("statusPill")
        top_bar_layout.addWidget(status_pill)

        main_panel_layout.addWidget(top_bar)

        self.chat_view = QTextBrowser()
        self.chat_view.setObjectName("chatView")
        self.chat_view.setReadOnly(True)
        self.chat_view.setOpenExternalLinks(False)
        main_panel_layout.addWidget(self.chat_view, 1)

        composer_row = QWidget()
        composer_layout = QHBoxLayout(composer_row)
        composer_layout.setContentsMargins(0, 0, 0, 0)
        composer_layout.setSpacing(10)

        self.input = InputField()
        self.input.setObjectName("composer")
        composer_layout.addWidget(self.input, 1)

        aux_button = QPushButton("Attach")
        aux_button.setObjectName("auxButton")
        composer_layout.addWidget(aux_button)

        send_button = QPushButton("Send")
        send_button.setObjectName("sendButton")
        composer_layout.addWidget(send_button)

        main_panel_layout.addWidget(composer_row)

        root_layout.addWidget(sidebar, 1)
        root_layout.addWidget(main_panel, 4)

        self.setCentralWidget(main_widget)
        self.statusBar().showMessage("Model ready · 12.1 tok/s")

        send_button.clicked.connect(self.send_message)
        new_chat.clicked.connect(self.new_chat)

        QShortcut(QKeySequence("Ctrl+N"), self, self.new_chat)
        QShortcut(QKeySequence("Ctrl+Comma"), self, self.show_status)
        QShortcut(QKeySequence("Escape"), self, self.stop_streaming)

    def _load_demo_data(self):
        entries = [
            ("GPU triage", "three hidden bottlenecks in the render pass"),
            ("LLM notes", "prototype memory-safe attention paths"),
            ("Server logs", "watching llama.cpp begin a clean startup")
        ]
        for title, preview in entries:
            item = QListWidgetItem(title)
            item.setToolTip(preview)
            self.chat_list.addItem(item)

        self.chat_view.setHtml(
            textwrap.dedent(
                """
                <div class='msg assistant'>
                    <div class='meta'>Local AI</div>
                    <div class='bubble'>
                        Offline model ready.<br><br>
                        I can help you inspect prompt routing, memory pressure, GPU offload, or the next code patch.
                    </div>
                </div>
                """
            )
        )

    def new_chat(self):
        self.chat_view.clear()
        self.input.clear()
        self.chat_view.setHtml(
            textwrap.dedent(
                """
                <div class='msg assistant'>
                    <div class='meta'>Local AI</div>
                    <div class='bubble'>New workspace ready. Ask for a patch, a design note, or an architecture review.</div>
                </div>
                """
            )
        )
        self.statusBar().showMessage("Fresh session started")

    def stop_streaming(self):
        self.statusBar().showMessage("Streaming stopped")

    def show_status(self):
        self.statusBar().showMessage("Settings panel pending for the next milestone")

    def send_message(self):
        message = self.input.toPlainText().strip()
        if not message:
            return

        prompt = message.replace("<", "&lt;").replace(">", "&gt;")
        self.input.clear()

        self.chat_view.append(
            textwrap.dedent(
                f"""
                <div class='msg user'>
                    <div class='meta'>You</div>
                    <div class='bubble'>{prompt}</div>
                </div>
                """
            )
        )

        response = """
        I am running locally and keeping your workflow offline. For a dev AI loop, I would inspect the bottleneck, map the relevant files, and validate the smallest safe patch before any risky change.
        """.strip()

        self.chat_view.append(
            textwrap.dedent(
                f"""
                <div class='msg assistant'>
                    <div class='meta'>Local AI</div>
                    <div class='bubble'>{response}</div>
                </div>
                """
            )
        )
        self.chat_view.verticalScrollBar().setValue(self.chat_view.verticalScrollBar().maximum())
        self.statusBar().showMessage("Response generated locally · 12.7 tok/s")


def main() -> None:
    app = QApplication([])
    app.setApplicationName("LocalChat")
    app.setApplicationDisplayName("LocalChat")
    app.setQuitOnLastWindowClosed(True)

    window = MainWindow()
    window.show()

    timer = QTimer(window)
    timer.timeout.connect(lambda: None)
    timer.start(100)

    app.exec()
