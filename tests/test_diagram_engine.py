"""Unit and integration tests for the Python Graphviz real-time diagram engine."""

import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import base64
import pytest
from PySide6.QtWidgets import QApplication

from localchat.diagram_engine import (
    render_dot_to_base64_png,
    get_topic_diagram,
    render_diagram_card,
    render_markdown_diagrams,
    PRESET_DIAGRAMS,
    HAS_GRAPHVIZ,
)
from localchat.offline_tutor import generate_offline_gce_response


def get_app():
    return QApplication.instance() or QApplication([])


def test_graphviz_availability():
    """Verifies that the graphviz python package is installed and operational."""
    assert HAS_GRAPHVIZ is True


def test_render_dot_to_base64_png_success():
    """Verifies rendering a simple valid DOT string to a base64 PNG."""
    dot = """
    digraph G {
        A -> B;
    }
    """
    b64 = render_dot_to_base64_png(dot)
    assert b64 is not None
    assert len(b64) > 50
    # Decode and check PNG magic bytes (\x89PNG\r\n\x1a\n)
    raw = base64.b64decode(b64)
    assert raw.startswith(b"\x89PNG\r\n\x1a\n")


def test_render_dot_to_base64_png_invalid():
    """Verifies that invalid DOT syntax fails gracefully returning None."""
    invalid_dot = "this is not valid dot syntax at all {[[("
    result = render_dot_to_base64_png(invalid_dot)
    assert result is None


def test_get_topic_diagram_matching():
    """Verifies topic matching for key Cameroon GCE subjects."""
    assert get_topic_diagram("acid base titration experiment") == PRESET_DIAGRAMS["titration"]
    assert get_topic_diagram("factors affecting reaction rate") == PRESET_DIAGRAMS["reaction_rate"]
    assert get_topic_diagram("simple pendulum shm") == PRESET_DIAGRAMS["pendulum"]
    assert get_topic_diagram("snell's law refraction of light") == PRESET_DIAGRAMS["refraction"]
    assert get_topic_diagram("series and parallel circuits") == PRESET_DIAGRAMS["circuits"]
    assert get_topic_diagram("calvin cycle and photosynthesis") == PRESET_DIAGRAMS["photosynthesis"]
    assert get_topic_diagram("mitochondria cellular respiration") == PRESET_DIAGRAMS["respiration"]
    assert get_topic_diagram("quadratic equation roots") == PRESET_DIAGRAMS["quadratic"]
    assert get_topic_diagram("explain trigonometry") == PRESET_DIAGRAMS["trigonometry"]
    assert get_topic_diagram("figure: explain trigonometry") == PRESET_DIAGRAMS["trigonometry"]
    assert get_topic_diagram("draw figure of differentiation and calculus") == PRESET_DIAGRAMS["calculus"]
    assert get_topic_diagram("something completely unrelated like xyz123") is None


def test_render_diagram_card():
    """Verifies standalone diagram card HTML rendering."""
    card = render_diagram_card(PRESET_DIAGRAMS["titration"], "ACID-BASE TITRATION")
    assert card != ""
    assert "data:image/png;base64," in card
    assert "ACID-BASE TITRATION" in card


def test_render_markdown_diagrams():
    """Verifies markdown transformation replacing ```dot with embedded image."""
    markdown = (
        "Here is the mechanism:\n\n"
        "```dot\n"
        "digraph Simple {\n"
        "    Node1 -> Node2;\n"
        "}\n"
        "```\n\n"
        "End of explanation."
    )
    result = render_markdown_diagrams(markdown)
    assert "data:image/png;base64," in result
    assert "REAL-TIME GRAPHVIZ DIAGRAM" in result
    assert "```dot" not in result
    assert "Here is the mechanism:" in result
    assert "End of explanation." in result


def test_offline_tutor_generates_diagrams():
    """Verifies that offline GCE tutor embeds dot blocks in scientific explanations."""
    _, titr_content = generate_offline_gce_response("explain titration")
    assert "```dot" in titr_content
    assert "TitrationWorkflow" in titr_content

    _, pend_content = generate_offline_gce_response("simple pendulum period")
    assert "```dot" in pend_content
    assert "SimplePendulum" in pend_content

    _, photo_content = generate_offline_gce_response("photosynthesis process")
    assert "```dot" in photo_content
    assert "PhotosynthesisCycle" in photo_content


def test_main_window_format_message_content_renders_diagram():
    """Verifies that MainWindow._format_message_content converts ```dot to an inline PNG."""
    get_app()
    from localchat.app import MainWindow

    markdown = "Explaining reaction:\n```dot\ndigraph R { A -> B; }\n```"
    html = MainWindow._format_message_content(markdown)
    assert "data:image/png;base64," in html
    assert "GRAPHVIZ DIAGRAM" in html


def test_main_window_diagram_command_execution():
    """Verifies that typing 'diagram titration' in terminal directly creates a diagram."""
    app = get_app()
    from localchat.app import MainWindow

    window = MainWindow()
    try:
        window.input.setPlainText("diagram titration")
        window.send_message()

        # The chat should now contain the rendered diagram
        chat_html = window.chat_view.toHtml()
        assert "data:image/png;base64," in chat_html
        assert "Titration" in chat_html
    finally:
        window.close()
        window.deleteLater()
        app.sendPostedEvents()
        app.processEvents()


def test_main_window_draw_figure_trigonometry_command():
    """Verifies that 'draw figure: explain trigonometry' renders a diagram and never raw escaped HTML."""
    app = get_app()
    from localchat.app import MainWindow

    window = MainWindow()
    try:
        window.input.setPlainText("draw figure: explain trigonometry")
        window.send_message()

        chat_html = window.chat_view.toHtml()
        assert "data:image/png;base64," in chat_html
        # Must not contain escaped raw HTML tags like &lt;div or <div
        assert "&lt;div" not in chat_html
        assert "&lt;img" not in chat_html
    finally:
        window.close()
        window.deleteLater()
        app.sendPostedEvents()
        app.processEvents()


def test_format_message_content_preserves_pre_rendered_html():
    """Verifies that pre-existing HTML diagram cards are preserved without escaping."""
    get_app()
    from localchat.app import MainWindow

    raw_html_card = '<div style="margin:10px;"><img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUg==" /></div>'
    markdown = f"Here is the card:\n\n{raw_html_card}\n\nDone."
    output = MainWindow._format_message_content(markdown)

    assert "&lt;div" not in output
    assert "&lt;img" not in output
    assert '<img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUg=="' in output

