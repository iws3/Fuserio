import html
import os
import re
import secrets
import socket
import threading
import time

import requests

from PySide6.QtCore import QProcess, QProcessEnvironment, Qt, QThread, QTimer, Signal
from PySide6.QtGui import QIcon, QKeySequence, QPixmap, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QTextBrowser,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtGui import QTextDocument

from localchat.client import stream_chat
from localchat.gce import (
    LEARNING_MODES,
    STREAMS,
    SUBJECTS,
    build_tutor_system_prompt,
    load_progress,
    save_progress,
    suggested_topic_areas,
)
from localchat.models import MODEL_OPTIONS, model_option


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

    #studyCard {
        background: rgba(7, 31, 26, 0.92);
        border: 1px solid rgba(75, 186, 153, 0.42);
        border-radius: 10px;
        color: #e4fff2;
        padding: 18px;
        min-height: 74px;
        text-align: left;
        font-size: 15px;
        font-weight: 700;
    }

    #studyCard:hover {
        background: rgba(14, 58, 45, 0.98);
        border-color: #69efb5;
    }

    #studyModeButton {
        background: rgba(10, 39, 32, 0.9);
        border: 1px solid rgba(75, 186, 153, 0.4);
        border-radius: 8px;
        color: #baf3d4;
        padding: 8px 12px;
        font-size: 11px;
        font-weight: 700;
    }

    #studyModeButton:hover {
        background: rgba(17, 74, 54, 0.98);
        border-color: #69efb5;
        color: #effff7;
    }

    #studyHeading {
        color: #e6fff3;
        font-size: 24px;
        font-weight: 800;
    }

    #studySubheading {
        color: #90b8a7;
        font-size: 12px;
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

    #modelBar {
        background: rgba(5, 24, 21, 0.72);
        border: 1px solid rgba(64, 208, 176, 0.22);
        border-radius: 10px;
        padding: 6px 10px;
    }

    #modelEyebrow {
        color: #70bea3;
        font-size: 9px;
        font-weight: 800;
    }

    #modelDetail {
        color: #90b8a7;
        font-size: 10px;
    }

    #modelReconnectButton {
        background: rgba(11, 48, 39, 0.9);
        border: 1px solid rgba(83, 200, 171, 0.36);
        border-radius: 8px;
        color: #b7efd9;
        padding: 8px 11px;
        font-size: 10px;
        font-weight: 700;
    }

    #modelReconnectButton:hover {
        background: rgba(16, 68, 53, 0.96);
        border-color: #69efb5;
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

    def __init__(
        self,
        base_url: str,
        api_key: str,
        messages: list[dict[str, str]],
        parameters: dict[str, object] | None = None,
    ):
        super().__init__()
        self.base_url = base_url
        self.api_key = api_key
        self.messages = messages
        self.parameters = parameters or {}
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
                parameters=self.parameters,
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
        self.progress = load_progress()
        self.gce_level = ""
        self.gce_stream = ""
        self.gce_subject = ""
        self.gce_system_prompt = ""
        self.gce_modes = []
        self.gce_screen = "chat"
        self.gce_pages: dict[str, QWidget] = {}
        self.progress_save_timer = QTimer(self)
        self.progress_save_timer.setSingleShot(True)
        self.progress_save_timer.timeout.connect(self._save_progress)
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
        self._restore_gce_selection()
        self.existing_server_probe = ExistingServerProbe("http://127.0.0.1:8081")
        self.existing_server_probe.found.connect(self._existing_server_found)
        self.existing_server_probe.failed.connect(self._existing_server_missing)
        self.existing_server_probe.start()

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

        self.back_button = QPushButton("← Back")
        self.back_button.setObjectName("newChatButton")
        self.back_button.hide()
        self.back_button.clicked.connect(self.gce_back)
        header_layout.addWidget(self.back_button)

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

        self.content_stack = QStackedWidget()
        main_layout.addWidget(self.content_stack, 1)

        self._build_chat_page()
        self._build_gce_pages()

        self.gce_study_button = QPushButton("GCE Study")
        self.gce_study_button.setText("GCE Learning")
        self.gce_study_button.setObjectName("newChatButton")
        self.gce_study_button.setAccessibleName("Open GCE level and subject selection")
        side_layout.insertWidget(1, self.gce_study_button)
        self.gce_study_button.clicked.connect(self.open_gce_levels)

        self.ai_workspace_button = QPushButton("AI Workspace")
        self.ai_workspace_button.setObjectName("newChatButton")
        self.ai_workspace_button.setAccessibleName("Open general AI chat workspace")
        side_layout.insertWidget(2, self.ai_workspace_button)
        self.ai_workspace_button.clicked.connect(self.open_ai_workspace)

        outer.addWidget(sidebar, 1)
        outer.addWidget(main_panel, 5)

        self.setCentralWidget(root)
        self.content_stack.setCurrentWidget(self.level_page)
        self.gce_screen = "level"
        self.back_button.hide()
        self.statusBar().showMessage("Connecting to local model...")
        new_chat.clicked.connect(self.new_chat)
        QShortcut(QKeySequence("Ctrl+N"), self, self.new_chat)
        QShortcut(QKeySequence("Ctrl+Comma"), self, self.show_status)
        QShortcut(QKeySequence("Escape"), self, self.stop_streaming)

    def _build_chat_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.study_context_label = QLabel("")
        self.study_context_label.setObjectName("studySubheading")
        self.study_context_label.hide()
        layout.addWidget(self.study_context_label)

        self.chat_view = QTextBrowser()
        self.chat_view.setObjectName("chatView")
        self.chat_view.setReadOnly(True)
        self.chat_view.setOpenExternalLinks(False)
        layout.addWidget(self.chat_view, 1)

        self.mode_bar = QWidget()
        mode_layout = QHBoxLayout(self.mode_bar)
        mode_layout.setContentsMargins(0, 0, 0, 0)
        mode_layout.setSpacing(8)
        self.mode_buttons = []
        for mode in LEARNING_MODES:
            button = QPushButton(mode)
            button.setObjectName("studyModeButton")
            button.clicked.connect(lambda _checked=False, selected=mode: self.start_learning_mode(selected))
            mode_layout.addWidget(button)
            self.mode_buttons.append(button)
        self.mode_bar.hide()
        layout.addWidget(self.mode_bar)

        model_bar = QWidget()
        model_bar.setObjectName("modelBar")
        model_layout = QHBoxLayout(model_bar)
        model_layout.setContentsMargins(8, 4, 8, 4)
        model_layout.setSpacing(10)

        model_eyebrow = QLabel("LOCAL MODEL")
        model_eyebrow.setObjectName("modelEyebrow")
        model_layout.addWidget(model_eyebrow)

        self.model_selector = QComboBox()
        self.model_selector.setObjectName("modelSelector")
        self.model_selector.setAccessibleName("Choose a local language model")
        self.model_selector.setMinimumWidth(210)
        for option in MODEL_OPTIONS:
            self.model_selector.addItem(option.name, option.model_id)
            self.model_selector.setItemData(
                self.model_selector.count() - 1,
                f"{option.description} · {option.quantization}",
                Qt.ToolTipRole,
            )
        model_layout.addWidget(self.model_selector)

        self.model_detail = QLabel("")
        self.model_detail.setObjectName("modelDetail")
        model_layout.addWidget(self.model_detail, 1)

        self.model_reconnect_button = QPushButton("Connect")
        self.model_reconnect_button.setObjectName("modelReconnectButton")
        self.model_reconnect_button.setToolTip("Connect or restart the selected local model")
        model_layout.addWidget(self.model_reconnect_button)
        self._update_model_detail()
        layout.addWidget(model_bar)

        composer = QWidget()
        composer_layout = QHBoxLayout(composer)
        composer_layout.setContentsMargins(0, 0, 0, 0)
        composer_layout.setSpacing(12)

        self.input = InputField()
        self.input.setObjectName("composer")
        composer_layout.addWidget(self.input, 1)

        self.send_button = QPushButton("Send")
        self.send_button.setObjectName("sendButton")
        self.send_button.setEnabled(False)
        composer_layout.addWidget(self.send_button)
        self.send_button.clicked.connect(self._send_or_stop)
        self.model_selector.currentIndexChanged.connect(self._model_selected)
        self.model_reconnect_button.clicked.connect(self._retry_selected_model)
        layout.addWidget(composer)

        self.chat_page = page
        self.content_stack.addWidget(page)
        self.gce_pages["chat"] = page

    def _build_gce_pages(self):
        self.level_page = self._selection_page(
            "Choose your GCE level",
            "Select the exam level you are preparing for.",
        )
        level_layout = self.level_page.layout()
        start_logo = QLabel()
        start_logo.setObjectName("startLogo")
        start_logo.setAlignment(Qt.AlignCenter)
        start_logo.setPixmap(
            QPixmap(self.logo_path).scaled(
                72,
                72,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
        )
        level_layout.addWidget(start_logo)
        level_grid = QGridLayout()
        level_grid.setSpacing(14)
        for column, level in enumerate(("Ordinary Level", "Advanced Level")):
            button = self._study_card(level, "O Level" if column == 0 else "A Level")
            button.clicked.connect(lambda _checked=False, value=level: self.select_gce_level(value))
            level_grid.addWidget(button, 0, column)
        level_layout.addLayout(level_grid)
        level_layout.addStretch(1)
        self.content_stack.addWidget(self.level_page)
        self.gce_pages["level"] = self.level_page

        self.stream_page = self._selection_page(
            "Choose your stream",
            "Pick the subject group for your selected level.",
        )
        stream_grid = QGridLayout()
        stream_grid.setSpacing(14)
        self.stream_card_buttons = {}
        for index, stream in enumerate(STREAMS):
            button = self._study_card(stream, f"{len(SUBJECTS['Ordinary Level'][stream])} O Level subjects")
            self.stream_card_buttons[stream] = button
            button.clicked.connect(lambda _checked=False, value=stream: self.select_gce_stream(value))
            stream_grid.addWidget(button, index // 2, index % 2)
        self.stream_page.layout().addLayout(stream_grid)
        self.stream_page.layout().addStretch(1)
        self.content_stack.addWidget(self.stream_page)
        self.gce_pages["stream"] = self.stream_page

        self.subject_page = self._selection_page(
            "Choose a subject",
            "Select a subject to open its AI tutor session.",
        )
        self.subject_grid_container = QWidget()
        self.subject_grid = QGridLayout(self.subject_grid_container)
        self.subject_grid.setContentsMargins(0, 0, 0, 0)
        self.subject_grid.setSpacing(10)
        subject_scroll = QScrollArea()
        subject_scroll.setWidgetResizable(True)
        subject_scroll.setFrameShape(QScrollArea.NoFrame)
        subject_scroll.setWidget(self.subject_grid_container)
        self.subject_page.layout().addWidget(subject_scroll, 1)
        self.content_stack.addWidget(self.subject_page)
        self.gce_pages["subjects"] = self.subject_page

    def _selection_page(self, heading: str, subheading: str) -> QWidget:
        page = QWidget()
        page.setObjectName("selectionPage")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(14)
        title = QLabel(heading)
        title.setObjectName("studyHeading")
        subtitle = QLabel(subheading)
        subtitle.setObjectName("studySubheading")
        layout.addWidget(title)
        layout.addWidget(subtitle)
        return page

    @staticmethod
    def _study_card(title: str, detail: str) -> QPushButton:
        button = QPushButton(f"{title}\n{detail}")
        button.setObjectName("studyCard")
        button.setMinimumHeight(96)
        return button

    def open_gce_levels(self):
        selection = self.progress.get("selection", {})
        level = selection.get("level", "")
        stream = selection.get("stream", "")
        subject = selection.get("subject", "")
        if subject in SUBJECTS.get(level, {}).get(stream, []):
            self.gce_level = level
            self.gce_stream = stream
            self._populate_subjects()
            self.open_gce_subject(subject)
            return
        self.gce_screen = "level"
        self.back_button.show()
        self.content_stack.setCurrentWidget(self.level_page)
        self._save_selection()

    def open_ai_workspace(self):
        self.gce_level = ""
        self.gce_stream = ""
        self.gce_subject = ""
        self.gce_system_prompt = ""
        self.gce_modes = []
        self.gce_screen = "chat"
        self.study_context_label.hide()
        self.mode_bar.hide()
        self.back_button.hide()
        self.content_stack.setCurrentWidget(self.chat_page)
        self._render_messages()

    def _restore_gce_selection(self):
        selection = self.progress.get("selection", {})
        level = selection.get("level", "")
        stream = selection.get("stream", "")
        subject = selection.get("subject", "")
        if subject not in SUBJECTS.get(level, {}).get(stream, []):
            return
        self.gce_level = level
        self.gce_stream = stream
        self.gce_subject = subject
        self._populate_subjects()

    def select_gce_level(self, level: str):
        self.gce_level = level
        for stream, button in self.stream_card_buttons.items():
            count = len(SUBJECTS[level][stream])
            button.setText(f"{stream}\n{count} subjects")
        self.gce_screen = "stream"
        self.content_stack.setCurrentWidget(self.stream_page)
        self._save_selection()

    def select_gce_stream(self, stream: str):
        if not self.gce_level:
            self.open_gce_levels()
            return
        self.gce_stream = stream
        self._populate_subjects()
        self.gce_screen = "subjects"
        self.content_stack.setCurrentWidget(self.subject_page)
        self._save_selection()

    def _populate_subjects(self):
        while self.subject_grid.count():
            item = self.subject_grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        subjects = SUBJECTS.get(self.gce_level, {}).get(self.gce_stream, [])
        for index, subject in enumerate(subjects):
            button = self._study_card(subject, "OPEN SUBJECT TUTOR  →")
            button.clicked.connect(lambda _checked=False, value=subject: self.open_gce_subject(value))
            self.subject_grid.addWidget(button, index // 3, index % 3)

    def open_gce_subject(self, subject: str):
        if subject not in SUBJECTS.get(self.gce_level, {}).get(self.gce_stream, []):
            return
        self.gce_subject = subject
        self.gce_system_prompt = build_tutor_system_prompt(
            self.gce_level,
            self.gce_stream,
            self.gce_subject,
        )
        saved_session = self.progress.get("sessions", {}).get(self._session_key(), {})
        saved_messages = saved_session.get("messages", [])
        if isinstance(saved_messages, list) and any(
            isinstance(item, dict) and item.get("content") for item in saved_messages
        ):
            self.messages = saved_messages
            self.gce_modes = saved_session.get("modes", [])
        else:
            self.gce_modes = []
            self.messages = [{"role": "assistant", "content": "", "reasoning": ""}]
        self.study_context_label.setText(
            f"CAMEROON GCE  /  {self.gce_level.upper()}  /  {self.gce_stream.upper()}  /  {subject.upper()}\n"
            "Suggested topic areas are a study scaffold, not a verified or exhaustive official syllabus."
        )
        self.study_context_label.show()
        self.mode_bar.show()
        self.back_button.show()
        self.gce_screen = "chat"
        self.content_stack.setCurrentWidget(self.chat_page)
        self._save_selection()
        self._save_progress()
        self._render_messages()
        if not saved_messages:
            self._request_tutor_greeting()

    def _request_tutor_greeting(self):
        if not self.base_url:
            self.statusBar().showMessage("Subject selected. Waiting for the local model to connect.")
            return
        self.send_button.setEnabled(False)
        self.statusBar().showMessage("Preparing your subject tutor...")
        self._start_chat_request([
            {"role": "system", "content": self.gce_system_prompt},
            {
                "role": "user",
                "content": "Give me a short greeting. Then show the suggested study-area label and menu from your instructions, followed by all four study modes. Keep it under 170 words.",
            },
        ], parameters={"max_tokens": 640, "temperature": 0.3})

    def gce_back(self):
        if self.gce_screen == "chat":
            self.gce_screen = "subjects"
            self.content_stack.setCurrentWidget(self.subject_page)
            self.mode_bar.hide()
            self.study_context_label.hide()
            self.back_button.show()
            return
        if self.gce_screen == "subjects":
            self.gce_screen = "stream"
            self.content_stack.setCurrentWidget(self.stream_page)
            return
        if self.gce_screen == "stream":
            self.gce_screen = "level"
            self.content_stack.setCurrentWidget(self.level_page)
            return
        self.gce_screen = "chat"
        self.content_stack.setCurrentWidget(self.chat_page)
        self.back_button.hide()

    def start_learning_mode(self, mode: str):
        if mode not in LEARNING_MODES or not self.gce_subject:
            return
        if not self.base_url or (self.chat_worker and self.chat_worker.isRunning()):
            self.statusBar().showMessage("Wait for the local model to be ready before starting a study activity.")
            return
        self.gce_modes.append({"mode": mode, "time": int(time.time())})
        self._schedule_progress_save()
        mode_prompts = {
            "Lesson": f"Start a clear, step-by-step lesson in {self.gce_subject}. Show the suggested study-topic menu as a non-official scaffold, then ask me to choose a topic.",
            "Practice": f"Give me one {self.gce_subject} practice question at {self.gce_level} level. Wait for my attempt, then mark it and give a full model answer.",
            "Past-paper quiz": f"Give me one original past-paper-style {self.gce_subject} quiz question at {self.gce_level} level. Do not claim it is an official past-paper question. Wait for my answer, then mark it using a clear mark scheme and model answer.",
            "Ask a question": "Invite me to type my question. Answer only within my selected subject and level.",
        }
        display_text = {
            "Lesson": "Start a lesson",
            "Practice": "Start a practice question",
            "Past-paper quiz": "Start a past-paper-style quiz",
            "Ask a question": "I would like to ask a question",
        }[mode]
        self._submit_tutor_turn(mode_prompts[mode], display_text)

    def _session_key(self) -> str:
        return "|".join((self.gce_level, self.gce_stream, self.gce_subject))

    def _save_selection(self):
        self.progress["selection"] = {
            "level": self.gce_level,
            "stream": self.gce_stream,
            "subject": self.gce_subject,
        }
        self._schedule_progress_save()

    def _schedule_progress_save(self):
        self.progress_save_timer.start(300)

    def _save_progress(self):
        if self.gce_subject and self.messages:
            self.progress.setdefault("sessions", {})[self._session_key()] = {
                "updated": int(time.time()),
                "messages": self.messages,
                "modes": self.gce_modes,
            }
        try:
            save_progress(self.progress)
        except OSError as error:
            self.statusBar().showMessage(f"Could not save local study progress: {error}")

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
        self._submit_tutor_turn(message, message)

    def _send_or_stop(self):
        if self.chat_worker and self.chat_worker.isRunning():
            self.stop_streaming()
        else:
            self.send_message()

    def _model_selected(self):
        self.generation += 1
        model_id = self.model_selector.currentData()
        self._update_model_detail()
        self.base_url = ""
        self.api_key = ""
        self.active_model = ""
        self.send_button.setEnabled(False)
        self.model_reconnect_button.setText("Loading…")
        self.model_reconnect_button.setEnabled(False)
        self.connection_status.setText("LOADING")
        self.model_info.setText(f"Model: {self.model_selector.currentText()}")
        self.statusBar().showMessage("Loading selected local model...")
        if self.chat_worker and self.chat_worker.isRunning():
            self.pending_model_start = model_id
            self.stop_streaming()
            return
        self._prepare_model(model_id, self.generation)

    def _retry_selected_model(self):
        self.generation += 1
        self.base_url = ""
        self.api_key = ""
        self.active_model = ""
        self.send_button.setEnabled(False)
        self.model_reconnect_button.setText("Checking…")
        self.model_reconnect_button.setEnabled(False)
        self.connection_status.setText("CONNECTING")
        self.statusBar().showMessage("Checking for a local model server...")
        self.retry_probe = ExistingServerProbe("http://127.0.0.1:8081")
        self.retry_probe.found.connect(self._retry_server_found)
        self.retry_probe.failed.connect(self._retry_server_missing)
        self.retry_probe.start()

    def _retry_server_found(self, base_url: str, model_id: str):
        selected_model = self.model_selector.currentData()
        if model_id.lower() == selected_model.lower():
            self.external_server = (base_url, model_id)
            self._connect_model(base_url, "", model_id, self.generation)
            return
        self._start_model(selected_model, self.generation)

    def _retry_server_missing(self):
        self._start_model(self.model_selector.currentData(), self.generation)

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
        self.model_reconnect_button.setText("Loading…")
        self.model_reconnect_button.setEnabled(False)
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
            self.model_reconnect_button.setText("Retry")
            self.model_reconnect_button.setEnabled(True)
            self.statusBar().showMessage("The model server stopped.")

    def _server_ready(self, generation: int, base_url: str, api_key: str, model_id: str):
        self._connect_model(base_url, api_key, model_id, generation)

    def _connect_model(self, base_url: str, api_key: str, model_id: str, generation: int):
        if generation != self.generation:
            return
        self.base_url = base_url
        self.api_key = api_key
        self.active_model = model_id
        option = model_option(model_id)
        label = option.name if option else model_id
        self.model_info.setText(f"Model: {label}")
        if option:
            self.model_detail.setText(f"{option.description}  ·  {option.quantization}  ·  local only")
        self.model_reconnect_button.setText("Connected")
        self.model_reconnect_button.setEnabled(False)
        self.connection_status.setText("READY")
        self.send_button.setEnabled(True)
        self.statusBar().showMessage("Local model ready. Your messages stay on this computer.")
        if (
            self.gce_subject
            and len(self.messages) == 1
            and self.messages[0]["role"] == "assistant"
            and not self.messages[0].get("content")
            and not (self.chat_worker and self.chat_worker.isRunning())
        ):
            QTimer.singleShot(0, self._request_tutor_greeting)

    def _model_error(self, generation: int, message: str):
        if generation != self.generation:
            return
        detail = self.server_output[-1200:].strip()
        self.base_url = ""
        self.connection_status.setText("ERROR")
        self.send_button.setEnabled(False)
        self.model_reconnect_button.setText("Retry")
        self.model_reconnect_button.setEnabled(True)
        self.statusBar().showMessage(message + (f" Check llama-server output: {detail}" if detail else ""))

    def _update_model_detail(self):
        option = model_option(self.model_selector.currentData() or "")
        if option:
            self.model_detail.setText(f"{option.description}  ·  {option.quantization}  ·  local only")
        else:
            self.model_detail.setText("Local model")

    def _append_stream_chunk(self, reasoning: str, content: str):
        if not self.messages:
            return
        self.messages[-1]["reasoning"] += reasoning
        self.messages[-1]["content"] += content
        self._render_messages()
        self._schedule_progress_save()

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
        self._save_progress()

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

    def _submit_tutor_turn(self, model_prompt: str, display_text: str):
        if not self.base_url or (self.chat_worker and self.chat_worker.isRunning()):
            self.statusBar().showMessage("Wait for the local model to be ready before starting a study activity.")
            return
        self.messages.append({"role": "user", "content": display_text})
        self.messages.append({"role": "assistant", "content": "", "reasoning": ""})
        api_messages = [
            {"role": item["role"], "content": item["content"]}
            for item in self.messages[:-1]
        ]
        api_messages[-1]["content"] = model_prompt
        if self.gce_system_prompt:
            api_messages.insert(0, {"role": "system", "content": self.gce_system_prompt})
        self._render_messages()
        self._schedule_progress_save()
        self._start_chat_request(api_messages)

    def _start_chat_request(
        self,
        api_messages: list[dict[str, str]],
        parameters: dict[str, object] | None = None,
    ):
        if not self.base_url:
            self.statusBar().showMessage("Connect a local model before chatting.")
            return
        self.send_button.setText("Stop")
        self.send_button.setEnabled(True)
        self.statusBar().showMessage("Generating locally...")
        self.chat_worker = ChatWorker(self.base_url, self.api_key, api_messages, parameters)
        self.chat_worker.chunk.connect(self._append_stream_chunk)
        self.chat_worker.error.connect(self._chat_error)
        self.chat_worker.finished.connect(self._chat_finished)
        self.chat_worker.start()

    @staticmethod
    def _format_message_content(content: str) -> str:
        code_fragments: list[tuple[str, str]] = []

        def preserve_code(match: re.Match[str]) -> str:
            token = match.group(0)
            placeholder = f"FUSERIOCODETOKEN{len(code_fragments)}END"
            if token.startswith("```"):
                code_lines = token[3:-3].split("\n", 1)
                language = code_lines[0].strip()
                code = code_lines[1] if len(code_lines) > 1 else code_lines[0]
                language_label = html.escape(language.upper() or "CODE")
                rendered_code = (
                    '<table width="100%" cellspacing="0" cellpadding="0" bgcolor="#050d0c" '
                    'border="1" bordercolor="#254239"><tr><td style="padding:8px 12px;">'
                    f'<div style="color:#69d9a8;font-size:9px;">{language_label} / CODE BLOCK</div>'
                    f'<pre style="color:#d8eee3;font-family:monospace;white-space:pre-wrap;">'
                    f'{html.escape(code)}</pre></td></tr></table>'
                )
            else:
                rendered_code = (
                    '<code style="color:#9ee7bf;background-color:#13261f;">'
                    f'{html.escape(token[1:-1])}</code>'
                )
            code_fragments.append((placeholder, rendered_code))
            return placeholder

        markdown_source = re.sub(r"```[\s\S]*?```|`[^`\n]*`", preserve_code, content)
        math_fragments: list[tuple[str, bool]] = []
        math_pattern = re.compile(
            r"\\\[[\s\S]*?\\\]|"
            r"\\\([\s\S]*?\\\)|\$\$[\s\S]*?\$\$|(?<!\\)\$(?!\$)[^\n$]+(?<!\\)\$"
        )

        def preserve_math(match: re.Match[str]) -> str:
            token = match.group(0)
            if token.startswith("\\["):
                expression, display = token[2:-2], True
            elif token.startswith("\\("):
                expression, display = token[2:-2], False
            elif token.startswith("$$"):
                expression, display = token[2:-2], True
            else:
                expression, display = token[1:-1], False
            placeholder = f"FUSERIOMATHTOKEN{len(math_fragments)}END"
            math_fragments.append((placeholder, MainWindow._render_latex(expression, display)))
            return placeholder

        markdown_source = math_pattern.sub(preserve_math, markdown_source)
        markdown_source = markdown_source.replace("&", "&amp;")
        markdown_source = re.sub(
            r"<(/?[A-Za-z][^<>]*)>",
            lambda match: f"&lt;{match.group(1)}&gt;",
            markdown_source,
        )
        document = QTextDocument()
        document.setMarkdown(markdown_source)
        rendered = document.toHtml()
        body_match = re.search(r"(?is)<body[^>]*>(.*?)</body>", rendered)
        body = body_match.group(1) if body_match else rendered
        for placeholder, math_html in math_fragments:
            body = body.replace(placeholder, math_html)
        for placeholder, code_html in code_fragments:
            body = body.replace(placeholder, code_html)
        return body

    @staticmethod
    def _render_latex(expression: str, display: bool = False) -> str:
        symbols = {
            "alpha": "α", "beta": "β", "gamma": "γ", "delta": "δ",
            "epsilon": "ε", "theta": "θ", "lambda": "λ", "mu": "μ",
            "pi": "π", "rho": "ρ", "sigma": "σ", "phi": "φ",
            "omega": "ω", "Gamma": "Γ", "Delta": "Δ", "Theta": "Θ",
            "Lambda": "Λ", "Pi": "Π", "Sigma": "Σ", "Phi": "Φ", "Omega": "Ω",
            "times": "×", "cdot": "·", "div": "÷", "pm": "±", "mp": "∓",
            "le": "≤", "leq": "≤", "ge": "≥", "geq": "≥", "ne": "≠",
            "neq": "≠", "approx": "≈", "infty": "∞", "rightarrow": "→",
            "to": "→", "pi": "π", "degree": "°", "partial": "∂",
            "nabla": "∇", "sum": "∑", "prod": "∏", "int": "∫",
            "sqrt": "√", "therefore": "∴", "because": "∵", "perp": "⊥",
            "parallel": "∥", "angle": "∠", "Delta": "Δ", "emptyset": "∅",
        }

        def read_argument(source: str, start: int) -> tuple[str, int]:
            while start < len(source) and source[start].isspace():
                start += 1
            if start >= len(source):
                return "", start
            if source[start] != "{":
                if source[start] == "\\":
                    command = re.match(r"\\[A-Za-z]+|\\.", source[start:])
                    if command:
                        return command.group(0), start + len(command.group(0))
                return source[start], start + 1
            depth = 1
            index = start + 1
            while index < len(source) and depth:
                if source[index] == "\\":
                    index += 2
                    continue
                if source[index] == "{":
                    depth += 1
                elif source[index] == "}":
                    depth -= 1
                index += 1
            return source[start + 1:index - 1], index

        def render(source: str) -> str:
            output: list[str] = []
            index = 0
            while index < len(source):
                char = source[index]
                if char == "\\":
                    command_match = re.match(r"\\([A-Za-z]+|.)", source[index:])
                    if not command_match:
                        output.append("\\")
                        index += 1
                        continue
                    command = command_match.group(1)
                    index += len(command_match.group(0))
                    if command in {"frac", "dfrac", "tfrac"}:
                        numerator, index = read_argument(source, index)
                        denominator, index = read_argument(source, index)
                        output.append(
                            '<span style="white-space:nowrap;vertical-align:middle;">'
                            f'<sup>{render(numerator)}</sup>⁄<sub>{render(denominator)}</sub></span>'
                        )
                    elif command == "sqrt":
                        radicand, index = read_argument(source, index)
                        output.append(f'√<span style="text-decoration:overline;">{render(radicand)}</span>')
                    elif command in {"text", "mathrm", "mathbf", "mathit", "operatorname"}:
                        text_value, index = read_argument(source, index)
                        output.append(html.escape(text_value))
                    elif command == "left" or command == "right":
                        continue
                    elif command in symbols:
                        output.append(symbols[command])
                    elif command in {"{", "}", "\\", "%", "_", "&"}:
                        output.append(html.escape(command))
                    else:
                        output.append(html.escape(command))
                    continue
                if char in {"^", "_"}:
                    argument, index = read_argument(source, index + 1)
                    tag = "sup" if char == "^" else "sub"
                    output.append(f"<{tag}>{render(argument)}</{tag}>")
                    continue
                if char in "{}":
                    index += 1
                    continue
                output.append(html.escape(char))
                index += 1
            return "".join(output)

        expression_html = render(expression.strip())
        if display:
            return (
                '<span style="color:#d8eee3;background-color:#07120f;'
                'font-family:serif;font-size:18px;">'
                f"　{expression_html}　</span>"
            )
        return (
            '<span style="color:#dcf7e9;font-family:serif;font-size:15px;">'
            f"{expression_html}</span>"
        )

    def closeEvent(self, event):
        self.progress_save_timer.stop()
        self._save_progress()
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
