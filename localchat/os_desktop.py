import math
import os

from PySide6.QtCore import QMimeData, QPoint, QPointF, QRectF, QSize, Qt, Signal
from PySide6.QtGui import (
    QBrush,
    QColor,
    QDrag,
    QFont,
    QIcon,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QRadialGradient,
)
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
SUBJECT_ASSETS = os.path.join(ASSETS_DIR, "subject_folders")


class SubjectFolderCard(QFrame):
    """3D Glass Subject Folder Card with reflective shelf floor and hover elevation."""

    clicked = Signal(str)

    def __init__(
        self,
        subject_key: str,
        title: str,
        icon_filename: str,
        accent_color: str,
        subtitle: str = "",
        parent=None,
    ):
        super().__init__(parent)
        self.subject_key = subject_key
        self.title = title
        self.accent_color = QColor(accent_color)
        self.subtitle = subtitle
        self.hovered = False
        self.elevation_offset = 0

        self.setFixedSize(148, 172)
        self.setCursor(Qt.OpenHandCursor)
        self.setAccessibleName(f"Open {title} subject workspace")

        icon_path = os.path.join(SUBJECT_ASSETS, icon_filename)
        self.icon_pixmap = QPixmap(icon_path) if os.path.exists(icon_path) else QPixmap()

        self._drag_origin = QPoint()
        self._drag_started = False
        self.setAcceptDrops(False)

    def enterEvent(self, event):
        self.hovered = True
        self.elevation_offset = -8
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.hovered = False
        self.elevation_offset = 0
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_origin = event.position().toPoint()
            self._drag_started = False
            self.setCursor(Qt.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if (
            event.buttons() & Qt.LeftButton
            and not self._drag_started
            and (event.position().toPoint() - self._drag_origin).manhattanLength()
            >= QApplication.startDragDistance()
        ):
            self._drag_started = True
            drag = QDrag(self)
            mime_data = QMimeData()
            mime_data.setText(self.subject_key)
            drag.setMimeData(mime_data)
            drag.setPixmap(self.grab())
            drag.setHotSpot(self._drag_origin)
            drag.exec(Qt.MoveAction)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and not self._drag_started:
            self.clicked.emit(self.subject_key)
        self._drag_started = False
        self.setCursor(Qt.OpenHandCursor)
        super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        w = self.width()
        h = self.height()
        dy = self.elevation_offset

        # 1. Glass Tile Backing
        tile_w = 132.0
        tile_h = 118.0
        tile_x = (w - tile_w) / 2.0
        tile_y = 10.0 + dy

        tile_rect = QRectF(tile_x, tile_y, tile_w, tile_h)

        # Ambient Glow on hover
        if self.hovered:
            glow_grad = QRadialGradient(tile_rect.center(), tile_w * 0.8)
            glow_col = QColor(self.accent_color)
            glow_col.setAlpha(85)
            glow_grad.setColorAt(0, glow_col)
            glow_grad.setColorAt(0.7, QColor(glow_col.red(), glow_col.green(), glow_col.blue(), 25))
            glow_grad.setColorAt(1, QColor(0, 0, 0, 0))
            painter.setPen(Qt.NoPen)
            painter.setBrush(glow_grad)
            painter.drawRoundedRect(tile_rect.adjusted(-12, -12, 12, 12), 22, 22)

        # Translucent glass plate
        glass_grad = QLinearGradient(tile_x, tile_y, tile_x, tile_y + tile_h)
        if self.hovered:
            glass_grad.setColorAt(0, QColor(14, 46, 82, 180))
            glass_grad.setColorAt(1, QColor(8, 28, 54, 210))
            border_pen = QPen(self.accent_color, 1.6)
        else:
            glass_grad.setColorAt(0, QColor(10, 36, 68, 140))
            glass_grad.setColorAt(1, QColor(5, 20, 42, 180))
            border_pen = QPen(QColor(88, 216, 208, 75), 1.1)

        painter.setPen(border_pen)
        painter.setBrush(glass_grad)
        painter.drawRoundedRect(tile_rect, 18, 18)

        # Inner subtle gloss highlight
        highlight_rect = QRectF(tile_x + 2, tile_y + 2, tile_w - 4, 32)
        h_grad = QLinearGradient(highlight_rect.topLeft(), highlight_rect.bottomLeft())
        h_grad.setColorAt(0, QColor(255, 255, 255, 45))
        h_grad.setColorAt(1, QColor(255, 255, 255, 0))
        painter.setPen(Qt.NoPen)
        painter.setBrush(h_grad)
        painter.drawRoundedRect(highlight_rect, 16, 16)

        # 2. Draw Subject Folder 3D Icon
        if not self.icon_pixmap.isNull():
            icon_target_w = 98
            icon_target_h = 92
            ix = int(tile_x + (tile_w - icon_target_w) / 2.0)
            iy = int(tile_y + 12)
            icon_scaled = self.icon_pixmap.scaled(
                icon_target_w,
                icon_target_h,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
            # Center within target
            actual_x = ix + (icon_target_w - icon_scaled.width()) // 2
            actual_y = iy + (icon_target_h - icon_scaled.height()) // 2
            painter.drawPixmap(actual_x, actual_y, icon_scaled)

            # 3. Downward Mirrored Floor Reflection
            # We draw a faded reflection below the card base on the floor
            refl_h = 24
            refl_y = tile_y + tile_h + 3
            if refl_y + refl_h <= h:
                refl_img = icon_scaled.toImage().mirrored(False, True)
                refl_pixmap = QPixmap.fromImage(refl_img)
                refl_sub = refl_pixmap.copy(0, 0, icon_scaled.width(), min(refl_h, refl_pixmap.height()))

                painter.save()
                painter.setOpacity(0.25 if self.hovered else 0.14)
                painter.drawPixmap(actual_x, int(refl_y), refl_sub)
                # Gradient fade over reflection
                fade_grad = QLinearGradient(0, refl_y, 0, refl_y + refl_h)
                fade_grad.setColorAt(0, QColor(0, 0, 0, 0))
                fade_grad.setColorAt(1, QColor(3, 16, 34, 255))
                painter.setBrush(fade_grad)
                painter.setPen(Qt.NoPen)
                painter.drawRect(QRectF(tile_x, refl_y, tile_w, refl_h))
                painter.restore()

        # 4. Subject Label Below
        painter.setFont(QFont("sans-serif", 9, QFont.Bold if self.hovered else QFont.Normal))
        painter.setPen(QColor("#ffffff") if self.hovered else QColor("#b4e5dc"))
        label_rect = QRectF(0, tile_y + tile_h - 1, w, 22)
        painter.drawText(label_rect, Qt.AlignCenter, self.title)


class GCEMasteryWidget(QFrame):
    """Floating Frosted Glass GCE Syllabus Mastery & Learning Wave Widget."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(196, 178)
        self.mastery_pct = 78
        self.topics_count = 34
        self.practicals_count = 6
        self.setAccessibleName("GCE Syllabus Mastery Progress Tracker")

    def set_progress(self, percentage: int, topics: int = 34, practicals: int = 6):
        self.mastery_pct = max(0, min(100, percentage))
        self.topics_count = topics
        self.practicals_count = practicals
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        w = float(self.width())
        h = float(self.height())
        rect = QRectF(4, 4, w - 8, h - 8)

        # 1. Frosted Glass Container
        bg_grad = QLinearGradient(0, 0, w, h)
        bg_grad.setColorAt(0, QColor(8, 28, 54, 210))
        bg_grad.setColorAt(0.6, QColor(5, 20, 42, 230))
        bg_grad.setColorAt(1, QColor(3, 14, 30, 240))

        painter.setBrush(bg_grad)
        painter.setPen(QPen(QColor(88, 216, 208, 90), 1.2))
        painter.drawRoundedRect(rect, 20, 20)

        # 2. Top-right indicator dots (••)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(88, 216, 208, 180))
        painter.drawEllipse(QPointF(w - 24, 18), 2.2, 2.2)
        painter.drawEllipse(QPointF(w - 16, 18), 2.2, 2.2)

        # 3. Circular Progress Ring with Graduation Cap
        ring_cx = w / 2.0
        ring_cy = 58.0
        ring_radius = 34.0
        ring_rect = QRectF(ring_cx - ring_radius, ring_cy - ring_radius, ring_radius * 2, ring_radius * 2)

        # Background Track
        track_pen = QPen(QColor(18, 54, 84, 160), 5.5, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(track_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(ring_rect)

        # Value Arc
        span_angle = int(- (self.mastery_pct / 100.0) * 360 * 16)
        arc_pen = QPen(QColor("#58d8d0"), 5.5, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(arc_pen)
        painter.drawArc(ring_rect, 90 * 16, span_angle)

        # Graduation Cap Icon in Center
        self._draw_grad_cap(painter, ring_cx, ring_cy)

        # 4. Learning Activity Sine Wave Curve
        wave_y = 120.0
        wave_path = QPainterPath()
        wave_path.moveTo(12, h - 12)
        wave_path.lineTo(12, wave_y + 12)

        # Smooth Bezier wave
        wave_path.cubicTo(
            QPointF(w * 0.28, wave_y - 12),
            QPointF(w * 0.42, wave_y + 18),
            QPointF(w * 0.65, wave_y - 8),
        )
        wave_path.cubicTo(
            QPointF(w * 0.82, wave_y - 24),
            QPointF(w * 0.92, wave_y - 2),
            QPointF(w - 12, wave_y + 6),
        )
        wave_path.lineTo(w - 12, h - 12)
        wave_path.closeSubpath()

        wave_grad = QLinearGradient(0, wave_y - 24, 0, h - 12)
        wave_grad.setColorAt(0, QColor(87, 250, 188, 120))
        wave_grad.setColorAt(0.5, QColor(88, 216, 208, 40))
        wave_grad.setColorAt(1, QColor(88, 216, 208, 0))

        painter.setBrush(wave_grad)
        painter.setPen(Qt.NoPen)
        painter.drawPath(wave_path)

        # Wave Stroke
        stroke_path = QPainterPath()
        stroke_path.moveTo(12, wave_y + 12)
        stroke_path.cubicTo(
            QPointF(w * 0.28, wave_y - 12),
            QPointF(w * 0.42, wave_y + 18),
            QPointF(w * 0.65, wave_y - 8),
        )
        stroke_path.cubicTo(
            QPointF(w * 0.82, wave_y - 24),
            QPointF(w * 0.92, wave_y - 2),
            QPointF(w - 12, wave_y + 6),
        )
        painter.setPen(QPen(QColor("#58d8d0"), 2.0))
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(stroke_path)

        # 5. Text Label
        painter.setFont(QFont("sans-serif", 9, QFont.Bold))
        painter.setPen(QColor("#e8f7ef"))
        painter.drawText(QRectF(10, 102, w - 20, 18), Qt.AlignCenter, f"{self.mastery_pct}% GCE SYLLABUS")

        painter.setFont(QFont("sans-serif", 7, QFont.Normal))
        painter.setPen(QColor("#89b6a8"))
        painter.drawText(QRectF(10, h - 22, w - 20, 14), Qt.AlignCenter, f"{self.topics_count} Topics · {self.practicals_count} Practicals")

    def _draw_grad_cap(self, painter: QPainter, cx: float, cy: float):
        painter.save()
        painter.setBrush(QColor("#58d8d0"))
        painter.setPen(Qt.NoPen)

        # Diamond cap top
        diamond = QPainterPath()
        diamond.moveTo(cx, cy - 11)
        diamond.lineTo(cx + 14, cy - 4)
        diamond.lineTo(cx, cy + 3)
        diamond.lineTo(cx - 14, cy - 4)
        diamond.closeSubpath()
        painter.drawPath(diamond)

        # Skull cap base
        skull = QPainterPath()
        skull.moveTo(cx - 8, cy - 1)
        skull.quadTo(cx, cy + 7, cx + 8, cy - 1)
        skull.quadTo(cx, cy + 11, cx - 8, cy - 1)
        painter.drawPath(skull)

        # Tassel line & drop
        painter.setPen(QPen(QColor("#57fabc"), 1.3))
        painter.drawLine(QPointF(cx + 10, cy - 3), QPointF(cx + 14, cy + 6))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(cx + 14, cy + 7.5), 1.8, 1.8)

        painter.restore()


class FloatingDock(QFrame):
    """Bottom Floating OS Dock Pill with Launcher and App Shortcuts."""

    launch_app = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(48)
        self.setObjectName("osFloatingDock")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 4, 14, 4)
        layout.setSpacing(10)

        # App launcher (4 grid)
        self.btn_apps = self._create_dock_btn("⊞", "All GCE Apps & Syllabus", "gce")
        # Folders
        self.btn_folders = self._create_dock_btn("📁", "Subject Practicals & Labs", "lab")
        # AI Terminal
        self.btn_ai = self._create_dock_btn(">_", "Terminal (Fuserio AI Tutor)", "chat")
        # Math & Data
        self.btn_math = self._create_dock_btn("📊", "Math Data Lab & Grapher", "math")
        # Settings
        self.btn_settings = self._create_dock_btn("⚙", "System & Local Models", "settings")

        layout.addWidget(self.btn_apps)
        layout.addWidget(self._create_separator())
        layout.addWidget(self.btn_folders)
        layout.addWidget(self.btn_ai)
        layout.addWidget(self.btn_math)
        layout.addWidget(self._create_separator())
        layout.addWidget(self.btn_settings)

    def _create_dock_btn(self, icon_str: str, tooltip: str, action_key: str) -> QPushButton:
        btn = QPushButton(icon_str)
        btn.setFixedSize(36, 36)
        btn.setToolTip(tooltip)
        btn.setCursor(Qt.PointingHandCursor)
        font_family = "'JetBrains Mono', 'Fira Code', monospace" if icon_str == ">_" else "sans-serif"
        font_size = "13px" if icon_str == ">_" else "16px"
        btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(18, 54, 88, 120);
                border: 1px solid rgba(88, 216, 208, 90);
                border-radius: 18px;
                color: #58d8d0;
                font-family: {font_family};
                font-size: {font_size};
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: rgba(40, 160, 220, 180);
                border: 1px solid #57fabc;
                color: #ffffff;
            }}
            QPushButton:pressed {{
                background: rgba(87, 250, 188, 220);
                color: #031422;
            }}
        """)
        btn.clicked.connect(lambda _=False, k=action_key: self.launch_app.emit(k))
        return btn

    def _create_separator(self) -> QLabel:
        sep = QLabel("│")
        sep.setStyleSheet("color: rgba(88, 216, 208, 100); font-size: 14px;")
        return sep

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        grad = QLinearGradient(0, 0, 0, self.height())
        grad.setColorAt(0, QColor(10, 32, 58, 215))
        grad.setColorAt(1, QColor(4, 18, 36, 235))

        painter.setBrush(grad)
        painter.setPen(QPen(QColor(88, 216, 208, 100), 1.2))
        painter.drawRoundedRect(rect, 24, 24)


class SystemTrayWidget(QFrame):
    """Bottom-Right Floating System Tray Pill (Offline First, Sound, Compute Status)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(36)
        self.setObjectName("osSystemTray")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 2, 12, 2)
        layout.setSpacing(12)

        # Offline badge
        self.wifi_lbl = QLabel("📶")
        self.wifi_lbl.setToolTip("Offline First • 100% Local AI (No internet required)")
        self.wifi_lbl.setStyleSheet("color: #57fabc; font-size: 13px;")

        # Sound icon
        self.vol_lbl = QLabel("🔊")
        self.vol_lbl.setToolTip("Audio Feedback Enabled")
        self.vol_lbl.setStyleSheet("color: #58d8d0; font-size: 13px;")

        # Battery / Local compute icon
        self.bat_lbl = QLabel("🔋")
        self.bat_lbl.setToolTip("Local Compute: Ready (Optimized for 4GB-8GB RAM)")
        self.bat_lbl.setStyleSheet("color: #58d8d0; font-size: 13px;")

        layout.addWidget(self.wifi_lbl)
        layout.addWidget(self.vol_lbl)
        layout.addWidget(self.bat_lbl)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        grad = QLinearGradient(0, 0, 0, self.height())
        grad.setColorAt(0, QColor(8, 26, 48, 200))
        grad.setColorAt(1, QColor(4, 16, 32, 220))

        painter.setBrush(grad)
        painter.setPen(QPen(QColor(88, 216, 208, 80), 1.1))
        painter.drawRoundedRect(rect, 18, 18)


class OSDesktopView(QWidget):
    """Main Fuserio OS Desktop view rendering wallpaper, 3D emblem, and subject shelf."""

    subject_selected = Signal(str)
    launch_action = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("osDesktopView")
        self.setAcceptDrops(True)

        bg_path = os.path.join(SUBJECT_ASSETS, "osbg.png")
        self.bg_pixmap = QPixmap(bg_path) if os.path.exists(bg_path) else QPixmap()

        fus_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fus.png")
        self.emblem_pixmap = QPixmap(fus_path) if os.path.exists(fus_path) else QPixmap()

        self._init_ui()

    def _init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(28, 20, 28, 16)
        root_layout.setSpacing(12)

        # --- Top Area: Right-aligned Mastery Widget ---
        top_row = QHBoxLayout()
        top_row.addStretch(1)

        self.mastery_widget = GCEMasteryWidget(self)
        top_row.addWidget(self.mastery_widget)
        root_layout.addLayout(top_row)

        root_layout.addStretch(1)

        # --- Middle Area: 6 Subject Folder Cards on the Reflective Shelf ---
        shelf_layout = QHBoxLayout()
        shelf_layout.setSpacing(16)
        shelf_layout.setAlignment(Qt.AlignCenter)

        subjects_data = [
            ("Chemistry", "Chemistry", "chemistry.png", "#57fabc"),
            ("Biology", "Biology", "biology.png", "#ff9f43"),
            ("Physics", "Physics", "physics.png", "#3867d6"),
            ("Mathematics", "Mathematics", "maths.png", "#20bf6b"),
            ("Computer Science", "Computer Sci", "coding.png", "#9f3df8"),
            ("ICT", "ICT & Systems", "computers.png", "#00d2d3"),
        ]

        self.folder_cards: list[SubjectFolderCard] = []
        for key, title, icon_file, color in subjects_data:
            card = SubjectFolderCard(key, title, icon_file, color, parent=self)
            card.clicked.connect(self._on_subject_clicked)
            self.folder_cards.append(card)
            shelf_layout.addWidget(card)

        self.shelf_layout = shelf_layout

        self.terminal_icon = DesktopAppIcon(parent=self)
        self.terminal_icon.launched.connect(self._on_terminal_launched)
        shelf_layout.addWidget(self.terminal_icon)
        root_layout.addLayout(shelf_layout)

        root_layout.addSpacing(18)

        # --- Bottom Area: Floating Dock centered + System Tray right ---
        bottom_row = QHBoxLayout()
        bottom_row.addStretch(1)

        self.dock = FloatingDock(self)
        self.dock.launch_app.connect(self._on_dock_launch)
        bottom_row.addWidget(self.dock)

        bottom_row.addStretch(1)

        self.tray = SystemTrayWidget(self)
        bottom_row.addWidget(self.tray)

        root_layout.addLayout(bottom_row)

    def _on_subject_clicked(self, subject_key: str):
        self.subject_selected.emit(subject_key)

    def _on_dock_launch(self, action_key: str):
        self.launch_action.emit(action_key)

    def _on_terminal_launched(self):
        # Special handling if needed when terminal icon is launched
        self.launch_action.emit("terminal")

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
            return
        event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
            return
        event.ignore()

    def dropEvent(self, event):
        dragged_key = event.mimeData().text()
        self._reorder_desktop_icon(dragged_key, event.position().toPoint())
        event.acceptProposedAction()

    def _reorder_desktop_icon(self, dragged_key: str, position: QPoint) -> bool:
        icons = {card.subject_key: card for card in self.folder_cards}
        icons["terminal"] = self.terminal_icon
        dragged_icon = icons.get(dragged_key)
        if dragged_icon is None:
            return False

        target_index = self.shelf_layout.count()
        for index in range(self.shelf_layout.count()):
            item = self.shelf_layout.itemAt(index)
            widget = item.widget()
            if widget is not dragged_icon and position.x() < widget.geometry().center().x():
                target_index = index
                break

        current_index = self.shelf_layout.indexOf(dragged_icon)
        if current_index < 0:
            return False
        self.shelf_layout.removeWidget(dragged_icon)
        if current_index < target_index:
            target_index -= 1
        self.shelf_layout.insertWidget(target_index, dragged_icon)
        return True

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        w = self.width()
        h = self.height()

        # 1. Background Wallpaper
        if not self.bg_pixmap.isNull():
            scaled_bg = self.bg_pixmap.scaled(
                w,
                h,
                Qt.KeepAspectRatioByExpanding,
                Qt.SmoothTransformation,
            )
            # Center crop
            sx = (scaled_bg.width() - w) // 2
            sy = (scaled_bg.height() - h) // 2
            painter.drawPixmap(0, 0, scaled_bg, sx, sy, w, h)
        else:
            # Fallback gradient
            bg_grad = QLinearGradient(0, 0, 0, h)
            bg_grad.setColorAt(0, QColor("#020b18"))
            bg_grad.setColorAt(0.5, QColor("#041c38"))
            bg_grad.setColorAt(1, QColor("#020d1c"))
            painter.fillRect(self.rect(), bg_grad)

        # 2. Glowing 3D Fuserio Monogram in Center Background
        if not self.emblem_pixmap.isNull():
            emblem_size = min(360, int(h * 0.45))
            ex = (w - emblem_size) // 2
            ey = int(h * 0.16)

            # Ambient Cyan Radial Glow
            glow = QRadialGradient(w / 2.0, ey + emblem_size / 2.0, emblem_size * 0.8)
            glow.setColorAt(0, QColor(88, 216, 208, 90))
            glow.setColorAt(0.5, QColor(40, 160, 220, 40))
            glow.setColorAt(1, QColor(0, 0, 0, 0))
            painter.setPen(Qt.NoPen)
            painter.setBrush(glow)
            painter.drawEllipse(QPointF(w / 2.0, ey + emblem_size / 2.0), emblem_size * 0.85, emblem_size * 0.85)

            # Draw emblem with subtle blending
            painter.save()
            painter.setOpacity(0.88)
            scaled_emblem = self.emblem_pixmap.scaled(
                emblem_size,
                emblem_size,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
            painter.drawPixmap(ex, ey, scaled_emblem)
            painter.restore()

        # 3. Glass Horizon / Reflective Floor Line
        shelf_y = h * 0.76
        horizon_grad = QLinearGradient(0, shelf_y - 20, 0, shelf_y + 40)
        horizon_grad.setColorAt(0, QColor(88, 216, 208, 0))
        horizon_grad.setColorAt(0.3, QColor(88, 216, 208, 85))
        horizon_grad.setColorAt(0.7, QColor(40, 160, 220, 40))
        horizon_grad.setColorAt(1, QColor(2, 12, 26, 0))

        painter.setPen(Qt.NoPen)
        painter.setBrush(horizon_grad)
        painter.drawRect(QRectF(0, shelf_y - 12, w, 32))

        # Thin illuminated horizon edge
        line_pen = QPen(QColor(88, 216, 208, 140), 1.2)
        painter.setPen(line_pen)
        painter.drawLine(0, int(shelf_y), w, int(shelf_y))


class DesktopAppIcon(QFrame):
    """A playful desktop launcher with an icon pulse and click launch effect."""

    launched = Signal()

    def __init__(self, title: str = "Terminal", subtitle: str = "Neural Shell", parent=None):
        super().__init__(parent)
        self.title = title
        self.subtitle = subtitle
        self.hovered = False
        self.setFixedSize(92, 112)
        self.setCursor(Qt.OpenHandCursor)
        self.setAccessibleName("Open Fuserio Neural Terminal")

        self._drag_origin = QPoint()
        self._drag_started = False

    def enterEvent(self, event):
        self.hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.hovered = False
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_origin = event.position().toPoint()
            self._drag_started = False
            self.setCursor(Qt.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if (
            event.buttons() & Qt.LeftButton
            and not self._drag_started
            and (event.position().toPoint() - self._drag_origin).manhattanLength()
            >= QApplication.startDragDistance()
        ):
            self._drag_started = True
            drag = QDrag(self)
            mime_data = QMimeData()
            mime_data.setText("terminal")
            drag.setMimeData(mime_data)
            drag.setPixmap(self.grab())
            drag.setHotSpot(self._drag_origin)
            drag.exec(Qt.MoveAction)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.setCursor(Qt.OpenHandCursor)
            if not self._drag_started:
                self.launched.emit()
        self._drag_started = False
        super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        cx = self.width() / 2.0
        glow_radius = 38 if self.hovered else 34
        glow = QRadialGradient(cx, 38, glow_radius)
        glow.setColorAt(0, QColor(87, 250, 188, 90 if self.hovered else 45))
        glow.setColorAt(1, QColor(87, 250, 188, 0))
        painter.setBrush(glow)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(cx, 38), glow_radius, glow_radius)

        rect = QRectF(cx - 34, 8, 68, 68)
        grad = QLinearGradient(rect.left(), rect.top(), rect.right(), rect.bottom())
        grad.setColorAt(0, QColor(16, 67, 92, 245))
        grad.setColorAt(1, QColor(5, 24, 48, 255))
        painter.setBrush(grad)
        painter.setPen(QPen(QColor("#57fabc" if self.hovered else "#58d8d0"), 1.5))
        painter.drawRoundedRect(rect, 17, 17)

        painter.setPen(QPen(QColor("#57fabc"), 3.0, Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(QPointF(cx - 16, 30), QPointF(cx - 5, 41))
        painter.drawLine(QPointF(cx - 5, 41), QPointF(cx - 16, 52))
        painter.setPen(QPen(QColor("#dfffee"), 3.0, Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(QPointF(cx - 1, 53), QPointF(cx + 16, 53))

        painter.setFont(QFont("sans-serif", 9, QFont.Bold))
        painter.setPen(QColor("#ffffff" if self.hovered else "#b9eee1"))
        painter.drawText(QRectF(0, 80, self.width(), 18), Qt.AlignCenter, self.title)
        painter.setFont(QFont("sans-serif", 7))
        painter.setPen(QColor("#7ea5c4"))
        painter.drawText(QRectF(0, 96, self.width(), 14), Qt.AlignCenter, self.subtitle)
