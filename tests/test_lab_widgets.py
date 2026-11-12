import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from localchat.lab_data import EXPERIMENTS, experiment_by_id
from localchat.lab_widgets import LabCanvas


def app():
    return QApplication.instance() or QApplication([])


def test_every_experiment_canvas_paints_offscreen():
    app()
    canvas = LabCanvas()
    canvas.resize(640, 380)

    for experiment in EXPERIMENTS:
        canvas.set_experiment(experiment)
        image = canvas.grab().toImage()
        assert not image.isNull(), experiment.identifier
        assert image.width() == 640
        assert image.height() == 380

    canvas.close()


def test_physics_measurements_respond_to_controls():
    app()
    canvas = LabCanvas()
    projectile = experiment_by_id("projectile-motion")
    assert projectile is not None
    canvas.set_experiment(projectile)
    initial_range = float(canvas.measurements()["RANGE"].split()[0])

    canvas.set_parameter("speed", 35)

    assert float(canvas.measurements()["RANGE"].split()[0]) > initial_range
    canvas.set_experiment(experiment_by_id("ohms-law"))
    assert canvas.measurements()["CURRENT"] == "1.00 A"
    canvas.set_parameter("resistance", 24)
    assert canvas.measurements()["CURRENT"] == "0.50 A"


def test_canvas_play_pause_reset_controls_animation_clock():
    app()
    canvas = LabCanvas()
    canvas.set_experiment(EXPERIMENTS[0])
    canvas.play()
    assert canvas.running
    assert canvas.timer.isActive()
    canvas._tick()
    assert canvas.elapsed > 0
    canvas.pause()
    assert not canvas.running
    assert not canvas.timer.isActive()
    canvas.reset()
    assert canvas.elapsed == 0


def test_canvas_single_step_and_playback_rate_are_bounded():
    app()
    canvas = LabCanvas()
    canvas.set_experiment(EXPERIMENTS[0])
    canvas.set_playback_rate(1.5)
    canvas.step()
    assert canvas.elapsed == 0.05

    canvas.set_playback_rate(9)
    assert canvas.playback_rate == 2.0
    canvas.set_playback_rate(0)
    assert canvas.playback_rate == 0.25

    canvas.play()
    current_time = canvas.elapsed
    canvas.step()
    assert canvas.elapsed == current_time
    canvas.pause()


def test_chemistry_playground_adds_water_and_salt_and_reports_saturation():
    app()
    canvas = LabCanvas()
    experiment = experiment_by_id("chemistry-playground")
    assert experiment is not None
    canvas.set_playground(experiment)
    canvas.add_playground_item("water")
    canvas.add_playground_item("salt")
    canvas.add_playground_item("salt")

    readings = canvas.measurements()
    assert readings["WATER"] == "25 mL"
    assert readings["DISSOLVED SALT"] == "9.0 g"
    assert readings["SOLID LEFT"] == "1.0 g"
    canvas.close()


def test_circuit_playground_switch_controls_current_and_bulb():
    app()
    canvas = LabCanvas()
    experiment = experiment_by_id("circuit-playground")
    assert experiment is not None
    canvas.set_playground(experiment)
    for item in ("battery", "wire", "bulb", "switch"):
        canvas.add_playground_item(item)
    assert canvas.measurements()["CURRENT"] == "0.30 A"
    assert canvas.measurements()["BULB"] == "Lit"

    canvas.add_playground_item("switch")
    assert canvas.measurements()["CURRENT"] == "0.00 A"
    assert canvas.measurements()["BULB"] == "Off"
    canvas.close()