import pytest
from PySide6.QtCore import Qt, QPoint, QPointF, QEvent
from PySide6.QtGui import QImage, QPainter, QMouseEvent, QEnterEvent
from PySide6.QtWidgets import QApplication

from localchat.app import MainWindow
from localchat.os_explorer import ExplorerFolderCard, OSFolderExplorerView


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if not app:
        app = QApplication([])
    return app


def test_explorer_folder_card_interaction_and_rendering(qapp):
    card = ExplorerFolderCard(
        item_type="folder",
        title="Ordinary Level",
        subtitle="Form 3 - Form 5 GCE",
        accent_color="#57fabc",
        item_data={"target_segment": "Ordinary Level"},
    )
    card.resize(164, 180)

    # Test click signal
    clicked_data = []
    card.clicked.connect(lambda item_type, data: clicked_data.append((item_type, data)))

    card.mousePressEvent(
        QMouseEvent(QEvent.Type.MouseButtonPress, QPointF(10, 10), Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
    )
    assert len(clicked_data) == 1
    assert clicked_data[0][0] == "folder"
    assert clicked_data[0][1]["target_segment"] == "Ordinary Level"

    # Test enter / leave hover
    enter_ev = QEnterEvent(QPointF(10, 10), QPointF(10, 10), QPointF(10, 10))
    card.enterEvent(enter_ev)
    assert card.hovered is True
    assert card.elevation_offset == -6

    leave_ev = QEvent(QEvent.Type.Leave)
    card.leaveEvent(leave_ev)
    assert card.hovered is False
    assert card.elevation_offset == 0

    # Test offscreen render
    image = QImage(164, 180, QImage.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    card.paintEvent(None)
    painter.end()


def test_os_folder_explorer_hierarchy_navigation(qapp):
    explorer = OSFolderExplorerView()
    explorer.resize(1200, 800)

    # 1. Initial subject set to Physics
    explorer.set_subject("Physics")
    assert explorer.current_subject == "Physics"
    assert explorer.path_segments == ["Desktop", "Physics"]
    assert explorer.breadcrumbs_layout.count() == 3  # Desktop, separator, Physics

    # Verify root cards (Ordinary Level, Advanced Level, Virtual Practicals, AI Tutor)
    assert explorer.cards_grid.count() >= 4

    # 2. Drill into Ordinary Level
    ord_card = None
    for i in range(explorer.cards_grid.count()):
        w = explorer.cards_grid.itemAt(i).widget()
        if isinstance(w, ExplorerFolderCard) and w.title == "Ordinary Level":
            ord_card = w
            break
    assert ord_card is not None
    ord_card.mousePressEvent(
        QMouseEvent(QEvent.Type.MouseButtonPress, QPointF(10, 10), Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
    )

    # Now inside Desktop > Physics > Ordinary Level
    assert explorer.path_segments == ["Desktop", "Physics", "Ordinary Level"]
    assert explorer.cards_grid.count() >= 4

    # 3. Drill into Virtual Practicals
    prac_card = None
    for i in range(explorer.cards_grid.count()):
        w = explorer.cards_grid.itemAt(i).widget()
        if isinstance(w, ExplorerFolderCard) and w.title == "Virtual Practicals":
            prac_card = w
            break
    assert prac_card is not None
    prac_card.mousePressEvent(
        QMouseEvent(QEvent.Type.MouseButtonPress, QPointF(10, 10), Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
    )

    # Now inside Desktop > Physics > Ordinary Level > Virtual Practicals
    assert explorer.path_segments == ["Desktop", "Physics", "Ordinary Level", "Virtual Practicals"]

    # Click a practical experiment card and verify launch_experiment signal
    launched_exps = []
    explorer.launch_experiment.connect(lambda exp_id: launched_exps.append(exp_id))

    first_exp_card = explorer.cards_grid.itemAt(0).widget()
    assert isinstance(first_exp_card, ExplorerFolderCard)
    first_exp_card.mousePressEvent(
        QMouseEvent(QEvent.Type.MouseButtonPress, QPointF(10, 10), Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
    )
    assert len(launched_exps) == 1
    assert launched_exps[0] != ""

    # 4. Test Up Navigation
    explorer._navigate_up()
    assert explorer.path_segments == ["Desktop", "Physics", "Ordinary Level"]

    explorer._navigate_up()
    assert explorer.path_segments == ["Desktop", "Physics"]

    desktop_emitted = []
    explorer.navigate_to_desktop.connect(lambda: desktop_emitted.append(True))
    explorer._navigate_up()
    assert len(desktop_emitted) == 1


def test_os_folder_explorer_search_filter(qapp):
    explorer = OSFolderExplorerView()
    explorer.resize(1200, 800)
    explorer.set_subject("Chemistry")

    # Drill into Virtual Practicals
    explorer.path_segments.append("Virtual Practicals")
    explorer._refresh_view()

    initial_count = explorer.cards_grid.count()
    assert initial_count > 0

    # Filter for titration
    explorer.search_filter.setText("titration")
    filtered_count = explorer.cards_grid.count()
    assert 0 < filtered_count <= initial_count

    # Clear filter
    explorer.search_filter.clear()
    assert explorer.cards_grid.count() == initial_count


def test_main_window_explorer_integration(qapp):
    window = MainWindow()
    window.resize(1440, 900)

    # Selecting subject opens explorer
    window.open_subject_explorer("Biology")
    assert window.active_workspace == "explorer"
    assert window.content_stack.currentWidget() is window.explorer_page
    assert "Biology" in window.os_header.breadcrumb_label.text()
    assert window.sidebar.isHidden()

    # Explorer navigate to desktop
    window.explorer_page.navigate_to_desktop.emit()
    assert window.active_workspace == "desktop"
    assert window.content_stack.currentWidget() is window.desktop_page

    # Launching experiment from explorer
    window.open_subject_explorer("Physics")
    window.explorer_page.launch_experiment.emit("pendulum-lab")
    assert window.active_workspace == "experiments"
    assert window.content_stack.currentWidget() is window.lab_detail_page
    assert window.active_experiment.identifier == "pendulum-lab"

    window.close()


def test_offline_tutor_streaming_and_stop(qapp):
    import time
    window = MainWindow()
    window.resize(1200, 800)
    window.open_ai_workspace()

    assert window.sidebar.isHidden()
    assert window.send_button.isEnabled()

    window.input.setPlainText("Explain Newton's second law")
    window.send_message()

    assert len(window.messages) == 2
    assert window.messages[1]["role"] == "assistant"
    assert window.messages[1]["streaming"] is True

    # Advance stream by processing events
    for _ in range(10):
        qapp.processEvents()
        time.sleep(0.01)

    assert window.messages[1]["stream_chunks"] > 0
    assert len(window.messages[1]["content"]) > 0

    # Test stop streaming
    window.stop_streaming()
    assert window.messages[1]["streaming"] is False
    assert window.send_button.text() == "Send"

    window.close()
