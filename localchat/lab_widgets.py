import math

from PySide6.QtCore import QPointF, QRectF, QTimer, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QFont, QLinearGradient, QPainter, QPainterPath, QPen, QRadialGradient
from PySide6.QtWidgets import QWidget

from localchat.lab_data import Experiment
from localchat.titration import INDICATORS, TITRATION_FLAVORS, flavor_by_id, indicator_color, titration_ph


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

    metrics_updated = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(320, 300)
        self.setObjectName("labCanvas")
        self.setAccessibleName("Interactive science experiment simulation")
        self.experiment: Experiment | None = None
        self.parameters: dict[str, int] = {}
        self.elapsed = 0.0
        self.running = False
        self.playback_rate = 1.0
        self.playground_items: dict[str, float | bool] = {}

        # Realistic Titration Laboratory State
        self.titration_analyte_ml: float = 25.0
        self.titration_analyte_pipetted: bool = True
        self.titration_indicator_drops: int = 3
        self.titration_water_wash_ml: float = 0.0
        self.titration_swirl_intensity: float = 0.0
        self.titration_transient_flash: float = 0.0
        self.titration_drop_progress: float = 0.0
        self._tick_counter = 0

        self.timer = QTimer(self)
        self.timer.setInterval(33)
        self.timer.timeout.connect(self._tick)

    def set_experiment(self, experiment: Experiment, parameters: dict[str, int] | None = None):
        self.experiment = experiment
        self.playground_items = {}
        self.parameters = {
            parameter.key: parameter.value for parameter in experiment.parameters
        }
        if parameters:
            self.parameters.update(parameters)
        if experiment.identifier == "titration":
            self.titration_analyte_ml = 25.0
            self.titration_analyte_pipetted = True
            self.titration_indicator_drops = 3
            self.titration_water_wash_ml = 0.0
            self.titration_swirl_intensity = 0.0
            self.titration_transient_flash = 0.0
            self.titration_drop_progress = 0.0
        self.elapsed = 0.0
        self.running = False
        self.timer.stop()
        self.update()

    def set_playground(self, experiment: Experiment):
        self.set_experiment(experiment)
        self.playground_items = {
            "water_ml": 0.0,
            "salt_g": 0.0,
            "acid_ml": 0.0,
            "base_ml": 0.0,
            "stir_count": 0.0,
            "battery": False,
            "switch": False,
            "wire": False,
            "bulb": False,
        }
        self.play()

    def add_playground_item(self, item: str):
        if item == "water":
            self.playground_items["water_ml"] = float(self.playground_items.get("water_ml", 0)) + 25
        elif item == "salt":
            self.playground_items["salt_g"] = float(self.playground_items.get("salt_g", 0)) + 5
        elif item == "acid":
            self.playground_items["acid_ml"] = float(self.playground_items.get("acid_ml", 0)) + 5
        elif item == "base":
            self.playground_items["base_ml"] = float(self.playground_items.get("base_ml", 0)) + 5
        elif item == "stir":
            self.playground_items["stir_count"] = float(self.playground_items.get("stir_count", 0)) + 1
        elif item in {"battery", "wire", "bulb"}:
            self.playground_items[item] = True
        elif item == "switch":
            self.playground_items["switch"] = not bool(self.playground_items.get("switch", False))
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

    def titration_action(self, action: str):
        if not self.experiment or self.experiment.identifier != "titration":
            return
        if action == "pipette_acid":
            self.titration_analyte_ml = 25.0
            self.titration_analyte_pipetted = True
            self.titration_transient_flash = 0.0
        elif action == "add_indicator":
            self.titration_indicator_drops = min(12, self.titration_indicator_drops + 1)
        elif action == "clear_indicator":
            self.titration_indicator_drops = 0
        elif action == "fill_burette":
            self.parameters["volume"] = 0
            self.titration_transient_flash = 0.0
        elif action == "dropwise":
            vol = float(self.parameters.get("volume", 0)) + 0.10
            self.parameters["volume"] = min(50.0, round(vol, 2))
            self.titration_drop_progress = 1.0
            conc = self.parameters.get("concentration", 50)
            equiv = 25.0 * 50.0 / max(10, conc)
            if abs(self.parameters["volume"] - equiv) <= 2.5:
                self.titration_transient_flash = 1.0
        elif action == "add_half_ml":
            vol = float(self.parameters.get("volume", 0)) + 0.50
            self.parameters["volume"] = min(50.0, round(vol, 2))
            self.titration_drop_progress = 1.0
            conc = self.parameters.get("concentration", 50)
            equiv = 25.0 * 50.0 / max(10, conc)
            if abs(self.parameters["volume"] - equiv) <= 2.5:
                self.titration_transient_flash = 1.0
        elif action == "add_1ml":
            vol = float(self.parameters.get("volume", 0)) + 1.00
            self.parameters["volume"] = min(50.0, round(vol, 2))
            self.titration_drop_progress = 1.0
            conc = self.parameters.get("concentration", 50)
            equiv = 25.0 * 50.0 / max(10, conc)
            if abs(self.parameters["volume"] - equiv) <= 2.5:
                self.titration_transient_flash = 1.0
        elif action == "swirl":
            self.titration_swirl_intensity = 1.0
            self.titration_transient_flash = max(0.0, self.titration_transient_flash - 0.6)
        elif action == "wash_water":
            self.titration_water_wash_ml = min(50.0, self.titration_water_wash_ml + 5.0)
        elif action == "reset":
            self.titration_analyte_ml = 25.0
            self.titration_analyte_pipetted = True
            self.titration_indicator_drops = 3
            self.titration_water_wash_ml = 0.0
            self.titration_swirl_intensity = 0.0
            self.titration_transient_flash = 0.0
            self.titration_drop_progress = 0.0
            self.parameters["volume"] = 0
            self.pause()
        self.update()
        self.metrics_updated.emit()

    def reset(self):
        self.elapsed = 0.0
        if self.experiment and self.experiment.identifier == "titration":
            self.titration_analyte_ml = 25.0
            self.titration_analyte_pipetted = True
            self.titration_indicator_drops = 3
            self.titration_water_wash_ml = 0.0
            self.titration_swirl_intensity = 0.0
            self.titration_transient_flash = 0.0
            self.titration_drop_progress = 0.0
            self.parameters["volume"] = 0
        self.pause()
        self.update()
        self.metrics_updated.emit()

    def _tick(self):
        self.elapsed += self.playback_rate / 30
        self._tick_counter += 1
        if self.experiment and self.experiment.identifier == "titration":
            if self.running:
                d_vol = (0.45 * self.playback_rate) / 30.0
                curr_vol = float(self.parameters.get("volume", 0))
                new_vol = min(50.0, curr_vol + d_vol)
                self.parameters["volume"] = new_vol
                self.titration_drop_progress = (self.titration_drop_progress + 0.16 * self.playback_rate) % 1.0
                conc = self.parameters.get("concentration", 50)
                equiv = 25.0 * 50.0 / max(10, conc)
                if abs(new_vol - equiv) < 2.0:
                    self.titration_transient_flash = min(1.0, self.titration_transient_flash + 0.08)
                if new_vol >= 50.0:
                    self.pause()
            else:
                if self.titration_drop_progress > 0:
                    self.titration_drop_progress = (self.titration_drop_progress + 0.15) % 1.0
                    if self.titration_drop_progress < 0.1:
                        self.titration_drop_progress = 0.0

            if self.titration_swirl_intensity > 0:
                self.titration_swirl_intensity = max(0.0, self.titration_swirl_intensity - 0.02)
            if self.titration_transient_flash > 0:
                decay = 0.025 + 0.05 * self.titration_swirl_intensity
                self.titration_transient_flash = max(0.0, self.titration_transient_flash - decay)
        self.update()
        if self._tick_counter % 3 == 0:
            self.metrics_updated.emit()

    def measurements(self) -> dict[str, str]:
        experiment_id = self.experiment.identifier if self.experiment else ""
        p = self.parameters
        if experiment_id == "chemistry-playground":
            water = float(self.playground_items.get("water_ml", 0))
            salt = float(self.playground_items.get("salt_g", 0))
            dissolved = min(salt, water * 0.36)
            acid_ml = float(self.playground_items.get("acid_ml", 0))
            base_ml = float(self.playground_items.get("base_ml", 0))
            total_volume = water + acid_ml + base_ml
            excess = (acid_ml - base_ml) * 0.1 / 1000
            if total_volume <= 0 or abs(excess) < 1e-12:
                ph = 7.0
            elif excess > 0:
                ph = -math.log10(max(excess / (total_volume / 1000), 1e-14))
            else:
                ph = 14 + math.log10(max(-excess / (total_volume / 1000), 1e-14))
            return {
                "WATER": f"{water:.0f} mL",
                "DISSOLVED SALT": f"{dissolved:.1f} g",
                "SOLID LEFT": f"{max(0, salt - dissolved):.1f} g",
                "MODEL pH": f"{max(0, min(14, ph)):.2f}",
            }
        if experiment_id == "circuit-playground":
            complete = all(bool(self.playground_items.get(part, False)) for part in ("battery", "wire", "bulb", "switch"))
            return {
                "BATTERY": "9 V" if self.playground_items.get("battery") else "Not added",
                "SWITCH": "Closed" if self.playground_items.get("switch") else "Open",
                "CURRENT": "0.30 A" if complete else "0.00 A",
                "BULB": "Lit" if complete else "Off",
            }
        if experiment_id == "salt-solubility":
            water = p.get("water", 100)
            salt = p.get("salt", 20)
            temperature = p.get("temperature", 20)
            dissolved = min(salt, water * (0.32 + temperature * 0.0007))
            return {
                "WATER": f"{water} mL",
                "DISSOLVED": f"{dissolved:.1f} g",
                "SOLID LEFT": f"{max(0, salt - dissolved):.1f} g",
            }
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
            volume = float(p.get("volume", 0))
            flavor = flavor_by_id(TITRATION_FLAVORS[p.get("flavor", 0)].identifier)
            indicator = INDICATORS[p.get("indicator", 0)]
            acid_molarity = 0.1
            base_molarity = max(0.01, 0.1 * (p.get("concentration", 50) / 50.0))
            analyte_vol = self.titration_analyte_ml if getattr(self, "titration_analyte_pipetted", True) else 0.001
            ph = titration_ph(flavor, acid_molarity, max(0.1, analyte_vol), base_molarity, volume)
            equiv_vol = acid_molarity * analyte_vol / base_molarity
            drops = getattr(self, "titration_indicator_drops", 3)
            diff = volume - equiv_vol

            if abs(diff) < 0.2:
                status = "★ Equivalence (Neutral)"
            elif diff < -2.0:
                status = "Acidic buffer region"
            elif diff < 0:
                status = "Approaching endpoint"
            elif diff <= 2.0:
                status = "End point passed"
            else:
                status = "Alkaline excess"

            return {
                "VOLUME": f"{volume:.1f} mL",
                "MODEL pH": f"{ph:.2f}",
                "INDICATOR": f"{indicator} ({drops} drops)" if drops > 0 else f"{indicator} (0 drops)",
                "TITRE": f"{volume:.2f} mL",
                "EQUIVALENCE": f"{equiv_vol:.1f} mL",
                "STATUS": status,
            }
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
        if self.experiment.identifier == "chemistry-playground":
            self._draw_chemistry_playground(painter, bounds)
            self._draw_overlay(painter, bounds)
            painter.end()
            return
        if self.experiment.identifier == "circuit-playground":
            self._draw_circuit_playground(painter, bounds)
            self._draw_overlay(painter, bounds)
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
        volume = float(self.parameters.get("volume", 0))
        flavor = flavor_by_id(TITRATION_FLAVORS[self.parameters.get("flavor", 0)].identifier)
        indicator = INDICATORS[self.parameters.get("indicator", 0)]
        concentration = self.parameters.get("concentration", 50)
        acid_molarity = 0.1
        base_molarity = max(0.01, 0.1 * (concentration / 50.0))
        analyte_vol = self.titration_analyte_ml if getattr(self, "titration_analyte_pipetted", True) else 0.001
        ph = titration_ph(flavor, acid_molarity, max(0.1, analyte_vol), base_molarity, volume)
        equiv_vol = acid_molarity * analyte_vol / base_molarity
        drops = getattr(self, "titration_indicator_drops", 3)

        W = bounds.width()
        H = bounds.height()
        cx = W * 0.40
        bench_y = H - 38

        # --- 1. Lab Bench Surface ---
        bench_grad = QLinearGradient(0, bench_y, 0, H)
        bench_grad.setColorAt(0, QColor("#132924"))
        bench_grad.setColorAt(0.2, QColor("#0d1d19"))
        bench_grad.setColorAt(1, QColor("#060e0c"))
        painter.fillRect(QRectF(0, bench_y, W, H - bench_y), bench_grad)
        painter.setPen(QPen(QColor("#275347"), 2))
        painter.drawLine(QPointF(0, bench_y), QPointF(W, bench_y))
        painter.setPen(QPen(QColor(104, 239, 178, 40), 1))
        painter.drawLine(QPointF(0, bench_y + 2), QPointF(W, bench_y + 2))

        # --- 2. Retort Stand Base & Vertical Steel Rod ---
        # Stand Base (Cast-Iron Heavy Rectangular Block)
        stand_left = cx - 95
        stand_w = 145
        stand_h = 12
        stand_rect = QRectF(stand_left, bench_y - stand_h, stand_w, stand_h)
        base_grad = QLinearGradient(stand_left, stand_rect.top(), stand_left, stand_rect.bottom())
        base_grad.setColorAt(0, QColor("#2b443c"))
        base_grad.setColorAt(0.4, QColor("#1b2c27"))
        base_grad.setColorAt(1, QColor("#0c1513"))
        painter.setPen(QPen(QColor("#3d5e53"), 1))
        painter.setBrush(base_grad)
        painter.drawRoundedRect(stand_rect, 3, 3)
        # Rubber foot pads
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#080f0d"))
        painter.drawRect(QRectF(stand_left + 8, bench_y, 14, 2))
        painter.drawRect(QRectF(stand_left + stand_w - 22, bench_y, 14, 2))

        # Vertical Polished Steel Rod
        rod_x = cx - 72
        rod_top_y = 22
        rod_w = 7
        rod_rect = QRectF(rod_x - rod_w / 2, rod_top_y, rod_w, (bench_y - stand_h) - rod_top_y)
        rod_grad = QLinearGradient(rod_rect.left(), 0, rod_rect.right(), 0)
        rod_grad.setColorAt(0.0, QColor("#49665d"))
        rod_grad.setColorAt(0.25, QColor("#d3e6df"))
        rod_grad.setColorAt(0.65, QColor("#8faea4"))
        rod_grad.setColorAt(1.0, QColor("#364b44"))
        painter.setPen(Qt.NoPen)
        painter.setBrush(rod_grad)
        painter.drawRoundedRect(rod_rect, 2, 2)
        # Rod top metallic dome cap
        painter.setBrush(QColor("#c5ded5"))
        painter.drawEllipse(QPointF(rod_x, rod_top_y), 4, 3)

        # --- 3. White Ceramic Contrast Tile ---
        tile_w = 114
        tile_h = 7
        tile_x = cx - tile_w / 2
        tile_y = (bench_y - stand_h) - tile_h
        tile_rect = QRectF(tile_x, tile_y, tile_w, tile_h)
        tile_grad = QLinearGradient(tile_x, tile_y, tile_x, tile_y + tile_h)
        tile_grad.setColorAt(0, QColor("#ffffff"))
        tile_grad.setColorAt(0.3, QColor("#f2faf7"))
        tile_grad.setColorAt(1, QColor("#d5e8e0"))
        painter.setBrush(tile_grad)
        painter.setPen(QPen(QColor("#adc9bd"), 1))
        painter.drawRoundedRect(tile_rect, 2, 2)
        # Tile gloss highlight
        painter.setPen(QPen(QColor(255, 255, 255, 220), 1))
        painter.drawLine(QPointF(tile_x + 3, tile_y + 1), QPointF(tile_x + tile_w - 3, tile_y + 1))

        # --- 4. Erlenmeyer Conical Flask (250 mL) ---
        flask_bottom_y = tile_y
        flask_h = min(120.0, max(85.0, (tile_y - 80) * 0.30))
        flask_top_y = flask_bottom_y - flask_h
        neck_h = flask_h * 0.22
        neck_w = 30
        base_w = 104

        # Burette Geometry: Delivery tip sits just above flask mouth rim!
        tip_y = flask_top_y - 18
        stopcock_y = tip_y - 34
        bur_top_y = 28
        bur_w = 20
        bur_left = cx - bur_w / 2
        bur_right = cx + bur_w / 2

        # Stand Bosshead & Dual-Prong Burette Clamps
        clamp_y1 = int(bur_top_y + (stopcock_y - bur_top_y) * 0.28)
        clamp_y2 = int(bur_top_y + (stopcock_y - bur_top_y) * 0.82)
        for cy in (clamp_y1, clamp_y2):
            boss_rect = QRectF(rod_x - 5, cy - 6, 10, 12)
            painter.setBrush(QColor("#243831"))
            painter.setPen(QPen(QColor("#425f55"), 1))
            painter.drawRoundedRect(boss_rect, 2, 2)
            # Thumbscrew knob
            painter.setBrush(QColor("#c9a150"))
            painter.setPen(QPen(QColor("#7f6327"), 1))
            painter.drawRoundedRect(QRectF(rod_x - 11, cy - 3, 6, 6), 1, 1)
            # Horizontal clamp arm
            arm_grad = QLinearGradient(rod_x + 5, cy - 2, cx - 11, cy - 2)
            arm_grad.setColorAt(0, QColor("#354f46"))
            arm_grad.setColorAt(1, QColor("#8daea3"))
            painter.setBrush(arm_grad)
            painter.setPen(Qt.NoPen)
            painter.drawRect(QRectF(rod_x + 5, cy - 2, (cx - 11) - (rod_x + 5), 4))
            # Rubberized clamp jaws gripping burette
            painter.setBrush(QColor("#b54341"))
            painter.setPen(QPen(QColor("#e86f6d"), 0.8))
            painter.drawRoundedRect(QRectF(cx - 13, cy - 5, 4, 10), 1, 1)
            painter.drawRoundedRect(QRectF(cx + 9, cy - 5, 4, 10), 1, 1)

        # Flask glass contour path
        neck_left = cx - neck_w / 2
        neck_right = cx + neck_w / 2
        base_left = cx - base_w / 2
        base_right = cx + base_w / 2

        flask_path = QPainterPath()
        flask_path.moveTo(neck_left - 2, flask_top_y)
        flask_path.lineTo(neck_right + 2, flask_top_y)
        flask_path.lineTo(neck_right + 2, flask_top_y + 3)
        flask_path.lineTo(neck_right, flask_top_y + 3)
        flask_path.lineTo(neck_right, flask_top_y + neck_h)
        flask_path.lineTo(base_right, flask_bottom_y - 7)
        flask_path.quadTo(base_right, flask_bottom_y, base_right - 8, flask_bottom_y)
        flask_path.lineTo(base_left + 8, flask_bottom_y)
        flask_path.quadTo(base_left, flask_bottom_y, base_left, flask_bottom_y - 7)
        flask_path.lineTo(neck_left, flask_top_y + neck_h)
        flask_path.lineTo(neck_left, flask_top_y + 3)
        flask_path.lineTo(neck_left - 2, flask_top_y + 3)
        flask_path.closeSubpath()

        # Solution Volume inside Conical Flask
        v_in_flask = (analyte_vol if getattr(self, "titration_analyte_pipetted", True) else 0.0) + getattr(self, "titration_water_wash_ml", 0.0) + volume
        fill_fraction = min(1.0, max(0.0, v_in_flask / 90.0))
        fill_h = 16 + fill_fraction * (flask_h - neck_h - 22)
        surface_y = flask_bottom_y - fill_h

        # Compute width of conical flask at surface_y
        slope = (base_w / 2 - neck_w / 2) / (flask_h - neck_h)
        h_from_bottom = flask_bottom_y - surface_y
        surf_w_half = min(base_w / 2 - 2, (neck_w / 2) + slope * (flask_h - neck_h - min(flask_h - neck_h, h_from_bottom)))
        swirl = getattr(self, "titration_swirl_intensity", 0.0)
        wave_amp = 1.0 + 3.8 * swirl

        # Liquid color determination
        if drops == 0:
            sol_base_color = QColor(200, 230, 225, 45)
            sol_top_color = QColor(220, 245, 240, 70)
        else:
            r, g, b = indicator_color(indicator, ph)
            sol_alpha = min(225, int(110 + drops * 22))
            sol_base_color = QColor(r, g, b, sol_alpha)
            sol_top_color = QColor(min(255, r + 35), min(255, g + 35), min(255, b + 35), min(240, sol_alpha + 25))

        # Liquid fill path
        liquid_path = QPainterPath()
        surf_left_x = cx - surf_w_half
        surf_right_x = cx + surf_w_half
        liquid_path.moveTo(surf_left_x, surface_y)

        steps = 14
        for i in range(1, steps + 1):
            t = i / steps
            wx = surf_left_x + t * (surf_right_x - surf_left_x)
            wy = surface_y + math.sin(self.elapsed * 6.0 + t * 4.5) * wave_amp
            liquid_path.lineTo(wx, wy)

        liquid_path.lineTo(base_right - 2, flask_bottom_y - 6)
        liquid_path.quadTo(base_right - 2, flask_bottom_y - 1, base_right - 8, flask_bottom_y - 1)
        liquid_path.lineTo(base_left + 8, flask_bottom_y - 1)
        liquid_path.quadTo(base_left + 2, flask_bottom_y - 1, base_left + 2, flask_bottom_y - 6)
        liquid_path.closeSubpath()

        # Draw flask interior shadow
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#071915"))
        painter.drawPath(flask_path)

        # Draw solution liquid
        liq_grad = QLinearGradient(cx, surface_y, cx, flask_bottom_y)
        liq_grad.setColorAt(0, sol_top_color)
        liq_grad.setColorAt(1, sol_base_color)
        painter.setBrush(liq_grad)
        painter.setPen(Qt.NoPen)
        painter.drawPath(liquid_path)

        # Meniscus top ellipse on liquid surface
        painter.setBrush(QColor(sol_top_color.red(), sol_top_color.green(), sol_top_color.blue(), 90))
        painter.setPen(QPen(QColor(255, 255, 255, 120), 1))
        painter.drawEllipse(QRectF(cx - surf_w_half, surface_y - 3, surf_w_half * 2, 6))

        # Transient Localized Endpoint Color Flash (Drop Impact Bloom)
        trans_flash = getattr(self, "titration_transient_flash", 0.0)
        if trans_flash > 0.02 and drops > 0:
            flash_rad = 12 + 32 * (1.0 - trans_flash)
            flash_center_x = cx + math.sin(self.elapsed * 3.0) * 4
            flash_center_y = surface_y + 7
            flash_r = QRadialGradient(flash_center_x, flash_center_y, flash_rad)
            if indicator == "Phenolphthalein":
                flash_r.setColorAt(0, QColor(255, 35, 140, int(220 * trans_flash)))
                flash_r.setColorAt(0.6, QColor(255, 100, 180, int(130 * trans_flash)))
                flash_r.setColorAt(1, QColor(255, 100, 180, 0))
            elif indicator == "Methyl orange":
                flash_r.setColorAt(0, QColor(255, 220, 40, int(220 * trans_flash)))
                flash_r.setColorAt(0.6, QColor(255, 180, 50, int(130 * trans_flash)))
                flash_r.setColorAt(1, QColor(255, 180, 50, 0))
            else:
                flash_r.setColorAt(0, QColor(40, 170, 255, int(220 * trans_flash)))
                flash_r.setColorAt(0.6, QColor(60, 200, 240, int(130 * trans_flash)))
                flash_r.setColorAt(1, QColor(60, 200, 240, 0))
            painter.setPen(Qt.NoPen)
            painter.setBrush(flash_r)
            painter.drawEllipse(QPointF(flash_center_x, flash_center_y), flash_rad, flash_rad * 0.7)

        # Flask Volume Markings (Frosted Etchings on glass)
        painter.setPen(QPen(QColor(255, 255, 255, 90), 1))
        marks = ((50, flask_bottom_y - 25), (100, flask_bottom_y - 45), (150, flask_bottom_y - 65), (200, flask_bottom_y - 82))
        for m_val, m_y in marks:
            painter.drawLine(QPointF(cx + 6, m_y), QPointF(cx + 18, m_y))
        font_marks = QFont()
        font_marks.setPixelSize(7)
        painter.setFont(font_marks)
        painter.setPen(QColor(255, 255, 255, 80))
        painter.drawText(int(cx + 21), int(flask_bottom_y - 42), "100 mL")
        painter.drawText(int(cx + 21), int(flask_bottom_y - 80), "200 mL")
        painter.drawText(int(cx - 24), int(flask_bottom_y - 20), "PYREX® 250mL")

        # Conical Flask Glass Wall Outline & Specular Glare
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(QColor("#a4d1c3"), 2.2))
        painter.drawPath(flask_path)
        painter.setPen(QPen(QColor(255, 255, 255, 130), 2))
        painter.drawLine(QPointF(neck_left + 3, flask_top_y + neck_h + 2), QPointF(base_left + 8, flask_bottom_y - 12))
        painter.setPen(QPen(QColor(255, 255, 255, 180), 1.5))
        painter.drawLine(QPointF(neck_left - 1, flask_top_y + 1), QPointF(neck_right + 1, flask_top_y + 1))

        # --- 5. Class A 50.00 mL Glass Burette ---
        # Burette Glass Barrel
        bur_rect = QRectF(bur_left, bur_top_y, bur_w, stopcock_y - bur_top_y)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(10, 32, 27, 120))
        painter.drawRect(bur_rect)

        # Titrant Liquid Level in Burette
        zero_y = bur_top_y + 14
        fifty_y = stopcock_y - 8
        v_dispensed = min(50.0, max(0.0, volume))
        liq_top_y = zero_y + (v_dispensed / 50.0) * (fifty_y - zero_y)

        if v_dispensed < 50.0:
            b_liq_rect = QRectF(bur_left + 1.5, liq_top_y, bur_w - 3, (stopcock_y - liq_top_y) + 2)
            b_liq_grad = QLinearGradient(bur_left, liq_top_y, bur_right, liq_top_y)
            b_liq_grad.setColorAt(0, QColor(75, 205, 192, 110))
            b_liq_grad.setColorAt(0.4, QColor(135, 245, 235, 150))
            b_liq_grad.setColorAt(1, QColor(65, 185, 175, 110))
            painter.setBrush(b_liq_grad)
            painter.setPen(Qt.NoPen)
            painter.drawRect(b_liq_rect)

            # Curved Concave Meniscus
            meniscus_path = QPainterPath()
            meniscus_path.moveTo(bur_left + 1.5, liq_top_y)
            meniscus_path.quadTo(cx, liq_top_y + 2.8, bur_right - 1.5, liq_top_y)
            painter.setPen(QPen(QColor(220, 255, 250, 220), 1.5))
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(meniscus_path)

        # Graduations and Numerals (0 to 50 mL)
        tick_font = QFont()
        tick_font.setPixelSize(7)
        painter.setFont(tick_font)
        for ml in range(0, 51):
            my = zero_y + (ml / 50.0) * (fifty_y - zero_y)
            if ml % 10 == 0:
                painter.setPen(QPen(QColor(165, 215, 202, 210), 1.2))
                painter.drawLine(QPointF(cx + 2, my), QPointF(bur_right - 1.5, my))
                painter.setPen(QColor("#9ed4c6"))
                painter.drawText(int(bur_right + 4), int(my + 2.5), str(ml))
            elif ml % 5 == 0:
                painter.setPen(QPen(QColor(145, 195, 185, 170), 1))
                painter.drawLine(QPointF(cx + 4, my), QPointF(bur_right - 1.5, my))
            else:
                painter.setPen(QPen(QColor(125, 175, 165, 110), 0.8))
                painter.drawLine(QPointF(cx + 6, my), QPointF(bur_right - 1.5, my))

        # Burette Glass Walls & Edge Glare
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(QColor("#7ab7a6"), 1.8))
        painter.drawLine(QPointF(bur_left, bur_top_y), QPointF(bur_left, stopcock_y))
        painter.drawLine(QPointF(bur_right, bur_top_y), QPointF(bur_right, stopcock_y))
        painter.setPen(QPen(QColor(255, 255, 255, 160), 1))
        painter.drawLine(QPointF(bur_left + 2, bur_top_y + 4), QPointF(bur_left + 2, stopcock_y - 2))

        # Stopcock Assembly (Barrel, Plug & Tapered Delivery Jet)
        stopcock_rect = QRectF(cx - 13, stopcock_y, 26, 12)
        sc_grad = QLinearGradient(cx - 13, stopcock_y, cx + 13, stopcock_y)
        sc_grad.setColorAt(0, QColor("#1e3d35"))
        sc_grad.setColorAt(0.5, QColor("#316155"))
        sc_grad.setColorAt(1, QColor("#17332b"))
        painter.setBrush(sc_grad)
        painter.setPen(QPen(QColor("#5aa390"), 1.2))
        painter.drawRoundedRect(stopcock_rect, 3, 3)

        # Stopcock Valve Handle / Key (Horizontal = Closed, Vertical/Angled = Flowing)
        painter.setPen(QPen(QColor("#41e0d0" if self.running else "#38b8aa"), 4, Qt.SolidLine, Qt.RoundCap))
        if self.running:
            painter.drawLine(QPointF(cx, stopcock_y - 3), QPointF(cx, stopcock_y + 15))
            painter.setPen(QPen(QColor("#68efb2"), 1.5))
            painter.drawEllipse(QPointF(cx, stopcock_y + 6), 2, 2)
        else:
            painter.drawLine(QPointF(cx - 12, stopcock_y + 6), QPointF(cx + 12, stopcock_y + 6))

        # Tapered Delivery Jet
        jet_path = QPainterPath()
        jet_path.moveTo(cx - 4, stopcock_y + 12)
        jet_path.lineTo(cx - 1.5, tip_y)
        jet_path.lineTo(cx + 1.5, tip_y)
        jet_path.lineTo(cx + 4, stopcock_y + 12)
        jet_path.closeSubpath()
        painter.setPen(QPen(QColor("#7ab7a6"), 1.2))
        painter.setBrush(QColor(80, 180, 165, 80))
        painter.drawPath(jet_path)

        # Droplet Animation
        drop_p = getattr(self, "titration_drop_progress", 0.0)
        if self.running or drop_p > 0:
            y_drop = tip_y + 2 + drop_p * (surface_y - (tip_y + 2))
            drop_path = QPainterPath()
            drop_path.moveTo(cx, y_drop - 5)
            drop_path.quadTo(cx - 2.5, y_drop, cx, y_drop + 2)
            drop_path.quadTo(cx + 2.5, y_drop, cx, y_drop - 5)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor("#72f0db"))
            painter.drawPath(drop_path)
            if drop_p > 0.85:
                ripple_r = (drop_p - 0.85) * 35
                painter.setPen(QPen(QColor(114, 240, 219, int(200 * (1.0 - drop_p) / 0.15)), 1.2))
                painter.setBrush(Qt.NoBrush)
                painter.drawEllipse(QPointF(cx, surface_y), ripple_r, ripple_r * 0.35)

        # --- 6. Glass pH Electrode Probe ---
        probe_top = QPointF(cx + 38, flask_top_y - 20)
        probe_tip = QPointF(cx + 14, surface_y + 14)
        painter.setPen(QPen(QColor(150, 210, 200, 150), 3))
        painter.drawLine(probe_top, probe_tip)
        painter.setPen(QPen(QColor(230, 245, 240, 210), 1))
        painter.drawLine(probe_top, probe_tip)
        bulb_grad = QRadialGradient(probe_tip.x(), probe_tip.y(), 5)
        bulb_grad.setColorAt(0, QColor(104, 239, 178, 220))
        bulb_grad.setColorAt(0.7, QColor(88, 216, 208, 140))
        bulb_grad.setColorAt(1, QColor(88, 216, 208, 0))
        painter.setPen(Qt.NoPen)
        painter.setBrush(bulb_grad)
        painter.drawEllipse(probe_tip, 5, 5)
        cable_path = QPainterPath()
        cable_path.moveTo(probe_top)
        meter_x = max(cx + 95, W * 0.65)
        meter_y = 38
        cable_path.cubicTo(probe_top.x() + 30, probe_top.y() - 15, meter_x - 30, meter_y + 40, meter_x + 10, meter_y + 35)
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(QColor("#2c4a41"), 2.2))
        painter.drawPath(cable_path)

        # --- 7. Digital Benchtop pH Meter (HUD Display) ---
        meter_w = min(210.0, max(170.0, W - meter_x - 18))
        meter_h = 162
        meter_rect = QRectF(meter_x, meter_y, meter_w, meter_h)

        m_grad = QLinearGradient(meter_x, meter_y, meter_x, meter_y + meter_h)
        m_grad.setColorAt(0, QColor("#102521"))
        m_grad.setColorAt(0.5, QColor("#0a1815"))
        m_grad.setColorAt(1, QColor("#06100e"))
        painter.setBrush(m_grad)
        painter.setPen(QPen(QColor("#244a3f"), 1.5))
        painter.drawRoundedRect(meter_rect, 10, 10)

        painter.setPen(QPen(QColor(104, 239, 178, 50), 1))
        painter.drawRoundedRect(meter_rect.adjusted(1, 1, -1, -1), 9, 9)

        t_font = QFont()
        t_font.setPixelSize(9)
        t_font.setBold(True)
        painter.setFont(t_font)
        painter.setPen(QColor("#58d8d0"))
        painter.drawText(int(meter_x + 12), int(meter_y + 18), "DIGITAL pH ANALYSER")

        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#57fabc"))
        painter.drawEllipse(QPointF(meter_x + meter_w - 14, meter_y + 14), 3, 3)

        lcd_rect = QRectF(meter_x + 10, meter_y + 26, meter_w - 20, 68)
        painter.setBrush(QColor("#040d0b"))
        painter.setPen(QPen(QColor("#16352c"), 1.2))
        painter.drawRoundedRect(lcd_rect, 6, 6)

        lcd_font = QFont("Monospace")
        lcd_font.setPixelSize(22)
        lcd_font.setBold(True)
        painter.setFont(lcd_font)
        if abs(ph - 7.0) < 0.3:
            ph_glow = QColor("#57fabc")
        elif ph < 7.0:
            ph_glow = QColor("#ffbc74") if ph > 3.5 else QColor("#ff7186")
        else:
            ph_glow = QColor("#58d8d0") if ph < 10.0 else QColor("#d08eff")
        painter.setPen(ph_glow)
        painter.drawText(int(lcd_rect.left() + 10), int(lcd_rect.top() + 32), f"pH {ph:.2f}")

        sub_font = QFont("Monospace")
        sub_font.setPixelSize(9)
        painter.setFont(sub_font)
        painter.setPen(QColor("#7da598"))
        potential_mv = (7.0 - ph) * 59.16
        painter.drawText(int(lcd_rect.left() + 10), int(lcd_rect.top() + 48), f"EMF {potential_mv:+.1f} mV")
        painter.drawText(int(lcd_rect.left() + 10), int(lcd_rect.top() + 61), "25.0 °C · ATC ON")

        status_rect = QRectF(meter_x + 10, meter_y + 102, meter_w - 20, 24)
        diff = volume - equiv_vol
        if drops == 0:
            badge_color = QColor(140, 160, 155, 30)
            badge_border = QColor("#8faea4")
            badge_text = "⚠ NO INDICATOR (CLEAR)"
            badge_tcolor = QColor("#d3e6df")
        elif abs(diff) < 0.15:
            badge_color = QColor(104, 239, 178, 45)
            badge_border = QColor("#68efb2")
            badge_text = "★ EQUIVALENCE (NEUTRAL)"
            badge_tcolor = QColor("#68efb2")
        elif diff < -2.0:
            badge_color = QColor(255, 188, 116, 30)
            badge_border = QColor("#ffbc74")
            badge_text = "● ACIDIC BUFFER ZONE"
            badge_tcolor = QColor("#ffbc74")
        elif diff < 0:
            badge_color = QColor(255, 113, 134, 40)
            badge_border = QColor("#ff7186")
            badge_text = "● NEAR ENDPOINT (DROPWISE)"
            badge_tcolor = QColor("#ff7186")
        elif diff <= 1.0:
            badge_color = QColor(255, 100, 180, 45)
            badge_border = QColor("#ff64b4")
            badge_text = "★ END POINT REACHED!"
            badge_tcolor = QColor("#ff64b4")
        else:
            badge_color = QColor(88, 216, 208, 30)
            badge_border = QColor("#58d8d0")
            badge_text = "● ALKALINE EXCESS"
            badge_tcolor = QColor("#58d8d0")

        painter.setBrush(badge_color)
        painter.setPen(QPen(badge_border, 1))
        painter.drawRoundedRect(status_rect, 4, 4)

        b_font = QFont()
        b_font.setPixelSize(8)
        b_font.setBold(True)
        painter.setFont(b_font)
        painter.setPen(badge_tcolor)
        painter.drawText(status_rect, Qt.AlignCenter, badge_text)

        bur_info_rect = QRectF(meter_x + 10, meter_y + 132, meter_w - 20, 22)
        painter.setBrush(QColor(16, 42, 36, 120))
        painter.setPen(QPen(QColor("#1e4d41"), 1))
        painter.drawRoundedRect(bur_info_rect, 4, 4)
        info_font = QFont()
        info_font.setPixelSize(8)
        painter.setFont(info_font)
        painter.setPen(QColor("#a4d1c3"))
        painter.drawText(bur_info_rect, Qt.AlignCenter, f"TITRE: {volume:.2f} mL  (Equiv: {equiv_vol:.1f} mL)")

        # --- 8. Top Apparatus Header & Indicator Callout ---
        self._caption(painter, "CLASS A PRECISION TITRATION APPARATUS", 18, 50, CYAN)
        ind_label = f"{indicator.upper()} ({drops} DROPS)" if drops > 0 else f"{indicator.upper()} (NO INDICATOR ADDED)"
        self._caption(painter, f"{flavor.label}  ·  {ind_label}", 18, 68, AMBER if drops > 0 else PINK)

    def _draw_chemistry_playground(self, painter: QPainter, bounds):
        water = float(self.playground_items.get("water_ml", 0))
        salt = float(self.playground_items.get("salt_g", 0))
        acid = float(self.playground_items.get("acid_ml", 0))
        base = float(self.playground_items.get("base_ml", 0))
        dissolved = min(salt, water * 0.36)
        beaker = QRectF(bounds.width() * 0.34, bounds.height() * 0.29, bounds.width() * 0.30, bounds.height() * 0.54)
        bench_y = bounds.height() * 0.87
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#102c25"))
        painter.drawRoundedRect(QRectF(28, bench_y, bounds.width() - 56, 20), 8, 8)
        painter.setBrush(QColor("#071a16"))
        painter.drawRoundedRect(QRectF(beaker.left() + 7, beaker.top() + 9, beaker.width(), beaker.height()), 12, 12)
        liquid_height = min(beaker.height() * 0.68, water * 0.0019 * beaker.height())
        liquid = QRectF(beaker.left() + 5, beaker.bottom() - liquid_height, beaker.width() - 10, liquid_height)
        if water:
            painter.setBrush(QColor("#3d9d9a"))
            painter.drawRoundedRect(liquid, 8, 8)
            painter.setBrush(QColor(121, 229, 215, 155))
            painter.drawEllipse(QRectF(liquid.left(), liquid.top() - 5, liquid.width(), 14))
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(QColor("#b7dfd1"), 3))
        painter.drawRoundedRect(beaker, 11, 11)
        painter.setPen(QPen(QColor(228, 255, 245, 120), 3))
        painter.drawLine(QPointF(beaker.left() + 15, beaker.top() + 18), QPointF(beaker.left() + 15, beaker.bottom() - 18))
        for index in range(int(dissolved * 2)):
            phase = self.elapsed * 2.4 if self.running else 0
            x = beaker.left() + 20 + (index * 31 % max(int(beaker.width() - 40), 1))
            y = liquid.top() + 12 + ((index * 23 + int(phase * 9)) % max(int(liquid.height() - 18), 1)) if water and liquid.height() > 20 else beaker.bottom() - 18
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor("#f6e4a0"))
            painter.drawEllipse(QPointF(x, y), 3, 3)
        solid_count = min(20, int(max(0, salt - dissolved) * 1.5))
        for index in range(solid_count):
            x = beaker.left() + 18 + (index * 29 % max(int(beaker.width() - 36), 1))
            y = beaker.bottom() - 13 - (index % 3) * 4
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor("#fff0bb"))
            painter.drawRect(QRectF(x, y, 4, 4))
        self._caption(painter, "VIRTUAL MIXING BENCH", 30, 52, CYAN)
        self._caption(painter, f"WATER {water:.0f} mL  ·  SALT {salt:.0f} g", 30, bounds.height() - 22, AMBER)
        if acid or base:
            self._caption(painter, f"ACID {acid:.0f} mL  ·  BASE {base:.0f} mL", bounds.width() - 240, bounds.height() - 22, PINK)

    def _draw_circuit_playground(self, painter: QPainter, bounds):
        center_y = bounds.height() * 0.52
        left, right = bounds.width() * 0.22, bounds.width() * 0.78
        top, bottom = bounds.height() * 0.25, bounds.height() * 0.78
        battery = bool(self.playground_items.get("battery"))
        switch = bool(self.playground_items.get("switch"))
        wire = bool(self.playground_items.get("wire"))
        bulb = bool(self.playground_items.get("bulb"))
        complete = battery and switch and wire and bulb
        painter.setPen(QPen(MINT if complete else QColor("#52776a"), 5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        if wire:
            painter.drawLine(QPointF(left, center_y), QPointF(left, top))
            painter.drawLine(QPointF(left, top), QPointF(right, top))
            painter.drawLine(QPointF(right, top), QPointF(right, center_y))
            painter.drawLine(QPointF(right, center_y), QPointF(right, bottom))
            painter.drawLine(QPointF(right, bottom), QPointF(left, bottom))
            painter.drawLine(QPointF(left, bottom), QPointF(left, center_y))
        if battery:
            painter.setPen(QPen(QColor("#9acbb9"), 2))
            painter.setBrush(QColor("#234d40"))
            painter.drawRoundedRect(QRectF(left - 32, center_y - 40, 64, 80), 9, 9)
            painter.setPen(QColor("#f4d480"))
            painter.drawText(QRectF(left - 30, center_y - 11, 60, 22), Qt.AlignCenter, "9 V")
        if switch:
            switch_x = (left + right) / 2
            painter.setPen(QPen(AMBER, 4, Qt.SolidLine, Qt.RoundCap))
            painter.drawLine(QPointF(switch_x - 25, top), QPointF(switch_x + 20, top - 18))
            painter.setBrush(AMBER)
            painter.drawEllipse(QPointF(switch_x - 25, top), 5, 5)
            painter.drawEllipse(QPointF(switch_x + 25, top), 5, 5)
        if bulb:
            bulb_center = QPointF(right, center_y)
            painter.setPen(QPen(QColor("#ffdb85" if complete else "#749083"), 3))
            painter.setBrush(QColor(255, 201, 88, 125 if complete else 24))
            painter.drawEllipse(bulb_center, 24 if complete else 18, 24 if complete else 18)
            painter.drawLine(QPointF(right - 10, center_y + 20), QPointF(right + 10, center_y + 20))
        if complete:
            for index in range(8):
                progress = (self.elapsed * 0.45 + index / 8) % 1
                x = left + (right - left) * progress
                painter.setPen(Qt.NoPen)
                painter.setBrush(AMBER)
                painter.drawEllipse(QPointF(x, top), 4, 4)
        self._caption(painter, "VIRTUAL CIRCUIT · 9 V MAX", 30, 52, CYAN)
        self._caption(painter, "CLOSED LOOP" if complete else "ADD PARTS, THEN CLOSE THE SWITCH", 30, bounds.height() - 22, AMBER)

    def _draw_salt_solubility(self, painter: QPainter, bounds):
        water = self.parameters.get("water", 100)
        salt = self.parameters.get("salt", 20)
        temperature = self.parameters.get("temperature", 20)
        dissolved = min(salt, water * (0.32 + temperature * 0.0007))
        beaker = QRectF(bounds.width() * 0.34, bounds.height() * 0.25, bounds.width() * 0.32, bounds.height() * 0.60)
        fill = QRectF(beaker.left() + 5, beaker.bottom() - beaker.height() * 0.62, beaker.width() - 10, beaker.height() * 0.62 - 5)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#348f91"))
        painter.drawRoundedRect(fill, 8, 8)
        painter.setBrush(QColor(117, 222, 209, 140))
        painter.drawEllipse(QRectF(fill.left(), fill.top() - 5, fill.width(), 14))
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(QColor("#b7dfd1"), 3))
        painter.drawRoundedRect(beaker, 10, 10)
        for index in range(min(25, int(dissolved))):
            x = beaker.left() + 18 + (index * 31 % max(int(beaker.width() - 36), 1))
            y = fill.top() + 15 + (index * 19 % max(int(fill.height() - 25), 1))
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor("#fff0bb"))
            painter.drawEllipse(QPointF(x, y), 3, 3)
        for index in range(min(20, int(max(0, salt - dissolved) * 1.5))):
            x = beaker.left() + 18 + (index * 29 % max(int(beaker.width() - 36), 1))
            painter.setBrush(QColor("#fff0bb"))
            painter.drawRect(QRectF(x, beaker.bottom() - 14 - index % 3 * 4, 4, 4))
        self._caption(painter, f"{temperature} °C  ·  {dissolved:.1f} g DISSOLVED", 26, bounds.height() - 20, AMBER)

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