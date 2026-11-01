import pytest
pytest.importorskip("PySide6")

from PySide6.QtCore import Qt

from core.templates import REACT_WEB
from ui.create_view import CreateView


def test_assistente_tem_4_etapas(qtbot):
    view = CreateView()
    qtbot.addWidget(view)
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
