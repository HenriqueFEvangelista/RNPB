"""Testes do pipeline completo, sem executar npm ou Expo de verdade."""

import json

import pytest

pytest.importorskip("PySide6")

from core.environment import EnvironmentTools
from core.templates import JAVASCRIPT, REACT_NATIVE, REACT_WEB, TYPESCRIPT
from ui.app import MainWindow


@pytest.fixture
def prepared(qtbot, monkeypatch):
    import ui.app as app
    monkeypatch.setattr(app, "verificar_ambiente", lambda: (
        True, "Ambiente OK", EnvironmentTools("/bin/node", "/bin/npm", "/bin/npx")
    ))
    window = MainWindow()
    qtbot.addWidget(window)
    plans = []
    monkeypatch.setattr(window.runner, "run", lambda plan: (plans.append(plan) or True))
    return window, plans


def manifest(tmp_path, packages=()):
    directory = tmp_path / "app"
    directory.mkdir(exist_ok=True)
    data = {"name": "app", "dependencies": {p: "^1.0.0" for p in packages}}
    (directory / "package.json").write_text(json.dumps(data), encoding="utf-8")
    return directory


def test_expo_instala_pacotes_depois_de_gerar(tmp_path, prepared):
    window, plans = prepared
    window._create_project("app", str(tmp_path), REACT_NATIVE, TYPESCRIPT,
                           "blank-typescript", ("expo-image", "zustand"))
    assert window._stage == "generating"
    assert plans[0].arguments[0] == "create-expo-app@latest"

    directory = manifest(tmp_path)
    window._process_completed("success", 0)
    assert window._stage == "packages"
    assert plans[1].arguments[:4] == ("expo", "install", "expo-image", "zustand")
    assert plans[1].working_directory == str(directory)
    assert not window.create_view.create_button.isEnabled()

    (directory / "package.json").write_text(json.dumps({
        "dependencies": {"expo-image": "^1", "zustand": "^1"}
    }), encoding="utf-8")
    window._process_completed("success", 0)
    assert window._stage is None
    assert "sucesso" in window.create_view.status_label.text()


def test_vite_instala_base_e_extras_em_sequencia(tmp_path, prepared):
    window, plans = prepared
    window._create_project("app", str(tmp_path), REACT_WEB, JAVASCRIPT,
                           "react", ("axios",))
    directory = manifest(tmp_path)
    window._process_completed("success", 0)
    assert window._stage == "installing"
    assert plans[1].arguments[0] == "install"

    (directory / "node_modules").mkdir()
    window._process_completed("success", 0)
    assert window._stage == "packages"
    assert plans[2].arguments[:2] == ("install", "axios")

    (directory / "package.json").write_text(json.dumps({
        "dependencies": {"axios": "^1"}
    }), encoding="utf-8")
    window._process_completed("success", 0)
    assert window._stage is None
    assert "sucesso" in window.create_view.status_label.text()


def test_instalacao_parcial_nao_exibe_sucesso(tmp_path, prepared):
    window, _ = prepared
    window._create_project("app", str(tmp_path), REACT_NATIVE, JAVASCRIPT,
                           "blank", ("expo-image",))
    manifest(tmp_path)
    window._process_completed("success", 0)
    window._process_completed("failed", 7)
    assert window._stage is None
    assert "Projeto criado, mas" in window.create_view.status_label.text()
    assert "sucesso" not in window.create_view.status_label.text()


def test_exit_zero_sem_manifest_de_pacotes_nao_conta_como_instalado(tmp_path, prepared):
    window, _ = prepared
    window._create_project("app", str(tmp_path), REACT_NATIVE, JAVASCRIPT,
                           "blank", ("expo-image",))
    manifest(tmp_path)
    window._process_completed("success", 0)
    window._process_completed("success", 0)
    assert "não foi confirmada" in window.create_view.status_label.text()


def test_cancelamento_preserva_arquivos(tmp_path, prepared):
    window, _ = prepared
    window._create_project("app", str(tmp_path), REACT_NATIVE, JAVASCRIPT,
                           "blank", ("expo-image",))
    target = manifest(tmp_path)
    window._process_completed("success", 0)
    window._process_completed("cancelled", -1)
    assert window._stage is None
    assert target.exists()
    assert "cancelada" in window.create_view.status_label.text()


def test_parametro_malicioso_e_rejeitado_antes_do_npx(tmp_path, prepared):
    window, plans = prepared
    window._create_project("app", str(tmp_path), REACT_WEB, JAVASCRIPT,
                           "react", ("axios;del",))
    assert not plans
    assert "inválido" in window.create_view.status_label.text()


def test_revisao_exibe_status_de_compatibilidade(qtbot):
    from PySide6.QtCore import Qt
    from core.package_catalog import CatalogResult
    from core.packages import PackageInfo
    from ui.create_view import CreateView
    view = CreateView()
    qtbot.addWidget(view)
    selector = view.package_selector
    selector.search_input.setText("image")
    selector.apply_results("image", REACT_NATIVE, CatalogResult((
        PackageInfo("expo-image", "Imagem", expo_go=False, source="directory"),
    )))
    selector.results.item(0).setCheckState(Qt.CheckState.Checked)
    view._render_review()
    assert "incompatível" in view.review_summary.text()
