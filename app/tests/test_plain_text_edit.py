"""Le collage dans PlainTextEdit ne doit jamais importer la police du
document source (bug : la police d'un copier/coller externe n'était pas
neutralisée à partir de la 2e ligne)."""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

PySide6 = pytest.importorskip("PySide6")

from PySide6.QtCore import QMimeData
from PySide6.QtWidgets import QApplication

from ui.widgets.plain_text_edit import PlainTextEdit

_FOREIGN_HTML = (
    "<html><body>"
    "<p style=\"font-family:'Courier New'; font-size:20pt;\">Ligne 1</p>"
    "<p style=\"font-family:'Courier New'; font-size:20pt;\">Ligne 2</p>"
    "<p style=\"font-family:'Courier New'; font-size:20pt;\">Ligne 3</p>"
    "</body></html>"
)


@pytest.fixture(scope="module", autouse=True)
def qapp():
    return QApplication.instance() or QApplication([])


def _mime_with_foreign_font() -> QMimeData:
    mime = QMimeData()
    mime.setText("Ligne 1\nLigne 2\nLigne 3")
    mime.setHtml(_FOREIGN_HTML)
    return mime


def test_paste_keeps_widget_font_on_every_line():
    editor = PlainTextEdit()
    editor.setPlainText("")

    editor.insertFromMimeData(_mime_with_foreign_font())

    assert editor.toPlainText() == "Ligne 1\nLigne 2\nLigne 3"

    default_family = editor.font().family()
    block = editor.document().begin()
    while block.isValid():
        it = block.begin()
        while not it.atEnd():
            fragment = it.fragment()
            if fragment.isValid() and fragment.text().strip():
                assert fragment.charFormat().font().family() == default_family
            it += 1
        block = block.next()


def test_paste_without_html_falls_back_to_plain_text():
    editor = PlainTextEdit()
    mime = QMimeData()
    mime.setText("juste du texte")

    editor.insertFromMimeData(mime)

    assert editor.toPlainText() == "juste du texte"
