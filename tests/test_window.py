import pytest

pytest.importorskip("PySide6")

from ui.app import MainWindow


def test_tela_inicial(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()

    assert window.windowTitle().startswith("RNPB")
    assert window.create_view.create_button.isEnabled()
    assert not window.create_view.cancel_button.isEnabled()
    assert window.create_view.name_input.placeholderText() == "meu-projeto"


def test_entrada_invalida_nao_executa(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.create_view.name_input.setText("../invalido")
    window._create_project("../invalido", "")
    assert not window.runner.is_running
    assert "Erro:" in window.create_view.status_label.text()
