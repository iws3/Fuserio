import html
import os
import re
import secrets
import socket
import threading
import time
import unicodedata

import requests

from PySide6.QtCore import QEvent, QEasingCurve, QProcess, QProcessEnvironment, QPropertyAnimation, Qt, QThread, QTimer, Signal
from PySide6.QtGui import QColor, QIcon, QKeySequence, QPainter, QPen, QPixmap, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QBoxLayout,
    QComboBox,
    QDoubleSpinBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QLineEdit,
    QMenu,
    QPushButton,
    QSpinBox,
    QScrollArea,
    QSlider,
    QSizePolicy,
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
from localchat.lab_data import (
    SUBJECTS as LAB_SUBJECTS,
    experiment_by_id,
    experiments_for_subject,
    model_equation,
    model_limitation,
)
from localchat.lab_widgets import LabCanvas
from localchat.chemistry_practicals import (
    CHEMISTRY,
    Experiment as PracticalExperiment,
    Level as ChemistryLevel,
    Topic as ChemistryTopic,
    experiment_by_route,
    level_by_slug,
)
from localchat.math_analysis import AnalysisResult, analyse_function, analyse_xy_data


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

    #windowControlButton {
        background: rgba(9, 31, 28, 0.96);
        border: 1px solid rgba(89, 201, 178, 0.38);
        border-radius: 8px;
        color: #dffdf1;
        min-width: 28px;
        max-width: 28px;
        min-height: 28px;
        max-height: 28px;
        padding: 0;
        font-size: 14px;
        font-weight: 800;
    }

    #windowControlButton:hover {
        background: rgba(17, 69, 58, 0.98);
        border-color: rgba(137, 248, 206, 0.72);
        color: #ffffff;
    }

    #windowControlButton[variant="close"] {
        color: #ffb5ac;
    }

    #windowControlButton[variant="close"]:hover {
        background: rgba(220, 53, 69, 0.9);
        border-color: #ff6b6b;
        color: #ffffff;
    }

    #studyCard {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(8, 34, 28, 0.95), stop:1 rgba(11, 44, 36, 0.98));
        border: 1px solid rgba(75, 186, 153, 0.45);
        border-radius: 12px;
        color: #e4fff2;
        padding: 20px 22px;
        min-height: 80px;
        text-align: left;
        font-size: 15px;
        font-weight: 700;
    }

    #studyCard:hover {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(16, 64, 52, 0.98), stop:1 rgba(12, 54, 44, 0.98));
        border-color: #57fabc;
        color: #ffffff;
    }

    #studyModeButton {
        background: rgba(10, 39, 32, 0.9);
        border: 1px solid rgba(75, 186, 153, 0.45);
        border-radius: 8px;
        color: #baf3d4;
        padding: 8px 14px;
        font-size: 11px;
        font-weight: 700;
    }

    #studyModeButton:hover {
        background: rgba(18, 76, 58, 0.98);
        border-color: #57fabc;
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

    #sidebarSection {
        color: #5da98b;
        font-size: 9px;
        font-weight: 800;
        padding: 8px 3px 2px 3px;
    }

    #labNavButton {
        background: rgba(8, 33, 28, 0.88);
        border: 1px solid rgba(61, 133, 107, 0.3);
        border-radius: 8px;
        color: #a9cdbb;
        text-align: left;
        padding: 10px 12px;
        font-size: 11px;
        font-weight: 700;
    }

    #labNavButton:hover, #labNavButton:checked {
        background: rgba(15, 58, 44, 0.95);
        border-color: #58c999;
        color: #e7fff0;
    }

    #labSubjectButton {
        background: transparent;
        border: 1px solid transparent;
        border-radius: 7px;
        color: #8eaa9b;
        text-align: left;
        padding: 8px 12px;
        font-size: 11px;
    }

    #labSubjectButton:hover {
        background: rgba(11, 42, 34, 0.86);
        color: #d7f5e4;
    }

    #labMetric {
        background: #0a1a15;
        border: 1px solid #204837;
        border-radius: 8px;
        padding: 10px;
    }

    #labMetricName {
        color: #6fa88d;
        font-size: 9px;
        font-weight: 700;
    }

    #labMetricValue {
        color: #b7f4d0;
        font-size: 17px;
        font-weight: 800;
    }

    #labControlLabel {
        color: #d8eee2;
        font-size: 11px;
        font-weight: 700;
    }

    #labControlValue {
        color: #6fe4aa;
        font-size: 11px;
        font-weight: 700;
    }

    QSlider::groove:horizontal {
        height: 5px;
        background: #18372a;
        border-radius: 2px;
    }

    QSlider::sub-page:horizontal {
        background: #39a975;
        border-radius: 2px;
    }

    QSlider::handle:horizontal {
        width: 15px;
        margin: -6px 0;
        background: #b8f5d0;
        border: 2px solid #287b52;
        border-radius: 7px;
    }

    #labSafety {
        color: #ffce90;
        background: #211b11;
        border: 1px solid #65502d;
        border-radius: 8px;
        padding: 10px 12px;
    }

    #chemistryLevelButton, #chemistryTopicButton {
        background: transparent;
        border: 1px solid transparent;
        border-radius: 6px;
        color: #a5cabc;
        text-align: left;
        padding: 7px 8px;
        font-size: 10px;
    }

    #chemistryLevelButton:hover, #chemistryTopicButton:hover {
        background: rgba(36, 91, 73, 0.55);
        color: #effff7;
    }

    #chemistryLevelButton[active="true"], #chemistryTopicButton[active="true"] {
        background: rgba(25, 99, 72, 0.64);
        border-color: rgba(117, 239, 177, 0.45);
        color: #a8f4c9;
        font-weight: 700;
    }

    #chemistryTopicHeading {
        color: #e8fff2;
        font-size: 22px;
        font-weight: 800;
    }

    #practicalExperimentCard {
        background: #0c211b;
        border: 1px solid #285244;
        border-radius: 8px;
        color: #dff8eb;
        padding: 16px;
        text-align: left;
        font-size: 12px;
        min-height: 190px;
    }

    #practicalExperimentCard:hover {
        background: #123026;
        border-color: #69d7a4;
    }

    #practicalExperimentCard:pressed {
        background: #174131;
    }

    #practicalCardImage {
        background: #102b23;
        border: 1px dashed #477661;
        border-radius: 6px;
        color: #93cdb0;
        font-size: 10px;
        font-weight: 700;
    }

    #practicalCardTitle {
        color: #e8fff2;
        font-size: 14px;
        font-weight: 700;
    }

    #practicalCardSummary {
        color: #a7c7b7;
        font-size: 11px;
    }

    #mathPlotPreview {
        background: #071512;
        border: 1px solid #285244;
        border-radius: 8px;
        color: #8eb6a4;
        padding: 8px;
    }

    #mathResults, #mathExplanation {
        background: #091713;
        border: 1px solid #204837;
        border-radius: 8px;
        color: #dff8eb;
        padding: 12px;
    }

    #mathFunctionInput {
        background: rgba(6, 26, 21, 0.95);
        border: 1.5px solid rgba(81, 204, 175, 0.55);
        border-radius: 10px;
        color: #6cf5c2;
        font-family: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', 'Consolas', monospace;
        font-size: 14px;
        font-weight: 600;
        padding: 8px 12px;
        min-width: 0;
    }

    #mathFunctionInput:hover {
        border-color: rgba(125, 255, 214, 0.85);
        background: rgba(8, 35, 28, 0.95);
    }

    #mathFunctionInput:focus {
        border: 2px solid #57fabc;
        background: rgba(9, 40, 32, 0.98);
        color: #ffffff;
    }

    #mathDataInput {
        min-width: 0;
    }

    #practicalImageFallback {
        background: #102b23;
        border: 1px dashed #477661;
        border-radius: 6px;
        color: #93cdb0;
        padding: 18px;
        font-size: 11px;
    }

    #mathTutorSidebar, #labTutorPanel {
        background: rgba(8, 26, 22, 0.96);
        border: 1px solid rgba(89, 220, 169, 0.38);
        border-radius: 12px;
        padding: 4px;
    }

    #labEquation {
        background: #091713;
        border: 1px solid #204837;
        border-radius: 8px;
        color: #b7f4d0;
        padding: 5px 9px;
        font-family: serif;
        font-size: 15px;
    }

    #labModelNote {
        color: #87a596;
        font-size: 10px;
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

    #chatRail {
        background: rgba(3, 20, 17, 0.98);
        border: 1px solid rgba(53, 170, 149, 0.3);
        border-radius: 12px;
    }

    #chatRail #chatView {
        padding: 10px;
        font-size: 13px;
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
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(6, 26, 22, 0.95), stop:1 rgba(9, 36, 30, 0.95));
        border: 1px solid rgba(81, 204, 175, 0.4);
        border-radius: 12px;
        padding: 8px 12px;
    }

    #modelEyebrow {
        background: rgba(14, 56, 46, 0.9);
        border: 1px solid rgba(81, 204, 175, 0.45);
        border-radius: 6px;
        color: #6cf5c2;
        font-size: 10px;
        font-weight: 800;
        letter-spacing: 0.12em;
        padding: 4px 8px;
    }

    #modelSelector {
        background: rgba(6, 24, 20, 0.95);
        border: 1.5px solid rgba(81, 204, 175, 0.45);
        border-radius: 8px;
        color: #ffffff;
        font-size: 13px;
        font-weight: 600;
        padding: 7px 30px 7px 12px;
        min-width: 220px;
    }

    #modelSelector:hover {
        border-color: rgba(125, 255, 214, 0.85);
        background: rgba(9, 36, 30, 0.98);
    }

    #modelSelector:focus {
        border: 2px solid #57fabc;
    }

    #modelDetail {
        color: #b0e3d2;
        font-size: 11px;
        font-weight: 500;
        padding: 0 4px;
    }

    #modelReconnectButton {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(16, 68, 54, 0.95), stop:1 rgba(10, 48, 38, 0.95));
        border: 1px solid rgba(89, 220, 180, 0.5);
        border-radius: 8px;
        color: #bbf8e1;
        padding: 7px 14px;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.04em;
    }

    #modelReconnectButton:hover {
        background: rgba(22, 90, 72, 0.98);
        border-color: #57fabc;
        color: #ffffff;
    }

    #modelReconnectButton:disabled {
        background: rgba(10, 30, 25, 0.5);
        border-color: rgba(60, 120, 100, 0.3);
        color: #6e9484;
    }

    QComboBox::drop-down {
        border: none;
        width: 26px;
    }

    QComboBox QAbstractItemView {
        background: #06231e;
        color: #e6fff6;
        selection-background-color: #0b6551;
        border: 1.5px solid #287d69;
        border-radius: 8px;
        padding: 4px;
        outline: none;
    }

    QComboBox QAbstractItemView::item {
        min-height: 28px;
        padding: 4px 8px;
        border-radius: 4px;
    }

    QComboBox QAbstractItemView::item:hover {
        background: rgba(20, 80, 65, 0.85);
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

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter) and not event.modifiers() & Qt.ShiftModifier:
            self.window().send_message()
            return
        super().keyPressEvent(event)


class PlotPreview(QLabel):
    def __init__(self, parent=None):
        super().__init__("Run an analysis to plot a graph", parent)
        self.setObjectName("mathPlotPreview")
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumSize(260, 310)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._source_pixmap: QPixmap | None = None

    def set_plot_png(self, content: bytes):
        pixmap = QPixmap()
        if not pixmap.loadFromData(content, "PNG"):
            self._source_pixmap = None
            self.setText("Could not render this graph")
            return
        self._source_pixmap = pixmap
        self._scale_plot()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._scale_plot()

    def _scale_plot(self):
        if self._source_pixmap:
            self.setPixmap(
                self._source_pixmap.scaled(
                    max(1, self.width() - 16),
                    max(1, self.height() - 16),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation,
                )
            )


class MathEquationInput(QLineEdit):
    """Equation input field with an inviting blinking caret to encourage input."""

    def __init__(self, text: str = "", parent: QWidget | None = None):
        super().__init__(text, parent)
        self.setClearButtonEnabled(True)
        self._cursor_visible = True
        self._cursor_timer = QTimer(self)
        self._cursor_timer.setInterval(500)
        self._cursor_timer.timeout.connect(self._toggle_cursor_blink)
        self._cursor_timer.start()

    def _toggle_cursor_blink(self):
        self._cursor_visible = not self._cursor_visible
        self.update()

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self._cursor_visible = True
        self.update()

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self._cursor_visible = True
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self.hasFocus() and self._cursor_visible:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing, True)
            fm = self.fontMetrics()
            text = self.text()
            x = 13 + (fm.horizontalAdvance(text) if text else 0)
            x = min(x, max(13, self.width() - 24))
            caret_height = min(fm.height(), max(12, self.height() - 14))
            y = (self.height() - caret_height) // 2
            pen = QPen(QColor("#57fabc"), 2.2)
            painter.setPen(pen)
            painter.drawLine(x, y + 2, x, y + caret_height - 2)
            painter.end()


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
        self.setWindowFlags(
            Qt.Window
            | Qt.CustomizeWindowHint
            | Qt.WindowTitleHint
            | Qt.WindowSystemMenuHint
            | Qt.WindowMinimizeButtonHint
            | Qt.WindowMaximizeButtonHint
            | Qt.WindowCloseButtonHint
        )
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
        self.active_workspace = "gce"
        self.lab_screen = "home"
        self.lab_subject = ""
        self.active_experiment = None
        self.lab_parameter_labels = {}
        self.lab_parameter_sliders = {}
        self.lab_metric_labels = {}
        self.lab_side_panel_active = False
        self.lab_tutor_content = ""
        self.lab_tutor_expanded = False
        self.math_analysis_active = False
        self.math_explanation_content = ""
        self.math_analysis_result: AnalysisResult | None = None
        self.chemistry_route = "/chemistry"
        self.chemistry_route_history: list[str] = []
        self.chemistry_level_slug = ""
        self.chemistry_topic_number: int | None = None
        self.chemistry_practicals_open = False
        self.chemistry_level_buttons: dict[str, QPushButton] = {}
        self.chemistry_topic_buttons: dict[int, QPushButton] = {}
        self._menu_animations: list[QPropertyAnimation] = []
        self.gce_pages: dict[str, QWidget] = {}
        self.progress_save_timer = QTimer(self)
        self.progress_save_timer.setSingleShot(True)
        self.progress_save_timer.timeout.connect(self._save_progress)
        self.lab_notes_save_timer = QTimer(self)
        self.lab_notes_save_timer.setSingleShot(True)
        self.lab_notes_save_timer.timeout.connect(self._save_lab_notes)
        self.chat_render_timer = QTimer(self)
        self.chat_render_timer.setSingleShot(True)
        self.chat_render_timer.setInterval(40)
        self.chat_render_timer.timeout.connect(self._flush_chat_render)
        self.chat_render_dirty = False
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
        self.sidebar = sidebar
        sidebar.setObjectName("sidebar")
        sidebar.setMinimumWidth(0)
        sidebar.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Expanding)
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(18, 18, 18, 18)
        side_layout.setSpacing(12)

        self.new_chat_button = QPushButton("+ New chat")
        self.new_chat_button.setObjectName("newChatButton")
        self.new_chat_button.clicked.connect(self.new_chat)
        side_layout.addWidget(self.new_chat_button)

        lab_label = QLabel("INTERACTIVE LAB")
        lab_label.setObjectName("sidebarSection")
        side_layout.addWidget(lab_label)

        self.lab_library_button = QPushButton("✳  Experiment library")
        self.lab_library_button.setObjectName("labNavButton")
        self.lab_library_button.clicked.connect(self.open_experiment_library)
        side_layout.addWidget(self.lab_library_button)

        self.lab_subject_buttons = {}
        for subject in LAB_SUBJECTS:
            button = QPushButton(f"›  {subject}")
            button.setObjectName("labSubjectButton")
            if subject == "Chemistry":
                button.setCheckable(True)
                button.setAccessibleName("Chemistry practicals, expand or collapse levels")
                button.setAccessibleDescription("Press to show Ordinary Level and Advanced Level practical topics")
                button.clicked.connect(self._toggle_chemistry_practicals)
            else:
                button.clicked.connect(lambda _checked=False, value=subject: self.open_experiments_subject(value))
            side_layout.addWidget(button)
            self.lab_subject_buttons[subject] = button
            if subject == "Chemistry":
                self.chemistry_practical_nav = QWidget()
                self.chemistry_practical_nav.setObjectName("chemistryPracticalNav")
                practical_nav_layout = QVBoxLayout(self.chemistry_practical_nav)
                practical_nav_layout.setContentsMargins(8, 0, 0, 0)
                practical_nav_layout.setSpacing(3)
                self.chemistry_level_navs = {}
                for level in CHEMISTRY.levels:
                    level_nav = QWidget()
                    level_nav_layout = QVBoxLayout(level_nav)
                    level_nav_layout.setContentsMargins(0, 0, 0, 0)
                    level_nav_layout.setSpacing(2)
                    level_button = QPushButton(f"›  {level.label}")
                    level_button.setObjectName("chemistryLevelButton")
                    level_button.setCheckable(True)
                    level_button.setAccessibleName(f"{level.label} chemistry topics, expand or collapse")
                    level_button.clicked.connect(
                        lambda _checked=False, slug=level.slug: self._select_chemistry_level(slug)
                    )
                    level_button.installEventFilter(self)
                    level_nav_layout.addWidget(level_button)
                    topic_nav = QWidget()
                    topic_nav_layout = QVBoxLayout(topic_nav)
                    topic_nav_layout.setContentsMargins(10, 0, 0, 0)
                    topic_nav_layout.setSpacing(2)
                    topic_buttons = {}
                    for topic in level.topics:
                        topic_button = QPushButton(f"{topic.number}. {topic.title}")
                        topic_button.setObjectName("chemistryTopicButton")
                        topic_button.setCheckable(True)
                        topic_button.setAccessibleName(f"Open {level.label} topic {topic.number}: {topic.title}")
                        topic_button.setAccessibleDescription("Press Enter or Space to show the practical cards")
                        topic_button.clicked.connect(
                            lambda _checked=False, level_slug=level.slug, number=topic.number: self._select_chemistry_topic(level_slug, number)
                        )
                        topic_button.installEventFilter(self)
                        topic_nav_layout.addWidget(topic_button)
                        topic_buttons[topic.number] = topic_button
                    topic_nav.setMaximumHeight(0)
                    topic_nav.hide()
                    level_nav_layout.addWidget(topic_nav)
                    practical_nav_layout.addWidget(level_nav)
                    self.chemistry_level_navs[level.slug] = {
                        "level": level,
                        "button": level_button,
                        "topic_nav": topic_nav,
                        "topic_buttons": topic_buttons,
                    }
                self.chemistry_practical_nav.setMaximumHeight(0)
                self.chemistry_practical_nav.hide()
                side_layout.addWidget(self.chemistry_practical_nav)

            self.math_lab_button = QPushButton("Math Data Lab")
            self.math_lab_button.setObjectName("labSubjectButton")
            self.math_lab_button.setToolTip("Plot functions or analyze a measured data set")
            self.math_lab_button.clicked.connect(self.open_math_analysis)
            side_layout.addWidget(self.math_lab_button)

        workspace_label = QLabel("STUDY & CREATE")
        workspace_label.setObjectName("sidebarSection")
        side_layout.addWidget(workspace_label)

        self.gce_study_button = QPushButton("GCE Learning")
        self.gce_study_button.setObjectName("labNavButton")
        self.gce_study_button.setAccessibleName("Open GCE level and subject selection")
        self.gce_study_button.clicked.connect(self.open_gce_levels)
        side_layout.addWidget(self.gce_study_button)

        self.ai_workspace_button = QPushButton("AI Workspace")
        self.ai_workspace_button.setObjectName("labNavButton")
        self.ai_workspace_button.setAccessibleName("Open general AI chat workspace")
        self.ai_workspace_button.clicked.connect(self.open_ai_workspace)
        side_layout.addWidget(self.ai_workspace_button)

        side_layout.addStretch(1)
        lab_note = QLabel("VIRTUAL PRE-LAB\nExplore safely before the bench.")
        lab_note.setObjectName("studySubheading")
        lab_note.setWordWrap(True)
        side_layout.addWidget(lab_note)

        main_panel = QWidget()
        main_panel.setObjectName("chatPanel")
        main_panel.setMinimumWidth(0)
        main_panel.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Expanding)
        main_layout = QVBoxLayout(main_panel)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(14)

        header = QWidget()
        header.setObjectName("headerBar")
        header.setMinimumWidth(0)
        header.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
        header_layout = QHBoxLayout(header)
        self.header_layout = header_layout
        header_layout.setContentsMargins(16, 10, 16, 10)
        header_layout.setSpacing(18)

        self.mobile_menu_button = QPushButton("Menu")
        self.mobile_menu_button.setObjectName("newChatButton")
        self.mobile_menu_button.setAccessibleName("Open app navigation")
        self.mobile_menu_button.clicked.connect(self._show_mobile_navigation)
        self.mobile_menu_button.hide()
        header_layout.addWidget(self.mobile_menu_button)

        self.back_button = QPushButton("← Back")
        self.back_button.setObjectName("newChatButton")
        self.back_button.hide()
        self.back_button.clicked.connect(self.navigate_back)
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

        self.connection_status = QLabel("CONNECTING")
        self.connection_status.setObjectName("statPill")

        self.window_controls = QWidget()
        self.window_controls.setObjectName("windowControls")
        window_controls_layout = QHBoxLayout(self.window_controls)
        window_controls_layout.setContentsMargins(0, 0, 0, 0)
        window_controls_layout.setSpacing(8)

        self.window_minimize_button = QPushButton("—")
        self.window_minimize_button.setObjectName("windowControlButton")
        self.window_minimize_button.setToolTip("Minimize")
        self.window_minimize_button.clicked.connect(self.showMinimized)
        window_controls_layout.addWidget(self.window_minimize_button)

        self.window_maximize_button = QPushButton("▢")
        self.window_maximize_button.setObjectName("windowControlButton")
        self.window_maximize_button.setToolTip("Maximize")
        self.window_maximize_button.clicked.connect(self._toggle_window_maximize)
        window_controls_layout.addWidget(self.window_maximize_button)

        self.window_close_button = QPushButton("×")
        self.window_close_button.setObjectName("windowControlButton")
        self.window_close_button.setProperty("variant", "close")
        self.window_close_button.setToolTip("Close")
        self.window_close_button.clicked.connect(self.close)
        window_controls_layout.addWidget(self.window_close_button)

        header_layout.addWidget(self.model_info)
        header_layout.addWidget(self.connection_status)
        header_layout.addWidget(self.window_controls)

        main_layout.addWidget(header)

        self.content_stack = QStackedWidget()
        self.content_stack.setMinimumWidth(0)
        self.content_stack.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Expanding)
        main_layout.addWidget(self.content_stack, 1)

        self._build_chat_page()
        self._build_gce_pages()
        self._build_experiment_pages()
        self._build_chemistry_practical_pages()
        self._build_math_analysis_page()

        outer.addWidget(sidebar, 1)
        outer.addWidget(main_panel, 5)

        self.setCentralWidget(root)
        self.content_stack.setCurrentWidget(self.level_page)
        self.gce_screen = "level"
        self.back_button.hide()
        self.statusBar().showMessage("Connecting to local model...")
        QShortcut(QKeySequence("Ctrl+N"), self, self.new_chat)
        QShortcut(QKeySequence("Ctrl+Comma"), self, self.show_status)
        QShortcut(QKeySequence("Escape"), self, self.stop_streaming)

    def _show_mobile_navigation(self):
        menu = QMenu(self)
        menu.addAction("Experiment library", self.open_experiment_library)
        menu.addAction("Physics", lambda: self.open_experiments_subject("Physics"))
        menu.addAction("Biology", lambda: self.open_experiments_subject("Biology"))
        chemistry = menu.addMenu("Chemistry practicals")
        for level in CHEMISTRY.levels:
            level_menu = chemistry.addMenu(level.label)
            for topic in level.topics:
                level_menu.addAction(
                    f"{topic.number}. {topic.title}",
                    lambda _checked=False, slug=level.slug, number=topic.number: self._open_chemistry_topic_from_menu(slug, number),
                )
        menu.addAction("Math Data Lab", self.open_math_analysis)
        menu.addSeparator()
        menu.addAction("GCE Learning", self.open_gce_levels)
        menu.addAction("AI Workspace", self.open_ai_workspace)
        menu.exec(self.mobile_menu_button.mapToGlobal(self.mobile_menu_button.rect().bottomLeft()))

    def _open_chemistry_topic_from_menu(self, level_slug: str, topic_number: int):
        if not self.chemistry_practicals_open:
            self._toggle_chemistry_practicals()
        self._select_chemistry_level(level_slug)
        self._select_chemistry_topic(level_slug, topic_number)

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
        model_layout.setContentsMargins(12, 6, 12, 6)
        model_layout.setSpacing(12)

        model_eyebrow = QLabel("⚡ LOCAL MODEL")
        model_eyebrow.setObjectName("modelEyebrow")
        model_layout.addWidget(model_eyebrow)

        self.model_selector = QComboBox()
        self.model_selector.setObjectName("modelSelector")
        self.model_selector.setAccessibleName("Choose a local language model")
        self.model_selector.setMinimumWidth(230)
        self.model_selector.setMinimumContentsLength(20)
        self.model_selector.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
        for option in MODEL_OPTIONS:
            self.model_selector.addItem(f"{option.icon}  {option.name}", option.model_id)
            self.model_selector.setItemData(
                self.model_selector.count() - 1,
                f"{option.name} [{option.tag}]\n{option.description} · {option.quantization}",
                Qt.ToolTipRole,
            )
        saved_model_id = self.progress.get("model_id", "")
        saved_model_index = self.model_selector.findData(saved_model_id)
        if saved_model_index >= 0:
            self.model_selector.setCurrentIndex(saved_model_index)
        model_layout.addWidget(self.model_selector)

        self.model_detail = QLabel("")
        self.model_detail.setObjectName("modelDetail")
        self.model_detail.setAccessibleName("Selected model description and quantization")
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
        level_scroll = QScrollArea()
        level_scroll.setWidgetResizable(True)
        level_scroll.setFrameShape(QScrollArea.NoFrame)
        level_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        level_container = QWidget()
        level_inner_layout = QVBoxLayout(level_container)
        level_inner_layout.setContentsMargins(0, 0, 0, 0)
        level_inner_layout.setSpacing(14)
        level_inner_layout.addWidget(start_logo)
        level_inner_layout.addLayout(level_grid)
        level_inner_layout.addStretch(1)
        level_scroll.setWidget(level_container)
        level_layout.addWidget(level_scroll, 1)
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
        stream_scroll = QScrollArea()
        stream_scroll.setWidgetResizable(True)
        stream_scroll.setFrameShape(QScrollArea.NoFrame)
        stream_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        stream_container = QWidget()
        stream_inner_layout = QVBoxLayout(stream_container)
        stream_inner_layout.setContentsMargins(0, 0, 0, 0)
        stream_inner_layout.setSpacing(14)
        stream_inner_layout.addLayout(stream_grid)
        stream_inner_layout.addStretch(1)
        stream_scroll.setWidget(stream_container)
        self.stream_page.layout().addWidget(stream_scroll, 1)
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

    def _build_experiment_pages(self):
        self.lab_home_page = self._selection_page(
            "The virtual pre-lab",
            "Explore a scientific idea safely. Change a variable, watch the model respond, and make a prediction before the real bench.",
        )
        self.lab_subject_grid = QGridLayout()
        self.lab_subject_grid.setSpacing(14)
        for index, subject in enumerate(LAB_SUBJECTS):
            count = len(experiments_for_subject(subject))
            button = self._study_card(subject, f"{count} interactive experiments  ·  OPEN LAB  →")
            button.clicked.connect(lambda _checked=False, value=subject: self.open_experiments_subject(value))
            self.lab_subject_grid.addWidget(button, 0, index)
        math_card = self._study_card("Math Data Lab", "Plot functions and analyze measurements")
        math_card.setAccessibleName("Open Mathematics data analysis workspace")
        math_card.clicked.connect(self.open_math_analysis)
        self.lab_subject_grid.addWidget(math_card, 1, 0)
        lab_home_scroll = QScrollArea()
        lab_home_scroll.setWidgetResizable(True)
        lab_home_scroll.setFrameShape(QScrollArea.NoFrame)
        lab_home_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        lab_home_container = QWidget()
        lab_home_inner_layout = QVBoxLayout(lab_home_container)
        lab_home_inner_layout.setContentsMargins(0, 0, 0, 0)
        lab_home_inner_layout.setSpacing(14)
        lab_home_inner_layout.addLayout(self.lab_subject_grid)
        lab_home_inner_layout.addStretch(1)
        lab_home_scroll.setWidget(lab_home_container)
        self.lab_home_page.layout().addWidget(lab_home_scroll, 1)
        self.content_stack.addWidget(self.lab_home_page)

        self.lab_gallery_page = self._selection_page(
            "Choose an experiment",
            "Short, interactive models for exploring variables before a practical lesson.",
        )
        self.lab_gallery_heading = self.lab_gallery_page.findChild(QLabel, "studyHeading")
        self.lab_gallery_grid_container = QWidget()
        self.lab_gallery_grid = QGridLayout(self.lab_gallery_grid_container)
        self.lab_gallery_grid.setContentsMargins(0, 0, 0, 0)
        self.lab_gallery_grid.setSpacing(12)
        self.lab_gallery_grid.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.lab_gallery_grid.setColumnStretch(0, 1)
        gallery_scroll = QScrollArea()
        gallery_scroll.setWidgetResizable(True)
        gallery_scroll.setFrameShape(QScrollArea.NoFrame)
        gallery_scroll.setWidget(self.lab_gallery_grid_container)
        self.lab_gallery_scroll = gallery_scroll
        self.lab_gallery_page.layout().addWidget(gallery_scroll, 1)
        self.content_stack.addWidget(self.lab_gallery_page)

        self.lab_detail_page = QWidget()
        detail_page_layout = QVBoxLayout(self.lab_detail_page)
        detail_page_layout.setContentsMargins(0, 0, 0, 0)
        self.lab_detail_content = QWidget()
        self.lab_detail_layout = QBoxLayout(QBoxLayout.LeftToRight, self.lab_detail_content)
        self.lab_detail_layout.setContentsMargins(22, 18, 22, 20)
        self.lab_detail_layout.setSpacing(14)

        self.lab_detail_main = QWidget()
        self.lab_detail_main_layout = QVBoxLayout(self.lab_detail_main)
        self.lab_detail_main_layout.setContentsMargins(0, 0, 0, 0)
        self.lab_detail_main_layout.setSpacing(12)
        detail_scroll = QScrollArea()
        detail_scroll.setWidgetResizable(True)
        detail_scroll.setFrameShape(QScrollArea.NoFrame)
        detail_scroll.setWidget(self.lab_detail_main)
        self.lab_detail_layout.addWidget(detail_scroll, 3)

        self.lab_detail_title = QLabel("")
        self.lab_detail_title.setObjectName("studyHeading")
        self.lab_detail_main_layout.addWidget(self.lab_detail_title)
        self.lab_detail_subtitle = QLabel("")
        self.lab_detail_subtitle.setObjectName("studySubheading")
        self.lab_detail_main_layout.addWidget(self.lab_detail_subtitle)

        self.lab_workspace = QWidget()
        self.lab_workspace_layout = QVBoxLayout(self.lab_workspace)
        self.lab_workspace_layout.setContentsMargins(0, 0, 0, 0)
        self.lab_workspace_layout.setSpacing(0)
        self.lab_canvas_shell = QWidget()
        self.lab_canvas_shell.setObjectName("labCanvas")
        self.lab_canvas_shell.setMinimumHeight(520)
        self.lab_canvas_shell_layout = QVBoxLayout(self.lab_canvas_shell)
        self.lab_canvas_shell_layout.setContentsMargins(10, 10, 10, 10)
        self.lab_canvas = LabCanvas()
        self.lab_canvas.metrics_updated.connect(self._sync_lab_runtime)
        self.lab_canvas.setMinimumHeight(480)
        self.lab_canvas_shell_layout.addWidget(self.lab_canvas)
        self.lab_workspace_layout.addWidget(self.lab_canvas_shell, 1)

        self.lab_tutor_panel = QWidget()
        self.lab_tutor_panel.setObjectName("labTutorPanel")
        self.lab_tutor_panel.setMinimumWidth(320)
        self.lab_tutor_panel.hide()
        self.lab_tutor_panel_layout = QVBoxLayout(self.lab_tutor_panel)
        self.lab_tutor_panel_layout.setContentsMargins(12, 12, 12, 12)
        self.lab_tutor_panel_layout.setSpacing(10)
        tutor_header = QWidget()
        tutor_header_layout = QHBoxLayout(tutor_header)
        tutor_header_layout.setContentsMargins(0, 0, 0, 0)
        tutor_header_layout.setSpacing(10)
        self.lab_tutor_panel_title = QLabel("Fuserio explainer")
        self.lab_tutor_panel_title.setObjectName("labControlLabel")
        tutor_header_layout.addWidget(self.lab_tutor_panel_title)
        tutor_header_layout.addStretch(1)
        self.lab_tutor_close_button = QPushButton("Back to experiment")
        self.lab_tutor_close_button.setObjectName("studyModeButton")
        self.lab_tutor_close_button.clicked.connect(self._close_lab_tutor)
        tutor_header_layout.addWidget(self.lab_tutor_close_button)
        self.lab_tutor_panel_layout.addWidget(tutor_header)
        self.lab_tutor_stream = QTextBrowser()
        self.lab_tutor_stream.setObjectName("chatView")
        self.lab_tutor_stream.setReadOnly(True)
        self.lab_tutor_stream.setOpenExternalLinks(False)
        self.lab_tutor_stream.setMinimumHeight(350)
        self.lab_tutor_panel_layout.addWidget(self.lab_tutor_stream, 1)
        self.lab_detail_main_layout.addWidget(self.lab_workspace, 1)

        self.lab_toolbar = QWidget()
        toolbar_layout = QHBoxLayout(self.lab_toolbar)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        toolbar_layout.setSpacing(8)
        self.lab_play_button = QPushButton("▶  Run simulation")
        self.lab_play_button.setObjectName("sendButton")
        self.lab_play_button.clicked.connect(self._toggle_lab_simulation)
        toolbar_layout.addWidget(self.lab_play_button)
        self.lab_reset_button = QPushButton("↺  Reset")
        self.lab_reset_button.setObjectName("studyModeButton")
        self.lab_reset_button.clicked.connect(self._reset_lab_simulation)
        toolbar_layout.addWidget(self.lab_reset_button)
        self.lab_tutor_button = QPushButton("Ask Fuserio")
        self.lab_tutor_button.setObjectName("studyModeButton")
        self.lab_tutor_button.setToolTip("Ask the local AI tutor to explain this model and its current results")
        self.lab_tutor_button.clicked.connect(self.ask_lab_tutor)
        toolbar_layout.addWidget(self.lab_tutor_button)
        self.lab_step_button = QPushButton("Step →")
        self.lab_step_button.setObjectName("studyModeButton")
        self.lab_step_button.clicked.connect(self._step_lab_simulation)
        toolbar_layout.addWidget(self.lab_step_button)
        toolbar_layout.addStretch(1)
        speed_label = QLabel("SPEED")
        speed_label.setObjectName("labControlLabel")
        toolbar_layout.addWidget(speed_label)
        self.lab_speed_slider = QSlider(Qt.Horizontal)
        self.lab_speed_slider.setRange(25, 200)
        self.lab_speed_slider.setValue(100)
        self.lab_speed_slider.setFixedWidth(110)
        self.lab_speed_slider.setAccessibleName("Simulation playback speed")
        self.lab_speed_slider.valueChanged.connect(self._set_lab_speed)
        toolbar_layout.addWidget(self.lab_speed_slider)
        self.lab_speed_value = QLabel("1.00×")
        self.lab_speed_value.setObjectName("labControlValue")
        toolbar_layout.addWidget(self.lab_speed_value)
        self.lab_detail_main_layout.addWidget(self.lab_toolbar)

        self.lab_metrics_row = QWidget()
        self.lab_metrics_layout = QHBoxLayout(self.lab_metrics_row)
        self.lab_metrics_layout.setContentsMargins(0, 0, 0, 0)
        self.lab_metrics_layout.setSpacing(8)
        self.lab_detail_main_layout.addWidget(self.lab_metrics_row)

        self.lab_controls_widget = QWidget()
        self.lab_controls_layout = QVBoxLayout(self.lab_controls_widget)
        self.lab_controls_layout.setContentsMargins(0, 0, 0, 0)
        self.lab_controls_layout.setSpacing(6)
        self.lab_detail_main_layout.addWidget(self.lab_controls_widget)

        self.lab_objective = QLabel("")
        self.lab_objective.setWordWrap(True)
        self.lab_objective.setObjectName("studySubheading")
        self.lab_detail_main_layout.addWidget(self.lab_objective)

        equation_label = QLabel("MODEL RELATIONSHIP")
        equation_label.setObjectName("labControlLabel")
        self.lab_detail_main_layout.addWidget(equation_label)
        self.lab_equation = QTextBrowser()
        self.lab_equation.setObjectName("labEquation")
        self.lab_equation.setReadOnly(True)
        self.lab_equation.setOpenExternalLinks(False)
        self.lab_equation.setFixedHeight(58)
        self.lab_detail_main_layout.addWidget(self.lab_equation)
        self.lab_model_note = QLabel("")
        self.lab_model_note.setObjectName("labModelNote")
        self.lab_model_note.setWordWrap(True)
        self.lab_detail_main_layout.addWidget(self.lab_model_note)

        prediction_label = QLabel("MAKE A PREDICTION")
        prediction_label.setObjectName("labControlLabel")
        self.lab_detail_main_layout.addWidget(prediction_label)
        self.lab_prediction_edit = QTextEdit()
        self.lab_prediction_edit.setObjectName("composer")
        self.lab_prediction_edit.setPlaceholderText("What do you predict will happen when you change one variable?")
        self.lab_prediction_edit.setFixedHeight(68)
        self.lab_prediction_edit.textChanged.connect(self._schedule_lab_notes_save)
        self.lab_detail_main_layout.addWidget(self.lab_prediction_edit)

        observation_label = QLabel("OBSERVATIONS & CONCLUSION")
        observation_label.setObjectName("labControlLabel")
        self.lab_detail_main_layout.addWidget(observation_label)
        self.lab_observation_edit = QTextEdit()
        self.lab_observation_edit.setObjectName("composer")
        self.lab_observation_edit.setPlaceholderText("Record what changed, compare with your prediction, and explain why.")
        self.lab_observation_edit.setFixedHeight(82)
        self.lab_observation_edit.textChanged.connect(self._schedule_lab_notes_save)
        self.lab_detail_main_layout.addWidget(self.lab_observation_edit)

        self.lab_safety = QLabel("")
        self.lab_safety.setWordWrap(True)
        self.lab_safety.setObjectName("labSafety")
        self.lab_detail_main_layout.addWidget(self.lab_safety)

        self.lab_detail_layout.addWidget(self.lab_tutor_panel, 2)
        self.lab_detail_page.setMinimumHeight(0)
        detail_page_layout.addWidget(self.lab_detail_content, 1)
        self.content_stack.addWidget(self.lab_detail_page)

    def _build_chemistry_practical_pages(self):
        self.chemistry_practical_page = QWidget()
        practical_layout = QVBoxLayout(self.chemistry_practical_page)
        practical_layout.setContentsMargins(26, 22, 26, 22)
        practical_layout.setSpacing(12)
        self.chemistry_practical_heading = QLabel("Chemistry practicals")
        self.chemistry_practical_heading.setObjectName("chemistryTopicHeading")
        practical_layout.addWidget(self.chemistry_practical_heading)
        self.chemistry_practical_subheading = QLabel("Choose a level and topic from the sidebar to explore practical work.")
        self.chemistry_practical_subheading.setObjectName("studySubheading")
        self.chemistry_practical_subheading.setWordWrap(True)
        practical_layout.addWidget(self.chemistry_practical_subheading)
        self.chemistry_practical_grid_host = QWidget()
        self.chemistry_practical_grid_host.setMinimumWidth(0)
        self.chemistry_practical_grid_host.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Expanding)
        self.chemistry_practical_grid = QGridLayout(self.chemistry_practical_grid_host)
        self.chemistry_practical_grid.setContentsMargins(0, 8, 0, 0)
        self.chemistry_practical_grid.setSpacing(14)
        self.chemistry_practical_grid.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.chemistry_practical_grid_host.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.chemistry_practical_scroll = QScrollArea()
        self.chemistry_practical_scroll.setObjectName("chemistryPracticalScroll")
        self.chemistry_practical_scroll.setWidgetResizable(True)
        self.chemistry_practical_scroll.setMinimumWidth(0)
        self.chemistry_practical_scroll.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Expanding)
        self.chemistry_practical_scroll.setFrameShape(QScrollArea.NoFrame)
        self.chemistry_practical_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.chemistry_practical_scroll.setWidget(self.chemistry_practical_grid_host)
        practical_layout.addWidget(self.chemistry_practical_scroll, 1)
        self.content_stack.addWidget(self.chemistry_practical_page)

        self.chemistry_detail_page = QWidget()
        detail_layout = QVBoxLayout(self.chemistry_detail_page)
        detail_layout.setContentsMargins(26, 22, 26, 22)
        detail_layout.setSpacing(14)
        self.chemistry_detail_title = QLabel("")
        self.chemistry_detail_title.setObjectName("chemistryTopicHeading")
        detail_layout.addWidget(self.chemistry_detail_title)
        self.chemistry_detail_image = QLabel("")
        self.chemistry_detail_image.setObjectName("practicalImageFallback")
        self.chemistry_detail_image.setMinimumHeight(190)
        self.chemistry_detail_image.setAlignment(Qt.AlignCenter)
        detail_layout.addWidget(self.chemistry_detail_image)
        self.chemistry_detail_summary = QLabel("")
        self.chemistry_detail_summary.setObjectName("studySubheading")
        self.chemistry_detail_summary.setWordWrap(True)
        detail_layout.addWidget(self.chemistry_detail_summary)
        sections = QGridLayout()
        sections.setSpacing(12)
        for index, name in enumerate(("Aim", "Apparatus", "Procedure", "Observations", "Calculations")):
            section = QWidget()
            section.setObjectName("labMetric")
            section_layout = QVBoxLayout(section)
            section_layout.setContentsMargins(14, 12, 14, 12)
            heading = QLabel(name.upper())
            heading.setObjectName("labControlLabel")
            empty = QLabel("Content will be added here.")
            empty.setObjectName("labModelNote")
            empty.setWordWrap(True)
            section_layout.addWidget(heading)
            section_layout.addWidget(empty, 1)
            sections.addWidget(section, index // 2, index % 2)
        detail_layout.addLayout(sections)
        detail_layout.addStretch(1)
        self.content_stack.addWidget(self.chemistry_detail_page)

    def _build_math_analysis_page(self):
        self.math_analysis_page = QWidget()
        page_layout = QVBoxLayout(self.math_analysis_page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(0)

        math_scroll = QScrollArea()
        math_scroll.setObjectName("mathAnalysisScroll")
        math_scroll.setWidgetResizable(True)
        math_scroll.setFrameShape(QScrollArea.NoFrame)
        math_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.math_analysis_scroll = math_scroll

        self.math_analysis_container = QWidget()
        self.math_page_layout = QBoxLayout(QBoxLayout.LeftToRight, self.math_analysis_container)
        self.math_page_layout.setContentsMargins(0, 0, 0, 0)
        self.math_page_layout.setSpacing(0)

        self.math_analysis_controls = QWidget()
        self.math_analysis_controls.setObjectName("mathAnalysisLeft")
        controls_layout = QVBoxLayout(self.math_analysis_controls)
        controls_layout.setContentsMargins(18, 18, 12, 18)
        controls_layout.setSpacing(10)

        title = QLabel("Math Data Lab")
        title.setObjectName("studyHeading")
        controls_layout.addWidget(title)

        mode_row = QHBoxLayout()
        mode_label = QLabel("ANALYSIS")
        mode_label.setObjectName("labControlLabel")
        mode_row.addWidget(mode_label)
        self.math_mode_selector = QComboBox()
        self.math_mode_selector.addItems(("Function of x", "Measured data"))
        self.math_mode_selector.setAccessibleName("Choose function plotting or measured data analysis")
        mode_row.addWidget(self.math_mode_selector)
        mode_row.addStretch(1)
        controls_layout.addLayout(mode_row)

        quick_layout = QHBoxLayout()
        for label, expression in (
            ("Linear", "2*x + 1"),
            ("Quadratic", "x**2 - 4*x + 3"),
            ("Sine", "sin(x)"),
            ("Exponential", "exp(x/3)"),
        ):
            button = QPushButton(label)
            button.setObjectName("studyModeButton")
            button.clicked.connect(lambda _checked=False, value=expression: self.math_function_edit.setText(value))
            quick_layout.addWidget(button)
        quick_layout.addStretch(1)
        controls_layout.addLayout(quick_layout)

        self.math_function_row = QWidget()
        function_row_layout = QHBoxLayout(self.math_function_row)
        function_row_layout.setContentsMargins(0, 0, 0, 0)
        function_label = QLabel("y =")
        function_label.setObjectName("labControlLabel")
        function_row_layout.addWidget(function_label)
        self.math_function_edit = MathEquationInput("x**2 - 4*x + 3")
        self.math_function_edit.setObjectName("mathFunctionInput")
        self.math_function_edit.setPlaceholderText("Type a formula like 2*x + 1 or sin(x)")
        self.math_function_edit.setAccessibleName("Function of x to plot")
        function_row_layout.addWidget(self.math_function_edit, 1)
        controls_layout.addWidget(self.math_function_row)

        self.math_data_edit = QTextEdit()
        self.math_data_edit.setObjectName("mathDataInput")
        self.math_data_edit.setAccessibleName("Measured x and y data")
        self.math_data_edit.setPlaceholderText("Paste x,y pairs, one row per line")
        self.math_data_edit.setPlainText("x,y\n1,2.1\n2,3.9\n3,6.2\n4,7.8\n5,10.1")
        self.math_data_edit.setFixedHeight(112)
        self.math_data_edit.hide()
        controls_layout.addWidget(self.math_data_edit)

        range_row = QHBoxLayout()
        self.math_x_min = QDoubleSpinBox()
        self.math_x_min.setRange(-1_000_000, 1_000_000)
        self.math_x_min.setDecimals(3)
        self.math_x_min.setValue(-1)
        self.math_x_max = QDoubleSpinBox()
        self.math_x_max.setRange(-1_000_000, 1_000_000)
        self.math_x_max.setDecimals(3)
        self.math_x_max.setValue(5)
        self.math_samples = QSpinBox()
        self.math_samples.setRange(10, 1000)
        self.math_samples.setValue(160)
        for label_text, control, name in (
            ("X MIN", self.math_x_min, "Minimum x value"),
            ("X MAX", self.math_x_max, "Maximum x value"),
            ("SAMPLES", self.math_samples, "Number of plotted samples"),
        ):
            label = QLabel(label_text)
            label.setObjectName("labControlLabel")
            control.setAccessibleName(name)
            control.setMinimumWidth(88)
            range_row.addWidget(label)
            range_row.addWidget(control)
        range_row.addStretch(1)
        self.math_range_row = QWidget()
        self.math_range_row.setLayout(range_row)
        controls_layout.addWidget(self.math_range_row)

        action_row = QHBoxLayout()
        self.math_plot_button = QPushButton("Plot")
        self.math_plot_button.setObjectName("sendButton")
        self.math_plot_button.clicked.connect(self._run_math_analysis)
        action_row.addWidget(self.math_plot_button)
        self.math_explain_button = QPushButton("Ask Fuserio")
        self.math_explain_button.setObjectName("studyModeButton")
        self.math_explain_button.setToolTip("Ask Fuserio AI tutor to analyze and explain this graph in a dedicated sidebar")
        self.math_explain_button.clicked.connect(self._explain_math_analysis)
        action_row.addWidget(self.math_explain_button)
        action_row.addStretch(1)
        controls_layout.addLayout(action_row)

        self.math_status = QLabel("Ready. Choose a preset or type an equation to plot.")
        self.math_status.setObjectName("labModelNote")
        self.math_status.setWordWrap(True)
        controls_layout.addWidget(self.math_status)

        self.math_analysis_workspace = QWidget()
        self.math_analysis_workspace.setObjectName("mathAnalysisRight")
        self.math_workspace_layout = QBoxLayout(QBoxLayout.LeftToRight, self.math_analysis_workspace)
        self.math_workspace_layout.setContentsMargins(12, 18, 18, 18)
        self.math_workspace_layout.setSpacing(14)

        self.math_stage = QWidget()
        self.math_stage.setObjectName("mathStage")
        stage_layout = QVBoxLayout(self.math_stage)
        stage_layout.setContentsMargins(0, 0, 0, 0)
        stage_layout.setSpacing(10)

        self.math_plot_view = PlotPreview()
        stage_layout.addWidget(self.math_plot_view, 3)

        self.math_results_view = QTextBrowser()
        self.math_results_view.setObjectName("mathResults")
        self.math_results_view.setReadOnly(True)
        self.math_results_view.setMinimumHeight(120)
        self.math_results_view.setMaximumHeight(200)
        stage_layout.addWidget(self.math_results_view)

        self.math_workspace_layout.addWidget(self.math_stage, 3)

        self.math_tutor_sidebar = QWidget()
        self.math_tutor_sidebar.setObjectName("mathTutorSidebar")
        self.math_tutor_sidebar.setMinimumWidth(320)
        sidebar_layout = QVBoxLayout(self.math_tutor_sidebar)
        sidebar_layout.setContentsMargins(12, 12, 12, 12)
        sidebar_layout.setSpacing(10)

        tutor_header = QWidget()
        tutor_header_layout = QHBoxLayout(tutor_header)
        tutor_header_layout.setContentsMargins(0, 0, 0, 0)
        tutor_header_layout.setSpacing(8)

        tutor_title = QLabel("FUSERIO MATH TUTOR")
        tutor_title.setObjectName("labControlLabel")
        tutor_header_layout.addWidget(tutor_title)
        tutor_header_layout.addStretch(1)

        self.math_tutor_close_button = QPushButton("Close sidebar")
        self.math_tutor_close_button.setObjectName("studyModeButton")
        self.math_tutor_close_button.setToolTip("Close tutor sidebar")
        self.math_tutor_close_button.clicked.connect(self._close_math_tutor_sidebar)
        tutor_header_layout.addWidget(self.math_tutor_close_button)
        sidebar_layout.addWidget(tutor_header)

        self.math_explanation_view = QTextBrowser()
        self.math_explanation_view.setObjectName("mathExplanation")
        self.math_explanation_view.setReadOnly(True)
        self.math_explanation_view.setMinimumHeight(240)
        sidebar_layout.addWidget(self.math_explanation_view, 1)

        question_header = QLabel("TUTOR Q&A")
        question_header.setObjectName("labControlLabel")
        sidebar_layout.addWidget(question_header)

        question_row = QHBoxLayout()
        self.math_question_input = QLineEdit()
        self.math_question_input.setObjectName("searchBox")
        self.math_question_input.setPlaceholderText("Ask the tutor about this graph, pattern, or next step...")
        self.math_question_input.setClearButtonEnabled(True)
        self.math_question_input.returnPressed.connect(self._ask_math_follow_up)
        question_row.addWidget(self.math_question_input, 1)
        self.math_question_button = QPushButton("Ask")
        self.math_question_button.setObjectName("studyModeButton")
        self.math_question_button.clicked.connect(self._ask_math_follow_up)
        question_row.addWidget(self.math_question_button)
        sidebar_layout.addLayout(question_row)

        self.math_workspace_layout.addWidget(self.math_tutor_sidebar, 2)
        self.math_tutor_sidebar.hide()

        self.math_live_timer = QTimer(self)
        self.math_live_timer.setSingleShot(True)
        self.math_live_timer.setInterval(180)
        self.math_live_timer.timeout.connect(self._run_math_analysis)
        self.math_function_edit.textChanged.connect(self._schedule_live_math_plot)
        self.math_data_edit.textChanged.connect(self._schedule_live_math_plot)
        self.math_x_min.valueChanged.connect(self._schedule_live_math_plot)
        self.math_x_max.valueChanged.connect(self._schedule_live_math_plot)
        self.math_samples.valueChanged.connect(self._schedule_live_math_plot)
        self.math_mode_selector.currentIndexChanged.connect(self._set_math_input_mode)

        self.math_page_layout.addWidget(self.math_analysis_controls, 2)
        self.math_page_layout.addWidget(self.math_analysis_workspace, 5)
        math_scroll.setWidget(self.math_analysis_container)
        page_layout.addWidget(math_scroll)
        self.content_stack.addWidget(self.math_analysis_page)

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() == QEvent.WindowStateChange and hasattr(self, "window_maximize_button"):
            self._sync_window_maximize_state()

    def _toggle_window_maximize(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()
        self._sync_window_maximize_state()

    def _sync_window_maximize_state(self):
        if not hasattr(self, "window_maximize_button"):
            return
        is_max = self.isMaximized()
        self.window_maximize_button.setText("❐" if is_max else "▢")
        self.window_maximize_button.setToolTip("Restore Down" if is_max else "Maximize")

    def _schedule_live_math_plot(self):
        if self.math_analysis_page.isVisible():
            self.math_live_timer.start()

    def _set_math_input_mode(self, index: int):
        measured_data = index == 1
        self.math_function_row.setVisible(not measured_data)
        self.math_range_row.setVisible(not measured_data)
        self.math_data_edit.setVisible(measured_data)
        self.math_plot_button.setText("Analyze data" if measured_data else "Plot")
        self._schedule_live_math_plot()

    def _run_math_analysis(self):
        try:
            if self.math_mode_selector.currentIndex() == 0:
                result = analyse_function(
                    self.math_function_edit.text(),
                    self.math_x_min.value(),
                    self.math_x_max.value(),
                    self.math_samples.value(),
                )
            else:
                result = analyse_xy_data(self.math_data_edit.toPlainText())
        except ValueError as error:
            self.math_status.setText(str(error))
            return False

        self.math_analysis_result = result
        self.math_plot_view.set_plot_png(result.plot_png)
        self.math_results_view.setHtml(self._math_results_html(result))
        self.math_status.setText(f"Analysis ready. {len(result.x_values)} points plotted.")
        self.math_explanation_content = ""
        self._render_math_explanation("Press Explain with tutor for a step-by-step interpretation.")
        return True

    def open_math_analysis(self):
        self.active_workspace = "math"
        self.gce_subject = ""
        self.gce_system_prompt = ""
        self.gce_modes = []
        self.study_context_label.hide()
        self.mode_bar.hide()
        self.back_button.show()
        self.content_stack.setCurrentWidget(self.math_analysis_page)

    @staticmethod
    def _math_results_html(result: AnalysisResult) -> str:
        rows = "".join(
            "<tr><td style='padding:5px 12px 5px 0;color:#8eb6a4;'>"
            f"{html.escape(name)}</td><td style='padding:5px;color:#e5f5ec;font-weight:bold;'>"
            f"{html.escape(value)}</td></tr>"
            for name, value in result.metrics.items()
        )
        return (
            "<html><body style='font-family:DejaVu Sans,sans-serif;font-size:13px;'>"
            f"<p style='color:#ffe0a6;'>{html.escape(result.summary)}</p>"
            f"<table>{rows}</table></body></html>"
        )

    def _close_math_tutor_sidebar(self):
        self.math_tutor_sidebar.hide()

    def _explain_math_analysis(self):
        self.math_tutor_sidebar.show()
        if self.math_analysis_result is None and not self._run_math_analysis():
            return
        result = self.math_analysis_result
        if result is None:
            return
        if not self.base_url:
            self.statusBar().showMessage("Connect a local model to get a tutor explanation. The graph and statistics work offline.")
            return
        if self.chat_worker and self.chat_worker.isRunning():
            self.statusBar().showMessage("Wait for the current model response to finish before asking for an explanation.")
            return
        sample = list(zip(result.x_values[:30].tolist(), result.y_values[:30].tolist()))
        prompt = "\n".join((
            "You are a careful mathematics and data-analysis tutor.",
            "Explain what the computed graph and statistics show in plain language. Distinguish correlation from causation, name limitations, and never invent measurements or claim a trend the results do not support.",
            f"Analysis source: {result.source}",
            f"Computed metrics: {result.metrics}",
            f"Deterministic summary: {result.summary}",
            f"First plotted data pairs (up to 30): {sample}",
            "Use short Markdown headings and bullets. Explain the slope and R squared accurately if relevant.",
        ))
        self.math_analysis_active = True
        self.math_explanation_content = ""
        self._render_math_explanation("Preparing an explanation from the computed results...")
        self._start_chat_request(
            [
                {"role": "system", "content": prompt},
                {"role": "user", "content": "Explain this analysis and one useful next question to investigate."},
            ],
            analysis_panel=True,
        )

    def _render_math_explanation(self, placeholder: str = ""):
        body = self._format_message_content(self.math_explanation_content) if self.math_explanation_content else html.escape(placeholder)
        self.math_explanation_view.setHtml(
            "<html><body style='background:#091713;color:#e5f5ec;"
            "font-family:DejaVu Sans,sans-serif;font-size:13px;line-height:1.55;'>"
            f"{body}</body></html>"
        )

    def _ask_math_follow_up(self):
        self.math_tutor_sidebar.show()
        question = self.math_question_input.text().strip()
        if not question:
            return
        if self.math_analysis_result is None:
            self.math_status.setText("Plot an equation or dataset before asking a follow-up question.")
            return
        if not self.base_url:
            self.statusBar().showMessage("Connect a local model before asking follow-up questions.")
            return
        if self.chat_worker and self.chat_worker.isRunning():
            self.statusBar().showMessage("The current tutor answer is still running. Please wait a moment.")
            return
        result = self.math_analysis_result
        followup_prompt = "\n".join((
            "You are tutoring a student about a plotted mathematical relationship.",
            "Answer the follow-up question with direct, concrete reasoning tied to the current graph and summary statistics.",
            f"Current source: {result.source}",
            f"Current metrics: {result.metrics}",
            f"Current summary: {result.summary}",
            f"Student question: {question}",
        ))
        self.math_analysis_active = True
        self.math_explanation_content += f"\n\n**Student question:** {question}\n"
        self._render_math_explanation()
        self.math_question_input.clear()
        self._start_chat_request(
            [
                {"role": "system", "content": followup_prompt},
                {"role": "user", "content": question},
            ],
            analysis_panel=True,
        )

    def _animate_menu_widget(self, widget: QWidget, expanded: bool):
        animation = getattr(widget, "_menu_animation", None)
        if animation:
            animation.stop()
        if expanded:
            widget.show()
            start_height = widget.maximumHeight() if widget.maximumHeight() < 1_000_000 else 0
            widget.setMaximumHeight(start_height)
            end_height = widget.sizeHint().height()
        else:
            start_height = widget.height()
            end_height = 0
        duration = 0 if os.getenv("FUSERIO_REDUCE_MOTION") == "1" else 170
        animation = QPropertyAnimation(widget, b"maximumHeight", widget)
        widget._menu_animation = animation
        animation.setDuration(duration)
        animation.setStartValue(start_height)
        animation.setEndValue(end_height)
        animation.setEasingCurve(QEasingCurve.OutCubic)

        def finish():
            widget.setMaximumHeight(1_000_000 if expanded else 0)
            if not expanded:
                widget.hide()

        animation.finished.connect(finish)
        animation.start()

    def _toggle_chemistry_practicals(self):
        self.chemistry_practicals_open = not self.chemistry_practicals_open
        button = self.lab_subject_buttons["Chemistry"]
        button.setProperty("active", self.chemistry_practicals_open)
        button.setAccessibleDescription(
            "Expanded: choose a level and topic" if self.chemistry_practicals_open else "Collapsed"
        )
        button.style().unpolish(button)
        button.style().polish(button)
        self._animate_menu_widget(self.chemistry_practical_nav, self.chemistry_practicals_open)
        if self.chemistry_practicals_open:
            self.active_workspace = "practicals"
            self._set_chemistry_route("/chemistry")
            self._show_chemistry_prompt("Chemistry practicals", "Choose a level and topic from the sidebar to see the practical experiments.")
            self.back_button.show()
        else:
            self.chemistry_level_slug = ""
            self.chemistry_topic_number = None
            self.active_workspace = "gce"
            self.back_button.hide()

    def eventFilter(self, watched, event):
        if event.type() == QEvent.KeyPress and watched.objectName() in {"chemistryLevelButton", "chemistryTopicButton"}:
            key = event.key()
            if key in (Qt.Key_Up, Qt.Key_Down):
                if watched.objectName() == "chemistryLevelButton":
                    siblings = [entry["button"] for entry in self.chemistry_level_navs.values()]
                else:
                    siblings = [
                        button
                        for item in self.chemistry_level_navs.values()
                        for button in item["topic_buttons"].values()
                        if button.isVisible()
                    ]
                if watched in siblings and siblings:
                    step = -1 if key == Qt.Key_Up else 1
                    siblings[(siblings.index(watched) + step) % len(siblings)].setFocus()
                    return True
            if key == Qt.Key_Left and watched.objectName() == "chemistryTopicButton":
                for item in self.chemistry_level_navs.values():
                    if watched in item["topic_buttons"].values():
                        item["button"].setFocus()
                        return True
        return super().eventFilter(watched, event)

    def _select_chemistry_level(self, level_slug: str):
        level_data = self.chemistry_level_navs[level_slug]
        is_expanded = self.chemistry_level_slug == level_slug and level_data["topic_nav"].isVisible()
        for slug, item in self.chemistry_level_navs.items():
            active = slug == level_slug and not is_expanded
            item["button"].setChecked(active)
            item["button"].setProperty("active", active)
            item["button"].setAccessibleDescription("Expanded" if active else "Collapsed")
            item["button"].style().unpolish(item["button"])
            item["button"].style().polish(item["button"])
            self._animate_menu_widget(item["topic_nav"], active)
        self.chemistry_level_slug = "" if is_expanded else level_slug
        self.chemistry_topic_number = None
        for item in self.chemistry_level_navs.values():
            for topic_button in item["topic_buttons"].values():
                topic_button.setChecked(False)
                topic_button.setProperty("active", False)
        if is_expanded:
            self._set_chemistry_route("/chemistry")
            self._show_chemistry_prompt("Chemistry practicals", "Choose a level and topic from the sidebar to see the practical experiments.")
            return
        level = level_data["level"]
        self._set_chemistry_route(f"/chemistry/{level_slug}")
        self._show_chemistry_prompt(level.label, "Pick a topic to see its experiments.")

    def _select_chemistry_topic(self, level_slug: str, topic_number: int):
        level = level_by_slug(level_slug)
        if not level:
            return
        topic = next((item for item in level.topics if item.number == topic_number), None)
        if not topic:
            return
        self.chemistry_level_slug = level_slug
        self.chemistry_topic_number = topic_number
        for slug, nav in self.chemistry_level_navs.items():
            for number, button in nav["topic_buttons"].items():
                active = slug == level_slug and number == topic_number
                button.setChecked(active)
                button.setProperty("active", active)
                button.setAccessibleDescription("Current topic" if active else "Open topic")
                button.style().unpolish(button)
                button.style().polish(button)
        self._set_chemistry_route(f"/chemistry/{level_slug}/{topic_number}")
        self._show_chemistry_topic(level.label, topic)

    def _show_chemistry_prompt(self, heading: str, prompt: str):
        self.chemistry_practical_heading.setText(heading)
        self.chemistry_practical_subheading.setText(prompt)
        self._clear_layout(self.chemistry_practical_grid)
        self.content_stack.setCurrentWidget(self.chemistry_practical_page)

    def _show_chemistry_topic(self, level_label: str, topic: ChemistryTopic):
        self.chemistry_practical_heading.setText(f"{topic.number}. {topic.title}")
        self.chemistry_practical_subheading.setText(
            f"{level_label}  ·  {len(topic.experiments)} practical experiments"
        )
        self._clear_layout(self.chemistry_practical_grid)
        available_width = max(1, self.chemistry_practical_scroll.viewport().width() - 8)
        columns = 1 if available_width < 600 else max(2, min(4, available_width // 270))
        card_width = max(1, (available_width - self.chemistry_practical_grid.spacing() * (columns - 1)) // columns)
        for column in range(4):
            self.chemistry_practical_grid.setColumnStretch(column, 1 if column < columns else 0)
        for index, experiment in enumerate(topic.experiments):
            button = QPushButton()
            button.setObjectName("practicalExperimentCard")
            button.setFixedWidth(card_width)
            button.setMinimumHeight(190)
            button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
            card_layout = QVBoxLayout(button)
            card_layout.setContentsMargins(14, 14, 14, 14)
            card_layout.setSpacing(9)
            image_fallback = QLabel("FLASK  /  APPARATUS PREVIEW")
            image_fallback.setObjectName("practicalCardImage")
            image_fallback.setMinimumHeight(72)
            image_fallback.setAlignment(Qt.AlignCenter)
            image_fallback.setAttribute(Qt.WA_TransparentForMouseEvents)
            title_label = QLabel(experiment.title)
            title_label.setObjectName("practicalCardTitle")
            title_label.setWordWrap(True)
            title_label.setMinimumWidth(0)
            title_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
            title_label.setAttribute(Qt.WA_TransparentForMouseEvents)
            summary_label = QLabel(experiment.summary)
            summary_label.setObjectName("practicalCardSummary")
            summary_label.setWordWrap(True)
            summary_label.setMinimumWidth(0)
            summary_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
            summary_label.setAttribute(Qt.WA_TransparentForMouseEvents)
            card_layout.addWidget(image_fallback)
            card_layout.addWidget(title_label)
            card_layout.addWidget(summary_label, 1)
            button.setAccessibleName(f"{experiment.title}. {experiment.summary}")
            button.setAccessibleDescription(f"Open practical detail. Image path: {experiment.image}")
            button.clicked.connect(
                lambda _checked=False, slug=self.chemistry_level_slug, number=topic.number, item_id=experiment.id: self._open_practical_detail(slug, number, item_id)
            )
            self.chemistry_practical_grid.addWidget(button, index // columns, index % columns)
        self.content_stack.setCurrentWidget(self.chemistry_practical_page)

    def _open_practical_detail(self, level_slug: str, topic_number: int, experiment_id: str):
        result = experiment_by_route(level_slug, topic_number, experiment_id)
        if not result:
            return
        _topic, experiment = result
        self.chemistry_detail_title.setText(experiment.title)
        self.chemistry_detail_image.setText(f"⚗\nAPPARATUS PREVIEW\n\n{experiment.title}")
        self.chemistry_detail_image.setAccessibleName(experiment.image_alt)
        self.chemistry_detail_summary.setText(experiment.summary)
        self._set_chemistry_route(f"/chemistry/{level_slug}/{topic_number}/{experiment.id}")
        self.content_stack.setCurrentWidget(self.chemistry_detail_page)

    def _set_chemistry_route(self, route: str, push_history: bool = True):
        if push_history and route != self.chemistry_route:
            self.chemistry_route_history.append(self.chemistry_route)
        self.chemistry_route = route
        self.progress["chemistry_route"] = route
        if hasattr(self, "progress_save_timer"):
            self.progress_save_timer.start(300)

    def _restore_chemistry_route(self):
        route = self.progress.get("chemistry_route", "/chemistry")
        parts = [part for part in route.strip("/").split("/") if part]
        if not parts or parts[0] != "chemistry":
            return
        self.chemistry_practicals_open = True
        self.lab_subject_buttons["Chemistry"].setChecked(True)
        self.lab_subject_buttons["Chemistry"].setProperty("active", True)
        self.chemistry_practical_nav.show()
        self.chemistry_practical_nav.setMaximumHeight(1_000_000)
        self.active_workspace = "practicals"
        if len(parts) == 1:
            self._set_chemistry_route("/chemistry", push_history=False)
            self._show_chemistry_prompt("Chemistry practicals", "Choose a level and topic from the sidebar to see the practical experiments.")
            return
        level = level_by_slug(parts[1])
        if not level:
            return
        self.chemistry_level_slug = level.slug
        level_nav = self.chemistry_level_navs[level.slug]
        level_nav["button"].setChecked(True)
        level_nav["button"].setProperty("active", True)
        level_nav["topic_nav"].show()
        level_nav["topic_nav"].setMaximumHeight(1_000_000)
        if len(parts) == 2:
            self._set_chemistry_route(f"/chemistry/{level.slug}", push_history=False)
            self._show_chemistry_prompt(level.label, "Pick a topic to see its experiments.")
            return
        try:
            topic_number = int(parts[2])
        except ValueError:
            return
        self._select_chemistry_topic(level.slug, topic_number)
        if len(parts) > 3:
            self._open_practical_detail(level.slug, topic_number, parts[3])
        self.chemistry_route_history.clear()

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.hide()
                widget.setParent(None)
                widget.deleteLater()
            layout.invalidate()

    def open_experiment_library(self):
        self.active_workspace = "experiments"
        self.lab_screen = "home"
        self.back_button.hide()
        self.content_stack.setCurrentWidget(self.lab_home_page)

    def open_experiments_subject(self, subject: str):
        if subject not in LAB_SUBJECTS:
            return
        self.active_workspace = "experiments"
        self.gce_subject = ""
        self.gce_system_prompt = ""
        self.gce_modes = []
        self.lab_subject = subject
        self.lab_screen = "gallery"
        self.lab_gallery_heading.setText(f"{subject} experiments")
        self._clear_layout(self.lab_gallery_grid)
        self.lab_gallery_experiments = list(experiments_for_subject(subject))
        self._populate_lab_gallery()
        self.back_button.show()
        self.content_stack.setCurrentWidget(self.lab_gallery_page)

    def _populate_lab_gallery(self):
        self._clear_layout(self.lab_gallery_grid)
        available_width = max(1, self.lab_gallery_scroll.viewport().width() - 24)
        columns = max(1, min(4, available_width // 280))
        for index, experiment in enumerate(self.lab_gallery_experiments):
            detail = f"{experiment.subtitle}\nOPEN PRE-LAB  →"
            button = self._study_card(experiment.title, detail)
            button.setAccessibleName(f"Open {experiment.title} interactive simulation")
            button.clicked.connect(lambda _checked=False, value=experiment.identifier: self.open_experiment(value))
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            self.lab_gallery_grid.addWidget(button, index // columns, index % columns)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "mobile_menu_button"):
            mobile_layout = self.width() < 760
            self.sidebar.setVisible(not mobile_layout)
            self.mobile_menu_button.setVisible(mobile_layout)
            self.model_info.setVisible(not mobile_layout)
            self.connection_status.setVisible(not mobile_layout)
            brand = self.findChild(QLabel, "brand")
            if brand:
                brand.setVisible(not mobile_layout)
            self.header_layout.setContentsMargins(8 if mobile_layout else 16, 8 if mobile_layout else 10, 8 if mobile_layout else 16, 8 if mobile_layout else 10)
            self.header_layout.setSpacing(8 if mobile_layout else 18)
        if hasattr(self, "lab_gallery_experiments") and self.lab_gallery_experiments:
            self._populate_lab_gallery()
        if getattr(self, "chemistry_topic_number", None) is not None:
            level = level_by_slug(self.chemistry_level_slug)
            topic = next((item for item in level.topics if item.number == self.chemistry_topic_number), None) if level else None
            if level and topic and hasattr(self, "chemistry_practical_scroll"):
                self._show_chemistry_topic(level.label, topic)
        if hasattr(self, "math_page_layout"):
            if self.width() < 960:
                self.math_page_layout.setDirection(QBoxLayout.TopToBottom)
                self.math_analysis_controls.setMaximumWidth(16777215)
            else:
                self.math_page_layout.setDirection(QBoxLayout.LeftToRight)
                self.math_analysis_controls.setMaximumWidth(460)
        if hasattr(self, "math_workspace_layout") and hasattr(self, "math_tutor_sidebar"):
            if self.width() < 1050:
                self.math_workspace_layout.setDirection(QBoxLayout.TopToBottom)
                self.math_tutor_sidebar.setMinimumWidth(0)
            else:
                self.math_workspace_layout.setDirection(QBoxLayout.LeftToRight)
                self.math_tutor_sidebar.setMinimumWidth(320)
        if hasattr(self, "lab_detail_layout"):
            if self.width() < 960:
                self.lab_detail_layout.setDirection(QBoxLayout.TopToBottom)
                self.lab_tutor_panel.setMinimumWidth(0)
            else:
                self.lab_detail_layout.setDirection(QBoxLayout.LeftToRight)
                self.lab_tutor_panel.setMinimumWidth(320)
        if hasattr(self, "model_detail"):
            self.model_detail.setVisible(self.width() >= 760)

    def open_experiment(self, identifier: str):
        experiment = experiment_by_id(identifier)
        if not experiment:
            return
        self.active_workspace = "experiments"
        self.lab_screen = "detail"
        self.active_experiment = experiment
        self.lab_detail_title.setText(experiment.title)
        self.lab_detail_subtitle.setText(f"{experiment.subject.upper()}  /  VIRTUAL PRE-LAB  /  {experiment.subtitle}")
        self.lab_objective.setText(f"<b>INVESTIGATE</b>  {html.escape(experiment.objective)}")
        self.lab_equation.setHtml(self._format_message_content(model_equation(identifier)))
        self.lab_model_note.setText(f"MODEL LIMIT  /  {html.escape(model_limitation(identifier))}")
        self.lab_safety.setText(f"<b>SAFETY NOTE</b>  {html.escape(experiment.safety)}")
        if identifier in {"chemistry-playground", "circuit-playground"}:
            self.lab_canvas.set_playground(experiment)
        else:
            self.lab_canvas.set_experiment(experiment)
        self.lab_canvas.set_playback_rate(self.lab_speed_slider.value() / 100)
        self._build_lab_controls(experiment)
        self._update_lab_metrics()
        notes = self.progress.setdefault("experiments", {}).get(experiment.identifier, {})
        self.lab_prediction_edit.blockSignals(True)
        self.lab_observation_edit.blockSignals(True)
        self.lab_prediction_edit.setPlainText(notes.get("prediction", ""))
        self.lab_observation_edit.setPlainText(notes.get("observation", ""))
        self.lab_prediction_edit.blockSignals(False)
        self.lab_observation_edit.blockSignals(False)
        if identifier not in {"chemistry-playground", "circuit-playground"}:
            self.lab_canvas.play()
        self.lab_play_button.setText("Ⅱ  Pause simulation")
        self.back_button.show()
        self.content_stack.setCurrentWidget(self.lab_detail_page)

    def _build_lab_controls(self, experiment):
        self._clear_layout(self.lab_controls_layout)
        self.lab_parameter_labels = {}
        self.lab_parameter_sliders = {}
        playground_tools = {
            "chemistry-playground": (
                ("Add water +25 mL", "water"),
                ("Add salt +5 g", "salt"),
                ("Add acid +5 mL", "acid"),
                ("Add base +5 mL", "base"),
                ("Stir", "stir"),
            ),
            "circuit-playground": (
                ("Add battery", "battery"),
                ("Add wire", "wire"),
                ("Add bulb", "bulb"),
                ("Add / toggle switch", "switch"),
            ),
        }
        tools = playground_tools.get(experiment.identifier)
        if tools:
            tool_row = QWidget()
            tool_layout = QHBoxLayout(tool_row)
            tool_layout.setContentsMargins(0, 4, 0, 4)
            tool_layout.setSpacing(8)
            for label, item in tools:
                button = QPushButton(label)
                button.setObjectName("studyModeButton")
                button.clicked.connect(lambda _checked=False, value=item: self._add_playground_item(value))
                tool_layout.addWidget(button)
            self.lab_controls_layout.addWidget(tool_row)
            return

        if experiment.identifier == "titration":
            workbench = QWidget()
            workbench.setObjectName("titrationWorkbench")
            wb_layout = QVBoxLayout(workbench)
            wb_layout.setContentsMargins(0, 0, 0, 8)
            wb_layout.setSpacing(6)

            title_label = QLabel("🧪 TITRATION WORKBENCH (ADD INGREDIENTS)")
            title_label.setObjectName("labControlLabel")
            title_label.setStyleSheet("font-weight: bold; color: #57fabc; font-size: 11px;")
            wb_layout.addWidget(title_label)

            row1 = QHBoxLayout()
            row1.setSpacing(6)
            pipette_btn = QPushButton("🧪 Pipette 25 mL Acid")
            pipette_btn.setObjectName("studyModeButton")
            pipette_btn.setToolTip("Pipette 25.0 mL of analyte acid solution into the conical flask")
            pipette_btn.clicked.connect(lambda _=False: self._titration_action("pipette_acid"))

            indicator_btn = QPushButton("💧 Add Indicator (+1)")
            indicator_btn.setObjectName("studyModeButton")
            indicator_btn.setToolTip("Add indicator drops to the flask (Phenolphthalein, Methyl orange, Bromothymol blue)")
            indicator_btn.clicked.connect(lambda _=False: self._titration_action("add_indicator"))

            wash_btn = QPushButton("🚿 Wash Neck (+5 mL)")
            wash_btn.setObjectName("studyModeButton")
            wash_btn.setToolTip("Rinse flask neck with distilled water bottle")
            wash_btn.clicked.connect(lambda _=False: self._titration_action("wash_water"))

            row1.addWidget(pipette_btn)
            row1.addWidget(indicator_btn)
            row1.addWidget(wash_btn)
            wb_layout.addLayout(row1)

            row2 = QHBoxLayout()
            row2.setSpacing(6)
            drop_btn = QPushButton("💧 Dropwise (+0.10 mL)")
            drop_btn.setObjectName("studyModeButton")
            drop_btn.setStyleSheet("color: #57fabc; font-weight: bold;")
            drop_btn.setToolTip("Add single precision drop of titrant (0.10 mL)")
            drop_btn.clicked.connect(lambda _=False: self._titration_action("dropwise"))

            coarse_btn = QPushButton("💧 Add +1.0 mL")
            coarse_btn.setObjectName("studyModeButton")
            coarse_btn.setToolTip("Add 1.0 mL titrant when far from endpoint")
            coarse_btn.clicked.connect(lambda _=False: self._titration_action("add_1ml"))

            swirl_btn = QPushButton("🌀 Swirl Flask")
            swirl_btn.setObjectName("studyModeButton")
            swirl_btn.setToolTip("Swirl conical flask to mix solution and diffuse transient flashes")
            swirl_btn.clicked.connect(lambda _=False: self._titration_action("swirl"))

            refill_btn = QPushButton("↺ Refill Burette")
            refill_btn.setObjectName("studyModeButton")
            refill_btn.setToolTip("Reset titrant reading back to 0.00 mL")
            refill_btn.clicked.connect(lambda _=False: self._titration_action("fill_burette"))

            row2.addWidget(drop_btn)
            row2.addWidget(coarse_btn)
            row2.addWidget(swirl_btn)
            row2.addWidget(refill_btn)
            wb_layout.addLayout(row2)

            self.lab_controls_layout.addWidget(workbench)

        for parameter in experiment.parameters:
            row = QWidget()
            row_layout = QVBoxLayout(row)
            row_layout.setContentsMargins(0, 2, 0, 2)
            row_layout.setSpacing(2)
            label_row = QHBoxLayout()
            label = QLabel(parameter.label)
            label.setObjectName("labControlLabel")
            value_label = QLabel(f"{parameter.value} {parameter.unit}".strip())
            value_label.setObjectName("labControlValue")
            label_row.addWidget(label)
            label_row.addStretch(1)
            label_row.addWidget(value_label)
            row_layout.addLayout(label_row)
            slider = QSlider(Qt.Horizontal)
            slider.setRange(parameter.minimum, parameter.maximum)
            slider.setValue(parameter.value)
            slider.setAccessibleName(parameter.label)
            slider.valueChanged.connect(
                lambda value, item=parameter: self._lab_parameter_changed(item, value)
            )
            row_layout.addWidget(slider)
            self.lab_parameter_labels[parameter.key] = value_label
            self.lab_parameter_sliders[parameter.key] = slider
            self.lab_controls_layout.addWidget(row)

    def _sync_lab_runtime(self):
        if self.active_experiment and self.active_experiment.identifier == "titration":
            vol = float(self.lab_canvas.parameters.get("volume", 0))
            if "volume" in self.lab_parameter_sliders:
                slider = self.lab_parameter_sliders["volume"]
                slider.blockSignals(True)
                slider.setValue(int(vol))
                slider.blockSignals(False)
            if "volume" in self.lab_parameter_labels:
                self.lab_parameter_labels["volume"].setText(f"{vol:.1f} mL")
        self._update_lab_metrics()

    def _titration_action(self, action: str):
        self.lab_canvas.titration_action(action)
        vol = float(self.lab_canvas.parameters.get("volume", 0))
        if "volume" in self.lab_parameter_sliders:
            slider = self.lab_parameter_sliders["volume"]
            slider.blockSignals(True)
            slider.setValue(int(vol))
            slider.blockSignals(False)
        if "volume" in self.lab_parameter_labels:
            self.lab_parameter_labels["volume"].setText(f"{vol:.1f} mL")
        self._update_lab_metrics()

    def _add_playground_item(self, item: str):
        self.lab_canvas.add_playground_item(item)
        self._update_lab_metrics()

    def _lab_parameter_changed(self, parameter, value: int):
        self.lab_canvas.set_parameter(parameter.key, value)
        self.lab_parameter_labels[parameter.key].setText(f"{value} {parameter.unit}".strip())
        self._update_lab_metrics()

    def _update_lab_metrics(self):
        measurements = self.lab_canvas.measurements()
        if set(measurements) == set(self.lab_metric_labels):
            for name, value in measurements.items():
                self.lab_metric_labels[name].setText(value)
            return

        self._clear_layout(self.lab_metrics_layout)
        self.lab_metric_labels = {}
        for name, value in measurements.items():
            metric = QWidget()
            metric.setObjectName("labMetric")
            metric_layout = QVBoxLayout(metric)
            metric_layout.setContentsMargins(10, 7, 10, 7)
            metric_layout.setSpacing(3)
            name_label = QLabel(name)
            name_label.setObjectName("labMetricName")
            value_label = QLabel(value)
            value_label.setObjectName("labMetricValue")
            metric_layout.addWidget(name_label)
            metric_layout.addWidget(value_label)
            self.lab_metrics_layout.addWidget(metric, 1)
            self.lab_metric_labels[name] = value_label

    def _toggle_lab_simulation(self):
        if self.lab_canvas.running:
            self.lab_canvas.pause()
            self.lab_play_button.setText("▶  Resume simulation")
        else:
            self.lab_canvas.play()
            self.lab_play_button.setText("Ⅱ  Pause simulation")

    def _reset_lab_simulation(self):
        if self.active_experiment and self.active_experiment.identifier in {"chemistry-playground", "circuit-playground"}:
            self.lab_canvas.set_playground(self.active_experiment)
            self.lab_play_button.setText("Ⅱ  Pause simulation")
        else:
            self.lab_canvas.reset()
            self.lab_play_button.setText("▶  Run simulation")
        self._update_lab_metrics()

    def _schedule_lab_notes_save(self):
        self.lab_notes_save_timer.start(300)

    def _save_lab_notes(self):
        if not self.active_experiment:
            return
        self.progress.setdefault("experiments", {})[self.active_experiment.identifier] = {
            "prediction": self.lab_prediction_edit.toPlainText(),
            "observation": self.lab_observation_edit.toPlainText(),
            "updated": int(time.time()),
        }
        self._save_progress()

    def ask_lab_tutor(self):
        experiment = self.active_experiment
        if not experiment:
            return
        if not self.base_url:
            self.statusBar().showMessage("Connect a local model before asking the tutor about this experiment.")
            return
        current_readings = "; ".join(
            f"{name}: {value}" for name, value in self.lab_canvas.measurements().items()
        )
        prompt = "\n".join(
            (
                "You are a creative but precise science tutor for a pre-lab simulation.",
                "Respond as a lively, precise lab mentor. Format the answer as a short lab note with clear Markdown headings, concise bullets, an interpretation of the current readings, and one actionable next step.",
                "Use standard readable scientific notation such as degrees C, H2O, and x^2. Avoid emoji, decorative Unicode, box-drawing characters, unusual subscripts, and unsupported symbols.",
                f"The selected subject is {experiment.subject}; the experiment is {experiment.title}.",
                f"Learning objective: {experiment.objective}",
                f"Safety boundary: {experiment.safety}",
                f"Current readings: {current_readings}",
                f"Current playground components and ingredients: {self.lab_canvas.playground_items or 'preset experiment'}",
                "Use bullet points and short sections, not a generic textbook paragraph."
            )
        )
        self.lab_tutor_content = ""
        self.lab_tutor_stream.clear()
        self._render_lab_tutor_stream(waiting=True)
        self.lab_tutor_panel.setVisible(True)
        self.lab_tutor_panel.show()
        self.lab_tutor_panel.raise_()
        self.lab_side_panel_active = True
        self.study_context_label.setText(
            f"PRE-LAB TUTOR  /  {experiment.subject.upper()}  /  {experiment.title.upper()}"
        )
        self.study_context_label.show()
        self.mode_bar.hide()
        self.active_workspace = "experiments"
        self.lab_screen = "tutor"
        self.content_stack.setCurrentWidget(self.lab_detail_page)
        self._start_chat_request([
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Explain the experiment and tell me what to do next based on the current readings: {current_readings}."},
        ], side_panel=True)

    def _close_lab_tutor(self):
        self.lab_screen = "detail"
        self.lab_side_panel_active = False
        self.study_context_label.hide()
        self.lab_tutor_panel.hide()
        self.content_stack.setCurrentWidget(self.lab_detail_page)

    def _step_lab_simulation(self):
        self.lab_canvas.step()
        self._update_lab_metrics()

    def _set_lab_speed(self, value: int):
        rate = value / 100
        self.lab_canvas.set_playback_rate(rate)
        self.lab_speed_value.setText(f"{rate:.2f}×")

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
        self.active_workspace = "gce"
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
        self.active_workspace = "chat"
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
        if subject in SUBJECTS.get(level, {}).get(stream, []):
            self.gce_level = level
            self.gce_stream = stream
            self.gce_subject = subject
            self._populate_subjects()
        if self.progress.get("chemistry_route", "/chemistry") != "/chemistry":
            self._restore_chemistry_route()

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

    def navigate_back(self):
        if self.active_workspace == "practicals":
            parts = [part for part in self.chemistry_route.strip("/").split("/") if part]
            if len(parts) > 3:
                level_slug, topic_number = parts[1], int(parts[2])
                self._set_chemistry_route(f"/chemistry/{level_slug}/{topic_number}", push_history=False)
                self._select_chemistry_topic(level_slug, topic_number)
                self._set_chemistry_route(f"/chemistry/{level_slug}/{topic_number}", push_history=False)
            elif len(parts) == 3:
                level_slug = parts[1]
                self.chemistry_topic_number = None
                for nav in self.chemistry_level_navs.values():
                    for button in nav["topic_buttons"].values():
                        button.setChecked(False)
                        button.setProperty("active", False)
                        button.style().unpolish(button)
                        button.style().polish(button)
                level = level_by_slug(level_slug)
                if level:
                    self._set_chemistry_route(f"/chemistry/{level_slug}", push_history=False)
                    self._show_chemistry_prompt(level.label, "Pick a topic to see its experiments.")
            elif len(parts) == 2:
                self.chemistry_level_slug = ""
                for nav in self.chemistry_level_navs.values():
                    nav["button"].setChecked(False)
                    nav["button"].setProperty("active", False)
                    nav["button"].style().unpolish(nav["button"])
                    nav["button"].style().polish(nav["button"])
                    self._animate_menu_widget(nav["topic_nav"], False)
                self._set_chemistry_route("/chemistry", push_history=False)
                self._show_chemistry_prompt("Chemistry practicals", "Choose a level and topic from the sidebar to see the practical experiments.")
            else:
                self._toggle_chemistry_practicals()
            return
        if self.active_workspace == "experiments":
            if self.lab_screen == "tutor":
                self._close_lab_tutor()
            elif self.lab_screen == "detail":
                self.lab_screen = "gallery"
                self.content_stack.setCurrentWidget(self.lab_gallery_page)
            elif self.lab_screen == "gallery":
                self.lab_screen = "home"
                self.content_stack.setCurrentWidget(self.lab_home_page)
                self.back_button.hide()
            else:
                self.active_workspace = "gce"
                self.content_stack.setCurrentWidget(self.level_page)
                self.back_button.hide()
            return
        self.gce_back()

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
        if self.model_selector.currentData():
            self.progress["model_id"] = self.model_selector.currentData()
        try:
            save_progress(self.progress)
        except OSError as error:
            self.statusBar().showMessage(f"Could not save local study progress: {error}")

    def _load_demo_data(self):
        self._render_messages()

    def new_chat(self):
        if self.chat_worker and self.chat_worker.isRunning():
            self.stop_streaming()
        self.active_workspace = "chat"
        self.gce_level = ""
        self.gce_stream = ""
        self.gce_subject = ""
        self.gce_system_prompt = ""
        self.gce_modes = []
        self.gce_screen = "chat"
        self.lab_screen = "home"
        self.study_context_label.hide()
        self.mode_bar.hide()
        self.back_button.hide()
        self.content_stack.setCurrentWidget(self.chat_page)
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
        self.progress["model_id"] = model_id
        self._schedule_progress_save()
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
        if self.math_analysis_active:
            if content:
                self.math_explanation_content += content
                self._render_math_explanation()
            return
        if self.lab_side_panel_active:
            if content:
                self.lab_tutor_content += content
                self._render_lab_tutor_stream()
            return
        if not self.messages:
            return
        self.messages[-1]["reasoning"] += reasoning
        self.messages[-1]["content"] += content
        if content:
            self.messages[-1]["stream_chunks"] = self.messages[-1].get("stream_chunks", 0) + 1
        self.chat_render_dirty = True
        if not self.chat_render_timer.isActive():
            self.chat_render_timer.start()
        self._schedule_progress_save()

    def _flush_chat_render(self):
        if self.chat_render_dirty:
            self.chat_render_dirty = False
            self._render_messages()

    def _chat_error(self, message: str):
        if self.math_analysis_active:
            self.math_explanation_content += f"\n\n**Tutor connection issue:** {self._clean_model_text(message)}"
            self._render_math_explanation()
            self.math_analysis_active = False
            self.chat_worker = None
            self.send_button.setText("Send")
            self.send_button.setEnabled(bool(self.base_url))
            self.statusBar().showMessage(f"Analysis explanation failed: {message}")
            return
        if self.lab_side_panel_active:
            self.lab_tutor_content += f"\n\n**Tutor connection issue:** {self._clean_model_text(message)}"
            self._render_lab_tutor_stream(completed=True)
            self.lab_side_panel_active = False
            self.chat_worker = None
            self.send_button.setText("Send")
            self.send_button.setEnabled(bool(self.base_url))
            return
        if self.messages and self.messages[-1]["role"] == "assistant":
            self.messages[-1]["content"] += f"\n\n[Chat error: {message}]"
            self._render_messages()
        self.statusBar().showMessage(f"Chat failed: {message}")

    def _chat_finished(self):
        if self.math_analysis_active:
            self.math_analysis_active = False
            self.chat_worker = None
            self.send_button.setText("Send")
            self.send_button.setEnabled(bool(self.base_url))
            self.statusBar().showMessage("Math analysis explanation complete.")
            return
        if self.lab_side_panel_active:
            self._render_lab_tutor_stream(completed=True)
            self.lab_side_panel_active = False
            self.chat_worker = None
            self.send_button.setText("Send")
            self.send_button.setEnabled(bool(self.base_url))
            return
        self.chat_render_timer.stop()
        self._flush_chat_render()
        if self.messages and self.messages[-1]["role"] == "assistant":
            self.messages[-1]["streaming"] = False
            self._render_messages()
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
            'font-family:\'DejaVu Sans\',\'Noto Sans\',sans-serif;font-size:14px;margin:12px;">',
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
            is_streaming = bool(message.get("streaming"))
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
            elif is_streaming:
                content += '<span style="color:#65efb9;">▋</span>'
            generating_badge = (
                f'<span style="color:#70f2b7;">· GENERATING · '
                f'{message.get("stream_chunks", 0)} TOKENS</span>'
                if is_streaming
                else ""
            )

            document.append(
                '<table width="100%" cellspacing="0" cellpadding="0"><tr><td>'
                '<table width="100%" cellspacing="0" cellpadding="0" bgcolor="#0a1714" '
                'border="1" bordercolor="#1c4537"><tr>'
                '<td width="4" bgcolor="#59edaa"></td>'
                '<td style="padding:15px 19px;">'
                '<table width="100%" cellspacing="0" cellpadding="0"><tr>'
                '<td><span style="color:#70f2b7;font-weight:bold;">FUSERIO</span> '
                '<span style="color:#5c8375;">/ LOCAL INTELLIGENCE</span> '
                f'{generating_badge}</td>'
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
        side_panel: bool = False,
        analysis_panel: bool = False,
    ):
        if not self.base_url:
            self.statusBar().showMessage("Connect a local model before chatting.")
            return
        if side_panel:
            self.lab_side_panel_active = True
            self.lab_tutor_content = ""
            self.lab_tutor_stream.clear()
            self._render_lab_tutor_stream(waiting=True)
        elif not analysis_panel and self.messages and self.messages[-1]["role"] == "assistant":
            self.messages[-1]["streaming"] = True
            self.messages[-1]["stream_chunks"] = 0
            self._render_messages()
        self.send_button.setText("Stop")
        self.send_button.setEnabled(True)
        self.statusBar().showMessage("Generating locally...")
        self.chat_worker = ChatWorker(self.base_url, self.api_key, api_messages, parameters)
        self.chat_worker.chunk.connect(self._append_stream_chunk)
        self.chat_worker.error.connect(self._chat_error)
        self.chat_worker.finished.connect(self._chat_finished)
        self.chat_worker.start()

    @staticmethod
    def _clean_model_text(content: str) -> str:
        cleaned = unicodedata.normalize("NFC", content)
        replacements = {
            "â€™": "'",
            "â€˜": "'",
            "â€œ": '"',
            "â€�": '"',
            "â€“": "-",
            "â€”": "-",
            "â€¦": "...",
            "Â°": " degrees ",
            "Ã—": " x ",
            "â�": " ",
        }
        for broken, readable in replacements.items():
            cleaned = cleaned.replace(broken, readable)
        cleaned = re.sub(r"[ \t]*(?:\ufffd|[□■▯▮◻◼])+[ \t]*", " ", cleaned)
        cleaned = re.sub(r"[ \t]+\n", "\n", cleaned)
        return cleaned

    def _render_lab_tutor_stream(self, waiting: bool = False, completed: bool = False):
        body = self._format_message_content(self.lab_tutor_content)
        if waiting and not self.lab_tutor_content:
            body = '<p style="color:#a7c7b7;">Building your lab note...</p>'
        footer = (
            '<p style="color:#69d9a8;font-size:10px;font-weight:bold;">LAB NOTE READY</p>'
            if completed
            else '<p style="color:#66cbb4;font-size:10px;">LIVE LAB NOTES</p>'
        )
        self.lab_tutor_stream.setHtml(
            '<html><head><style>'
            'body{background:#071410;color:#e5f5ec;font-family:"DejaVu Sans","Noto Sans",sans-serif;'
            'font-size:14px;line-height:1.65;margin:10px;}'
            'h1,h2,h3{color:#70edb6;margin-top:18px;margin-bottom:8px;}'
            'strong{color:#ffe0a6;}li{margin:5px 0;}hr{border:0;border-top:1px solid #285244;}'
            'code{color:#a8ebca;background:#13261f;}'
            '</style></head><body>'
            '<p style="color:#62d8d0;font-size:10px;font-weight:bold;">FUSERIO / FIELD NOTE</p>'
            f'{body}{footer}</body></html>'
        )
        scrollbar = self.lab_tutor_stream.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    @staticmethod
    def _format_message_content(content: str) -> str:
        content = MainWindow._clean_model_text(content)
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
            "sin": "sin ", "cos": "cos ", "tan": "tan ",
            "log": "log ", "ln": "ln ", "propto": "∝",
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
        self.lab_notes_save_timer.stop()
        self._save_lab_notes()
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
    window.showMaximized()
    app.exec()
