"""Janela principal: pipeline de criação, instalação opcional e busca assíncrona."""

import json
import sys
from pathlib import Path

from PySide6.QtCore import QThreadPool
from PySide6.QtWidgets import (
    QApplication, QFrame, QHBoxLayout, QMainWindow, QMessageBox,
    QPushButton, QStackedWidget, QVBoxLayout, QWidget,
)

from core.environment import EnvironmentTools, verificar_ambiente
from core.package_catalog import CatalogService
from core.package_installer import montar_instalacao_bibliotecas, pacotes_instalados
from core.packages import validate_package_names
from core.process_runner import ProcessRunner
from core.project_creator import ProjectSpec, montar_comando, montar_comando_instalacao, validar_projeto
from core.templates import REACT_WEB
from ui.catalog_worker import CatalogWorker
from ui.create_view import CreateView
from ui.logs_view import LogsView
from ui.theme import APP_STYLE


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RNPB — React & React Native Project Builder")
        self.resize(1040, 650)
        self._expected_project: Path | None = None
        self._current_spec: ProjectSpec | None = None
        self._current_tools: EnvironmentTools | None = None
        self._selected_packages: tuple[str, ...] = ()
        self._stage: str | None = None
        self._close_after_process = False
        self.runner = ProcessRunner(self)
        self.create_view = CreateView()
        self.logs_view = LogsView()

        self.catalog = CatalogService()
        self._pool = QThreadPool(self)
        self._pool.setMaxThreadCount(2)
        self._search_seq = 0
        self._workers: dict[int, CatalogWorker] = {}

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
        self.create_view.package_selector.search_requested.connect(self._search_packages)
        self.runner.output.connect(self.logs_view.add_log)
        self.runner.started.connect(self._process_started)
        self.runner.completed.connect(self._process_completed)

    def _search_packages(self, query: str, target: str) -> None:
        if self._stage is not None:
            return
        self._search_seq += 1
        seq = self._search_seq
        worker = CatalogWorker(seq, query, target, self.catalog)
        self._workers[seq] = worker
        worker.signals.finished.connect(self._catalog_finished)
        worker.signals.failed.connect(self._catalog_failed)
        self._pool.start(worker)

    def _catalog_finished(self, seq: int, query: str, target: str, result) -> None:
        self._workers.pop(seq, None)
        if seq == self._search_seq:
            self.create_view.package_selector.apply_results(query, target, result)

    def _catalog_failed(self, seq: int, query: str, target: str, error: str) -> None:
        self._workers.pop(seq, None)
        if seq == self._search_seq:
            from core.package_catalog import CatalogResult
            self.create_view.package_selector.apply_results(
                query, target, CatalogResult((), f"Busca indisponível: {error}")
            )

    def _create_project(
        self, name: str, destination: str, target: str, language: str, template_id: str,
        packages=(),
    ) -> None:
        if self.runner.is_running or self._stage is not None:
            return
        spec = ProjectSpec(name, destination, target, language, template_id)
        try:
            selected_names = validate_package_names(packages)
            expected = validar_projeto(name, destination)
            ok, message, tools = verificar_ambiente()
            self.logs_view.add_log(message + "\n")
            if not ok or tools is None:
                self._failure(message)
                return
            plan = montar_comando(spec, tools)
        except ValueError as error:
            self._failure(str(error))
            return

        self._selected_packages = selected_names
        self._current_spec = spec
        self._current_tools = tools
        self._expected_project = expected
        self._stage = "generating"
        generator = "Vite" if target == REACT_WEB else "Expo"
        self.logs_view.add_log(
            f"\nGerando {generator} ({template_id}, {language}): {name}\n"
            f"Destino: {destination}\nBibliotecas: {', '.join(selected_names) or 'nenhuma'}\n"
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

    def _run_optional_packages(self) -> bool:
        if not self._selected_packages:
            return False
        if not self._current_spec or not self._current_tools:
            self._finish_error("Dados do projeto indisponíveis para instalar bibliotecas.")
            return True
        try:
            plan = montar_instalacao_bibliotecas(
                self._current_spec, self._selected_packages, self._current_tools
            )
        except ValueError as error:
            self._finish_error(f"Projeto criado, mas as bibliotecas não foram instaladas: {error}")
            return True
        self._stage = "packages"
        self.logs_view.add_log(
            f"\nProjeto criado. Instalando bibliotecas: {', '.join(self._selected_packages)}\n"
        )
        self.create_view.status_label.setText("Instalando bibliotecas selecionadas…")
        if not self.runner.run(plan):
            self._finish_error("Projeto criado, mas não foi possível iniciar a instalação das bibliotecas.")
        return True

    def _installed_packages_match_manifest(self) -> tuple[bool, str]:
        try:
            manifest_path = self._expected_project / "package.json"
            with manifest_path.open(encoding="utf-8") as handle:
                manifest = json.load(handle)
            present = set(pacotes_instalados(manifest, self._selected_packages))
            missing = [p for p in self._selected_packages if p not in present]
            if missing:
                return False, ", ".join(missing)
            return True, ""
        except (ValueError, OSError, TypeError) as error:
            return False, str(error)

    def _process_completed(self, status: str, code: int) -> None:
        if status == "cancelled":
            self.create_view.show_result(
                "Execução cancelada. O projeto pode ter sido criado parcialmente."
            )
            self.logs_view.add_log("\nCancelado; arquivos parciais foram preservados.\n")
        elif status != "success":
            if self._stage == "packages":
                self._failure(
                    f"Projeto criado, mas a instalação de bibliotecas falhou (código {code}). "
                    "Confira os logs."
                )
            else:
                self._failure(f"Falha na etapa '{self._stage}' (código {code}). Confira os logs.")
        elif self._expected_project is None or not (self._expected_project / "package.json").is_file():
            self._failure("O gerador terminou sem criar um package.json no destino.")
        elif self._stage == "generating" and self._current_spec and self._current_spec.target == REACT_WEB:
            self._stage = "installing"
            self.create_view.status_label.setText("Instalando dependências do React Web...")
            self.logs_view.add_log("\nProjeto Vite gerado. Executando npm install...\n")
            try:
                plan = montar_comando_instalacao(self._current_spec, self._current_tools)
            except ValueError as error:
                self._finish_error(str(error))
                return
            if not self.runner.run(plan):
                self._finish_error("Não foi possível iniciar a instalação das dependências.")
            return
        elif self._stage == "installing" and not (self._expected_project / "node_modules").is_dir():
            self._failure("npm terminou sem criar node_modules. Verifique a instalação.")
        elif self._stage in ("generating", "installing") and self._run_optional_packages():
            return
        elif self._stage == "packages" and not self._installed_packages_match_manifest()[0]:
            _, missing = self._installed_packages_match_manifest()
            self._failure(
                "Projeto criado, mas a instalação não foi confirmada no package.json: "
                + missing
            )
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
        self._selected_packages = ()
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
