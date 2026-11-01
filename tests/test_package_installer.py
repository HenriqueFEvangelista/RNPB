import json
import sys

import pytest

from core.environment import EnvironmentTools
from core.package_installer import montar_instalacao_bibliotecas, pacotes_instalados
from core.project_creator import ProjectSpec
from core.templates import REACT_NATIVE, REACT_WEB, JAVASCRIPT, TYPESCRIPT


@pytest.fixture
def tools():
    return EnvironmentTools("/bin/node", "/bin/npm", "/bin/npx")


def project(tmp_path, target=REACT_WEB):
    folder = tmp_path / "app"
    folder.mkdir()
    (folder / "package.json").write_text("{}", encoding="utf8")
    template = "react" if target == REACT_WEB else "blank-typescript"
    lang = JAVASCRIPT if target == REACT_WEB else TYPESCRIPT
    return ProjectSpec("app", str(tmp_path), target, lang, template)


def test_npm_instala_na_pasta_do_web(tmp_path, tools, monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    spec = project(tmp_path)
    plan = montar_instalacao_bibliotecas(spec, ["axios", "zustand"], tools)
    assert plan.program == "/bin/npm"
    assert plan.working_directory == str(tmp_path / "app")
    assert plan.arguments == ("install", "axios", "zustand", "--no-audit", "--no-fund")


def test_expo_install_respeita_sdk(tmp_path, tools, monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    spec = project(tmp_path, REACT_NATIVE)
    plan = montar_instalacao_bibliotecas(spec, ["expo-image", "zustand"], tools)
    assert plan.program == "/bin/npx"
    assert plan.arguments == ("expo", "install", "expo-image", "zustand", "--npm")


def test_rejeita_injecao_e_projeto_inexistente(tmp_path, tools):
    spec = ProjectSpec("app", str(tmp_path), REACT_WEB, JAVASCRIPT, "react")
    with pytest.raises(ValueError, match="package.json"):
        montar_instalacao_bibliotecas(spec, ["axios"], tools)
    (tmp_path / "app").mkdir()
    (tmp_path / "app" / "package.json").write_text("{}", encoding="utf8")
    with pytest.raises(ValueError, match="inválido"):
        montar_instalacao_bibliotecas(spec, ["--prefix=../"], tools)


def test_valida_manifest_depois_de_instalar():
    manifest = {"dependencies": {"axios": "^1.0"}, "devDependencies": {"zustand": "^1.0"}}
    assert pacotes_instalados(manifest, ("axios", "zustand", "expo-image")) == ("axios", "zustand")
    assert pacotes_instalados({}, ("axios",)) == ()
