"""Testes da descoberta dinâmica: filtros, cache, confiança e CLI segura."""

import sys

import pytest
import requests

from core.environment import EnvironmentTools
from core.project_creator import ProjectSpec, montar_comando
from core.template_catalog import (
    GITHUB_EXPO_EXAMPLES, GITHUB_REPOSITORY_SEARCH,
    TemplateCatalogService, parse_expo_examples, parse_github_references,
)
from core.templates import (
    JAVASCRIPT, TYPESCRIPT, REACT_NATIVE, REACT_WEB, TemplateSpec,
    opcoes_templates, validar_template,
)


def official(name="with-sqlite"):
    return {
        "name": name,
        "path": name,
        "type": "dir",
        "html_url": f"https://github.com/expo/examples/tree/master/{name}",
    }


class Response:
    def __init__(self, data, error=None):
        self.data = data
        self.error = error

    def raise_for_status(self):
        if self.error:
            raise self.error

    def json(self):
        return self.data


def example(name="with-sqlite"):
    return parse_expo_examples([official(name)])[0]


def test_catalogo_expo_valida_origem_e_nao_executa_entradas_estranhas():
    data = [
        official("with-sqlite"),
        official("with-camera"),
        {**official("with-camera"), "path": "subdir/with-camera"},
        official("../foo"),
        official("--help"),
        {**official("with-stripe"), "html_url": "https://evil.example/with-stripe"},
        {**official("with-auth0"), "type": "file"},
        {"name": "with-fake", "type": "dir"},
        "garbage",
    ]
    items = parse_expo_examples(data)
    assert [x.id for x in items] == ["with-camera", "with-sqlite"]
    assert all(x.source == "expo/examples" and x.strategy == "example" for x in items)
    assert all(x.language is None and x.installable for x in items)


def test_referencia_comunidade_nunca_executavel():
    data = {"items": [
        {"full_name": "dev/vite-react-starter", "html_url": "https://github.com/dev/vite-react-starter",
         "description": "Vite React starter", "archived": False, "fork": False,
         "license": {"spdx_id": "MIT"}},
        {"full_name": "evil/../repo", "html_url": "https://github.com/evil/../repo"},
        {"full_name": "dev/archived", "html_url": "https://github.com/dev/archived", "archived": True},
        {"full_name": "dev/bad", "html_url": "javascript:alert(1)"},
    ]}
    items = parse_github_references(data)
    assert len(items) == 1
    assert items[0].source == "github-community"
    assert items[0].strategy == "reference"
    assert not items[0].installable
    assert items[0].license == "MIT"


def test_expo_busca_e_cache_compartilhado_por_linguagem():
    calls = []
    time = [100.0]

    def fake_get(url, **kwargs):
        calls.append((url, kwargs))
        return Response([official("with-sqlite"), official("with-router")])

    service = TemplateCatalogService(fake_get, clock=lambda: time[0])
    a = service.search("sqlite", REACT_NATIVE, JAVASCRIPT)
    b = service.search("router", REACT_NATIVE, TYPESCRIPT)
    assert len(calls) == 1
    assert calls[0][0] == GITHUB_EXPO_EXAMPLES
    assert [x.id for x in a.templates] == ["with-sqlite"]
    assert [x.id for x in b.templates] == ["with-router"]

    time[0] += 601
    service.search("sqlite", REACT_NATIVE, TYPESCRIPT)
    assert len(calls) == 2


def test_vite_busca_marca_repositorios_somente_como_referencia():
    seen = []
    def fake_get(url, **kwargs):
        seen.append((url, kwargs))
        return Response({"items": [
            {"full_name": "user/react-vite-template",
             "html_url": "https://github.com/user/react-vite-template",
             "description": "A React Vite template"},
        ]})

    result = TemplateCatalogService(fake_get).search("react", REACT_WEB, JAVASCRIPT)
    assert len(result.templates) == 1
    assert not result.templates[0].installable
    assert seen[0][0] == GITHUB_REPOSITORY_SEARCH
    assert seen[0][1]["params"]["per_page"] <= 20
    assert seen[0][1]["timeout"] == (4, 8)


@pytest.mark.parametrize("language", [JAVASCRIPT, TYPESCRIPT])
def test_exemplo_expo_em_ambas_linguagens_sem_prometer_conversao(language):
    item = example()
    assert validar_template(REACT_NATIVE, language, item.id, (item,)) == item


def test_referencia_ou_exemplo_falso_nao_pode_ser_gerado(tmp_path):
    community = TemplateSpec("github:user/repo", "Repo", REACT_WEB, None,
                             strategy="reference", source="github-community",
                             url="https://github.com/user/repo", installable=False)
    tools = EnvironmentTools("/bin/node", "/bin/npm", "/bin/npx")
    with pytest.raises(ValueError, match="Template incompatível"):
        montar_comando(ProjectSpec("app", str(tmp_path), REACT_WEB, JAVASCRIPT,
                                  community.id, community), tools)
    with pytest.raises(ValueError, match="Template incompatível"):
        montar_comando(ProjectSpec("app", str(tmp_path), REACT_NATIVE, TYPESCRIPT,
                                  "with-sqlite"), tools)

    forged = TemplateSpec("with-sqlite", "SQLite", REACT_NATIVE, None,
                          strategy="example", source="random-owner",
                          url="https://github.com/random-owner/expo/tree/master/with-sqlite")
    with pytest.raises(ValueError):
        montar_comando(ProjectSpec("app", str(tmp_path), REACT_NATIVE, JAVASCRIPT,
                                  forged.id, forged), tools)

    altered_url = TemplateSpec("with-sqlite", "SQLite", REACT_NATIVE, None,
                               strategy="example", source="expo/examples",
                               url="https://attacker.invalid/")
    with pytest.raises(ValueError):
        montar_comando(ProjectSpec("app", str(tmp_path), REACT_NATIVE, JAVASCRIPT,
                                  altered_url.id, altered_url), tools)


def test_geracao_expo_exemplo_aprovado(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    item = example("with-camera")
    spec = ProjectSpec("app", str(tmp_path), REACT_NATIVE, TYPESCRIPT, item.id, item)
    plan = montar_comando(spec, EnvironmentTools("/bin/node", "/bin/npm", "/bin/npx"))
    assert plan.arguments == (
        "create-expo-app@latest", "app", "--example", "with-camera", "--yes"
    )


def test_falha_da_api_retorna_aviso_sem_impedir_presets_locais():
    def denied(*args, **kwargs):
        raise requests.HTTPError("429 Too Many Requests")
    service = TemplateCatalogService(denied)
    result = service.search("sqlite", REACT_NATIVE, JAVASCRIPT)
    assert result.templates == ()
    assert "indisponível" in result.warning
    assert any(x.id == "blank" for x in opcoes_templates(REACT_NATIVE, JAVASCRIPT))


@pytest.mark.parametrize("query,target,language", [
    ("a", REACT_NATIVE, JAVASCRIPT),
    ("", REACT_WEB, TYPESCRIPT),
])
def test_busca_curta_nao_dispara_http(query, target, language):
    def should_not_call(*args, **kwargs):
        raise AssertionError("No network expected")
    assert TemplateCatalogService(should_not_call).search(
        query, target, language
    ).templates == ()


@pytest.mark.parametrize("target,language,query", [
    ("android", JAVASCRIPT, "expo"),
    (REACT_WEB, "golang", "react"),
    (REACT_NATIVE, TYPESCRIPT, "x" * 101),
])
def test_entrada_de_busca_invalida(target, language, query):
    with pytest.raises(ValueError):
        TemplateCatalogService().search(query, target, language)


def test_json_malformado_e_tratado():
    service = TemplateCatalogService(lambda *a, **kw: Response({"error": "bad"}))
    result = service.search("sqlite", REACT_NATIVE, TYPESCRIPT)
    assert not result.templates
    assert result.warning


@pytest.mark.parametrize("status,headers,expected", [
    (429, {"Retry-After": "30"}, "Aguarde 30 segundos"),
    (403, {"X-RateLimit-Remaining": "0"}, "Limite de consultas"),
    (403, {}, "acesso negado"),
    (422, {}, "pesquisa não foi aceita"),
    (502, {}, "HTTP 502"),
])
def test_erro_http_apresenta_status_sem_esconder_causa(status, headers, expected):
    response = requests.Response()
    response.status_code = status
    response.headers.update(headers)

    def error(*args, **kwargs):
        raise requests.HTTPError(f"Error {status}", response=response)

    result = TemplateCatalogService(error).search("router", REACT_WEB, JAVASCRIPT)
    assert result.templates == ()
    assert f"HTTP {status}" in result.warning
    assert expected.casefold() in result.warning.casefold()
    assert "locais" in result.warning
