"""Painel de logs baseado em Qt Widgets."""

from PySide6.QtWidgets import QLabel, QPlainTextEdit, QVBoxLayout, QWidget


class LogsView(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        title = QLabel("Logs do sistema")
        title.setObjectName("pageTitle")
        self.log_box = QPlainTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setMaximumBlockCount(5000)
        layout.addWidget(title)
        layout.addWidget(self.log_box)
        self.add_log("RNPB iniciado.\n")

    def add_log(self, text: str) -> None:
        cursor = self.log_box.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertText(text)
        self.log_box.setTextCursor(cursor)
        self.log_box.ensureCursorVisible()
