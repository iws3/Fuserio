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

    .message {
        margin: 10px 0;
        padding: 14px 16px;
        border-radius: 14px;
        border: 1px solid rgba(101, 230, 197, 0.15);
    }

    .user-message {
        background: rgba(15, 46, 42, 0.72);
        margin-left: 92px;
    }

    .assistant-message {
        background: rgba(6, 26, 22, 0.9);
        margin-right: 92px;
    }

    .label {
        color: #8ef5d2;
        font-size: 10px;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        margin-bottom: 8px;
    }

    .body {
        color: #eafef6;
    }

    #composer {
        background: rgba(7, 23, 20, 0.9);
        border: 1px solid rgba(83, 200, 171, 0.38);
        border-radius: 12px;
        color: #ebfff8;
        padding: 14px 16px;
        font-size: 14px;
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
            self.parent().send_message()
            return
        super().keyPressEvent(event)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fuserio")
        self.resize(1440, 900)
        self.setStyleSheet(build_stylesheet())
        self._build_ui()
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
        header_layout.addWidget(brand)
        header_layout.addStretch()

        model_info = QLabel("Model: Qwen2.5-3B | Persona: general")
        model_info.setObjectName("modelInfo")
        header_layout.addWidget(model_info)

        status = QLabel("offline")
        status.setObjectName("statPill")
        header_layout.addWidget(status)

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

        attach = QPushButton("Attach")
        attach.setObjectName("attachButton")
        composer_layout.addWidget(attach)

        send = QPushButton("Send")
        send.setObjectName("sendButton")
        composer_layout.addWidget(send)

        main_layout.addWidget(composer)

        outer.addWidget(sidebar, 1)
        outer.addWidget(main_panel, 5)

        self.setCentralWidget(root)
        self.statusBar().showMessage("Fresh session started")

        send.clicked.connect(self.send_message)
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

        self.chat_view.setHtml(
            textwrap.dedent(
                """
                <div class="message assistant-message">
                    <div class="label">Local AI</div>
                    <div class="body">New workspace ready. Ask for a patch, a design note, or an architecture review.</div>
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
                <div class="message assistant-message">
                    <div class="label">Local AI</div>
                    <div class="body">New workspace ready. Ask for a patch, a design note, or an architecture review.</div>
                </div>
                """
            )
        )
        self.statusBar().showMessage("Fresh session started")

    def stop_streaming(self):
        self.statusBar().showMessage("Streaming stopped")

    def show_status(self):
        self.statusBar().showMessage("Settings panel pending")

    def send_message(self):
        message = self.input.toPlainText().strip()
        if not message:
            return

        prompt = message.replace("<", "&lt;").replace(">", "&gt;")
        self.input.clear()

        self.chat_view.append(
            textwrap.dedent(
                f"""
                <div class="message user-message">
                    <div class="label">You</div>
                    <div class="body">{prompt}</div>
                </div>
                """
            )
        )

        response = (
            "I am running locally and keeping your workflow offline. "
            "For a focused dev loop, I would inspect the bottleneck, map the relevant files, "
            "and validate the smallest safe patch before any risky change."
        )

        self.chat_view.append(
            textwrap.dedent(
                f"""
                <div class="message assistant-message">
                    <div class="label">Local AI</div>
                    <div class="body">{response}</div>
                </div>
                """
            )
        )

        self.chat_view.verticalScrollBar().setValue(self.chat_view.verticalScrollBar().maximum())
        self.statusBar().showMessage("Response generated locally · 12.7 tok/s")


def main() -> None:
    app = QApplication([])
    app.setApplicationName("Fuserio")
    app.setApplicationDisplayName("Fuserio")
    app.setStyle("Fusion")
    app.setQuitOnLastWindowClosed(True)

    window = MainWindow()
    window.show()

    timer = QTimer(window)
    timer.timeout.connect(lambda: None)
    timer.start(100)

    app.exec()
