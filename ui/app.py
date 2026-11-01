"""Composição da janela principal e orquestração das etapas por QProcess."""

import sys
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from core.environment import EnvironmentTools, verificar_ambiente
from core.process_runner import ProcessRunner
from core.project_creator import (
    ProjectSpec, montar_comando, montar_comando_instalacao, validar_projeto,
)
from core.templates import REACT_WEB
from ui.create_view import CreateView
from ui.logs_view import LogsView
from ui.theme import APP_STYLE


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RNPB — React & React Native Project Builder")
        self.resize(940, 590)
        self._expected_project: Path | None = None
        self._current_spec: ProjectSpec | None = None
        self._current_tools: EnvironmentTools | None = None
        self._stage: str | None = None
        self._close_after_process = False
        self.runner = ProcessRunner(self)
        self.create_view = CreateView()
        self.logs_view = LogsView()

        container = QWidget()
        self.setCentralWidget(container)
        root = QHBoxLayout(container)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(190)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(12, 20, 12, 20)
        self.create_nav = QPushButton("Criar projeto")
        self.logs_nav = QPushButton("Logs")
        sidebar_layout.addWidget(self.create_nav)
        sidebar_layout.addWidget(self.logs_nav)
        sidebar_layout.addStretch()
        root.addWidget(sidebar)

        self.pages = QStackedWidget()
        self.pages.addWidget(self.create_view)
        self.pages.addWidget(self.logs_view)
        root.addWidget(self.pages, 1)
        self.pages.setContentsMargins(20, 20, 20, 20)

        self.create_nav.clicked.connect(lambda: self.pages.setCurrentWidget(self.create_view))
        self.logs_nav.clicked.connect(lambda: self.pages.setCurrentWidget(self.logs_view))
        self.create_view.create_requested.connect(self._create_project)
        self.create_view.cancel_requested.connect(self.runner.cancel)
        self.runner.output.connect(self.logs_view.add_log)
        self.runner.started.connect(self._process_started)
        self.runner.completed.connect(self._process_completed)

    def _create_project(
        self, name: str, destination: str, target: str, language: str, template_id: str
    ) -> None:
        if self.runner.is_running or self._stage is not None:
            return

        spec = ProjectSpec(name, destination, target, language, template_id)
        try:
            # montar_comando valida a combinação e a pasta antes de executar.
            expected = validar_projeto(name, destination)
            ok, message, tools = verificar_ambiente()
            self.logs_view.add_log(message + "\n")
            if not ok or tools is None:
                self._failure(message)
                return
            plan = montar_comando(spec, tools)
        except ValueError as exc:
            self._failure(str(exc))
            return

        self._current_spec = spec
        self._current_tools = tools
        self._expected_project = expected
        self._stage = "generating"
        generator = "Vite" if target == REACT_WEB else "Expo"
        self.logs_view.add_log(
            f"\nGerando {generator} ({template_id}, {language}): {name}\nDestino: {destination}\n"
        )
        self.create_view.set_running(True)
        self.pages.setCurrentWidget(self.logs_view)
        if not self.runner.run(plan):
            self._finish_error("Já existe uma execução ativa.")

    def _failure(self, message: str) -> None:
        self.create_view.show_result(f"Erro: {message}")
        self.logs_view.add_log(f"Erro: {message}\n")
        self.pages.setCurrentWidget(self.create_view)

    def _process_started(self) -> None:
        self.logs_view.add_log("Processo iniciado.\n")

    def _process_completed(self, status: str, code: int) -> None:
        if status == "cancelled":
            self.create_view.show_result("Criação cancelada. Confira eventuais arquivos parciais.")
            self.logs_view.add_log("\nCriação cancelada; arquivos parciais preservados.\n")
        elif status != "success":
            self._failure(f"Falha na etapa '{self._stage}' (código {code}). Confira os logs.")
        elif self._expected_project is None or not (self._expected_project / "package.json").is_file():
            self._failure("O gerador terminou sem criar um package.json no destino.")
        elif self._stage == "generating" and self._current_spec and self._current_spec.target == REACT_WEB:
            # create-vite apenas escreve os arquivos; npm install é obrigatório.
            self._stage = "installing"
            self.create_view.status_label.setText("Instalando dependências do React Web...")
            self.logs_view.add_log("\nProjeto Vite gerado. Executando npm install...\n")
            try:
                plan = montar_comando_instalacao(self._current_spec, self._current_tools)
            except ValueError as exc:
                self._finish_error(str(exc))
                return
            if not self.runner.run(plan):
                self._finish_error("Não foi possível iniciar a instalação.")
            return
        elif self._stage == "installing" and not (self._expected_project / "node_modules").is_dir():
            self._failure("npm terminou sem criar node_modules. Verifique a instalação.")
        else:
            message = f"Projeto criado com sucesso: {self._expected_project}"
            self.create_view.show_result(message, success=True)
            self.logs_view.add_log(f"\n{message}\n")
        self._reset_operation()

    def _finish_error(self, message: str) -> None:
        self._failure(message)
        self._reset_operation()

    def _reset_operation(self) -> None:
        self.create_view.set_running(False)
        self._stage = None
        self._expected_project = None
        self._current_spec = None
        self._current_tools = None
        if self._close_after_process:
            self.close()

    def closeEvent(self, event) -> None:
        if self.runner.is_running:
            if not self._close_after_process:
                choice = QMessageBox.question(
                    self,
                    "Processo em execução",
                    "Cancelar a criação e fechar o RNPB? O projeto pode ficar incompleto.",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
                )
                if choice != QMessageBox.StandardButton.Yes:
                    event.ignore()
                    return
                self._close_after_process = True
                self.runner.cancel()
            event.ignore()
            return
        event.accept()


def start_app() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyleSheet(APP_STYLE)
    window = MainWindow()
    window.show()
    return app.exec()
