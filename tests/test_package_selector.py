import pytest
pytest.importorskip("PySide6")

from PySide6.QtCore import Qt

from core.package_catalog import CatalogResult
from core.packages import PackageInfo
from core.templates import REACT_NATIVE, REACT_WEB
from ui.package_selector import PackageSelector


def test_catalogo_local_sem_rede(qtbot):
    widget = PackageSelector(REACT_NATIVE)
    qtbot.addWidget(widget)
    assert widget.results.count() >= 3
    assert "não verificado" in widget.results.item(0).text()


def test_selecao_persiste_em_busca_e_filtro(qtbot):
    widget = PackageSelector(REACT_WEB)
    qtbot.addWidget(widget)
    item = widget.results.item(0)
    first = item.data(Qt.ItemDataRole.UserRole).name
    item.setCheckState(Qt.CheckState.Checked)
    assert widget.selected_names == (first,)
    widget.search_input.setText("lucide")
    widget.apply_results("lucide", REACT_WEB, CatalogResult((
        PackageInfo("lucide-react", "ícones", source="npm"),)))
    assert widget.selected_names == (first,)
    widget.search_input.clear()
    assert widget.selected_names == (first,)


def test_mudanca_de_plataforma_limpa_selecao(qtbot):
    widget = PackageSelector(REACT_WEB)
    qtbot.addWidget(widget)
    widget.results.item(0).setCheckState(Qt.CheckState.Checked)
    widget.set_target(REACT_NATIVE)
    assert widget.selected_names == ()


def test_somente_expo_go_nao_exibe_desconhecidos(qtbot):
    widget = PackageSelector(REACT_NATIVE)
    qtbot.addWidget(widget)
    widget.search_input.setText("image")
    widget.apply_results("image", REACT_NATIVE, CatalogResult((
        PackageInfo("expo-image", "imagens", expo_go=True, source="directory"),
        PackageInfo("another-image", "imagens", expo_go=None, source="npm"),
    )))
    widget.expo_go_only.setChecked(True)
    assert widget.results.count() == 1
    assert "expo-image" in widget.results.item(0).text()


def test_ignora_resposta_obsoleta(qtbot):
    widget = PackageSelector(REACT_WEB)
    qtbot.addWidget(widget)
    widget.search_input.setText("react")
    count = widget.results.count()
    widget.apply_results("axios", REACT_WEB, CatalogResult((PackageInfo("axios"),)))
    assert widget.results.count() == count



def test_selecao_curada_recebe_compatibilidade_apos_busca(qtbot):
    widget = PackageSelector(REACT_NATIVE)
    qtbot.addWidget(widget)
    item = next(
        widget.results.item(index)
        for index in range(widget.results.count())
        if widget.results.item(index).data(Qt.ItemDataRole.UserRole).name == "expo-image"
    )
    item.setCheckState(Qt.CheckState.Checked)
    assert widget.selected_packages[0].expo_go is None
    widget.search_input.setText("expo-image")
    widget.apply_results("expo-image", REACT_NATIVE, CatalogResult((
        PackageInfo("expo-image", "Imagens", expo_go=True, source="directory"),
    )))
    assert widget.selected_packages[0].expo_go is True
