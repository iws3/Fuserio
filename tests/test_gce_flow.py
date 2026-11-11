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
