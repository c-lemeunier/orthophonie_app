"""Écran de verrouillage : création du mot de passe au premier lancement,
saisie ensuite, et récupération via code si le mot de passe est oublié."""
from __future__ import annotations

import time

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from auth import auth_service
from ui import theme

_LOCKOUT_BASE_SECONDS = 2


class LoginDialog(QDialog):
    """À l'issue de `exec()`, si `self.dek` est non None, l'authentification a
    réussi et `self.dek` contient la clé de déchiffrement de la base."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName(theme.LOGIN_DIALOG_OBJECT_NAME)
        self.setWindowTitle("Orthophonie — Connexion")
        self.setModal(True)
        self.setMinimumWidth(420)

        self.dek: bytes | None = None
        self._failed_attempts = 0

        self._stack = QStackedWidget(self)
        layout = QVBoxLayout(self)
        layout.addWidget(self._stack)

        self._setup_page = self._build_setup_page()
        self._login_page = self._build_login_page()
        self._recovery_page = self._build_recovery_page()
        self._recovery_display_page = self._build_recovery_display_page()

        self._stack.addWidget(self._setup_page)
        self._stack.addWidget(self._login_page)
        self._stack.addWidget(self._recovery_page)
        self._stack.addWidget(self._recovery_display_page)

        if auth_service.is_first_launch():
            self._stack.setCurrentWidget(self._setup_page)
        else:
            self._stack.setCurrentWidget(self._login_page)

    # ---- Page : création du mot de passe (premier lancement) ----
    def _build_setup_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(QLabel(
            "Premier lancement : choisissez un mot de passe pour protéger\n"
            "les données patients stockées sur cet ordinateur."
        ))

        form = QFormLayout()
        self._setup_pw1 = QLineEdit()
        self._setup_pw1.setEchoMode(QLineEdit.EchoMode.Password)
        self._setup_pw2 = QLineEdit()
        self._setup_pw2.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("Mot de passe :", self._setup_pw1)
        form.addRow("Confirmation :", self._setup_pw2)
        layout.addLayout(form)

        self._setup_error = QLabel()
        self._setup_error.setStyleSheet("color: #c0392b;")
        layout.addWidget(self._setup_error)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self._on_setup_submit)
        layout.addWidget(buttons)
        return page

    def _on_setup_submit(self) -> None:
        pw1 = self._setup_pw1.text()
        pw2 = self._setup_pw2.text()
        if len(pw1) < 8:
            self._setup_error.setText("Le mot de passe doit contenir au moins 8 caractères.")
            return
        if pw1 != pw2:
            self._setup_error.setText("Les deux mots de passe ne correspondent pas.")
            return

        dek, recovery_code = auth_service.create_password(pw1)
        self.dek = dek
        self._show_recovery_code(recovery_code)

    # ---- Page : affichage unique du code de récupération ----
    def _build_recovery_display_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(QLabel(
            "Notez ce code de récupération dans un endroit sûr (hors de cet\n"
            "ordinateur). Il est indispensable pour accéder aux données si le\n"
            "mot de passe est oublié. Il ne sera plus jamais affiché."
        ))
        self._recovery_code_display = QTextEdit()
        self._recovery_code_display.setReadOnly(True)
        self._recovery_code_display.setStyleSheet("font-family: monospace; font-size: 14pt;")
        self._recovery_code_display.setFixedHeight(50)
        layout.addWidget(self._recovery_code_display)

        self._recovery_ack = QCheckBox("J'ai noté ce code en lieu sûr.")
        layout.addWidget(self._recovery_ack)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        ok_button = buttons.button(QDialogButtonBox.StandardButton.Ok)
        ok_button.setEnabled(False)
        self._recovery_ack.toggled.connect(ok_button.setEnabled)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)
        return page

    def _show_recovery_code(self, recovery_code: str) -> None:
        self._recovery_code_display.setPlainText(recovery_code)
        self._stack.setCurrentWidget(self._recovery_display_page)

    # ---- Page : saisie du mot de passe ----
    def _build_login_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(QLabel("Mot de passe :"))
        self._login_pw = QLineEdit()
        self._login_pw.setEchoMode(QLineEdit.EchoMode.Password)
        self._login_pw.returnPressed.connect(self._on_login_submit)
        layout.addWidget(self._login_pw)

        self._login_error = QLabel()
        self._login_error.setStyleSheet("color: #c0392b;")
        layout.addWidget(self._login_error)

        forgot = QPushButton("Mot de passe oublié ?")
        forgot.setFlat(True)
        forgot.clicked.connect(lambda: self._stack.setCurrentWidget(self._recovery_page))
        layout.addWidget(forgot)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self._on_login_submit)
        layout.addWidget(buttons)
        return page

    def _on_login_submit(self) -> None:
        if self._failed_attempts:
            time.sleep(_LOCKOUT_BASE_SECONDS * self._failed_attempts)

        dek = auth_service.unlock_with_password(self._login_pw.text())
        if dek is None:
            self._failed_attempts += 1
            if self._failed_attempts >= auth_service.MAX_LOGIN_ATTEMPTS:
                QMessageBox.critical(
                    self, "Trop de tentatives",
                    "Trop de tentatives incorrectes. L'application va se fermer."
                )
                self.reject()
                return
            self._login_error.setText("Mot de passe incorrect.")
            self._login_pw.clear()
            return

        self.dek = dek
        self.accept()

    # ---- Page : récupération par code ----
    def _build_recovery_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(QLabel(
            "Saisissez votre code de récupération pour redéfinir un mot de\n"
            "passe. Sans ce code, les données ne peuvent pas être récupérées."
        ))
        self._recovery_code_input = QLineEdit()
        self._recovery_code_input.setPlaceholderText("XXXX-XXXX-XXXX-XXXX-XXXX-XXXX")
        layout.addWidget(self._recovery_code_input)

        self._recovery_error = QLabel()
        self._recovery_error.setStyleSheet("color: #c0392b;")
        layout.addWidget(self._recovery_error)

        row = QHBoxLayout()
        back = QPushButton("Retour")
        back.clicked.connect(lambda: self._stack.setCurrentWidget(self._login_page))
        row.addWidget(back)
        submit = QPushButton("Valider le code")
        submit.clicked.connect(self._on_recovery_submit)
        row.addWidget(submit)
        layout.addLayout(row)
        return page

    def _on_recovery_submit(self) -> None:
        dek = auth_service.unlock_with_recovery_code(self._recovery_code_input.text())
        if dek is None:
            self._recovery_error.setText("Code de récupération invalide.")
            return

        new_password, ok = self._ask_new_password()
        if not ok:
            return
        auth_service.change_password(dek, new_password)
        self.dek = dek
        self.accept()

    def _ask_new_password(self) -> tuple[str, bool]:
        dialog = QDialog(self)
        dialog.setWindowTitle("Nouveau mot de passe")
        layout = QVBoxLayout(dialog)
        form = QFormLayout()
        pw1 = QLineEdit()
        pw1.setEchoMode(QLineEdit.EchoMode.Password)
        pw2 = QLineEdit()
        pw2.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("Nouveau mot de passe :", pw1)
        form.addRow("Confirmation :", pw2)
        layout.addLayout(form)
        error = QLabel()
        error.setStyleSheet("color: #c0392b;")
        layout.addWidget(error)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        layout.addWidget(buttons)

        result = {"password": "", "ok": False}

        def on_accept() -> None:
            if len(pw1.text()) < 8:
                error.setText("Le mot de passe doit contenir au moins 8 caractères.")
                return
            if pw1.text() != pw2.text():
                error.setText("Les deux mots de passe ne correspondent pas.")
                return
            result["password"] = pw1.text()
            result["ok"] = True
            dialog.accept()

        buttons.accepted.connect(on_accept)
        buttons.rejected.connect(dialog.reject)
        dialog.exec()
        return result["password"], result["ok"]
