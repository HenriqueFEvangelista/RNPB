import requests
import pytest

from core.package_catalog import CatalogService, NPM_SEARCH, DIRECTORY_SEARCH
from core.packages import (
    curated_packages, parse_npm, parse_directory, merge_packages, validate_package_names,
)
from core.templates import REACT_NATIVE, REACT_WEB


def test_catálogo_inicial_disponivel_sem_rede():
    assert "axios" in [p.name for p in curated_packages(REACT_WEB)]
    assert "expo-image" in [p.name for p in curated_packages(REACT_NATIVE)]
    assert all(p.expo_go is None for p in curated_packages(REACT_NATIVE))


def test_parse_npm_nao_atribui_compatibilidade_mobile():
    data = {"objects": [{"package": {
        "name": "expo-image", "version": "1.0.0", "description": "Imagens"
    }}]}
    package = parse_npm(data, REACT_NATIVE)[0]
    assert package.source == "npm"
    assert package.expo_go is None


def test_parse_directory_indicadores_explicitos():
    payload = {"libraries": [{"npmPkg": "expo-image", "expoGo": True,
                              "ios": True, "android": True, "web": False,
                              "npm": {"latestRelease": "5.0.0"},
                              "github": {"description": "Imagens nativas"}}]}
    p = parse_directory(payload)[0]
    assert p.name == "expo-image"
    assert p.expo_go is True
    assert p.web is False
    assert p.compatibility_label.startswith("Expo Go: informado")


def test_parse_directory_sem_indicador_fica_desconhecido():
    p = parse_directory({"libraries": [{"npmPkg": "axios"}]})[0]
    assert p.expo_go is None
    assert p.compatibility_label == "Expo Go: não verificado"


def test_merge_preserva_dados_do_directory():
    a = parse_directory({"libraries": [{"npmPkg": "expo-image", "expoGo": False}]})
    b = parse_npm({"objects": [{"package": {
        "name": "expo-image", "description": "Descrição", "version": "4.0"
    }}]}, REACT_NATIVE)
    merged = merge_packages(a, b)[0]
    assert merged.expo_go is False
    assert merged.description == "Descrição"


@pytest.mark.parametrize("names", [
    ["--save-dev"], ["http://site"], ["foo;del"], ["@scope"], ["foo@latest"],
    ["$(pwd)"], ["../foo"], ["foo bar"], ["foo\nx"], ["."],
])
def test_rejeita_pacotes_que_nao_sao_identificadores_npm(names):
    with pytest.raises(ValueError):
        validate_package_names(names)


def test_deduplicacao_e_limite():
    assert validate_package_names(["axios", "axios", "@scope/name"]) == ("axios", "@scope/name")
    with pytest.raises(ValueError):
        validate_package_names([f"p-{i}" for i in range(31)])


class Response:
    def __init__(self, data):
        self.data = data

    def raise_for_status(self):
        pass

    def json(self):
        return self.data


def test_catalog_service_duas_apis_e_cache():
    calls = []
    def fetch(url, *, params, timeout):
        calls.append((url, params, timeout))
        if url == NPM_SEARCH:
            return Response({"objects": [{"package": {"name": "expo-image", "version": "2"}}]})
        if url == DIRECTORY_SEARCH:
            return Response({"libraries": [{"npmPkg": "expo-image", "expoGo": True}]})
        assert False, url
    clock = lambda: 1200
    catalog = CatalogService(http_get=fetch, clock=clock)
    one = catalog.search("expo", REACT_NATIVE)
    two = catalog.search("expo", REACT_NATIVE)
    assert one.packages == two.packages
    assert one.packages[0].expo_go is True
    assert len(calls) == 2


def test_catalog_service_fallback_parcial():
    def fetch(url, *, params, timeout):
        if url == NPM_SEARCH:
            raise requests.ConnectionError("off")
        return Response({"libraries": [{"npmPkg": "expo-image", "expoGo": True}]})
    result = CatalogService(http_get=fetch).search("image", REACT_NATIVE)
    assert len(result.packages) == 1
    assert "npm indisponível" in result.warning


def test_catalog_service_falha_total_nao_finge_resultado():
    def fetch(*args, **kwargs):
        raise requests.ConnectionError("off")
    result = CatalogService(http_get=fetch).search("zustand", REACT_WEB)
    assert result.packages == ()
    assert "indisponível" in result.warning


def test_queries_curta_e_alvo_invalido():
    catalog = CatalogService(http_get=lambda *a, **kw: pytest.fail("No HTTP expected"))
    assert catalog.search("a", REACT_WEB).packages == ()
    with pytest.raises(ValueError):
        catalog.search("axios", "other")
