from pathlib import Path
import sys

import pytest

from core.environment import EnvironmentTools, verificar_ambiente
from core.project_creator import montar_comando_expo, validar_projeto


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


def test_plano_expo_sem_shell(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    tools = EnvironmentTools("/bin/node", "/bin/npm", "/bin/npx")
    plan = montar_comando_expo("meu-app", str(tmp_path), tools)
    assert plan.program == "/bin/npx"
    assert plan.arguments == (
        "create-expo-app@latest", "meu-app", "--template", "blank", "--yes"
    )
    assert plan.working_directory == str(tmp_path.resolve())


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
