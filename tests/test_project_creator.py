import sys

import pytest

from core.environment import EnvironmentTools, verificar_ambiente
from core.project_creator import (
    ProjectSpec, montar_comando, montar_comando_expo, montar_comando_instalacao, validar_projeto,
)
from core.templates import JAVASCRIPT, TYPESCRIPT, REACT_NATIVE, REACT_WEB, opcoes_templates


@pytest.mark.parametrize("name", ["", "Nome", "nome com espaço", "../app", "a&calc", "CON", "a" * 64])
def test_rejeita_nomes_invalidos(tmp_path, name):
    with pytest.raises(ValueError):
        validar_projeto(name, str(tmp_path))


def test_nao_sobrescreve_projeto(tmp_path):
    (tmp_path / "app").mkdir()
    with pytest.raises(ValueError, match="já existe"):
        validar_projeto("app", str(tmp_path))


def test_rejeita_pasta_inexistente(tmp_path):
    with pytest.raises(ValueError, match="não existe"):
        validar_projeto("app", str(tmp_path / "nao-existe"))


def test_destino_valido(tmp_path):
    assert validar_projeto("meu-app", str(tmp_path)) == tmp_path / "meu-app"


@pytest.fixture
def tools():
    return EnvironmentTools("/bin/node", "/bin/npm", "/bin/npx")


@pytest.mark.parametrize(
    "target,language,template_id,package",
    [
        (REACT_WEB, JAVASCRIPT, "react", "create-vite@latest"),
        (REACT_WEB, JAVASCRIPT, "react-compiler", "create-vite@latest"),
        (REACT_WEB, TYPESCRIPT, "react-ts", "create-vite@latest"),
        (REACT_WEB, TYPESCRIPT, "react-compiler-ts", "create-vite@latest"),
        (REACT_NATIVE, JAVASCRIPT, "blank", "create-expo-app@latest"),
        (REACT_NATIVE, TYPESCRIPT, "blank-typescript", "create-expo-app@latest"),
        (REACT_NATIVE, TYPESCRIPT, "default", "create-expo-app@latest"),
        (REACT_NATIVE, TYPESCRIPT, "tabs", "create-expo-app@latest"),
    ],
)
def test_plano_de_geracao_por_template(tmp_path, monkeypatch, tools, target, language, template_id, package):
    monkeypatch.setattr(sys, "platform", "linux")
    spec = ProjectSpec("meu-app", str(tmp_path), target, language, template_id)
    plan = montar_comando(spec, tools)
    assert plan.program == tools.npx
    assert plan.arguments[:2] == (package, "meu-app")
    assert plan.arguments[2:4] == ("--template", template_id)
    assert plan.working_directory == str(tmp_path.resolve())
    assert plan.arguments[-1] == ("--no-interactive" if target == REACT_WEB else "--yes")


@pytest.mark.parametrize(
    "target,language,template_id",
    [
        (REACT_WEB, JAVASCRIPT, "react-ts"),
        (REACT_NATIVE, JAVASCRIPT, "default"),
        (REACT_NATIVE, TYPESCRIPT, "blank"),
        (REACT_WEB, TYPESCRIPT, "tabs"),
        ("other", JAVASCRIPT, "react"),
        (REACT_WEB, "go", "react"),
        (REACT_WEB, JAVASCRIPT, "evil;cmd"),
    ],
)
def test_template_incompativel_e_rejeitado(tmp_path, tools, target, language, template_id):
    spec = ProjectSpec("app", str(tmp_path), target, language, template_id)
    with pytest.raises(ValueError):
        montar_comando(spec, tools)


def test_nomes_suportados_catalogo():
    assert [x.id for x in opcoes_templates(REACT_WEB, JAVASCRIPT)] == ["react", "react-compiler"]
    assert [x.id for x in opcoes_templates(REACT_NATIVE, TYPESCRIPT)] == ["blank-typescript", "default", "tabs"]


def test_instalacao_vite_no_diretorio_correto(tmp_path, monkeypatch, tools):
    monkeypatch.setattr(sys, "platform", "linux")
    spec = ProjectSpec("app", str(tmp_path), REACT_WEB, TYPESCRIPT, "react-ts")
    target_dir = tmp_path / "app"
    target_dir.mkdir()
    (target_dir / "package.json").write_text("{}", encoding="utf8")
    command = montar_comando_instalacao(spec, tools)
    assert command.program == tools.npm
    assert command.working_directory == str(target_dir)
    assert command.arguments == ("install", "--no-audit", "--no-fund")


def test_nao_instala_em_expo_nem_pasta_sem_package(tmp_path, tools):
    expo = ProjectSpec("app", str(tmp_path), REACT_NATIVE, JAVASCRIPT, "blank")
    with pytest.raises(ValueError):
        montar_comando_instalacao(expo, tools)
    web = ProjectSpec("app", str(tmp_path), REACT_WEB, JAVASCRIPT, "react")
    with pytest.raises(ValueError):
        montar_comando_instalacao(web, tools)


def test_fluxo_expo_antigo_continua(tmp_path, monkeypatch, tools):
    monkeypatch.setattr(sys, "platform", "linux")
    plan = montar_comando_expo("app", str(tmp_path), tools)
    assert plan.arguments == ("create-expo-app@latest", "app", "--template", "blank", "--yes")


def test_ambiente_sem_npx(monkeypatch):
    import core.environment as environment

    monkeypatch.setattr(
        environment.shutil, "which",
        lambda exe: None if exe.startswith("npx") else f"/bin/{exe}",
    )
    ok, message, tools = verificar_ambiente()
    assert not ok
    assert "npx" in message
    assert tools is None
