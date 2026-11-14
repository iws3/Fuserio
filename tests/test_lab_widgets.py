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


def test_titration_interactive_actions_and_measurements():
    app()
    canvas = LabCanvas()
    experiment = experiment_by_id("titration")
    assert experiment is not None
    canvas.set_experiment(experiment)

    m = canvas.measurements()
    assert m["VOLUME"] == "0.0 mL"
    assert "MODEL pH" in m
    assert "Phenolphthalein" in m["INDICATOR"]
    assert "TITRE" in m
    assert "EQUIVALENCE" in m
    assert "STATUS" in m

    # Add indicator drop
    initial_drops = canvas.titration_indicator_drops
    canvas.titration_action("add_indicator")
    assert canvas.titration_indicator_drops == initial_drops + 1

    # Clear indicator
    canvas.titration_action("clear_indicator")
    assert canvas.titration_indicator_drops == 0
    assert "0 drops" in canvas.measurements()["INDICATOR"]

    # Pipette acid & restore indicator
    canvas.titration_action("pipette_acid")
    assert canvas.titration_analyte_ml == 25.0
    assert canvas.titration_analyte_pipetted is True
    canvas.titration_action("add_indicator")

    # Dropwise titrant addition
    canvas.titration_action("dropwise")
    assert canvas.parameters["volume"] == 0.10
    assert canvas.measurements()["TITRE"] == "0.10 mL"

    # Coarse titrant addition
    canvas.titration_action("add_1ml")
    assert canvas.parameters["volume"] == 1.10

    # Swirl flask
    canvas.titration_action("swirl")
    assert canvas.titration_swirl_intensity == 1.0

    # Wash flask neck with distilled water
    canvas.titration_action("wash_water")
    assert canvas.titration_water_wash_ml == 5.0

    # Reset titration
    canvas.titration_action("reset")
    assert canvas.parameters["volume"] == 0
    assert canvas.titration_water_wash_ml == 0.0
    canvas.close()


def test_titration_paints_apparatus_at_equivalence():
    app()
    canvas = LabCanvas()
    canvas.resize(720, 480)
    experiment = experiment_by_id("titration")
    assert experiment is not None
    canvas.set_experiment(experiment)
    # Set to equivalence volume (25.0 mL)
    canvas.set_parameter("volume", 25)
    canvas.titration_action("dropwise")
    canvas.titration_action("swirl")
    canvas._tick()

    m = canvas.measurements()
    assert float(m["MODEL pH"]) >= 7.0
    assert "Equivalence" in m["STATUS"] or "End point" in m["STATUS"]

    img = canvas.grab().toImage()
    assert not img.isNull()
    assert img.width() == 720
    assert img.height() == 480
    canvas.close()


def test_reaction_rate_interactive_actions_and_measurements():
    app()
    canvas = LabCanvas()
    experiment = experiment_by_id("reaction-rate")
    assert experiment is not None
    canvas.set_experiment(experiment)

    m = canvas.measurements()
    assert m["GAS VOLUME"] == "0.0 cm³"
    assert m["STATUS"] == "Ready"
    assert "RATE" in m
    assert "TEMP" in m
    assert "ACID CONC" in m
    assert "REACTANT" in m

    # Add acid increases concentration
    initial_conc = int(canvas.parameters.get("concentration", 50))
    canvas.reaction_rate_action("add_acid")
    assert int(canvas.parameters["concentration"]) == initial_conc + 10
    assert canvas.reaction_effervescence > 0

    # Add reactant increases mass
    initial_mass = int(canvas.parameters.get("mass", 3))
    canvas.reaction_rate_action("add_reactant")
    assert int(canvas.parameters["mass"]) == initial_mass + 1

    # Heat increases temperature
    initial_temp = int(canvas.parameters.get("temperature", 25))
    canvas.reaction_rate_action("heat")
    assert int(canvas.parameters["temperature"]) == initial_temp + 10

    # Cool decreases temperature
    canvas.reaction_rate_action("cool")
    assert int(canvas.parameters["temperature"]) == initial_temp

    # Add catalyst
    canvas.reaction_rate_action("add_catalyst")
    assert canvas.reaction_catalyst is True
    assert canvas.reaction_effervescence == 1.0

    # Flush syringe resets state
    canvas.reaction_rate_action("flush_syringe")
    assert canvas.reaction_gas_ml == 0.0
    assert canvas.reaction_rate_val == 0.0
    assert canvas.reaction_catalyst is False
    assert not canvas.running

    canvas.close()


def test_reaction_rate_paints_offscreen():
    app()
    canvas = LabCanvas()
    canvas.resize(720, 480)
    experiment = experiment_by_id("reaction-rate")
    assert experiment is not None
    canvas.set_experiment(experiment)
    canvas.reaction_rate_action("add_acid")
    canvas.play()
    canvas._tick()
    canvas._tick()

    img = canvas.grab().toImage()
    assert not img.isNull()
    assert img.width() == 720
    assert img.height() == 480
    canvas.close()


def test_salt_solubility_interactive_actions_and_measurements():
    app()
    canvas = LabCanvas()
    experiment = experiment_by_id("salt-solubility")
    assert experiment is not None
    canvas.set_experiment(experiment)

    m = canvas.measurements()
    assert "TEMP" in m
    assert "WATER" in m
    assert "DISSOLVED" in m
    assert "CRYSTALS" in m
    assert "STATUS" in m
    assert "LIMIT" in m

    # Add salt
    initial_salt = int(canvas.parameters.get("salt", 25))
    canvas.salt_solubility_action("add_salt")
    assert int(canvas.parameters["salt"]) == initial_salt + 5

    # Add water
    initial_water = int(canvas.parameters.get("water", 100))
    canvas.salt_solubility_action("add_water")
    assert int(canvas.parameters["water"]) == initial_water + 25

    # Heat lights burner and increases temperature
    initial_temp = int(canvas.parameters.get("temperature", 25))
    canvas.salt_solubility_action("heat")
    assert canvas.solubility_burner_lit is True
    assert int(canvas.parameters["temperature"]) == initial_temp + 15

    # Cool decreases temperature
    canvas.salt_solubility_action("cool")
    assert int(canvas.parameters["temperature"]) == initial_temp + 5

    # Toggle burner
    was_lit = canvas.solubility_burner_lit
    canvas.salt_solubility_action("toggle_burner")
    assert canvas.solubility_burner_lit != was_lit

    # Stir solution
    canvas.salt_solubility_action("stir")
    assert canvas.solubility_stir_intensity == 1.0

    # Reset returns to defaults
    canvas.salt_solubility_action("reset")
    assert canvas.solubility_burner_lit is True
    assert canvas.solubility_stir_intensity == 0.0
    assert not canvas.running

    canvas.close()


def test_salt_solubility_paints_offscreen():
    app()
    canvas = LabCanvas()
    canvas.resize(720, 480)
    experiment = experiment_by_id("salt-solubility")
    assert experiment is not None
    canvas.set_experiment(experiment)
    canvas.salt_solubility_action("heat")
    canvas.salt_solubility_action("stir")
    canvas.play()
    canvas._tick()

    img = canvas.grab().toImage()
    assert not img.isNull()
    assert img.width() == 720
    assert img.height() == 480
    canvas.close()


def test_precipitation_salts_interactive_actions_and_measurements():
    app()
    canvas = LabCanvas()
    experiment = experiment_by_id("precipitation-salts")
    assert experiment is not None
    canvas.set_experiment(experiment)

    m = canvas.measurements()
    assert "PRECIPITATE" in m
    assert "FILTRATE" in m
    assert "WASHES" in m
    assert "PURITY" in m
    assert "STATUS" in m

    # Mix reagents
    canvas.precipitation_salts_action("mix_reagents")
    assert canvas.precip_mixed is True

    # Pour into funnel starts running
    canvas.precipitation_salts_action("pour_funnel")
    assert canvas.precip_poured is True
    assert canvas.running is True

    # Wash increments wash count
    initial_washes = canvas.precip_wash_count
    canvas.precipitation_salts_action("wash")
    assert canvas.precip_wash_count == initial_washes + 1

    # Collect yield
    canvas.precipitation_salts_action("collect")
    assert canvas.precip_filtrate_ml > 0
    assert not canvas.running

    # Reset returns to defaults
    canvas.precipitation_salts_action("reset")
    assert canvas.precip_filtrate_ml == 0.0
    assert canvas.precip_drip_phase == 0.0
    assert canvas.precip_wash_count == 2
    assert not canvas.running

    canvas.close()


def test_precipitation_salts_paints_offscreen():
    app()
    canvas = LabCanvas()
    canvas.resize(720, 480)
    experiment = experiment_by_id("precipitation-salts")
    assert experiment is not None
    canvas.set_experiment(experiment)
    canvas.precipitation_salts_action("pour_funnel")
    canvas._tick()
    canvas._tick()

    img = canvas.grab().toImage()
    assert not img.isNull()
    assert img.width() == 720
    assert img.height() == 480
    canvas.close()