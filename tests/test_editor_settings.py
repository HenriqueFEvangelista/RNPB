"""Testes Qt do ciclo de abertura da IDE e persistência de preferências."""

import pytest

pytest.importorskip("PySide6")
from PySide6.QtCore import QSettings

from core.editor_manager import EditorManager
from core.environment import EnvironmentTools
from core.templates import JAVASCRIPT, REACT_NATIVE, REACT_WEB, TYPESCRIPT
from ui.app import MainWindow


def _manager(tmp_path):
    executable = tmp_path / "Code.exe"
    executable.write_text("mock", encoding="utf-8")
    return EditorManager(
        {"vscode": str(executable)}, platform_name="win32", environ={"PATH": ""}
    )


def _window(qtbot, tmp_path):
    settings = QSettings(str(tmp_path / "rnpb.ini"), QSettings.Format.IniFormat)
    window = MainWindow(editor_manager=_manager(tmp_path), settings=settings)
    qtbot.addWidget(window)
    return window, settings


def _environment(monkeypatch):
    import ui.app as app
    monkeypatch.setattr(app, "verificar_ambiente", lambda: (
        True, "Ambiente OK", EnvironmentTools("/bin/node", "/bin/npm", "/bin/npx")
    ))


def test_editor_preferido_e_auto_open_persistem(qtbot, tmp_path):
    window, settings = _window(qtbot, tmp_path)
    assert window.editor_view.selected_editor_id() == "vscode"
    assert window.editor_view.selected_installation() is not None
    window.editor_view.auto_checkbox.setChecked(True)
    settings.sync()
    other = QSettings(str(tmp_path / "rnpb.ini"), QSettings.Format.IniFormat)
    assert str(other.value("editors/auto_open")).lower() == "true"


def test_nao_abre_automaticamente_sem_preferencia(qtbot, tmp_path, monkeypatch):
    _environment(monkeypatch)
    window, _ = _window(qtbot, tmp_path)
    calls = []
    monkeypatch.setattr(window.editor_manager, "open_project", lambda *args: calls.append(args))
    monkeypatch.setattr(window.runner, "run", lambda plan: True)
    window._create_project("app", str(tmp_path), REACT_NATIVE, TYPESCRIPT, "blank-typescript")
    directory = tmp_path / "app"
    directory.mkdir()
    (directory / "package.json").write_text("{}", encoding="utf-8")
    window._process_completed("success", 0)
    assert not calls
    assert window.logs_view.open_editor_button.isEnabled()
    window.logs_view.open_editor_button.click()
    assert calls == [("vscode", directory)]


def test_abertura_automatica_apos_instalacao_base(qtbot, tmp_path, monkeypatch):
    _environment(monkeypatch)
    window, _ = _window(qtbot, tmp_path)
    window.editor_view.auto_checkbox.setChecked(True)
    calls = []
    monkeypatch.setattr(window.editor_manager, "open_project", lambda *args: calls.append(args))
    monkeypatch.setattr(window.runner, "run", lambda plan: True)
    window._create_project("app", str(tmp_path), REACT_WEB, JAVASCRIPT, "react")
    directory = tmp_path / "app"
    directory.mkdir()
    (directory / "package.json").write_text("{}", encoding="utf-8")
    window._process_completed("success", 0)
    assert not calls  # ainda falta npm install
    (directory / "node_modules").mkdir()
    window._process_completed("success", 0)
    assert calls == [("vscode", directory)]


def test_erro_e_cancelamento_nao_abrem_editor(qtbot, tmp_path, monkeypatch):
    _environment(monkeypatch)
    window, _ = _window(qtbot, tmp_path)
    window.editor_view.auto_checkbox.setChecked(True)
    calls = []
    monkeypatch.setattr(window.editor_manager, "open_project", lambda *args: calls.append(args))
    monkeypatch.setattr(window.runner, "run", lambda plan: True)
    window._create_project("app", str(tmp_path), REACT_NATIVE, JAVASCRIPT, "blank")
    window._process_completed("failed", 1)
    assert not calls
    assert not window.logs_view.open_editor_button.isEnabled()

    window._create_project("app", str(tmp_path), REACT_NATIVE, JAVASCRIPT, "blank")
    window._process_completed("cancelled", -1)
    assert not calls


def test_sem_editor_criacao_continua(qtbot, tmp_path, monkeypatch):
    _environment(monkeypatch)
    manager = EditorManager(platform_name="win32", environ={"PATH": ""})
    settings = QSettings(str(tmp_path / "prefs.ini"), QSettings.Format.IniFormat)
    window = MainWindow(editor_manager=manager, settings=settings)
    qtbot.addWidget(window)
    window.editor_view.auto_checkbox.setChecked(True)
    assert not window.editor_view.auto_checkbox.isEnabled()
    monkeypatch.setattr(window.runner, "run", lambda plan: True)
    window._create_project("app", str(tmp_path), REACT_NATIVE, JAVASCRIPT, "blank")
    directory = tmp_path / "app"
    directory.mkdir()
    (directory / "package.json").write_text("{}", encoding="utf-8")
    window._process_completed("success", 0)
    assert "sucesso" in window.create_view.status_label.text()
    assert not window.logs_view.open_editor_button.isEnabled()


def test_caminho_manual_pode_ser_removido(qtbot, tmp_path):
    window, settings = _window(qtbot, tmp_path)
    window.editor_view.clear_manual_path()
    assert "vscode" not in window.editor_manager.manual_paths
    assert not settings.contains("editors/vscode/path")
    assert not window.editor_view.auto_checkbox.isEnabled()
