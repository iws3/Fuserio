import math

from PySide6.QtCore import QPointF, QRectF, QTimer, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QWidget

from localchat.lab_data import Experiment


BACKGROUND = QColor("#06120f")
GRID = QColor("#17342b")
MINT = QColor("#68efb2")
CYAN = QColor("#58d8d0")
AMBER = QColor("#ffbc74")
TEXT = QColor("#e8f7ef")
MUTED = QColor("#79968a")
PINK = QColor("#ff7186")


class LabCanvas(QWidget):
    """Offline, deterministic 2D experiment visualizations built with Qt painting."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(420, 300)
        self.setObjectName("labCanvas")
        self.setAccessibleName("Interactive science experiment simulation")
        self.experiment: Experiment | None = None
        self.parameters: dict[str, int] = {}
        self.elapsed = 0.0
        self.running = False
        self.playback_rate = 1.0
        self.timer = QTimer(self)
        self.timer.setInterval(33)
        self.timer.timeout.connect(self._tick)

    def set_experiment(self, experiment: Experiment, parameters: dict[str, int] | None = None):
        self.experiment = experiment
        self.parameters = {
            parameter.key: parameter.value for parameter in experiment.parameters
        }
        if parameters:
            self.parameters.update(parameters)
        self.elapsed = 0.0
        self.running = False
        self.timer.stop()
        self.update()

    def set_parameter(self, key: str, value: int):
        if key in self.parameters:
            self.parameters[key] = value
            self.update()

    def play(self):
        if not self.experiment:
            return
        self.running = True
        self.timer.start()
        self.update()

    def pause(self):
        self.running = False
        self.timer.stop()
        self.update()

    def set_playback_rate(self, rate: float):
        self.playback_rate = max(0.25, min(float(rate), 2.0))

    def step(self, seconds: float = 1 / 30):
        if self.running:
            return
        self.elapsed += max(0.0, seconds) * self.playback_rate
        self.update()

    def reset(self):
        self.elapsed = 0.0
        self.pause()
        self.update()

    def _tick(self):
        self.elapsed += self.playback_rate / 30
        self.update()

    def measurements(self) -> dict[str, str]:
        experiment_id = self.experiment.identifier if self.experiment else ""
        p = self.parameters
        if experiment_id == "projectile-motion":
            angle = math.radians(p.get("angle", 45))
            speed = p.get("speed", 25)
            gravity = p.get("gravity", 10)
            flight = 2 * speed * math.sin(angle) / gravity
            return {
                "RANGE": f"{speed**2 * math.sin(2 * angle) / gravity:.1f} m",
                "APEX": f"{speed**2 * math.sin(angle)**2 / (2 * gravity):.1f} m",
                "FLIGHT": f"{flight:.2f} s",
            }
        if experiment_id == "pendulum-lab":
            length = p.get("length", 100) / 100
            return {"PERIOD": f"{2 * math.pi * math.sqrt(length / 9.81):.2f} s", "LENGTH": f"{length:.2f} m"}
        if experiment_id == "ohms-law":
            voltage = p.get("voltage", 12)
            resistance = p.get("resistance", 12)
            return {"CURRENT": f"{voltage / resistance:.2f} A", "POWER": f"{voltage**2 / resistance:.1f} W"}
        if experiment_id == "diffusion":
            gradient = p.get("gradient", 70)
            permeability = p.get("permeability", 55)
            return {"GRADIENT": f"{gradient}%", "NET FLOW": f"{gradient * permeability / 100:.0f} units/s"}
        if experiment_id == "enzyme-activity":
            temperature = p.get("temperature", 37)
            enzyme = p.get("enzyme", 5)
            activity = max(0, 100 - abs(temperature - 37) * 2.4) * enzyme / 5
            return {"TEMP": f"{temperature} °C", "RELATIVE RATE": f"{activity:.0f}%"}
        if experiment_id == "natural-selection":
            pressure = p.get("pressure", 55)
            generations = p.get("generations", 20)
            frequency = min(99, 10 + pressure * generations / 25)
            return {"GENERATIONS": str(generations), "FAVOURED TRAIT": f"{frequency:.0f}%"}
        if experiment_id == "reaction-rate":
            temperature = p.get("temperature", 40)
            concentration = p.get("concentration", 55)
            rate = max(1, temperature * concentration / 30)
            return {"TEMP": f"{temperature} °C", "COLLISIONS": f"{rate:.0f}/s"}
        if experiment_id == "titration":
            volume = p.get("volume", 0)
            ph = 3 + 11 / (1 + math.exp(-(volume - 25) / 2.8))
            return {"VOLUME": f"{volume:.1f} mL", "MODEL pH": f"{ph:.1f}"}
        temperature = p.get("temperature", 35)
        state = "SOLID-LIKE" if temperature < 30 else "LIQUID-LIKE" if temperature < 70 else "GAS-LIKE"
        return {"TEMP": f"{temperature} °C", "MODEL STATE": state}

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        bounds = self.rect()
        painter.fillRect(bounds, BACKGROUND)
        self._draw_grid(painter, bounds)
        if not self.experiment:
            self._draw_empty(painter, bounds)
            painter.end()
            return
        draw_method = getattr(
            self,
            f"_draw_{self.experiment.identifier.replace('-', '_')}",
            None,
        )
        if draw_method is None:
            self._draw_empty(painter, bounds)
            painter.end()
            return
        draw_method(painter, bounds)
        self._draw_overlay(painter, bounds)
        painter.end()

    @staticmethod
    def _draw_grid(painter: QPainter, bounds):
        pen = QPen(GRID, 1, Qt.DotLine)
        painter.setPen(pen)
        for x in range(24, bounds.width(), 40):
            painter.drawLine(x, 0, x, bounds.height())
        for y in range(24, bounds.height(), 40):
            painter.drawLine(0, y, bounds.width(), y)

    def _draw_overlay(self, painter: QPainter, bounds):
        painter.setPen(MINT if self.running else MUTED)
        painter.setFont(QFont("monospace", 9, QFont.Bold))
        status = "● LIVE MODEL" if self.running else "Ⅱ PAUSED"
        painter.drawText(18, 24, status)
        painter.setPen(QColor("#527366"))
        painter.drawText(bounds.width() - 115, 24, f"SIM  {self.elapsed:05.1f}s")

    @staticmethod
    def _draw_empty(painter: QPainter, bounds):
        painter.setPen(MUTED)
        painter.drawText(bounds, Qt.AlignCenter, "Choose an experiment to enter the lab")

    def _draw_projectile_motion(self, painter: QPainter, bounds):
        p = self.parameters
        angle = math.radians(p.get("angle", 45))
        speed = p.get("speed", 25)
        gravity = p.get("gravity", 10)
        flight = 2 * speed * math.sin(angle) / gravity
        t = (self.elapsed % max(flight, 0.1)) if self.running else flight * 0.48
        x = speed * math.cos(angle) * t
        y = speed * math.sin(angle) * t - 0.5 * gravity * t * t
        range_m = speed**2 * math.sin(2 * angle) / gravity
        scale_x = (bounds.width() - 100) / max(range_m, 1)
        max_height = speed**2 * math.sin(angle) ** 2 / (2 * gravity)
        scale_y = (bounds.height() - 100) / max(max_height * 1.4, 1)
        ground = bounds.height() - 48
        origin = QPointF(48, ground)
        painter.setPen(QPen(QColor("#44685a"), 2))
        painter.drawLine(28, ground, bounds.width() - 24, ground)
        path = QPainterPath(origin)
        for sample in range(1, 41):
            sample_t = flight * sample / 40
            sample_x = speed * math.cos(angle) * sample_t
            sample_y = speed * math.sin(angle) * sample_t - 0.5 * gravity * sample_t**2
            path.lineTo(origin.x() + sample_x * scale_x, ground - sample_y * scale_y)
        painter.setPen(QPen(QColor("#326b58"), 2, Qt.DashLine))
        painter.drawPath(path)
        ball = QPointF(origin.x() + x * scale_x, ground - max(0, y) * scale_y)
        painter.setPen(Qt.NoPen)
        painter.setBrush(AMBER)
        painter.drawEllipse(ball, 9, 9)
        self._caption(painter, "VELOCITY VECTOR", 30, bounds.height() - 18, AMBER)

    def _draw_pendulum_lab(self, painter: QPainter, bounds):
        length = self.parameters.get("length", 100)
        max_angle = math.radians(self.parameters.get("angle", 25))
        damping = self.parameters.get("damping", 4) / 100
        omega = math.sqrt(9.81 / max(length / 100, 0.2))
        angle = max_angle * math.cos(omega * self.elapsed) * math.exp(-damping * self.elapsed / 2) if self.running else max_angle
        pivot = QPointF(bounds.width() * 0.5, 65)
        scale = min(bounds.height() - 130, 180) / 1.8
        bob = QPointF(pivot.x() + math.sin(angle) * length / 100 * scale, pivot.y() + math.cos(angle) * length / 100 * scale)
        painter.setPen(QPen(QColor("#527767"), 2))
        painter.drawLine(pivot, bob)
        painter.setPen(Qt.NoPen)
        painter.setBrush(AMBER)
        painter.drawEllipse(bob, 18, 18)
        painter.setBrush(QColor("#baf3d4"))
        painter.drawEllipse(pivot, 5, 5)
        arc = QRectF(pivot.x() - 100, pivot.y() - 8, 200, 200)
        painter.setPen(QPen(QColor("#315443"), 1, Qt.DashLine))
        painter.drawArc(arc, 205 * 16, 130 * 16)
        self._caption(painter, "OSCILLATION · SMALL-ANGLE MODEL", 24, bounds.height() - 20)

    def _draw_ohms_law(self, painter: QPainter, bounds):
        left, right = 90, bounds.width() - 90
        top, bottom = 85, bounds.height() - 70
        path = QPainterPath(QPointF(left, top))
        for point in (QPointF(right, top), QPointF(right, bottom), QPointF(left, bottom), QPointF(left, top)):
            path.lineTo(point)
        painter.setPen(QPen(CYAN, 3))
        painter.drawPath(path)
        resistor = QRectF(bounds.width() / 2 - 38, top - 10, 76, 20)
        painter.setPen(QPen(AMBER, 2))
        painter.setBrush(BACKGROUND)
        painter.drawRoundedRect(resistor, 3, 3)
        painter.setFont(QFont("monospace", 10, QFont.Bold))
        painter.drawText(resistor, Qt.AlignCenter, f"{self.parameters.get('resistance', 12)} Ω")
        painter.setPen(QPen(MINT, 2))
        voltage_y = (top + bottom) / 2
        painter.drawLine(left - 8, voltage_y - 16, left + 8, voltage_y - 16)
        painter.drawLine(left - 16, voltage_y + 16, left + 16, voltage_y + 16)
        count = max(2, min(18, int(self.parameters.get("voltage", 12) / max(self.parameters.get("resistance", 12), 1) * 7)))
        for index in range(count):
            phase = (self.elapsed * 0.55 + index / count) % 1 if self.running else index / count
            point = self._circuit_point(phase, left, right, top, bottom)
            painter.setPen(Qt.NoPen)
            painter.setBrush(AMBER)
            painter.drawEllipse(point, 3.5, 3.5)
        self._caption(painter, "CONVENTIONAL CURRENT →", 24, bounds.height() - 22, CYAN)

    @staticmethod
    def _circuit_point(phase, left, right, top, bottom):
        width, height = right - left, bottom - top
        perimeter = 2 * (width + height)
        distance = phase * perimeter
        if distance < width:
            return QPointF(left + distance, top)
        distance -= width
        if distance < height:
            return QPointF(right, top + distance)
        distance -= height
        if distance < width:
            return QPointF(right - distance, bottom)
        distance -= width
        return QPointF(left, bottom - distance)

    def _draw_diffusion(self, painter: QPainter, bounds):
        middle = bounds.width() * 0.5
        top, bottom = 65, bounds.height() - 50
        painter.setPen(QPen(CYAN, 3, Qt.DashLine))
        painter.drawLine(middle, top, middle, bottom)
        painter.setPen(QPen(QColor("#527767"), 1))
        painter.setBrush(QColor("#0d241c"))
        painter.drawRoundedRect(QRectF(25, top, middle - 35, bottom - top), 8, 8)
        painter.drawRoundedRect(QRectF(middle + 10, top, middle - 35, bottom - top), 8, 8)
        concentration = self.parameters.get("gradient", 70)
        permeability = self.parameters.get("permeability", 55)
        count_left = int(5 + concentration * 0.35)
        count_right = int(5 + (100 - concentration) * 0.12)
        self._draw_molecules(painter, count_left, 42, middle - 50, top + 20, bottom - 20, AMBER, 0)
        self._draw_molecules(painter, count_right, middle + 25, bounds.width() - 42, top + 20, bottom - 20, CYAN, 1)
        if self.running and permeability:
            for index in range(int(permeability / 20)):
                phase = (self.elapsed * 0.18 + index * 0.21) % 1
                x = middle + (phase - 0.5) * 50
                y = top + 30 + ((index * 47 + int(self.elapsed * 13)) % max(int(bottom - top - 60), 1))
                painter.setPen(Qt.NoPen)
                painter.setBrush(AMBER)
                painter.drawEllipse(QPointF(x, y), 4, 4)
        self._caption(painter, "SELECTIVELY PERMEABLE MEMBRANE", 24, bounds.height() - 17, CYAN)

    def _draw_enzyme_activity(self, painter: QPainter, bounds):
        temperature = self.parameters.get("temperature", 37)
        activity = max(0, 100 - abs(temperature - 37) * 2.4)
        self._draw_reaction_particles(painter, bounds, activity / 100, self.parameters.get("enzyme", 5))
        baseline = bounds.height() - 44
        chart = QRectF(24, bounds.height() - 112, bounds.width() - 48, 56)
        painter.setPen(QPen(QColor("#395347"), 1))
        painter.drawRect(chart)
        path = QPainterPath(QPointF(chart.left(), chart.bottom()))
        for sample in range(1, 41):
            t = sample / 40
            rate = max(0, 1 - abs(t - 0.37) * 2.2)
            path.lineTo(chart.left() + t * chart.width(), chart.bottom() - rate * chart.height())
        painter.setPen(QPen(MINT, 2))
        painter.drawPath(path)
        marker_x = chart.left() + min(temperature / 90, 1) * chart.width()
        painter.setPen(QPen(AMBER, 2, Qt.DashLine))
        painter.drawLine(QPointF(marker_x, chart.top()), QPointF(marker_x, chart.bottom()))
        self._caption(painter, "RELATIVE ENZYME ACTIVITY", 26, baseline, MINT)

    def _draw_natural_selection(self, painter: QPainter, bounds):
        pressure = self.parameters.get("pressure", 55)
        variation = self.parameters.get("variation", 45)
        generations = self.parameters.get("generations", 20)
        progress = min(self.elapsed / max(generations / 4, 1), 1) if self.running else 0.55
        favored = min(0.95, 0.15 + progress * pressure / 100 * (0.6 + variation / 300))
        center = bounds.width() / 2
        self._draw_population(painter, int(40 * favored), 42, center - 12, 72, bounds.height() - 54, MINT, 0)
        self._draw_population(painter, int(40 * (1 - favored)), center + 12, bounds.width() - 42, 72, bounds.height() - 54, PINK, 2)
        painter.setPen(QPen(CYAN, 2, Qt.DashLine))
        painter.drawLine(center, 55, center, bounds.height() - 48)
        self._caption(painter, f"GENERATION {int(progress * generations):02d} · TRAIT FREQUENCY SHIFTS", 22, bounds.height() - 18)

    def _draw_reaction_rate(self, painter: QPainter, bounds):
        temperature = self.parameters.get("temperature", 40)
        concentration = self.parameters.get("concentration", 55)
        energy = min(1.0, temperature / 75)
        self._draw_reaction_particles(painter, bounds, energy, int(4 + concentration / 15))
        collisions = int(self.elapsed * max(1, temperature * concentration / 1500)) if self.running else 0
        self._caption(painter, f"EFFECTIVE COLLISIONS  {collisions:03d}", 24, bounds.height() - 18, AMBER)

    def _draw_titration(self, painter: QPainter, bounds):
        volume = self.parameters.get("volume", 0)
        center = bounds.width() * 0.53
        beaker = QRectF(center - 75, 120, 150, bounds.height() - 175)
        fill_height = beaker.height() * 0.58
        liquid = QRectF(beaker.left() + 4, beaker.bottom() - fill_height, beaker.width() - 8, fill_height - 4)
        color_amount = max(0, min(1, (volume - 18) / 14))
        liquid_color = QColor.fromRgbF(0.20 + color_amount * 0.45, 0.70 - color_amount * 0.42, 0.48 + color_amount * 0.27, 0.75)
        painter.setPen(QPen(QColor("#93b7a9"), 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(beaker, 4, 4)
        painter.fillRect(liquid, liquid_color)
        burette = QRectF(center + 105, 50, 25, bounds.height() * 0.48)
        painter.setPen(QPen(CYAN, 2))
        painter.drawRoundedRect(burette, 4, 4)
        painter.fillRect(QRectF(burette.left() + 3, burette.top() + 3, burette.width() - 6, burette.height() * max(0.1, 1 - volume / 55)), QColor("#63cfc7"))
        if self.running and int(self.elapsed * 2) % 2 == 0:
            painter.setPen(Qt.NoPen)
            painter.setBrush(AMBER)
            painter.drawEllipse(QPointF(center + 117, 325), 3, 5)
        self._caption(painter, "INDICATOR · COLOUR APPROACHES ENDPOINT", 22, bounds.height() - 18, AMBER)

    def _draw_particle_states(self, painter: QPainter, bounds):
        temperature = self.parameters.get("temperature", 35)
        attraction = self.parameters.get("attraction", 60)
        count = 42
        spread = 0.25 + temperature / 100 * 0.72
        center_x, center_y = bounds.width() / 2, bounds.height() / 2
        for index in range(count):
            column, row = index % 7, index // 7
            base_x = center_x + (column - 3) * 22
            base_y = center_y + (row - 2.5) * 22
            drift = math.sin(index * 2.2 + self.elapsed * (0.5 + spread * 4)) * 16 * spread if self.running else 0
            x = center_x + (base_x - center_x) * (0.4 + spread) + drift
            y = center_y + (base_y - center_y) * (0.4 + spread) + math.cos(index + self.elapsed * 3) * 11 * spread
            painter.setPen(Qt.NoPen)
            painter.setBrush(CYAN if index % 4 else AMBER)
            painter.drawEllipse(QPointF(x, y), 4, 4)
        state = "SOLID-LIKE" if temperature < 30 else "LIQUID-LIKE" if temperature < 70 else "GAS-LIKE"
        self._caption(painter, f"{state} · ATTRACTION {attraction}%", 24, bounds.height() - 18)

    def _draw_reaction_particles(self, painter, bounds, energy, concentration):
        count = max(8, min(32, 7 + concentration * 2))
        for index in range(count):
            x_seed = (index * 67 + 29) % max(bounds.width() - 50, 1)
            y_seed = (index * 43 + 17) % max(bounds.height() - 100, 1)
            drift = self.elapsed * (8 + energy * 62) if self.running else 0
            x = 25 + (x_seed + drift * (1 if index % 2 else -0.55)) % max(bounds.width() - 50, 1)
            y = 44 + (y_seed + math.sin(self.elapsed * 2 + index) * 20 * energy) % max(bounds.height() - 95, 1)
            painter.setPen(Qt.NoPen)
            painter.setBrush(AMBER if index % 3 else CYAN)
            painter.drawEllipse(QPointF(x, y), 5, 5)
        for index in range(max(1, concentration // 2)):
            x = 50 + (index * 83 + int(self.elapsed * 90)) % max(bounds.width() - 100, 1)
            y = 50 + (index * 51 + int(self.elapsed * 43)) % max(bounds.height() - 110, 1)
            painter.setPen(QPen(QColor("#d5e879"), 1))
            painter.drawLine(x - 6, y, x + 6, y)
            painter.drawLine(x, y - 6, x, y + 6)

    @staticmethod
    def _draw_molecules(painter, count, left, right, top, bottom, color, offset):
        width = max(right - left, 1)
        height = max(bottom - top, 1)
        for index in range(count):
            x = left + ((index * 43 + offset * 19) % int(width))
            y = top + ((index * 61 + offset * 37) % int(height))
            painter.setPen(Qt.NoPen)
            painter.setBrush(color)
            painter.drawEllipse(QPointF(x, y), 4, 4)

    @staticmethod
    def _draw_population(painter, count, left, right, top, bottom, color, phase):
        width, height = max(right - left, 1), max(bottom - top, 1)
        for index in range(count):
            x = left + ((index * 37 + phase * 23) % int(width))
            y = top + ((index * 59 + phase * 17) % int(height))
            painter.setPen(Qt.NoPen)
            painter.setBrush(color)
            painter.drawRoundedRect(QRectF(x, y, 7, 11), 3, 3)

    @staticmethod
    def _caption(painter, text, x, y, color=TEXT):
        painter.setPen(color)
        painter.setFont(QFont("monospace", 9, QFont.Bold))
        painter.drawText(x, y, text)