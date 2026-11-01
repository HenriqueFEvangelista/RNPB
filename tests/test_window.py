import pytest

pytest.importorskip("PySide6")

from core.environment import EnvironmentTools
from core.templates import JAVASCRIPT, REACT_NATIVE, REACT_WEB, TYPESCRIPT
from ui.app import MainWindow


def test_tela_inicial(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()

    assert window.windowTitle().startswith("RNPB")
    assert window.create_view.create_button.isEnabled()
    assert not window.create_view.cancel_button.isEnabled()
    assert window.create_view.name_input.placeholderText() == "meu-projeto"
    assert window.create_view.platform_combo.currentData() == REACT_NATIVE
    assert window.create_view.template_combo.currentData() == "blank"


def test_seletores_filtram_templates(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    view = window.create_view

    view.language_combo.setCurrentIndex(view.language_combo.findData(TYPESCRIPT))
    assert [view.template_combo.itemData(i) for i in range(view.template_combo.count())] == [
        "blank-typescript", "default", "tabs"
    ]

    view.platform_combo.setCurrentIndex(view.platform_combo.findData(REACT_WEB))
    assert [view.template_combo.itemData(i) for i in range(view.template_combo.count())] == [
        "react-ts", "react-compiler-ts"
    ]
    view.language_combo.setCurrentIndex(view.language_combo.findData(JAVASCRIPT))
    assert [view.template_combo.itemData(i) for i in range(view.template_combo.count())] == [
        "react", "react-compiler"
    ]


def test_entrada_invalida_nao_executa(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window._create_project("../invalido", "", REACT_WEB, TYPESCRIPT, "react-ts")
    assert not window.runner.is_running
    assert "Erro:" in window.create_view.status_label.text()


def test_fluxo_vite_gerar_instalar_concluir(qtbot, tmp_path, monkeypatch):
    import ui.app as app
    monkeypatch.setattr(app, "verificar_ambiente", lambda: (
        True, "Ambiente OK", EnvironmentTools("/bin/node", "/bin/npm", "/bin/npx")
    ))
    window = MainWindow()
    qtbot.addWidget(window)
    plans = []
    monkeypatch.setattr(window.runner, "run", lambda plan: (plans.append(plan) or True))

    window._create_project("app", str(tmp_path), REACT_WEB, JAVASCRIPT, "react")
    assert window._stage == "generating"
    assert plans[0].arguments[0] == "create-vite@latest"
    assert not window.create_view.create_button.isEnabled()

    target_dir = tmp_path / "app"
    target_dir.mkdir()
    (target_dir / "package.json").write_text("{}", encoding="utf8")
    window._process_completed("success", 0)
    assert window._stage == "installing"
    assert plans[1].arguments[0] == "install"
    assert not window.create_view.create_button.isEnabled()

    (target_dir / "node_modules").mkdir()
    window._process_completed("success", 0)
    assert window._stage is None
    assert window.create_view.create_button.isEnabled()
    assert "sucesso" in window.create_view.status_label.text()


def test_erro_npm_nao_parece_sucesso(qtbot, tmp_path, monkeypatch):
    import ui.app as app
    monkeypatch.setattr(app, "verificar_ambiente", lambda: (
        True, "Ambiente OK", EnvironmentTools("/bin/node", "/bin/npm", "/bin/npx")
    ))
    window = MainWindow()
    qtbot.addWidget(window)
    monkeypatch.setattr(window.runner, "run", lambda plan: True)

    window._create_project("app", str(tmp_path), REACT_WEB, TYPESCRIPT, "react-ts")
    target_dir = tmp_path / "app"
    target_dir.mkdir()
    (target_dir / "package.json").write_text("{}", encoding="utf8")
    window._process_completed("success", 0)
    window._process_completed("failed", 1)
    assert "Erro:" in window.create_view.status_label.text()
    assert window._stage is None


def test_expo_nao_exige_npm_install_extra(qtbot, tmp_path, monkeypatch):
    import ui.app as app
    monkeypatch.setattr(app, "verificar_ambiente", lambda: (
        True, "Ambiente OK", EnvironmentTools("/bin/node", "/bin/npm", "/bin/npx")
    ))
    window = MainWindow()
    qtbot.addWidget(window)
    plans = []
    monkeypatch.setattr(window.runner, "run", lambda plan: (plans.append(plan) or True))

    window._create_project("app", str(tmp_path), REACT_NATIVE, TYPESCRIPT, "blank-typescript")
    directory = tmp_path / "app"
    directory.mkdir()
    (directory / "package.json").write_text("{}", encoding="utf8")
    window._process_completed("success", 0)
    assert len(plans) == 1
    assert "sucesso" in window.create_view.status_label.text()
