import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from localchat.app import MainWindow


def test_markdown_and_latex_render_as_rich_text():
    QApplication.instance() or QApplication([])

    rendered = MainWindow._format_message_content(
        "**Working:** $v = \\frac{d}{t}$ and $$E = mc^2$$.\n\n"
        "- First step\n- Second step"
    )

    assert "font-weight:700" in rendered
    assert "⁄" in rendered
    assert "<sup>2</sup>" in rendered
    assert "<ul" in rendered and "First step" in rendered and "Second step" in rendered
    assert "\\frac" not in rendered
    assert "$$" not in rendered


def test_latex_supports_roots_greek_and_subscripts():
    QApplication.instance() or QApplication([])

    rendered = MainWindow._format_message_content(
        r"Solve $x_{1} = \sqrt{\alpha^2 + 4}$"
    )

    assert "√" in rendered
    assert "α" in rendered
    assert "<sub>1</sub>" in rendered
    assert "<sup>2</sup>" in rendered
    assert r"\sqrt" not in rendered


def test_markdown_keeps_code_blocks_and_escapes_html():
    QApplication.instance() or QApplication([])

    rendered = MainWindow._format_message_content(
        "Use `$x^2$` in the explanation, not a code block.\n\n"
        "```python\nprint('<script>')\n```"
    )

    assert "<pre" in rendered or "font-family:monospace" in rendered
    assert "&lt;script&gt;" in rendered
    assert "<script>" not in rendered
    assert "$x^2$" in rendered
