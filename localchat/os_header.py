import os

from PySide6.QtCore import QPoint, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont, QIcon, QLinearGradient, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class SpotlightSearchBar(QLineEdit):
    """Frosted Glass Capsule Search Bar."""

    search_triggered = Signal(str)
    open_item_requested = Signal(str, str)  # category, item_id_or_query

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("🔍  Search GCE subjects, practicals, formulas, or ask Fuserio AI...")
        self.setFixedHeight(38)
        self.setMinimumWidth(380)
        self.setMaximumWidth(520)
        self.setAccessibleName("Spotlight search subjects, topics and experiments")
        self.setStyleSheet("""
            QLineEdit {
                background: rgba(8, 30, 56, 175);
                border: 1px solid rgba(88, 216, 208, 90);
                border-radius: 19px;
                color: #e8f7ef;
                padding: 4px 18px 4px 18px;
                font-size: 12px;
                selection-background-color: #58d8d0;
                selection-color: #031422;
            }
            QLineEdit:focus {
                background: rgba(12, 42, 78, 220);
                border: 1.5px solid #57fabc;
                color: #ffffff;
            }
        """)

        self.popup = SpotlightSearchPopup(self)
        self.popup.hide()
        self.popup.item_selected.connect(self._on_popup_item_selected)

        self.textChanged.connect(self._on_text_changed)
        self.returnPressed.connect(self._on_return_pressed)

    def _on_text_changed(self, text: str):
        query = text.strip()
        if not query:
            self.popup.hide()
            return

        self.popup.filter_results(query)
        if not self.popup.isVisible():
            # Position popup right beneath search bar
            pos = self.mapToGlobal(QPoint(0, self.height() + 4))
            self.popup.move(pos)
            self.popup.setFixedWidth(self.width())
            self.popup.show()

    def _on_return_pressed(self):
        query = self.text().strip()
        if query:
            self.popup.hide()
            self.search_triggered.emit(query)

    def _on_popup_item_selected(self, category: str, identifier: str):
        self.popup.hide()
        self.clear()
        self.open_item_requested.emit(category, identifier)

    def focusOutEvent(self, event):
        # Allow small delay for item clicks
        super().focusOutEvent(event)


class SpotlightSearchPopup(QFrame):
    """Dropdown overlay displaying instant matching results across subjects, practicals, and AI."""

    item_selected = Signal(str, str)  # category, id

    def __init__(self, parent=None):
        super().__init__(None, Qt.Popup | Qt.FramelessWindowHint)
        self.setObjectName("spotlightSearchPopup")
        self.setFixedHeight(260)
        self.setStyleSheet("""
            QFrame#spotlightSearchPopup {
                background: rgba(6, 22, 42, 245);
                border: 1.5px solid #58d8d0;
                border-radius: 14px;
            }
            QListWidget {
                background: transparent;
                border: none;
                color: #e8f7ef;
                font-size: 12px;
                padding: 6px;
            }
            QListWidget::item {
                padding: 8px 12px;
                border-radius: 8px;
            }
            QListWidget::item:hover {
                background: rgba(40, 160, 220, 140);
                color: #ffffff;
            }
            QListWidget::item:selected {
                background: rgba(87, 250, 188, 180);
                color: #031422;
                font-weight: bold;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        self.list_widget = QListWidget(self)
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.list_widget)

    def filter_results(self, query: str):
        self.list_widget.clear()
        q = query.lower()

        # Database of searchable entities
        searchable = [
            ("subject", "Chemistry", "🧪 Chemistry — Practicals, Organic & GCE syllabus"),
            ("subject", "Biology", "🧬 Biology — Genetics, Cell biology & Ecology"),
            ("subject", "Physics", "⚛ Physics — Mechanics, Optics & Electricity"),
            ("subject", "Mathematics", "➗ Mathematics — Calculus, Data Analyst & Grapher"),
            ("subject", "Computer Science", "💻 Computer Science — Algorithms & Python"),
            ("lab", "titration", "🧪 Lab: Acid-Base Titration (Volumetric Analysis)"),
            ("lab", "reaction-rate", "⚡ Lab: Reaction Rate (Gas Syringe Kinetics)"),
            ("lab", "salt-solubility", "🔥 Lab: Salt Solubility (Thermal Crystallisation)"),
            ("lab", "precipitation-salts", "💧 Lab: Preparation of Salts (Gravity Filtration)"),
            ("lab", "projectile-motion", "🎯 Lab: Projectile Motion & Kinematics"),
            ("lab", "ohms-law", "⚡ Lab: Ohm's Law & Circuit Simulation"),
            ("lab", "pendulum-lab", "⏱ Lab: Simple Pendulum & Gravitational Period"),
            ("math", "math-lab", "📊 Math Data Lab: Function Plotter & XY Regression"),
            ("chat", "ai-workspace", ">_ Terminal: Fuserio Neural Offline AI Tutor"),
        ]

        # Add "Terminal Prompt" top option
        ask_item = QListWidgetItem(f">_ Terminal: \"{query}\"")
        ask_item.setData(Qt.UserRole, ("ai_prompt", query))
        self.list_widget.addItem(ask_item)

        matches = 0
        for category, identifier, label in searchable:
            if q in identifier.lower() or q in label.lower():
                item = QListWidgetItem(label)
                item.setData(Qt.UserRole, (category, identifier))
                self.list_widget.addItem(item)
                matches += 1
                if matches >= 8:
                    break

        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

    def _on_item_clicked(self, item: QListWidgetItem):
        data = item.data(Qt.UserRole)
        if data:
            self.item_selected.emit(data[0], data[1])


class OSHeader(QWidget):
    """Top OS Navigation & Window Control Bar."""

    back_clicked = Signal()
    minimize_clicked = Signal()
    maximize_clicked = Signal()
    close_clicked = Signal()
    search_triggered = Signal(str)
    item_opened = Signal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("osHeaderBar")
        self.setFixedHeight(54)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(14)

        # Back / Breadcrumb button
        self.back_button = QPushButton("← Desktop")
        self.back_button.setObjectName("osBackButton")
        self.back_button.setCursor(Qt.PointingHandCursor)
        self.back_button.setToolTip("Return to Fuserio OS Desktop")
        self.back_button.setStyleSheet("""
            QPushButton#osBackButton {
                background: rgba(18, 54, 88, 140);
                border: 1px solid rgba(88, 216, 208, 120);
                border-radius: 15px;
                color: #57fabc;
                font-size: 11px;
                font-weight: bold;
                padding: 6px 14px;
            }
            QPushButton#osBackButton:hover {
                background: rgba(40, 160, 220, 190);
                border: 1px solid #ffffff;
                color: #ffffff;
            }
        """)
        self.back_button.clicked.connect(self.back_clicked.emit)
        self.back_button.hide()
        layout.addWidget(self.back_button)

        # Breadcrumb label
        self.breadcrumb_label = QLabel("")
        self.breadcrumb_label.setStyleSheet("color: #b4e5dc; font-size: 12px; font-weight: bold;")
        self.breadcrumb_label.hide()
        layout.addWidget(self.breadcrumb_label)

        layout.addStretch(1)

        # Spotlight Search Bar (Centered)
        self.search_bar = SpotlightSearchBar(self)
        self.search_bar.search_triggered.connect(self.search_triggered.emit)
        self.search_bar.open_item_requested.connect(self.item_opened.emit)
        layout.addWidget(self.search_bar)

        layout.addStretch(1)

        # Local Model / Hardware Pill
        self.model_status = QLabel("⚡ LOCAL AI: READY")
        self.model_status.setStyleSheet("""
            color: #58d8d0;
            background: rgba(8, 28, 54, 180);
            border: 1px solid rgba(88, 216, 208, 70);
            border-radius: 14px;
            padding: 5px 12px;
            font-size: 10px;
            font-weight: bold;
        """)
        layout.addWidget(self.model_status)

        # Window Controls (—, ▢, ✕)
        controls = QWidget()
        ctrl_layout = QHBoxLayout(controls)
        ctrl_layout.setContentsMargins(0, 0, 0, 0)
        ctrl_layout.setSpacing(6)

        self.btn_min = self._create_win_btn("—", "Minimize")
        self.btn_min.clicked.connect(self.minimize_clicked.emit)

        self.btn_max = self._create_win_btn("▢", "Maximize")
        self.btn_max.clicked.connect(self.maximize_clicked.emit)

        self.btn_close = self._create_win_btn("✕", "Close", is_close=True)
        self.btn_close.clicked.connect(self.close_clicked.emit)

        ctrl_layout.addWidget(self.btn_min)
        ctrl_layout.addWidget(self.btn_max)
        ctrl_layout.addWidget(self.btn_close)

        layout.addWidget(controls)

    def _create_win_btn(self, text: str, tooltip: str, is_close: bool = False) -> QPushButton:
        btn = QPushButton(text)
        btn.setFixedSize(28, 28)
        btn.setToolTip(tooltip)
        btn.setCursor(Qt.PointingHandCursor)
        if is_close:
            btn.setStyleSheet("""
                QPushButton {
                    background: rgba(30, 40, 60, 120);
                    border: 1px solid rgba(88, 216, 208, 60);
                    border-radius: 14px;
                    color: #e8f7ef;
                    font-size: 11px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: #ff4757;
                    border: 1px solid #ff6b81;
                    color: #ffffff;
                }
            """)
        else:
            btn.setStyleSheet("""
                QPushButton {
                    background: rgba(30, 40, 60, 120);
                    border: 1px solid rgba(88, 216, 208, 60);
                    border-radius: 14px;
                    color: #e8f7ef;
                    font-size: 11px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: rgba(40, 160, 220, 180);
                    border: 1px solid #57fabc;
                    color: #ffffff;
                }
            """)
        return btn

    def set_breadcrumb(self, text: str):
        if text:
            self.breadcrumb_label.setText(text)
            self.breadcrumb_label.show()
            self.back_button.show()
        else:
            self.breadcrumb_label.hide()
            self.back_button.hide()
