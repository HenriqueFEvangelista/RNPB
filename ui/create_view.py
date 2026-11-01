"""Assistente de criação: projeto, template, bibliotecas e revisão."""

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox, QFileDialog, QFormLayout, QHBoxLayout, QLabel, QLineEdit,
    QProgressBar, QPushButton, QStackedWidget, QVBoxLayout, QWidget,
)

from core.templates import JAVASCRIPT, TYPESCRIPT, REACT_NATIVE, REACT_WEB, opcoes_templates
from ui.package_selector import PackageSelector


class CreateView(QWidget):
    create_requested = Signal(str, str, str, str, str, object)
    cancel_requested = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        title = QLabel("Novo projeto")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        self.step_label = QLabel()
        self.step_label.setObjectName("muted")
        layout.addWidget(self.step_label)

        self.steps = QStackedWidget()
        layout.addWidget(self.steps, 1)

        # Etapa 1 — Projeto
        project_page = QWidget()
        project_layout = QVBoxLayout(project_page)
        form = QFormLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("meu-projeto")
        self.name_input.setObjectName("projectName")
        form.addRow("Nome do projeto", self.name_input)

        self.platform_combo = QComboBox()
        self.platform_combo.addItem("React Native · Expo", REACT_NATIVE)
        self.platform_combo.addItem("React Web · Vite", REACT_WEB)
        form.addRow("Plataforma", self.platform_combo)

        self.language_combo = QComboBox()
        self.language_combo.addItem("JavaScript", JAVASCRIPT)
        self.language_combo.addItem("TypeScript", TYPESCRIPT)
        form.addRow("Linguagem", self.language_combo)

        destination_row = QHBoxLayout()
        self.directory_input = QLineEdit()
        self.directory_input.setPlaceholderText("Escolha uma pasta existente")
        self.directory_input.setObjectName("projectDirectory")
        self.browse_button = QPushButton("Procurar…")
        self.browse_button.clicked.connect(self.choose_directory)
        destination_row.addWidget(self.directory_input)
        destination_row.addWidget(self.browse_button)
        form.addRow("Destino", destination_row)
        project_layout.addLayout(form)
        project_layout.addStretch()
        self.steps.addWidget(project_page)

        # Etapa 2 — Template
        template_page = QWidget()
        template_layout = QVBoxLayout(template_page)
        template_layout.addWidget(QLabel("Selecione um template oficial"))
        self.template_combo = QComboBox()
        template_layout.addWidget(self.template_combo)
        template_note = QLabel("Somente opções compatíveis com a plataforma e a linguagem selecionadas.")
        template_note.setWordWrap(True)
        template_note.setObjectName("muted")
        template_layout.addWidget(template_note)
        template_layout.addStretch()
        self.steps.addWidget(template_page)

        # Etapa 3 — Bibliotecas (componente reutilizável futuramente)
        self.package_selector = PackageSelector(REACT_NATIVE)
        self.steps.addWidget(self.package_selector)

        # Etapa 4 — Revisão
        review_page = QWidget()
        review_layout = QVBoxLayout(review_page)
        review_title = QLabel("Revise as configurações")
        review_title.setObjectName("sectionTitle")
        review_layout.addWidget(review_title)
        self.review_summary = QLabel()
        self.review_summary.setWordWrap(True)
        self.review_summary.setTextInteractionFlags(self.review_summary.textInteractionFlags())
        review_layout.addWidget(self.review_summary)
        review_warning = QLabel(
            "Bibliotecas de terceiros podem executar scripts ao instalar. "
            "A compatibilidade informada pelo catálogo não garante funcionamento "
            "com seu SDK ou dispositivo. Confira os logs após a criação."
        )
        review_warning.setWordWrap(True)
        review_warning.setObjectName("muted")
        review_layout.addWidget(review_warning)
        review_layout.addStretch()
        self.steps.addWidget(review_page)

        self.platform_combo.currentIndexChanged.connect(self._refresh_templates)
        self.language_combo.currentIndexChanged.connect(self._refresh_templates)
        self._refresh_templates()

        # Navegação + processo
        controls = QHBoxLayout()
        self.back_button = QPushButton("Voltar")
        self.next_button = QPushButton("Continuar")
        self.create_button = QPushButton("Criar projeto")
        self.create_button.setObjectName("primaryButton")
        self.cancel_button = QPushButton("Cancelar execução")
        self.cancel_button.setEnabled(False)
        self.back_button.clicked.connect(self.previous_step)
        self.next_button.clicked.connect(self.next_step)
        self.create_button.clicked.connect(self._request_creation)
        self.cancel_button.clicked.connect(self.cancel_requested.emit)
        controls.addWidget(self.back_button)
        controls.addWidget(self.next_button)
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

        self._running = False
        self._refresh_navigation()

    def _refresh_templates(self, *_args) -> None:
        selected = self.template_combo.currentData()
        self.template_combo.clear()
        options = opcoes_templates(self.platform_combo.currentData(), self.language_combo.currentData())
        for item in options:
            self.template_combo.addItem(item.label, item.id)
        ids = [self.template_combo.itemData(i) for i in range(self.template_combo.count())]
        if selected in ids:
            self.template_combo.setCurrentIndex(ids.index(selected))
        self.package_selector.set_target(self.platform_combo.currentData())

    def _refresh_navigation(self) -> None:
        step = self.steps.currentIndex()
        self.step_label.setText(
            f"Etapa {step + 1} de 4 — " +
            ("Projeto", "Template", "Bibliotecas", "Revisão")[step]
        )
        self.back_button.setVisible(not self._running and step > 0)
        self.next_button.setVisible(not self._running and step < 3)
        self.create_button.setVisible(not self._running and step == 3)
        self.cancel_button.setVisible(self._running)

    def next_step(self) -> None:
        if self._running:
            return
        if self.steps.currentIndex() < 3:
            self.steps.setCurrentIndex(self.steps.currentIndex() + 1)
        if self.steps.currentIndex() == 3:
            self._render_review()
        self._refresh_navigation()

    def previous_step(self) -> None:
        if self._running:
            return
        self.steps.setCurrentIndex(max(0, self.steps.currentIndex() - 1))
        self._refresh_navigation()

    def _render_review(self) -> None:
        target = self.platform_combo.currentData()
        names = self.package_selector.selected_names
        installer = "npx expo install" if target == REACT_NATIVE else "npm install"
        description = ", ".join(names) if names else "Nenhuma biblioteca adicional"
        compat = (
            " | ".join(f"{p.name}: {p.compatibility_label}"
                     for p in self.package_selector.selected_packages)
            if target == REACT_NATIVE and names else "Não aplicável"
        )
        steps = "Gerar projeto → " + ("Instalar dependências base → " if target == REACT_WEB else "")
        if names:
            steps += "Instalar bibliotecas selecionadas"
        else:
            steps += "Concluir"
        self.review_summary.setText(
            f"Projeto: {self.name_input.text()}\n"
            f"Destino: {self.directory_input.text()}\n"
            f"Plataforma: {self.platform_combo.currentText()}\n"
            f"Linguagem: {self.language_combo.currentText()}\n"
            f"Template: {self.template_combo.currentData()}\n\n"
            f"Bibliotecas: {description}\n"
            f"Instalação opcional: {installer} {' '.join(names) if names else '(nenhuma)'}" +
            (" --npm" if target == REACT_NATIVE and names else "") + "\n"
            f"Compatibilidade Expo Go: {compat}\n\n"
            f"Fluxo: {steps}"
        )

    def choose_directory(self) -> None:
        directory = QFileDialog.getExistingDirectory(
            self, "Pasta de destino", self.directory_input.text() or str(Path.home())
        )
        if directory:
            self.directory_input.setText(directory)

    def _request_creation(self) -> None:
        self.create_requested.emit(
            self.name_input.text(), self.directory_input.text(),
            self.platform_combo.currentData(), self.language_combo.currentData(),
            self.template_combo.currentData(), self.package_selector.selected_names,
        )

    def set_running(self, running: bool) -> None:
        self._running = running
        self.steps.setEnabled(not running)
        self.back_button.setEnabled(not running)
        self.next_button.setEnabled(not running)
        self.create_button.setEnabled(not running)
        self.cancel_button.setEnabled(running)
        if running:
            self.progress.setRange(0, 0)
            self.status_label.setText("Criando projeto; acompanhe os logs.")
        else:
            self.progress.setRange(0, 100)
        self._refresh_navigation()

    def show_result(self, text: str, success: bool = False) -> None:
        self.status_label.setText(text)
        self.progress.setValue(100 if success else 0)
