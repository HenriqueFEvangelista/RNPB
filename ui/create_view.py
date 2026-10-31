"""Formulário Expo da primeira etapa da migração para PySide6."""

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class CreateView(QWidget):
    create_requested = Signal(str, str)
    cancel_requested = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        title = QLabel("Novo projeto")
        title.setObjectName("pageTitle")
        subtitle = QLabel("Criação React Native com Expo • primeira etapa da migração")
        subtitle.setObjectName("muted")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        form = QFormLayout()
        form.setSpacing(12)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("meu-projeto")
        self.name_input.setObjectName("projectName")
        form.addRow("Nome do projeto", self.name_input)

        platform = QComboBox()
        platform.addItem("React Native · Expo")
        platform.setEnabled(False)
        form.addRow("Plataforma", platform)

        language = QComboBox()
        language.addItem("JavaScript")
        language.setEnabled(False)
        form.addRow("Linguagem", language)

        template = QComboBox()
        template.addItem("Blank")
        template.setEnabled(False)
        form.addRow("Template", template)

        directory_row = QHBoxLayout()
        self.directory_input = QLineEdit()
        self.directory_input.setPlaceholderText("Selecione uma pasta para criar o projeto")
        self.directory_input.setObjectName("projectDirectory")
        self.browse_button = QPushButton("Procurar…")
        self.browse_button.clicked.connect(self.choose_directory)
        directory_row.addWidget(self.directory_input)
        directory_row.addWidget(self.browse_button)
        form.addRow("Destino", directory_row)
        layout.addLayout(form)

        hint = QLabel("React Web, TypeScript e bibliotecas chegarão nas próximas etapas.")
        hint.setObjectName("muted")
        layout.addWidget(hint)

        controls = QHBoxLayout()
        self.create_button = QPushButton("Criar projeto")
        self.create_button.setObjectName("primaryButton")
        self.cancel_button = QPushButton("Cancelar execução")
        self.cancel_button.setEnabled(False)
        self.create_button.clicked.connect(self._request_creation)
        self.cancel_button.clicked.connect(self.cancel_requested.emit)
        controls.addWidget(self.create_button)
        controls.addWidget(self.cancel_button)
        controls.addStretch()
        layout.addLayout(controls)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.status_label = QLabel("Aguardando configuração.")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.progress)
        layout.addWidget(self.status_label)
        layout.addStretch()

    def choose_directory(self) -> None:
        directory = QFileDialog.getExistingDirectory(
            self, "Selecione a pasta de destino", self.directory_input.text() or str(Path.home())
        )
        if directory:
            self.directory_input.setText(directory)

    def _request_creation(self) -> None:
        self.create_requested.emit(self.name_input.text(), self.directory_input.text())

    def set_running(self, running: bool) -> None:
        self.create_button.setEnabled(not running)
        self.cancel_button.setEnabled(running)
        self.browse_button.setEnabled(not running)
        self.name_input.setEnabled(not running)
        self.directory_input.setEnabled(not running)
        if running:
            self.progress.setRange(0, 0)
            self.status_label.setText("Criando o projeto; acompanhe os logs.")
        else:
            self.progress.setRange(0, 100)

    def show_result(self, text: str, success: bool = False) -> None:
        self.status_label.setText(text)
        self.progress.setValue(100 if success else 0)
