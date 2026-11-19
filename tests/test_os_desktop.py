import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from localchat.app import MainWindow
from localchat.os_desktop import OSDesktopView, SubjectFolderCard, GCEMasteryWidget, FloatingDock, SystemTrayWidget
from localchat.os_header import OSHeader, SpotlightSearchBar
from localchat.os_sidebar import OSSidebar


def app():
    return QApplication.instance() or QApplication([])


def test_os_desktop_view_renders_offscreen():
    app()
    desktop = OSDesktopView()
    desktop.resize(1440, 900)

    # Verify 6 subject folder cards exist
    assert len(desktop.folder_cards) == 6
    subject_keys = [c.subject_key for c in desktop.folder_cards]
    assert "Chemistry" in subject_keys
    assert "Biology" in subject_keys
    assert "Physics" in subject_keys
    assert "Mathematics" in subject_keys
    assert "Computer Science" in subject_keys
    assert "ICT" in subject_keys

    # Verify GCE Mastery Widget
    assert desktop.mastery_widget.mastery_pct == 78
    desktop.mastery_widget.set_progress(85, topics=40, practicals=8)
    assert desktop.mastery_widget.mastery_pct == 85
    assert desktop.mastery_widget.topics_count == 40
    assert desktop.mastery_widget.practicals_count == 8

    # Verify Floating Dock & System Tray exist
    assert desktop.dock is not None
    assert desktop.tray is not None

    # Render offscreen image
    img = desktop.grab().toImage()
    assert not img.isNull()
    assert img.width() == 1440
    assert img.height() == 900

    desktop.close()


def test_subject_folder_cards_hover_and_click():
    app()
    desktop = OSDesktopView()
    received = []
    desktop.subject_selected.connect(lambda s: received.append(s))

    chem_card = desktop.folder_cards[0]
    assert chem_card.subject_key == "Chemistry"

    # Test click signal
    chem_card.clicked.emit("Chemistry")
    assert received == ["Chemistry"]

    # Test hover elevation
    chem_card.enterEvent(None)
    assert chem_card.hovered is True
    assert chem_card.elevation_offset == -8

    chem_card.leaveEvent(None)
    assert chem_card.hovered is False
    assert chem_card.elevation_offset == 0

    desktop.close()


def test_floating_dock_and_sidebar_signals():
    app()
    desktop = OSDesktopView()
    dock_signals = []
    desktop.launch_action.connect(lambda a: dock_signals.append(a))

    desktop.dock.btn_apps.click()
    assert dock_signals == ["gce"]

    desktop.dock.btn_ai.click()
    assert dock_signals == ["gce", "chat"]

    desktop.dock.btn_math.click()
    assert dock_signals == ["gce", "chat", "math"]

    sidebar = OSSidebar()
    sidebar_signals = []
    sidebar.navigate.connect(lambda a: sidebar_signals.append(a))

    sidebar.buttons["desktop"].click()
    assert sidebar_signals == ["desktop"]
    assert sidebar.current_screen == "desktop"

    sidebar.buttons["lab"].click()
    assert sidebar_signals == ["desktop", "lab"]
    assert sidebar.current_screen == "lab"

    desktop.close()
    sidebar.close()


def test_os_header_spotlight_search_and_breadcrumbs():
    app()
    header = OSHeader()
    header.resize(1000, 54)

    # Test search filter
    search_bar = header.search_bar
    search_bar.popup.filter_results("titration")
    assert search_bar.popup.list_widget.count() > 1

    # Test breadcrumb
    assert header.breadcrumb_label.isHidden()
    header.set_breadcrumb("Desktop › Chemistry Practicals")
    assert not header.breadcrumb_label.isHidden()
    assert header.breadcrumb_label.text() == "Desktop › Chemistry Practicals"
    assert not header.back_button.isHidden()

    header.set_breadcrumb("")
    assert header.breadcrumb_label.isHidden()
    assert header.back_button.isHidden()

    header.close()


def test_main_window_os_desktop_integration():
    app()
    window = MainWindow()
    window.resize(1440, 900)

    # Verify startup is on desktop_page
    assert window.content_stack.currentWidget() is window.desktop_page
    assert window.os_header.breadcrumb_label.isHidden()
    assert window.os_sidebar.current_screen == "desktop"

    # Click Chemistry folder on desktop -> opens OS Explorer View
    window._on_desktop_subject_selected("Chemistry")
    assert window.content_stack.currentWidget() is window.explorer_page
    assert "Chemistry" in window.os_header.breadcrumb_label.text()

    # Return to desktop
    window.open_desktop()
    assert window.content_stack.currentWidget() is window.desktop_page
    assert window.os_header.breadcrumb_label.isHidden()
    assert window.os_sidebar.current_screen == "desktop"

    # Spotlight search opens AI chat
    window._on_spotlight_search("Explain Boyle's law")
    assert window.content_stack.currentWidget() is window.chat_page

    # Return to desktop
    window.open_desktop()
    assert window.content_stack.currentWidget() is window.desktop_page

    window.close()
