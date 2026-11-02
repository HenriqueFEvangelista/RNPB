"""Assistente de criação: navegação visual, validação por etapa e revisão."""

from pathlib import Path

from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtWidgets import (
    QComboBox, QFileDialog, QFormLayout, QHBoxLayout, QLabel, QLineEdit,
    QProgressBar, QPushButton, QStackedWidget, QStyle, QToolButton,
    QVBoxLayout, QWidget,
)

from core.packages import validate_package_names
from core.project_creator import validar_nome_projeto, validar_projeto
from core.templates import (
    JAVASCRIPT, TYPESCRIPT, REACT_NATIVE, REACT_WEB, opcoes_templates,
    validar_template,
)
from ui.package_selector import PackageSelector


STEP_NAMES = ("Projeto", "Template", "Bibliotecas", "Revisão")
STEP_ICONS = (
    QStyle.StandardPixmap.SP_DirIcon,
    QStyle.StandardPixmap.SP_FileIcon,
    QStyle.StandardPixmap.SP_DriveHDIcon,
    QStyle.StandardPixmap.SP_DialogApplyButton,
)


class CreateView(QWidget):
    create_requested = Signal(str, str, str, str, str, object)
    cancel_requested = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._running = False
        self._last_invalid_field = ""

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        title = QLabel("Novo projeto")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        # Indicador de progresso e navegação acessível, com ícones nativos do Qt.
        self.step_buttons = []
        navigator = QHBoxLayout()
        navigator.setSpacing(8)
        for index, (name, icon) in enumerate(zip(STEP_NAMES, STEP_ICONS)):
            button = QToolButton()
            button.setObjectName("wizardStepButton")
            button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
            button.setIcon(self.style().standardIcon(icon))
            button.setIconSize(QSize(24, 24))
            button.setText(f"{index + 1}. {name}")
            button.setToolTip(f"Ir para etapa {index + 1}: {name}")
            button.setAccessibleName(f"Etapa {index + 1}: {name}")
            button.setMinimumHeight(72)
            button.setMinimumWidth(120)
            button.clicked.connect(lambda _checked=False, i=index: self.navigate_to(i))
            navigator.addWidget(button, 1)
            self.step_buttons.append(button)
        layout.addLayout(navigator)

        self.wizard_progress = QProgressBar()
        self.wizard_progress.setObjectName("wizardProgress")
        self.wizard_progress.setRange(0, 3)
        self.wizard_progress.setValue(0)
        self.wizard_progress.setTextVisible(False)
        self.wizard_progress.setFixedHeight(5)
        layout.addWidget(self.wizard_progress)

        self.step_label = QLabel()
        self.step_label.setObjectName("muted")
        layout.addWidget(self.step_label)

        self.validation_banner = QLabel()
        self.validation_banner.setObjectName("validationBanner")
        self.validation_banner.setWordWrap(True)
        self.validation_banner.setVisible(False)
        self.validation_banner.setAccessibleName("Erro de validação")
        layout.addWidget(self.validation_banner)

        self.steps = QStackedWidget()
        layout.addWidget(self.steps, 1)

        # Etapa 1: configuração básica e erros junto aos campos.
        project_page = QWidget()
        project_layout = QVBoxLayout(project_page)
        form = QFormLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("meu-projeto")
        self.name_input.setObjectName("projectName")
        self.name_error = QLabel()
        self.name_error.setObjectName("inlineError")
        self.name_error.setWordWrap(True)
        self.name_error.setVisible(False)
        name_group = QWidget()
        name_layout = QVBoxLayout(name_group)
        name_layout.setContentsMargins(0, 0, 0, 0)
        name_layout.setSpacing(3)
        name_layout.addWidget(self.name_input)
        name_layout.addWidget(self.name_error)
        form.addRow("Nome do projeto", name_group)

        self.platform_combo = QComboBox()
        self.platform_combo.addItem("React Native · Expo", REACT_NATIVE)
        self.platform_combo.addItem("React Web · Vite", REACT_WEB)
        form.addRow("Plataforma", self.platform_combo)

        self.language_combo = QComboBox()
        self.language_combo.addItem("JavaScript", JAVASCRIPT)
        self.language_combo.addItem("TypeScript", TYPESCRIPT)
        form.addRow("Linguagem", self.language_combo)

        self.directory_input = QLineEdit()
        self.directory_input.setPlaceholderText("Escolha uma pasta existente")
        self.directory_input.setObjectName("projectDirectory")
        self.browse_button = QPushButton("Procurar…")
        self.browse_button.clicked.connect(self.choose_directory)
        directory_row = QHBoxLayout()
        directory_row.setContentsMargins(0, 0, 0, 0)
        directory_row.addWidget(self.directory_input)
        directory_row.addWidget(self.browse_button)
        self.directory_error = QLabel()
        self.directory_error.setObjectName("inlineError")
        self.directory_error.setWordWrap(True)
        self.directory_error.setVisible(False)
        directory_group = QWidget()
        directory_layout = QVBoxLayout(directory_group)
        directory_layout.setContentsMargins(0, 0, 0, 0)
        directory_layout.setSpacing(3)
        directory_layout.addLayout(directory_row)
        directory_layout.addWidget(self.directory_error)
        form.addRow("Destino", directory_group)
        project_layout.addLayout(form)
        help_text = QLabel(
            "Nome: letras minúsculas, números, hífen e sublinhado; deve começar "
            "com uma letra. O destino precisa ser uma pasta existente."
        )
        help_text.setObjectName("muted")
        help_text.setWordWrap(True)
        project_layout.addWidget(help_text)
        project_layout.addStretch()
        self.steps.addWidget(project_page)

        # Etapa 2: templates dependem da combinação selecionada.
        template_page = QWidget()
        template_layout = QVBoxLayout(template_page)
        template_layout.addWidget(QLabel("Selecione um template oficial"))
        self.template_combo = QComboBox()
        template_layout.addWidget(self.template_combo)
        template_note = QLabel("Somente opções compatíveis com plataforma e linguagem selecionadas.")
        template_note.setWordWrap(True)
        template_note.setObjectName("muted")
        template_layout.addWidget(template_note)
        template_layout.addStretch()
        self.steps.addWidget(template_page)

        # Etapa 3: catálogo reutilizável e opcional.
        self.package_selector = PackageSelector(REACT_NATIVE)
        self.steps.addWidget(self.package_selector)

        # Etapa 4: revisão.
        review_page = QWidget()
        review_layout = QVBoxLayout(review_page)
        review_title = QLabel("Revise as configurações")
        review_title.setObjectName("sectionTitle")
        review_layout.addWidget(review_title)
        self.review_summary = QLabel()
        self.review_summary.setWordWrap(True)
        review_layout.addWidget(self.review_summary)
        review_warning = QLabel(
            "Bibliotecas de terceiros podem executar scripts ao instalar. "
            "A compatibilidade informada não garante funcionamento com seu "
            "SDK ou dispositivo. Confira os logs após a criação."
        )
        review_warning.setWordWrap(True)
        review_warning.setObjectName("muted")
        review_layout.addWidget(review_warning)
        review_layout.addStretch()
        self.steps.addWidget(review_page)

        self.platform_combo.currentIndexChanged.connect(self._refresh_templates)
        self.language_combo.currentIndexChanged.connect(self._refresh_templates)
        self.name_input.textChanged.connect(lambda _: self._clear_field_error("name"))
        self.directory_input.textChanged.connect(lambda _: self._clear_field_error("directory"))
        self.template_combo.currentIndexChanged.connect(self._clear_template_error)
        self._refresh_templates()

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

    @staticmethod
    def _style_state(widget: QWidget, value: bool) -> None:
        widget.setProperty("invalid", "true" if value else "false")
        widget.style().unpolish(widget)
        widget.style().polish(widget)
        widget.update()

    def _clear_field_error(self, field: str) -> None:
        if field == "name":
            self.name_error.clear()
            self.name_error.hide()
            self._style_state(self.name_input, False)
        elif field == "directory":
            self.directory_error.clear()
            self.directory_error.hide()
            self._style_state(self.directory_input, False)
        if self._last_invalid_field == field:
            self._last_invalid_field = ""
            self.validation_banner.clear()
            self.validation_banner.hide()

    def _clear_template_error(self, *_args) -> None:
        if self._last_invalid_field == "template":
            self._last_invalid_field = ""
            self.validation_banner.clear()
            self.validation_banner.hide()

    def show_validation_error(self, message: str, step: int, field: str = "") -> None:
        """Navega para a etapa relevante e mostra erro na tela, não só nos logs."""
        if not 0 <= step < self.steps.count():
            step = 0
        self.steps.setCurrentIndex(step)
        text = message if message.startswith("Erro:") else f"Erro: {message}"
        self.validation_banner.setText(text)
        self.validation_banner.show()
        self.status_label.setText(text)
        self._last_invalid_field = field
        focus = None
        if field == "name":
            self.name_error.setText(message)
            self.name_error.show()
            self._style_state(self.name_input, True)
            focus = self.name_input
        elif field == "directory":
            self.directory_error.setText(message)
            self.directory_error.show()
            self._style_state(self.directory_input, True)
            focus = self.directory_input
        elif field == "template":
            focus = self.template_combo
        elif field == "packages":
            focus = self.package_selector.search_input
        self._refresh_navigation()
        if focus:
            focus.setFocus(Qt.FocusReason.OtherFocusReason)

    def show_failure(self, message: str) -> None:
        """Erros externos e do runner também ficam visíveis no wizard."""
        text = message if message.startswith("Erro:") else f"Erro: {message}"
        self.validation_banner.setText(text)
        self.validation_banner.show()
        self.status_label.setText(text)

    def _validate_project(self) -> bool:
        try:
            validar_nome_projeto(self.name_input.text())
        except ValueError as error:
            self.show_validation_error(str(error), 0, "name")
            return False
        try:
            validar_projeto(self.name_input.text(), self.directory_input.text())
        except ValueError as error:
            self.show_validation_error(str(error), 0, "directory")
            return False
        return True

    def _validate_template(self) -> bool:
        try:
            validar_template(
                self.platform_combo.currentData(),
                self.language_combo.currentData(),
                self.template_combo.currentData(),
            )
        except ValueError as error:
            self.show_validation_error(str(error), 1, "template")
            return False
        return True

    def _validate_packages(self) -> bool:
        try:
            validate_package_names(self.package_selector.selected_names)
        except ValueError as error:
            self.show_validation_error(str(error), 2, "packages")
            return False
        return True

    def _validate_until(self, target: int) -> bool:
        checks = (self._validate_project, self._validate_template, self._validate_packages)
        for index in range(min(target, len(checks))):
            if not checks[index]():
                return False
        return True

    def _refresh_navigation(self) -> None:
        step = self.steps.currentIndex()
        self.step_label.setText(f"Etapa {step + 1} de 4 — {STEP_NAMES[step]}")
        self.wizard_progress.setValue(step)
        for index, button in enumerate(self.step_buttons):
            state = "current" if index == step else ("completed" if index < step else "upcoming")
            button.setProperty("stepState", state)
            button.style().unpolish(button)
            button.style().polish(button)
            button.update()
            button.setEnabled(not self._running)
        self.back_button.setVisible(not self._running and step > 0)
        self.next_button.setVisible(not self._running and step < 3)
        self.create_button.setVisible(not self._running and step == 3)
        self.cancel_button.setVisible(self._running)

    def navigate_to(self, target: int) -> None:
        """Cliques futuros exigem passar pelas validações das etapas anteriores."""
        if self._running or not 0 <= target < self.steps.count():
            return
        if target > self.steps.currentIndex() and not self._validate_until(target):
            return
        self.steps.setCurrentIndex(target)
        if target == 3:
            self._render_review()
        self._refresh_navigation()

    def next_step(self) -> None:
        self.navigate_to(min(3, self.steps.currentIndex() + 1))

    def previous_step(self) -> None:
        self.navigate_to(max(0, self.steps.currentIndex() - 1))

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
        command = f"{installer} {' '.join(names)}" if names else "(nenhuma)"
        if names and target == REACT_NATIVE:
            command += " --npm"
        self.review_summary.setText(
            f"Projeto: {self.name_input.text()}\n"
            f"Destino: {self.directory_input.text()}\n"
            f"Plataforma: {self.platform_combo.currentText()}\n"
            f"Linguagem: {self.language_combo.currentText()}\n"
            f"Template: {self.template_combo.currentData()}\n\n"
            f"Bibliotecas: {description}\n"
            f"Instalação opcional: {command}\n"
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
        if self._running or not self._validate_until(3):
            return
        self.validation_banner.hide()
        self.validation_banner.clear()
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
            self.validation_banner.hide()
            self.progress.setRange(0, 0)
            self.status_label.setText("Criando projeto; acompanhe os logs.")
        else:
            self.progress.setRange(0, 100)
        self._refresh_navigation()

    def show_result(self, text: str, success: bool = False) -> None:
        self.status_label.setText(text)
        self.progress.setValue(100 if success else 0)
