import pytest
from PySide6.QtCore import Qt, QPointF, QEvent
from PySide6.QtGui import QMouseEvent, QKeyEvent
from PySide6.QtWidgets import QApplication

from localchat.os_shutdown import OSShutdownOverlay


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if not app:
        app = QApplication([])
    return app


def test_shutdown_overlay_shutdown_mode(qapp):
    overlay = OSShutdownOverlay(mode="shutdown")
    overlay.resize(1024, 768)

    assert overlay.mode == "shutdown"
    assert "Shutting down" in overlay.status_title
    assert overlay.anim_timer.isActive()

    shutdown_emitted = []
    overlay.shutdown_completed.connect(lambda: shutdown_emitted.append(True))

    # Trigger fade
    overlay._start_fade_out()
    assert overlay.is_fading is True

    # Advance ticks until fade completes
    for _ in range(30):
        overlay._on_tick()
        if overlay.is_finished:
            break

    assert overlay.is_finished is True
    assert len(shutdown_emitted) == 1
    overlay.deleteLater()


def test_shutdown_overlay_restart_mode(qapp):
    overlay = OSShutdownOverlay(mode="restart")
    overlay.resize(1024, 768)

    assert overlay.mode == "restart"
    assert "Restarting" in overlay.status_title

    restart_emitted = []
    overlay.restart_completed.connect(lambda: restart_emitted.append(True))

    overlay._start_fade_out()
    for _ in range(30):
        overlay._on_tick()
        if overlay.is_finished:
            break

    assert overlay.is_finished is True
    assert len(restart_emitted) == 1


def test_shutdown_overlay_lock_mode_unlock_via_mouse(qapp):
    overlay = OSShutdownOverlay(mode="lock")
    overlay.resize(1024, 768)

    assert overlay.mode == "lock"
    assert "unlock" in overlay.status_subtitle

    unlocked_emitted = []
    overlay.unlocked.connect(lambda: unlocked_emitted.append(True))

    mouse_ev = QMouseEvent(
        QEvent.Type.MouseButtonPress,
        QPointF(100, 100),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    overlay.mousePressEvent(mouse_ev)
    assert len(unlocked_emitted) == 1


def test_shutdown_overlay_lock_mode_unlock_via_key(qapp):
    overlay = OSShutdownOverlay(mode="lock")
    overlay.resize(1024, 768)

    unlocked_emitted = []
    overlay.unlocked.connect(lambda: unlocked_emitted.append(True))

    key_ev = QKeyEvent(
        QEvent.Type.KeyPress,
        Qt.Key.Key_Return,
        Qt.KeyboardModifier.NoModifier,
    )
    overlay.keyPressEvent(key_ev)
    assert len(unlocked_emitted) == 1
