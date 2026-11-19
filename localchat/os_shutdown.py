import math
import os
import time

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import (
    QColor,
    QFont,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QRadialGradient,
)
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget


ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")


class OSShutdownOverlay(QFrame):
    """Windows-style animated fading shutdown / restart / lock screen for Fuserio OS."""

    shutdown_completed = Signal()
    restart_completed = Signal()
    unlocked = Signal()

    def __init__(self, mode: str = "shutdown", parent=None):
        super().__init__(parent)
        self.mode = mode  # "shutdown", "restart", "lock"
        self.setObjectName("osShutdownOverlay")

        # Cover parent completely
        if parent:
            self.resize(parent.size())
            self.raise_()

        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocus()

        emblem_path = os.path.join(ASSETS_DIR, "fus-fuserio.png")
        self.emblem_pixmap = QPixmap(emblem_path) if os.path.exists(emblem_path) else QPixmap()

        self.spinner_angle = 0.0
        self.fade_alpha = 0
        self.is_fading = False
        self.is_finished = False

        # Animation timer (spinning dots)
        self.anim_timer = QTimer(self)
        self.anim_timer.setInterval(22)
        self.anim_timer.timeout.connect(self._on_tick)
        self.anim_timer.start()

        # Schedule shutdown / restart sequence
        if self.mode == "shutdown":
            self.status_title = "Shutting down Fuserio OS..."
            self.status_subtitle = "Saving offline student pre-lab progress & models..."
            QTimer.singleShot(1100, self._start_fade_out)
        elif self.mode == "restart":
            self.status_title = "Restarting Fuserio OS..."
            self.status_subtitle = "Reinitializing offline pre-lab environment..."
            QTimer.singleShot(1000, self._start_fade_out)
        elif self.mode == "lock":
            self.status_title = "Fuserio OS"
            self.status_subtitle = "Click anywhere or press Enter to unlock"

    def _start_fade_out(self):
        self.is_fading = True

    def _on_tick(self):
        self.spinner_angle = (self.spinner_angle + 6.0) % 360.0

        if self.is_fading and not self.is_finished:
            self.fade_alpha = min(255, self.fade_alpha + 14)
            if self.fade_alpha >= 255:
                self.is_finished = True
                self.anim_timer.stop()
                if self.mode == "shutdown":
                    self.shutdown_completed.emit()
                elif self.mode == "restart":
                    self.restart_completed.emit()
                    self.hide()
                    self.deleteLater()

        self.update()

    def mousePressEvent(self, event):
        if self.mode == "lock":
            self.anim_timer.stop()
            self.unlocked.emit()
            self.hide()
            self.deleteLater()
        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        if self.mode == "lock":
            self.anim_timer.stop()
            self.unlocked.emit()
            self.hide()
            self.deleteLater()
            return
        super().keyPressEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        w = float(self.width())
        h = float(self.height())
        cx = w / 2.0
        cy = h / 2.0

        # 1. Deep Space Windows Blue Background Gradient
        bg_grad = QLinearGradient(0, 0, 0, h)
        bg_grad.setColorAt(0, QColor("#020b18"))
        bg_grad.setColorAt(0.5, QColor("#041832"))
        bg_grad.setColorAt(1, QColor("#010914"))
        painter.fillRect(self.rect(), bg_grad)

        # 2. Ambient Central Cyan Glow
        glow = QRadialGradient(cx, cy - 20, 260)
        glow.setColorAt(0, QColor(88, 216, 208, 65))
        glow.setColorAt(0.5, QColor(40, 160, 220, 25))
        glow.setColorAt(1, QColor(0, 0, 0, 0))
        painter.setPen(Qt.NoPen)
        painter.setBrush(glow)
        painter.drawEllipse(QPointF(cx, cy - 20), 260, 260)

        # 3. Central 3D Fuserio Emblem
        if not self.emblem_pixmap.isNull():
            emblem_size = 84
            scaled_emblem = self.emblem_pixmap.scaled(
                emblem_size,
                emblem_size,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
            painter.drawPixmap(int(cx - emblem_size / 2), int(cy - 120), scaled_emblem)

        # 4. Windows-style Orbiting Progress Dots Spinner
        if self.mode in {"shutdown", "restart"}:
            num_dots = 6
            spinner_radius = 28.0
            spinner_cy = cy + 10.0
            base_rad = math.radians(self.spinner_angle)

            for i in range(num_dots):
                # Non-linear easing spacing for realistic Windows spinning effect
                dot_angle = base_rad - math.pow(i / float(num_dots), 1.3) * (math.pi * 0.9)
                dot_x = cx + spinner_radius * math.cos(dot_angle)
                dot_y = spinner_cy + spinner_radius * math.sin(dot_angle)
                alpha = max(35, int(255 - i * 36))

                dot_color = QColor("#57fabc")
                dot_color.setAlpha(alpha)
                painter.setPen(Qt.NoPen)
                painter.setBrush(dot_color)

                dot_size = max(3.0, 5.5 - i * 0.4)
                painter.drawEllipse(QPointF(dot_x, dot_y), dot_size, dot_size)

        # 5. Lock Screen Time (if mode == "lock")
        if self.mode == "lock":
            painter.setFont(QFont("sans-serif", 38, QFont.Bold))
            painter.setPen(QColor("#ffffff"))
            current_time = time.strftime("%H:%M")
            time_rect = QRectF(0, cy - 20, w, 50)
            painter.drawText(time_rect, Qt.AlignCenter, current_time)

            painter.setFont(QFont("sans-serif", 12, QFont.Normal))
            painter.setPen(QColor("#89d4c4"))
            current_date = time.strftime("%A, %B %d")
            date_rect = QRectF(0, cy + 35, w, 24)
            painter.drawText(date_rect, Qt.AlignCenter, current_date)

        # 6. Status Text (Title & Subtitle)
        if self.mode in {"shutdown", "restart"}:
            painter.setFont(QFont("sans-serif", 15, QFont.Bold))
            painter.setPen(QColor("#eaf7f5"))
            title_rect = QRectF(0, cy + 54, w, 26)
            painter.drawText(title_rect, Qt.AlignCenter, self.status_title)

            painter.setFont(QFont("sans-serif", 10, QFont.Normal))
            painter.setPen(QColor("#89b4c8"))
            sub_rect = QRectF(0, cy + 86, w, 22)
            painter.drawText(sub_rect, Qt.AlignCenter, self.status_subtitle)
        elif self.mode == "lock":
            painter.setFont(QFont("sans-serif", 11, QFont.Normal))
            painter.setPen(QColor("#58d8d0"))
            prompt_rect = QRectF(0, cy + 90, w, 24)
            painter.drawText(prompt_rect, Qt.AlignCenter, self.status_subtitle)

        # 7. Progressive Fade-to-Black Overlay
        if self.fade_alpha > 0:
            black_overlay = QColor(0, 0, 0, self.fade_alpha)
            painter.fillRect(self.rect(), black_overlay)
