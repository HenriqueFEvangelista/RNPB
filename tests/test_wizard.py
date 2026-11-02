import pytest
pytest.importorskip("PySide6")

from PySide6.QtCore import Qt

from core.templates import REACT_WEB
from ui.create_view import CreateView


def test_assistente_tem_4_etapas(qtbot, tmp_path):
    view = CreateView()
    qtbot.addWidget(view)
    view.name_input.setText("app")
    view.directory_input.setText(str(tmp_path))
    assert view.steps.count() == 4
    assert view.steps.currentIndex() == 0
    view.next_step()
    assert view.steps.currentIndex() == 1
    view.next_step()
    assert view.steps.currentIndex() == 2
    view.next_step()
    assert view.steps.currentIndex() == 3
    assert "Bibliotecas" in view.review_summary.text()
    view.previous_step()
    assert view.steps.currentIndex() == 2


def test_assistente_envia_pacotes_selecionados(qtbot, tmp_path):
    view = CreateView()
    qtbot.addWidget(view)
    view.platform_combo.setCurrentIndex(view.platform_combo.findData(REACT_WEB))
    view.name_input.setText("app")
    view.directory_input.setText(str(tmp_path))
    item = view.package_selector.results.item(0)
    package = item.data(Qt.ItemDataRole.UserRole)
    item.setCheckState(Qt.CheckState.Checked)
    result = []
    view.create_requested.connect(lambda *args: result.append(args))
    view._request_creation()
    assert result[0][-1] == (package.name,)


def test_running_disable_buttons(qtbot):
    view = CreateView()
    qtbot.addWidget(view)
    view.set_running(True)
    assert not view.create_button.isEnabled()
    assert not view.steps.isEnabled()
    view.set_running(False)
    assert view.steps.isEnabled()



def test_etapas_superiores_tem_icones_e_barra_de_progresso(qtbot, tmp_path):
    view = CreateView()
    qtbot.addWidget(view)
    view.show()
    view.name_input.setText("app")
    view.directory_input.setText(str(tmp_path))
    assert len(view.step_buttons) == 4
    assert all(not button.icon().isNull() for button in view.step_buttons)
    assert view.wizard_progress.value() == 0

    view.step_buttons[2].click()
    assert view.steps.currentIndex() == 2
    assert view.wizard_progress.value() == 2
    assert view.step_buttons[2].property("stepState") == "current"
    assert view.step_buttons[0].property("stepState") == "completed"

    view.step_buttons[0].click()
    assert view.steps.currentIndex() == 0
    assert view.wizard_progress.value() == 0


def test_nome_com_maiuscula_mostra_erro_no_campo(qtbot, tmp_path):
    view = CreateView()
    qtbot.addWidget(view)
    view.show()
    view.name_input.setText("MeuProjeto")
    view.directory_input.setText(str(tmp_path))
    view.next_step()

    assert view.steps.currentIndex() == 0
    assert view.validation_banner.isVisible()
    assert "Erro:" in view.validation_banner.text()
    assert "Nome inválido" in view.name_error.text()
    assert view.name_input.property("invalid") == "true"
    assert view.name_input.isEnabled()
    assert view.wizard_progress.value() == 0

    view.name_input.setText("meu-projeto")
    assert view.name_input.property("invalid") == "false"
    view.next_step()
    assert view.steps.currentIndex() == 1


def test_sem_nome_bloqueia_criacao_e_redireciona(qtbot, tmp_path):
    view = CreateView()
    qtbot.addWidget(view)
    view.show()
    view.directory_input.setText(str(tmp_path))
    view.steps.setCurrentIndex(3)  # simula usuário voltando de revisão
    emitted = []
    view.create_requested.connect(lambda *args: emitted.append(args))
    view._request_creation()
    assert view.steps.currentIndex() == 0
    assert not emitted
    assert view.name_error.text()
    assert view.name_input.property("invalid") == "true"


def test_diretorio_vazio_destacado_e_corrigido(qtbot):
    view = CreateView()
    qtbot.addWidget(view)
    view.show()
    view.name_input.setText("app")
    view.next_step()
    assert view.steps.currentIndex() == 0
    assert "pasta" in view.directory_error.text().lower()
    assert view.directory_input.property("invalid") == "true"


def test_pasta_inexistente_e_nome_ja_existente(qtbot, tmp_path):
    view = CreateView()
    qtbot.addWidget(view)
    view.show()
    view.name_input.setText("app")
    view.directory_input.setText(str(tmp_path / "nao-existe"))
    view.navigate_to(3)
    assert view.steps.currentIndex() == 0
    assert "não existe" in view.directory_error.text()

    (tmp_path / "app").mkdir()
    view.directory_input.setText(str(tmp_path))
    view.navigate_to(3)
    assert view.steps.currentIndex() == 0
    assert "já existe" in view.directory_error.text()


def test_template_invalido_leva_para_etapa_correta(qtbot, tmp_path):
    view = CreateView()
    qtbot.addWidget(view)
    view.show()
    view.name_input.setText("app")
    view.directory_input.setText(str(tmp_path))
    view.template_combo.clear()
    view.steps.setCurrentIndex(3)
    view._request_creation()
    assert view.steps.currentIndex() == 1
    assert "Template incompatível" in view.validation_banner.text()
    assert view.template_combo.isEnabled()


def test_progresso_nao_pula_etapa_sem_validar(qtbot, tmp_path):
    view = CreateView()
    qtbot.addWidget(view)
    view.show()
    view.name_input.setText("App")
    view.directory_input.setText(str(tmp_path))
    view.step_buttons[3].click()
    assert view.steps.currentIndex() == 0
    view.name_input.setText("app")
    view.step_buttons[3].click()
    assert view.steps.currentIndex() == 3
    assert view.wizard_progress.value() == 3


def test_completou_wizard_sem_bibliotecas(qtbot, tmp_path):
    view = CreateView()
    qtbot.addWidget(view)
    view.name_input.setText("app")
    view.directory_input.setText(str(tmp_path))
    view.navigate_to(3)
    emitted = []
    view.create_requested.connect(lambda *args: emitted.append(args))
    view._request_creation()
    assert len(emitted) == 1
    assert emitted[0][-1] == ()
