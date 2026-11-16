"""Integração do catálogo de templates com o wizard e a thread Qt."""

import threading

import pytest
pytest.importorskip("PySide6")

from PySide6.QtCore import QThreadPool

from core.environment import EnvironmentTools
from core.template_catalog import TemplateSearchResult
from core.templates import JAVASCRIPT, TYPESCRIPT, REACT_NATIVE, REACT_WEB, TemplateSpec
from ui.app import MainWindow
from ui.create_view import CreateView
from ui.template_catalog_worker import TemplateCatalogWorker


def expo_example():
    return TemplateSpec(
        "with-sqlite", "SQLite · Expo example", REACT_NATIVE, None,
        strategy="example", source="expo/examples",
        description="Exemplo oficial Expo", url="https://github.com/expo/examples/tree/master/with-sqlite",
    )


def community_ref():
    return TemplateSpec(
        "github:user/repo", "user/repo", REACT_WEB, None,
        strategy="reference", source="github-community", installable=False,
        description="Referência Vite", url="https://github.com/user/repo",
    )


def test_wizard_preserva_catalogo_local_e_adiciona_exemplo(qtbot, tmp_path):
    view = CreateView()
    qtbot.addWidget(view)
    view.name_input.setText("app")
    view.directory_input.setText(str(tmp_path))
    assert view.template_combo.currentData() == "blank"
    view.template_search.setText("sqlite")
    view.apply_template_results("sqlite", REACT_NATIVE, JAVASCRIPT,
                                TemplateSearchResult((expo_example(),)))
    ids = [view.template_combo.itemData(i) for i in range(view.template_combo.count())]
    assert "with-sqlite" in ids
    view.template_combo.setCurrentIndex(view.template_combo.findData("with-sqlite"))
    assert view.selected_template().strategy == "example"
    assert "expo/examples" in view.template_details.text()
    assert "não filtrável" in view.template_details.text()
    view._render_review()
    assert "with-sqlite" in view.review_summary.text()


def test_busca_referencia_comunitaria_nao_cria_projeto(qtbot, tmp_path):
    view = CreateView()
    qtbot.addWidget(view)
    view.name_input.setText("app")
    view.directory_input.setText(str(tmp_path))
    view.platform_combo.setCurrentIndex(view.platform_combo.findData(REACT_WEB))
    view.template_search.setText("repo")
    view.apply_template_results("repo", REACT_WEB, JAVASCRIPT,
                                TemplateSearchResult((community_ref(),)))
    view.template_combo.setCurrentIndex(view.template_combo.findData("github:user/repo"))
    assert "não instalável" in view.template_details.text()
    with pytest.raises(ValueError):
        view.selected_template()
    view.steps.setCurrentIndex(3)
    emitted = []
    view.create_requested.connect(lambda *args: emitted.append(args))
    view._request_creation()
    assert not emitted
    assert view.steps.currentIndex() == 1


def test_resultado_antigo_nao_substitui_contexto(qtbot):
    view = CreateView()
    qtbot.addWidget(view)
    view.template_search.setText("sqlite")
    view.language_combo.setCurrentIndex(view.language_combo.findData(TYPESCRIPT))
    view.apply_template_results("sqlite", REACT_NATIVE, JAVASCRIPT,
                                TemplateSearchResult((expo_example(),)))
    assert view.template_combo.findData("with-sqlite") == -1
    view.apply_template_results("sqlite", REACT_NATIVE, TYPESCRIPT,
                                TemplateSearchResult((expo_example(),)))
    assert view.template_combo.findData("with-sqlite") != -1
    view.template_search.clear()
    assert view.template_combo.findData("with-sqlite") == -1


def test_timer_dispara_apenas_busca_valida(qtbot):
    view = CreateView()
    qtbot.addWidget(view)
    emitted = []
    view.template_search_requested.connect(lambda *args: emitted.append(args))
    view.template_search.setText("x")
    view._dispatch_template_search()
    assert emitted == []
    view.template_search.setText("camera")
    view._dispatch_template_search()
    assert emitted == [("camera", REACT_NATIVE, JAVASCRIPT)]


def test_worker_template_fora_thread_ui(qtbot):
    class FakeService:
        thread_id = None

        def search(self, query, target, language):
            self.thread_id = threading.get_ident()
            return TemplateSearchResult((expo_example(),))

    service = FakeService()
    main_thread = threading.get_ident()
    pool = QThreadPool()
    worker = TemplateCatalogWorker(10, "sqlite", REACT_NATIVE, JAVASCRIPT, service)
    result = []
    worker.signals.finished.connect(lambda *args: result.append(args))
    with qtbot.waitSignal(worker.signals.finished, timeout=10000):
        pool.start(worker)
    assert service.thread_id != main_thread
    assert result[0][:4] == (10, "sqlite", REACT_NATIVE, JAVASCRIPT)
    pool.waitForDone(10000)


def test_expo_example_wizard_usa_flag_example(tmp_path, qtbot, monkeypatch):
    import ui.app as app
    monkeypatch.setattr(app, "verificar_ambiente", lambda: (
        True, "Ambiente OK", EnvironmentTools("/bin/node", "/bin/npm", "/bin/npx")
    ))
    window = MainWindow()
    qtbot.addWidget(window)
    view = window.create_view
    view.template_search.setText("sqlite")
    view.apply_template_results("sqlite", REACT_NATIVE, JAVASCRIPT,
                                TemplateSearchResult((expo_example(),)))
    view.template_combo.setCurrentIndex(view.template_combo.findData("with-sqlite"))
    plans = []
    monkeypatch.setattr(window.runner, "run", lambda plan: (plans.append(plan) or True))
    window._create_project("app", str(tmp_path), REACT_NATIVE, JAVASCRIPT, "with-sqlite")
    assert plans
    assert plans[0].arguments[2:4] == ("--example", "with-sqlite")
    window._reset_operation()


def test_fallback_local_visivel_quando_api_falha(qtbot):
    view = CreateView()
    qtbot.addWidget(view)
    view.template_search.setText("naoexisteapi")
    view.apply_template_results(
        "naoexisteapi", REACT_NATIVE, JAVASCRIPT,
        TemplateSearchResult((), "GitHub indisponível."),
    )
    assert "indisponível" in view.template_source_label.text()
    assert view.template_combo.findData("blank") != -1
    assert view.selected_template().id == "blank"


def test_busca_vite_exibe_ajuda_de_referencias(qtbot):
    view = CreateView()
    qtbot.addWidget(view)
    assert "Expo:" in view.template_search_hint.text()
    view.platform_combo.setCurrentIndex(view.platform_combo.findData(REACT_WEB))
    assert "dashboard" in view.template_search_hint.text()
    assert "referências comunitárias" in view.template_search_hint.text()


def test_vite_busca_acionada_apenas_por_botao(qtbot):
    from PySide6.QtCore import QTimer
    view = CreateView()
    qtbot.addWidget(view)
    view.platform_combo.setCurrentIndex(view.platform_combo.findData(REACT_WEB))
    calls = []
    view.template_search_requested.connect(lambda *args: calls.append(args))
    view.template_search.setText("dashboard")
    assert view.template_search_button.isEnabled()
    assert not view._template_timer.isActive()
    view.template_search_button.click()
    assert calls == [("dashboard", REACT_WEB, JAVASCRIPT)]


def test_expo_mantem_busca_automatica_com_debounce(qtbot):
    view = CreateView()
    qtbot.addWidget(view)
    view.template_search.setText("router")
    assert view._template_timer.isActive()
    assert not view.template_search_button.isVisible()
