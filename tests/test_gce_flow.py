import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication

import localchat.app as app_module


class FakeSignal:
    def connect(self, callback):
        self.callback = callback


class FakeServerProbe:
    instances = []

    def __init__(self, _url):
        self.found = FakeSignal()
        self.failed = FakeSignal()
        self.started = False
        self.instances.append(self)

    def start(self):
        self.started = True

    def isRunning(self):
        return False

    def cancel(self):
        pass


class FakeChatWorker:
    instances = []

    def __init__(self, base_url, api_key, messages, parameters=None):
        self.base_url = base_url
        self.api_key = api_key
        self.messages = messages
        self.parameters = parameters or {}
        self.chunk = FakeSignal()
        self.error = FakeSignal()
        self.finished = FakeSignal()
        self.instances.append(self)

    def start(self):
        pass

    def isRunning(self):
        return False


@pytest.fixture(scope="session")
def qapp():
    return QApplication.instance() or QApplication([])


@pytest.fixture

def window(qapp, monkeypatch):
    FakeChatWorker.instances.clear()
    monkeypatch.setattr(app_module, "ExistingServerProbe", FakeServerProbe)
    monkeypatch.setattr(app_module, "ChatWorker", FakeChatWorker)
    monkeypatch.setattr(app_module, "save_progress", lambda _progress: None)
    monkeypatch.setattr(app_module, "load_progress", lambda: {"selection": {}, "sessions": {}})
    test_window = app_module.MainWindow()
    test_window.base_url = "http://127.0.0.1:8081"
    yield test_window
    test_window.close()


def test_level_stream_subject_navigation_and_back(window):
    window.gce_study_button.click()
    assert window.content_stack.currentWidget() is window.level_page

    window.select_gce_level("Ordinary Level")
    assert window.content_stack.currentWidget() is window.stream_page

    window.select_gce_stream("Sciences")
    assert window.content_stack.currentWidget() is window.subject_page
    assert window.subject_grid.count() == 11

    window.open_gce_subject("Physics")
    assert window.content_stack.currentWidget() is window.chat_page

    window.gce_back()
    assert window.content_stack.currentWidget() is window.subject_page
    window.gce_back()
    assert window.content_stack.currentWidget() is window.stream_page
    window.gce_back()
    assert window.content_stack.currentWidget() is window.level_page


def test_startup_offers_levels_and_sidebar_links_switch_workspaces(window):
    from PySide6.QtWidgets import QLabel

    assert window.content_stack.currentWidget() is window.level_page
    assert window.gce_study_button.text() == "GCE Learning"
    assert window.ai_workspace_button.text() == "AI Workspace"
    assert not window.findChild(QLabel, "startLogo").pixmap().isNull()

    window.ai_workspace_button.click()
    assert window.content_stack.currentWidget() is window.chat_page
    window.gce_study_button.click()
    assert window.content_stack.currentWidget() is window.level_page


def test_model_retry_reuses_compatible_server(window):
    window.model_reconnect_button.setEnabled(True)
    window.model_reconnect_button.click()

    probe = FakeServerProbe.instances[-1]
    assert probe.started
    assert window.model_reconnect_button.text() == "Checking…"
    probe.found.callback(
        "http://127.0.0.1:8081",
        window.model_selector.currentData(),
    )

    assert window.base_url == "http://127.0.0.1:8081"
    assert window.connection_status.text() == "READY"
    assert window.model_reconnect_button.text() == "Connected"


def test_experiment_sidebar_opens_subject_gallery_and_live_simulation(window):
    from PySide6.QtWidgets import QPushButton, QSlider

    window.lab_subject_buttons["Physics"].click()

    assert window.active_workspace == "experiments"
    assert window.lab_subject == "Physics"
    assert window.content_stack.currentWidget() is window.lab_gallery_page
    assert window.lab_gallery_grid.count() == 3

    first_experiment = window.lab_gallery_grid.itemAt(0).widget()
    assert isinstance(first_experiment, QPushButton)
    first_experiment.click()
    assert window.content_stack.currentWidget() is window.lab_detail_page
    assert window.lab_canvas.experiment.identifier == "projectile-motion"
    assert window.lab_metric_labels
    assert "u" in window.lab_equation.toPlainText()
    assert "air resistance" in window.lab_model_note.text().lower()

    initial_range = window.lab_canvas.measurements()["RANGE"]
    speed_slider = next(
        slider for slider in window.lab_controls_widget.findChildren(QSlider)
        if slider.accessibleName() == "Launch speed"
    )
    speed_slider.setValue(35)
    assert window.lab_canvas.measurements()["RANGE"] != initial_range

    initial_time = window.lab_canvas.elapsed
    window.lab_step_button.click()
    assert window.lab_canvas.elapsed > initial_time
    window.lab_speed_slider.setValue(150)
    assert window.lab_canvas.playback_rate == 1.5
    assert window.lab_speed_value.text() == "1.50×"

    window.navigate_back()
    assert window.content_stack.currentWidget() is window.lab_gallery_page
    window.navigate_back()
    assert window.content_stack.currentWidget() is window.lab_home_page


def test_biology_and_chemistry_sidebar_subjects_open_their_own_catalogs(window):
    window.lab_subject_buttons["Biology"].click()
    biology_titles = {
        window.lab_gallery_grid.itemAt(index).widget().text().split("\n", 1)[0]
        for index in range(window.lab_gallery_grid.count())
    }
    assert biology_titles == {"Membrane diffusion", "Enzyme activity", "Natural selection"}

    window.lab_subject_buttons["Chemistry"].click()
    chemistry_titles = {
        window.lab_gallery_grid.itemAt(index).widget().text().split("\n", 1)[0]
        for index in range(window.lab_gallery_grid.count())
    }
    assert chemistry_titles == {"Reaction rate", "Acid-base titration", "States of matter"}


def test_experiment_tutor_receives_subject_readings_and_safety_context(window):
    window.open_experiments_subject("Physics")
    experiment_button = window.lab_gallery_grid.itemAt(0).widget()
    experiment_button.click()
    readings = window.lab_canvas.measurements()

    window.ask_lab_tutor()

    tutor_request = FakeChatWorker.instances[-1].messages
    system_prompt = tutor_request[0]["content"]
    assert tutor_request[0]["role"] == "system"
    assert "Physics" in system_prompt
    assert "Projectile motion" in system_prompt
    assert "Safety boundary" in system_prompt
    assert readings["RANGE"] in tutor_request[-1]["content"]
    assert window.active_workspace == "experiments"
    assert window.lab_screen == "tutor"
    window.navigate_back()
    assert window.content_stack.currentWidget() is window.lab_detail_page


def test_experiment_predictions_and_observations_restore_per_experiment(window):
    window.open_experiments_subject("Physics")
    window.lab_gallery_grid.itemAt(0).widget().click()
    window.lab_prediction_edit.setPlainText("A larger launch angle should increase the apex.")
    window.lab_observation_edit.setPlainText("At 60 degrees the height increased, but range changed too.")
    window._save_lab_notes()

    saved = window.progress["experiments"]["projectile-motion"]
    assert saved["prediction"].startswith("A larger launch angle")
    assert saved["observation"].startswith("At 60 degrees")

    window.navigate_back()
    window.open_experiment("projectile-motion")
    assert window.lab_prediction_edit.toPlainText() == saved["prediction"]
    assert window.lab_observation_edit.toPlainText() == saved["observation"]


def test_model_selector_updates_description_and_load_state(window, monkeypatch):
    requested = []
    monkeypatch.setattr(
        window,
        "_prepare_model",
        lambda model_id, generation: requested.append((model_id, generation)),
    )

    window.model_selector.setCurrentIndex(1)

    assert requested[-1][0] == window.model_selector.currentData()
    assert "general assistant" in window.model_detail.text()
    assert "3B" in window.model_detail.text()
    assert window.model_reconnect_button.text() == "Loading…"
    assert not window.model_reconnect_button.isEnabled()

    window._connect_model(
        "http://127.0.0.1:8081",
        "",
        window.model_selector.currentData(),
        window.generation,
    )
    assert window.connection_status.text() == "READY"
    assert window.model_reconnect_button.text() == "Connected"


def test_selected_model_is_saved(window):
    window.model_selector.setCurrentIndex(1)
    assert window.progress["model_id"] == window.model_selector.currentData()

    window._save_progress()
    assert window.progress["model_id"] == window.model_selector.currentData()


def test_saved_model_is_restored_on_startup(qapp, monkeypatch):
    monkeypatch.setattr(app_module, "ExistingServerProbe", FakeServerProbe)
    monkeypatch.setattr(app_module, "load_progress", lambda: {"selection": {}, "sessions": {}, "model_id": app_module.MODEL_OPTIONS[1].model_id})
    monkeypatch.setattr(app_module, "save_progress", lambda _progress: None)

    test_window = app_module.MainWindow()

    assert test_window.model_selector.currentData() == app_module.MODEL_OPTIONS[1].model_id
    test_window.close()


def test_stream_chunks_accumulate_before_rich_text_repaint(window, monkeypatch):
    window.messages = [{"role": "assistant", "content": "", "reasoning": "", "streaming": True}]
    renders = []
    monkeypatch.setattr(window, "_render_messages", lambda: renders.append(True))

    window._append_stream_chunk("Checking ", "Answer ")
    window._append_stream_chunk("the steps.", "is 42.")

    assert window.messages[0]["reasoning"] == "Checking the steps."
    assert window.messages[0]["content"] == "Answer is 42."
    assert window.messages[0]["stream_chunks"] == 2
    assert window.chat_render_timer.isActive()
    assert renders == []

    window._flush_chat_render()
    assert renders == [True]


def test_live_generation_badge_includes_answer_chunk_count(window):
    window.messages = [{
        "role": "assistant",
        "content": "Speed is 60 km/h.",
        "reasoning": "",
        "streaming": True,
        "stream_chunks": 7,
    }]

    window._render_messages()

    assert "GENERATING · 7 TOKENS" in window.chat_view.toHtml()


def test_assistant_shows_generating_indicator_until_worker_finishes(window):
    window.messages = [{"role": "assistant", "content": "", "reasoning": ""}]

    window._start_chat_request([{"role": "user", "content": "hello"}])

    assert window.messages[-1]["streaming"] is True
    assert "GENERATING" in window.chat_view.toHtml()
    window._chat_finished()
    assert window.messages[-1]["streaming"] is False
    assert "GENERATING" not in window.chat_view.toHtml()


def test_greeting_modes_and_typed_questions_use_subject_prompt(window):
    window.select_gce_level("Ordinary Level")
    window.select_gce_stream("Sciences")
    window.open_gce_subject("Physics")

    greeting = FakeChatWorker.instances[-1].messages
    system_prompt = greeting[0]["content"]
    assert greeting[0]["role"] == "system"
    assert "Ordinary Level" in system_prompt
    assert "Physics" in system_prompt
    assert "Cameroon GCE Board" in system_prompt
    assert "Suggested study areas, not a verified or exhaustive official syllabus" in system_prompt
    assert "not a verified or exhaustive official syllabus" in window.study_context_label.text()
    assert FakeChatWorker.instances[-1].parameters["max_tokens"] == 640

    window.start_learning_mode("Practice")
    practice = FakeChatWorker.instances[-1].messages
    assert practice[0]["role"] == "system"
    assert "Physics" in practice[0]["content"]
    assert "practice question" in practice[-1]["content"].lower()

    window.input.setPlainText("Explain refraction")
    window.send_message()
    follow_up = FakeChatWorker.instances[-1].messages
    assert follow_up[0]["role"] == "system"
    assert "Physics" in follow_up[0]["content"]
    assert follow_up[-1]["content"] == "Explain refraction"


def test_gce_button_restores_last_saved_subject_and_conversation(qapp, monkeypatch):
    saved_progress = {
        "selection": {
            "level": "Advanced Level",
            "stream": "Commercial",
            "subject": "Accounting",
        },
        "sessions": {
            "Advanced Level|Commercial|Accounting": {
                "messages": [
                    {"role": "user", "content": "Balance sheet practice"},
                    {"role": "assistant", "content": "Saved tutor feedback", "reasoning": "Checked entries."},
                ],
                "modes": [{"mode": "Practice", "time": 123}],
            }
        },
    }
    monkeypatch.setattr(app_module, "ExistingServerProbe", FakeServerProbe)
    monkeypatch.setattr(app_module, "ChatWorker", FakeChatWorker)
    monkeypatch.setattr(app_module, "load_progress", lambda: saved_progress)
    monkeypatch.setattr(app_module, "save_progress", lambda _progress: None)

    test_window = app_module.MainWindow()
    test_window.gce_study_button.click()
    assert test_window.gce_subject == "Accounting"
    assert test_window.content_stack.currentWidget() is test_window.chat_page
    assert test_window.messages[1]["content"] == "Saved tutor feedback"
    assert test_window.gce_modes[0]["mode"] == "Practice"
    test_window.close()
