import html
import os
from typing import Any

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, Signal
from PySide6.QtGui import (
    QColor,
    QFont,
    QFontMetrics,
    QIcon,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QRadialGradient,
)
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from localchat.gce import SUBJECTS, suggested_topic_areas, LEARNING_MODES
from localchat.lab_data import experiments_for_subject
from localchat.chemistry_practicals import CHEMISTRY

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
SUBJECT_ASSETS = os.path.join(ASSETS_DIR, "subject_folders")

EXPERIMENT_TOPIC_METADATA = {
    # Chemistry
    "titration": {
        "topic": "Acids, Bases & Salts",
        "color": "#57fabc",
        "symbol": "⚗",
        "badge": "TITRATION",
    },
    "reaction-rate": {
        "topic": "Reaction Kinetics",
        "color": "#ff9f43",
        "symbol": "⏱",
        "badge": "KINETICS",
    },
    "salt-solubility": {
        "topic": "Solubility & Thermal",
        "color": "#58d8d0",
        "symbol": "🔥",
        "badge": "SOLUBILITY",
    },
    "precipitation-salts": {
        "topic": "Precipitation & Salts",
        "color": "#a8ff78",
        "symbol": "🧪",
        "badge": "PRECIPITATE",
    },
    "chemistry-playground": {
        "topic": "Chemical Synthesis",
        "color": "#3867d6",
        "symbol": "⚛",
        "badge": "WORKBENCH",
    },
    # Physics
    "projectile-motion": {
        "topic": "Kinematics & Dynamics",
        "color": "#58d8d0",
        "symbol": "🎯",
        "badge": "MECHANICS",
    },
    "pendulum-lab": {
        "topic": "Oscillations & Gravity",
        "color": "#70a1ff",
        "symbol": "⌛",
        "badge": "HARMONIC",
    },
    "ohms-law": {
        "topic": "Current Electricity",
        "color": "#fed330",
        "symbol": "⚡",
        "badge": "CIRCUITS",
    },
    "circuit-playground": {
        "topic": "Electronics & Circuits",
        "color": "#fed330",
        "symbol": "🔌",
        "badge": "ELECTRONICS",
    },
    # Biology
    "diffusion": {
        "topic": "Cell Transport & Osmosis",
        "color": "#a8ff78",
        "symbol": "🧫",
        "badge": "DIFFUSION",
    },
    "enzyme-activity": {
        "topic": "Enzymology & Kinetics",
        "color": "#ff7186",
        "symbol": "🔬",
        "badge": "ENZYMOLOGY",
    },
    "natural-selection": {
        "topic": "Genetics & Evolution",
        "color": "#2ed573",
        "symbol": "🧬",
        "badge": "GENETICS",
    },
    # Mathematics
    "math_plot": {
        "topic": "Calculus & Curves",
        "color": "#3867d6",
        "symbol": "📈",
        "badge": "CALCULUS",
    },
    "math_data": {
        "topic": "Statistics & Regression",
        "color": "#a29bfe",
        "symbol": "📊",
        "badge": "STATISTICS",
    },
}


class ExplorerFolderCard(QFrame):
    """Glossy 3D Folder / Item Card in OS Explorer."""

    clicked = Signal(str, dict)  # item_type, item_data

    def __init__(
        self,
        item_type: str,
        title: str,
        subtitle: str,
        accent_color: str,
        icon_path: str = "",
        item_data: dict | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self.item_type = item_type
        self.title = title
        self.subtitle = subtitle
        self.accent_color = QColor(accent_color)
        self.item_data = item_data or {}
        self.hovered = False
        self.elevation_offset = 0

        self.setFixedSize(164, 168)
        self.setCursor(Qt.PointingHandCursor)
        self.setAccessibleName(f"{title}: {subtitle}")

        self.icon_pixmap = QPixmap(icon_path) if icon_path and os.path.exists(icon_path) else QPixmap()

    def enterEvent(self, event):
        self.hovered = True
        self.elevation_offset = -6
        self.update()
        try:
            super().enterEvent(event)
        except Exception:
            pass

    def leaveEvent(self, event):
        self.hovered = False
        self.elevation_offset = 0
        self.update()
        try:
            super().leaveEvent(event)
        except Exception:
            pass

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.item_type, self.item_data)
        super().mousePressEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        w = float(self.width())
        h = float(self.height())
        dy = float(self.elevation_offset)

        tile_w = 146.0
        tile_h = 106.0
        tile_x = (w - tile_w) / 2.0
        tile_y = 10.0 + dy

        tile_rect = QRectF(tile_x, tile_y, tile_w, tile_h)

        # 1. Hover Glow
        if self.hovered:
            glow_grad = QRadialGradient(tile_rect.center(), tile_w * 0.8)
            glow_col = QColor(self.accent_color)
            glow_col.setAlpha(70)
            glow_grad.setColorAt(0, glow_col)
            glow_grad.setColorAt(0.7, QColor(glow_col.red(), glow_col.green(), glow_col.blue(), 20))
            glow_grad.setColorAt(1, QColor(0, 0, 0, 0))
            painter.setPen(Qt.NoPen)
            painter.setBrush(glow_grad)
            painter.drawRoundedRect(tile_rect.adjusted(-10, -10, 10, 10), 20, 20)

        # 2. Translucent Glass Tile
        glass_grad = QLinearGradient(tile_x, tile_y, tile_x, tile_y + tile_h)
        if self.hovered:
            glass_grad.setColorAt(0, QColor(14, 46, 82, 190))
            glass_grad.setColorAt(1, QColor(8, 28, 54, 215))
            border_pen = QPen(self.accent_color, 1.5)
        else:
            glass_grad.setColorAt(0, QColor(10, 34, 64, 140))
            glass_grad.setColorAt(1, QColor(5, 20, 42, 175))
            border_pen = QPen(QColor(88, 216, 208, 65), 1.0)

        painter.setPen(border_pen)
        painter.setBrush(glass_grad)
        painter.drawRoundedRect(tile_rect, 16, 16)

        # Top gloss highlight
        hl_rect = QRectF(tile_x + 2, tile_y + 2, tile_w - 4, 28)
        hl_grad = QLinearGradient(hl_rect.topLeft(), hl_rect.bottomLeft())
        hl_grad.setColorAt(0, QColor(255, 255, 255, 35))
        hl_grad.setColorAt(1, QColor(255, 255, 255, 0))
        painter.setPen(Qt.NoPen)
        painter.setBrush(hl_grad)
        painter.drawRoundedRect(hl_rect, 14, 14)

        # 3. Center Icon or Folder Representation
        if not self.icon_pixmap.isNull() and self.item_type != "experiment":
            icon_target = 68
            icon_scaled = self.icon_pixmap.scaled(
                icon_target,
                icon_target,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
            actual_x = tile_x + (tile_w - icon_scaled.width()) / 2.0
            actual_y = tile_y + 16
            painter.drawPixmap(int(actual_x), int(actual_y), icon_scaled)
        else:
            # Vector stylized folder icon
            self._draw_vector_folder(painter, tile_x + (tile_w - 74) / 2.0, tile_y + 16)

        # 4. Item Title and Subtitle Below
        title_font = QFont("sans-serif", 9, QFont.Bold if self.hovered else QFont.Normal)
        painter.setFont(title_font)
        painter.setPen(QColor("#ffffff") if self.hovered else QColor("#e0f4ee"))
        fm = QFontMetrics(title_font)
        elided_title = fm.elidedText(self.title, Qt.ElideMiddle, int(w - 12))
        title_rect = QRectF(4, tile_y + tile_h + 4, w - 8, 18)
        painter.drawText(title_rect, Qt.AlignCenter, elided_title)

        sub_font = QFont("sans-serif", 8, QFont.Normal)
        painter.setFont(sub_font)
        painter.setPen(QColor("#89b6a8"))
        fm_sub = QFontMetrics(sub_font)
        elided_sub = fm_sub.elidedText(self.subtitle, Qt.ElideRight, int(w - 12))
        sub_rect = QRectF(4, tile_y + tile_h + 23, w - 8, 16)
        painter.drawText(sub_rect, Qt.AlignCenter, elided_sub)

    def _draw_vector_folder(self, painter: QPainter, x: float, y: float):
        painter.save()
        # 1. Back tab
        tab_path = QPainterPath()
        tab_path.moveTo(x + 4, y + 14)
        tab_path.lineTo(x + 28, y + 14)
        tab_path.lineTo(x + 36, y + 22)
        tab_path.lineTo(x + 68, y + 22)
        tab_path.quadTo(x + 72, y + 22, x + 72, y + 26)
        tab_path.lineTo(x + 72, y + 60)
        tab_path.lineTo(x + 2, y + 60)
        tab_path.lineTo(x + 2, y + 18)
        tab_path.quadTo(x + 2, y + 14, x + 6, y + 14)
        tab_path.closeSubpath()

        tab_grad = QLinearGradient(x, y + 14, x, y + 60)
        tab_grad.setColorAt(0, self.accent_color.darker(120))
        tab_grad.setColorAt(1, self.accent_color.darker(170))
        painter.setBrush(tab_grad)
        painter.setPen(QPen(self.accent_color.lighter(130), 1.2))
        painter.drawPath(tab_path)

        # 2. Front body (Glossy 3D folder flap)
        front_rect = QRectF(x + 2, y + 23, 70, 43)
        front_grad = QLinearGradient(front_rect.topLeft(), front_rect.bottomLeft())
        front_grad.setColorAt(0, self.accent_color)
        front_grad.setColorAt(0.55, self.accent_color.darker(115))
        front_grad.setColorAt(1, self.accent_color.darker(145))
        painter.setBrush(front_grad)
        painter.setPen(QPen(QColor(255, 255, 255, 110), 1.2))
        painter.drawRoundedRect(front_rect, 7, 7)

        # 3. Top Specular Shine
        shine_rect = QRectF(front_rect.left() + 2, front_rect.top() + 2, front_rect.width() - 4, 11)
        shine_grad = QLinearGradient(shine_rect.topLeft(), shine_rect.bottomLeft())
        shine_grad.setColorAt(0, QColor(255, 255, 255, 75))
        shine_grad.setColorAt(1, QColor(255, 255, 255, 0))
        painter.setPen(Qt.NoPen)
        painter.setBrush(shine_grad)
        painter.drawRoundedRect(shine_rect, 5, 5)

        # 4. Topic Symbol on folder face
        symbol = self.item_data.get("symbol", "")
        if not symbol:
            if self.item_type == "experiment":
                symbol = "⚗"
            elif self.item_type == "folder":
                symbol = "📁"
            elif self.item_type == "topic":
                symbol = "📖"
            else:
                symbol = "★"

        painter.setPen(QColor(255, 255, 255, 240))
        painter.setFont(QFont("Segoe UI Emoji", 14))
        painter.drawText(front_rect.adjusted(0, -3, 0, 0), Qt.AlignCenter, symbol)

        # 5. Bottom Topic Badge (if experiment)
        badge_text = self.item_data.get("badge", "LAB" if self.item_type == "experiment" else "")
        if badge_text:
            badge_font = QFont("sans-serif", 6, QFont.Bold)
            painter.setFont(badge_font)
            fm = painter.fontMetrics()
            bw = fm.horizontalAdvance(badge_text) + 8
            bh = 11
            bx = front_rect.center().x() - bw / 2
            by = front_rect.bottom() - 13
            badge_r = QRectF(bx, by, bw, bh)
            painter.setBrush(QColor(4, 16, 32, 230))
            painter.setPen(QPen(self.accent_color.lighter(130), 0.8))
            painter.drawRoundedRect(badge_r, 3, 3)
            painter.setPen(QColor("#ffffff"))
            painter.drawText(badge_r, Qt.AlignCenter, badge_text)

        painter.restore()


class OSFolderExplorerView(QWidget):
    """Parent-Child Directory Explorer for Fuserio OS Subjects."""

    navigate_to_desktop = Signal()
    launch_experiment = Signal(str)
    launch_topic_mode = Signal(str, str, str, str, str)  # level, stream, subject, topic, mode
    open_ai_chat = Signal(str, str)  # subject, level

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("osFolderExplorerView")

        self.current_subject = "Physics"
        self.path_segments: list[str] = ["Desktop", "Physics"]
        self.current_query = ""

        bg_path = os.path.join(SUBJECT_ASSETS, "osbg.png")
        self.bg_pixmap = QPixmap(bg_path) if os.path.exists(bg_path) else QPixmap()

        self._init_ui()

    def _init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(24, 16, 24, 18)
        root_layout.setSpacing(14)

        # --- Top Navigation Bar: Back / Up / Breadcrumbs / Search ---
        nav_bar = QFrame(self)
        nav_bar.setFixedHeight(50)
        nav_bar.setStyleSheet("""
            QFrame {
                background: rgba(8, 28, 54, 190);
                border: 1px solid rgba(88, 216, 208, 80);
                border-radius: 16px;
            }
        """)
        nav_layout = QHBoxLayout(nav_bar)
        nav_layout.setContentsMargins(12, 6, 12, 6)
        nav_layout.setSpacing(10)

        # Back button
        self.btn_back = QPushButton("← Back")
        self.btn_back.setCursor(Qt.PointingHandCursor)
        self.btn_back.setStyleSheet("""
            QPushButton {
                background: rgba(18, 54, 88, 140);
                border: 1px solid rgba(88, 216, 208, 90);
                border-radius: 12px;
                color: #57fabc;
                font-size: 11px;
                font-weight: bold;
                padding: 6px 14px;
            }
            QPushButton:hover {
                background: rgba(40, 160, 220, 180);
                color: #ffffff;
            }
        """)
        self.btn_back.clicked.connect(self._navigate_up)
        nav_layout.addWidget(self.btn_back)

        # Up button
        self.btn_up = QPushButton("↑ Up")
        self.btn_up.setCursor(Qt.PointingHandCursor)
        self.btn_up.setStyleSheet(self.btn_back.styleSheet())
        self.btn_up.clicked.connect(self._navigate_up)
        nav_layout.addWidget(self.btn_up)

        # Breadcrumbs container
        self.breadcrumbs_layout = QHBoxLayout()
        self.breadcrumbs_layout.setSpacing(6)
        nav_layout.addLayout(self.breadcrumbs_layout)

        nav_layout.addStretch(1)

        # Filter Search box
        self.search_filter = QLineEdit()
        self.search_filter.setPlaceholderText("🔍 Filter folders & practicals...")
        self.search_filter.setFixedWidth(260)
        self.search_filter.setStyleSheet("""
            QLineEdit {
                background: rgba(12, 38, 68, 160);
                border: 1px solid rgba(88, 216, 208, 80);
                border-radius: 14px;
                color: #e8f7ef;
                padding: 4px 12px;
                font-size: 11px;
            }
            QLineEdit:focus {
                border-color: #57fabc;
                color: #ffffff;
            }
        """)
        self.search_filter.textChanged.connect(self._on_filter_changed)
        nav_layout.addWidget(self.search_filter)

        root_layout.addWidget(nav_bar)

        # --- Middle Area: Scrollable Folder Cards Grid ---
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setStyleSheet("background: transparent; border: none;")

        self.grid_container = QWidget()
        self.grid_container.setStyleSheet("background: transparent;")
        self.cards_grid = QGridLayout(self.grid_container)
        self.cards_grid.setSizeConstraint(QGridLayout.SetMinAndMaxSize)
        self.cards_grid.setContentsMargins(12, 16, 12, 16)
        self.cards_grid.setSpacing(20)
        self.cards_grid.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        self.scroll_area.setWidget(self.grid_container)
        root_layout.addWidget(self.scroll_area, 1)

    def set_subject(self, subject: str):
        self.current_subject = subject
        self.path_segments = ["Desktop", subject]
        self.current_query = ""
        self.search_filter.clear()
        self._refresh_view()

    def _navigate_up(self):
        if len(self.path_segments) <= 2:
            # Back to desktop
            self.navigate_to_desktop.emit()
        else:
            self.path_segments.pop()
            self._refresh_view()

    def _navigate_to_index(self, index: int):
        if index == 0:
            self.navigate_to_desktop.emit()
            return
        self.path_segments = self.path_segments[: index + 1]
        self._refresh_view()

    def _on_filter_changed(self, text: str):
        self.current_query = text.strip().lower()
        self._refresh_cards()

    def _refresh_view(self):
        self._update_breadcrumbs()
        self._refresh_cards()

    def _update_breadcrumbs(self):
        # Clear existing breadcrumbs
        while self.breadcrumbs_layout.count():
            item = self.breadcrumbs_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)
                widget.deleteLater()

        for idx, segment in enumerate(self.path_segments):
            if idx > 0:
                sep = QLabel("›")
                sep.setStyleSheet("color: rgba(88, 216, 208, 120); font-weight: bold; font-size: 13px;")
                self.breadcrumbs_layout.addWidget(sep)

            chip = QPushButton(f"📁 {segment}" if idx > 0 else "🏠 Desktop")
            chip.setCursor(Qt.PointingHandCursor)
            is_current = idx == len(self.path_segments) - 1
            chip.setStyleSheet(f"""
                QPushButton {{
                    background: {'rgba(40, 160, 220, 180)' if is_current else 'transparent'};
                    border: {'1px solid #57fabc' if is_current else 'none'};
                    border-radius: 10px;
                    color: {'#ffffff' if is_current else '#89d4c4'};
                    font-size: 12px;
                    font-weight: {'bold' if is_current else 'normal'};
                    padding: 4px 10px;
                }}
                QPushButton:hover {{
                    color: #57fabc;
                    background: rgba(40, 160, 220, 110);
                }}
            """)
            chip.clicked.connect(lambda _=False, i=idx: self._navigate_to_index(i))
            self.breadcrumbs_layout.addWidget(chip)

    def _refresh_cards(self):
        # Clear existing cards in grid
        while self.cards_grid.count():
            item = self.cards_grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)
                widget.deleteLater()

        depth = len(self.path_segments)
        items: list[dict[str, Any]] = []

        if depth == 2:
            # Level 1: Inside Subject Root (e.g. Desktop > Physics)
            items = self._get_subject_root_items()
        elif depth == 3:
            # Level 2: Inside Level or Practicals Root (e.g. Desktop > Physics > Ordinary Level)
            selected_segment = self.path_segments[2]
            if selected_segment in {"Ordinary Level", "Advanced Level"}:
                items = self._get_level_subfolders(selected_segment)
            elif selected_segment == "Virtual Practicals":
                items = self._get_subject_practicals_items()
            elif selected_segment == "Syllabus Topics":
                items = self._get_subject_topics_items("Ordinary Level")
        elif depth >= 4:
            # Level 3: Inside Level > Subcategory (e.g. Desktop > Physics > Advanced Level > Virtual Practicals)
            level = self.path_segments[2]
            sub = self.path_segments[3]
            if "Practical" in sub or "Lab" in sub:
                items = self._get_subject_practicals_items(level)
            elif "Topic" in sub or "Syllabus" in sub:
                items = self._get_subject_topics_items(level)
            elif "Quiz" in sub or "Practice" in sub:
                items = self._get_practice_items(level)

        # Filter by search query if any
        if self.current_query:
            items = [
                it for it in items
                if self.current_query in it["title"].lower() or self.current_query in it["subtitle"].lower()
            ]

        # Layout cards in grid (5 columns max)
        cols = 5
        for idx, item in enumerate(items):
            card = ExplorerFolderCard(
                item_type=item["type"],
                title=item["title"],
                subtitle=item["subtitle"],
                accent_color=item.get("color", "#58d8d0"),
                icon_path=item.get("icon_path", ""),
                item_data=item,
                parent=self.grid_container,
            )
            card.clicked.connect(self._on_card_clicked)
            self.cards_grid.addWidget(card, idx // cols, idx % cols)

    def _get_subject_root_items(self) -> list[dict[str, Any]]:
        # Root folders: Ordinary Level, Advanced Level, Virtual Practicals, AI Tutor
        accent = self._subject_accent(self.current_subject)
        icon_file = self._subject_icon_file(self.current_subject)
        full_icon_path = os.path.join(SUBJECT_ASSETS, icon_file) if icon_file else ""

        return [
            {
                "type": "folder",
                "title": "Ordinary Level",
                "subtitle": "Form 3 - Form 5 GCE",
                "color": "#57fabc",
                "target_segment": "Ordinary Level",
                "icon_path": full_icon_path,
            },
            {
                "type": "folder",
                "title": "Advanced Level",
                "subtitle": "Lower - Upper Sixth GCE",
                "color": "#3867d6",
                "target_segment": "Advanced Level",
                "icon_path": full_icon_path,
            },
            {
                "type": "folder",
                "title": "Virtual Practicals",
                "subtitle": f"{self.current_subject} Lab Simulations",
                "color": "#ff9f43",
                "target_segment": "Virtual Practicals",
                "icon_path": full_icon_path,
            },
            {
                "type": "ai_chat",
                "title": "AI Study Tutor",
                "subtitle": f"Offline {self.current_subject} AI",
                "color": "#9f3df8",
                "subject": self.current_subject,
                "level": "Ordinary Level",
                "icon_path": os.path.join(ASSETS_DIR, "fus-fuserio.png"),
            },
        ]

    def _get_level_subfolders(self, level: str) -> list[dict[str, Any]]:
        accent = self._subject_accent(self.current_subject)
        return [
            {
                "type": "folder",
                "title": "Virtual Practicals",
                "subtitle": "Lab Apparatus & Experiments",
                "color": "#57fabc",
                "target_segment": "Virtual Practicals",
            },
            {
                "type": "folder",
                "title": "Syllabus Topics",
                "subtitle": "GCE Subject Curriculum",
                "color": "#3867d6",
                "target_segment": "Syllabus Topics",
            },
            {
                "type": "folder",
                "title": "Practice & Quizzes",
                "subtitle": "Past Questions & Quizzes",
                "color": "#ff9f43",
                "target_segment": "Practice & Quizzes",
            },
            {
                "type": "ai_chat",
                "title": "Ask Fuserio AI",
                "subtitle": f"{level} Study Companion",
                "color": "#9f3df8",
                "subject": self.current_subject,
                "level": level,
                "icon_path": os.path.join(ASSETS_DIR, "fus-fuserio.png"),
            },
        ]

    def _get_subject_practicals_items(self, level: str = "") -> list[dict[str, Any]]:
        items = []
        experiments = list(experiments_for_subject(self.current_subject))

        for exp in experiments:
            meta = EXPERIMENT_TOPIC_METADATA.get(exp.identifier, {})
            items.append({
                "type": "experiment",
                "title": exp.title,
                "subtitle": f"{meta.get('topic', exp.subtitle)} · Practical",
                "experiment_id": exp.identifier,
                "color": meta.get("color", self._subject_accent(self.current_subject)),
                "symbol": meta.get("symbol", "⚗"),
                "badge": meta.get("badge", "LAB"),
                "topic": meta.get("topic", self.current_subject),
            })

        # If chemistry, also add topics from chemistry practicals
        if self.current_subject == "Chemistry":
            chem_level = (
                CHEMISTRY.levels[0]
                if "Ordinary" in level
                else (CHEMISTRY.levels[1] if len(CHEMISTRY.levels) > 1 else CHEMISTRY.levels[0])
            )
            for topic in chem_level.topics:
                t_lower = topic.title.lower()
                if "titration" in t_lower or "acid" in t_lower:
                    t_col, t_sym, t_badge = "#57fabc", "⚗", "TITRATION"
                elif "rate" in t_lower or "kinetic" in t_lower:
                    t_col, t_sym, t_badge = "#ff9f43", "⏱", "KINETICS"
                elif "solubil" in t_lower or "crystal" in t_lower or "thermal" in t_lower:
                    t_col, t_sym, t_badge = "#58d8d0", "🔥", "SOLUBILITY"
                elif "precipitat" in t_lower or "salt" in t_lower:
                    t_col, t_sym, t_badge = "#a8ff78", "🧪", "PRECIPITATE"
                else:
                    t_col, t_sym, t_badge = "#3867d6", "⚗", "PRACTICAL"

                for exp in topic.experiments:
                    if exp.id not in [it.get("experiment_id") for it in items]:
                        items.append({
                            "type": "experiment",
                            "title": exp.title,
                            "subtitle": f"{topic.title} · Practical",
                            "experiment_id": exp.id,
                            "color": t_col,
                            "symbol": t_sym,
                            "badge": t_badge,
                            "topic": topic.title,
                        })
        return items

    def _get_subject_topics_items(self, level: str) -> list[dict[str, Any]]:
        stream = "Sciences"
        topics = []
        try:
            topics = list(suggested_topic_areas(level, stream, self.current_subject))
        except Exception:
            topics = [f"Topic {i}: Core {self.current_subject}" for i in range(1, 5)]

        items = []
        for i, t in enumerate(topics, 1):
            items.append({
                "type": "topic",
                "title": f"{i}. {t[:18]}...",
                "subtitle": "Study Lesson & Exercises",
                "topic_full": t,
                "level": level,
                "stream": stream,
                "subject": self.current_subject,
                "color": "#3867d6",
            })
        return items

    def _get_practice_items(self, level: str) -> list[dict[str, Any]]:
        return [
            {
                "type": "topic_mode",
                "title": "Comprehensive Quiz",
                "subtitle": f"{self.current_subject} Questions",
                "mode": "Past-paper quiz",
                "level": level,
                "stream": "Sciences",
                "subject": self.current_subject,
                "topic": "All Syllabus Topics",
                "color": "#ff9f43",
            },
            {
                "type": "topic_mode",
                "title": "Interactive Practice",
                "subtitle": "Step-by-step problem solver",
                "mode": "Practice",
                "level": level,
                "stream": "Sciences",
                "subject": self.current_subject,
                "topic": "All Syllabus Topics",
                "color": "#57fabc",
            },
        ]

    def _on_card_clicked(self, item_type: str, item_data: dict):
        if item_type == "folder":
            self.path_segments.append(item_data["target_segment"])
            self._refresh_view()
        elif item_type == "experiment":
            self.launch_experiment.emit(item_data["experiment_id"])
        elif item_type == "ai_chat":
            self.open_ai_chat.emit(item_data["subject"], item_data["level"])
        elif item_type == "topic":
            self.launch_topic_mode.emit(
                item_data["level"],
                item_data["stream"],
                item_data["subject"],
                item_data["topic_full"],
                "Lesson",
            )
        elif item_type == "topic_mode":
            self.launch_topic_mode.emit(
                item_data["level"],
                item_data["stream"],
                item_data["subject"],
                item_data["topic"],
                item_data["mode"],
            )

    def _subject_accent(self, subject: str) -> str:
        accents = {
            "Chemistry": "#57fabc",
            "Biology": "#ff9f43",
            "Physics": "#3867d6",
            "Mathematics": "#20bf6b",
            "Computer Science": "#9f3df8",
            "ICT": "#00d2d3",
        }
        return accents.get(subject, "#58d8d0")

    def _subject_icon_file(self, subject: str) -> str:
        icons = {
            "Chemistry": "chemistry.png",
            "Biology": "biology.png",
            "Physics": "physics.png",
            "Mathematics": "maths.png",
            "Computer Science": "coding.png",
            "ICT": "computers.png",
        }
        return icons.get(subject, "")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        w = self.width()
        h = self.height()

        if not self.bg_pixmap.isNull():
            scaled = self.bg_pixmap.scaled(
                w,
                h,
                Qt.KeepAspectRatioByExpanding,
                Qt.SmoothTransformation,
            )
            sx = (scaled.width() - w) // 2
            sy = (scaled_bg.height() - h) // 2 if 'scaled_bg' in locals() else (scaled.height() - h) // 2
            painter.drawPixmap(0, 0, scaled, sx, sy, w, h)
        else:
            bg_grad = QLinearGradient(0, 0, 0, h)
            bg_grad.setColorAt(0, QColor("#020b18"))
            bg_grad.setColorAt(0.5, QColor("#041c38"))
            bg_grad.setColorAt(1, QColor("#020d1c"))
            painter.fillRect(self.rect(), bg_grad)

        # Subtle dark frosted veil so cards pop
        painter.fillRect(self.rect(), QColor(2, 11, 24, 150))
