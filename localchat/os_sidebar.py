import os

from PySide6.QtCore import QPoint, QPointF, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont, QIcon, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")


class OSSidebar(QFrame):
    """Left Frosted Glass OS App Launcher Rail."""

    navigate = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("osSidebar")
        self.setFixedWidth(70)

        self.current_screen = "desktop"
        self.buttons: dict[str, QPushButton] = {}

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 16, 10, 16)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignHCenter)

        # 1. Top Logo Button
        self.logo_btn = QPushButton(self)
        self.logo_btn.setFixedSize(46, 46)
        self.logo_btn.setCursor(Qt.PointingHandCursor)
        self.logo_btn.setToolTip("Fuserio OS — Educational Desktop for Cameroonian Students")
        self.logo_btn.setStyleSheet("""
            QPushButton {
                background: rgba(14, 46, 82, 160);
                border: 1.5px solid #58d8d0;
                border-radius: 23px;
                padding: 4px;
            }
            QPushButton:hover {
                background: rgba(40, 160, 220, 220);
                border: 2px solid #57fabc;
            }
        """)
        logo_path = os.path.join(ASSETS_DIR, "fus-fuserio.png")
        if os.path.exists(logo_path):
            self.logo_btn.setIcon(QIcon(logo_path))
            self.logo_btn.setIconSize(QSize(36, 36))
        self.logo_btn.clicked.connect(lambda: self.navigate.emit("desktop"))
        layout.addWidget(self.logo_btn)

        layout.addSpacing(6)

        # 2. App Rail Buttons
        apps = [
            ("desktop", "🏠", "Home / Desktop (Fuserio OS)"),
            ("gce", "⊞", "GCE Syllabus & Subjects"),
            ("lab", "📁", "Interactive Science Lab (Experiments)"),
            ("chat", ">_", "Neural Terminal (Offline AI Tutor)"),
            ("math", "📊", "Math Data Lab (Plotter & Regression)"),
            ("settings", "⚙", "Settings & Local Models Manager"),
        ]

        for action_key, icon_str, tooltip in apps:
            btn = QPushButton(icon_str, self)
            btn.setFixedSize(44, 44)
            btn.setToolTip(tooltip)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda _=False, k=action_key: self._on_btn_clicked(k))
            layout.addWidget(btn)
            self.buttons[action_key] = btn

        layout.addStretch(1)

        # 3. Power Button
        self.power_btn = QPushButton("⏻", self)
        self.power_btn.setFixedSize(42, 42)
        self.power_btn.setToolTip("Exit Fuserio OS")
        self.power_btn.setCursor(Qt.PointingHandCursor)
        self.power_btn.setStyleSheet("""
            QPushButton {
                background: rgba(24, 38, 56, 120);
                border: 1px solid rgba(255, 107, 129, 90);
                border-radius: 21px;
                color: #ff6b81;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #ff4757;
                border: 1px solid #ffffff;
                color: #ffffff;
            }
        """)
        self.power_btn.clicked.connect(self._show_power_menu)
        layout.addWidget(self.power_btn)

        # 4. Status Indicator Pill (Green LED: Offline Local AI Ready)
        self.status_pill = QFrame(self)
        self.status_pill.setFixedSize(44, 20)
        self.status_pill.setToolTip("Offline First • 100% Local AI Active")
        self.status_pill.setStyleSheet("""
            QFrame {
                background: rgba(8, 28, 48, 180);
                border: 1px solid rgba(87, 250, 188, 90);
                border-radius: 10px;
            }
        """)
        pill_layout = QHBoxLayout(self.status_pill)
        pill_layout.setContentsMargins(0, 0, 0, 0)
        pill_layout.setAlignment(Qt.AlignCenter)

        dot = QLabel("●", self.status_pill)
        dot.setStyleSheet("color: #57fabc; font-size: 9px;")
        pill_layout.addWidget(dot)

        layout.addWidget(self.status_pill)

        self._update_styles()

    def set_active_screen(self, screen_key: str):
        self.current_screen = screen_key
        self._update_styles()

    def _on_btn_clicked(self, action_key: str):
        self.current_screen = action_key
        self._update_styles()
        self.navigate.emit(action_key)

    def _update_styles(self):
        for key, btn in self.buttons.items():
            font_family = "'JetBrains Mono', 'Fira Code', monospace" if key == "chat" else "sans-serif"
            font_size = "15px" if key == "chat" else "18px"
            if key == self.current_screen:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: rgba(40, 160, 220, 200);
                        border: 1.5px solid #57fabc;
                        border-radius: 16px;
                        color: #ffffff;
                        font-family: {font_family};
                        font-size: {font_size};
                        font-weight: bold;
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: rgba(12, 38, 66, 110);
                        border: 1px solid rgba(88, 216, 208, 60);
                        border-radius: 16px;
                        color: #58d8d0;
                        font-family: {font_family};
                        font-size: {font_size};
                        font-weight: bold;
                    }}
                    QPushButton:hover {{
                        background: rgba(40, 160, 220, 140);
                        border: 1px solid #58d8d0;
                        color: #ffffff;
                    }}
                """)

    def _show_power_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background: rgba(4, 18, 38, 0.98);
                border: 1.5px solid #58d8d0;
                border-radius: 14px;
                padding: 6px;
                color: #eaf7f5;
                font-family: sans-serif;
                font-size: 13px;
                font-weight: 600;
            }
            QMenu::item {
                padding: 10px 24px 10px 14px;
                border-radius: 8px;
                margin: 2px 0;
            }
            QMenu::item:selected {
                background: rgba(40, 160, 220, 0.35);
                color: #ffffff;
                border: 1px solid #57fabc;
            }
            QMenu::separator {
                height: 1px;
                background: rgba(88, 216, 208, 0.25);
                margin: 4px 6px;
            }
        """)
        action_shutdown = menu.addAction("⏻  Shut down")
        action_restart = menu.addAction("🔄  Restart")
        action_lock = menu.addAction("🔒  Lock screen")
        menu.addSeparator()
        action_cancel = menu.addAction("✕  Cancel")

        pos = self.power_btn.mapToGlobal(QPoint(self.power_btn.width() + 12, -70))
        selected = menu.exec(pos)
        if selected == action_shutdown:
            self.navigate.emit("shutdown")
        elif selected == action_restart:
            self.navigate.emit("restart")
        elif selected == action_lock:
            self.navigate.emit("lock")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        grad = QLinearGradient(0, 0, self.width(), self.height())
        grad.setColorAt(0, QColor(6, 22, 42, 230))
        grad.setColorAt(0.5, QColor(4, 16, 34, 240))
        grad.setColorAt(1, QColor(3, 12, 26, 245))

        painter.setBrush(grad)
        painter.setPen(QPen(QColor(88, 216, 208, 75), 1.2))
        painter.drawRoundedRect(rect, 22, 22)
