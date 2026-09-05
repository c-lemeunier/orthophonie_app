"""Point d'entrée de l'application Orthophonie."""
from __future__ import annotations

import sys
from pathlib import Path

# Permet `python app/main.py` comme `python main.py` (depuis app/) de trouver
# les packages internes (auth, db, services, ui) en import absolu.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from PySide6.QtWidgets import QApplication

from auth import auth_service
from auth.login import LoginDialog
from db import database, seed
from ui.theme import STYLESHEET


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("OrthophonieApp")
    app.setStyleSheet(STYLESHEET)

    login_dialog = LoginDialog()
    if login_dialog.exec() != LoginDialog.DialogCode.Accepted or login_dialog.dek is None:
        return 0

    key_hex = login_dialog.dek.hex()
    database.init_engine(auth_service.get_db_path(), key_hex)

    with database.session_scope() as session:
        seed.seed_default_data(session)

    from ui.main_windows import MainWindow

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
