"""Inicialização e composição da aplicação desktop PySide6."""

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

from core.environment import verificar_ambiente
from core.process_runner import ProcessRunner
from core.project_creator import montar_comando_expo, validar_projeto
from ui.create_view import CreateView
from ui.logs_view import LogsView
from ui.theme import APP_STYLE


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RNPB — React Native Project Builder")
        self.resize(900, 560)
        self._expected_project: Path | None = None
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
        root.setContentsMargins(0, 0, 0, 0)
        self.pages.setContentsMargins(20, 20, 20, 20)

        self.create_nav.clicked.connect(lambda: self.pages.setCurrentWidget(self.create_view))
        self.logs_nav.clicked.connect(lambda: self.pages.setCurrentWidget(self.logs_view))
        self.create_view.create_requested.connect(self._create_project)
        self.create_view.cancel_requested.connect(self.runner.cancel)
        self.runner.output.connect(self.logs_view.add_log)
        self.runner.started.connect(self._process_started)
        self.runner.completed.connect(self._process_completed)

    def _create_project(self, name: str, destination: str) -> None:
        if self.runner.is_running:
            return

        try:
            expected = validar_projeto(name, destination)
        except ValueError as exc:
            self._failure(str(exc))
            return

        ok, message, tools = verificar_ambiente()
        self.logs_view.add_log(message + "\n")
        if not ok or tools is None:
            self._failure(message)
            return

        try:
            plan = montar_comando_expo(name, destination, tools)
        except ValueError as exc:
            self._failure(str(exc))
            return

        self._expected_project = expected
        self.logs_view.add_log(
            f"\nIniciando projeto Expo (blank): {name}\nDestino: {destination}\n"
        )
        self.create_view.set_running(True)
        self.pages.setCurrentWidget(self.logs_view)
        if not self.runner.run(plan):
            self.create_view.set_running(False)
            self._failure("Já existe uma execução ativa.")

    def _failure(self, message: str) -> None:
        self.create_view.show_result(f"Erro: {message}")
        self.logs_view.add_log(f"Erro: {message}\n")
        self.pages.setCurrentWidget(self.create_view)

    def _process_started(self) -> None:
        self.logs_view.add_log("Processo iniciado.\n")

    def _process_completed(self, status: str, code: int) -> None:
        self.create_view.set_running(False)
        if status == "success":
            if self._expected_project and (self._expected_project / "package.json").is_file():
                message = f"Projeto criado: {self._expected_project}"
                self.create_view.show_result(message, success=True)
                self.logs_view.add_log(f"\n{message}\n")
            else:
                self._failure("O comando terminou sem criar um package.json no destino.")
        elif status == "cancelled":
            self.create_view.show_result("Criação cancelada. Confira eventuais arquivos parciais.")
            self.logs_view.add_log("\nCriação cancelada. Arquivos parciais foram preservados.\n")
        else:
            self._failure(f"A criação falhou (código de saída {code}). Confira os logs.")
        self._expected_project = None
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
