"""Instalação opcional de bibliotecas em projetos criados pelo RNPB."""

from pathlib import Path

from core.environment import EnvironmentTools
from core.packages import validate_package_names
from core.project_creator import CommandPlan, ProjectSpec, _montar_cli
from core.templates import REACT_NATIVE, REACT_WEB, validar_template


def montar_instalacao_bibliotecas(
    spec: ProjectSpec, names, tools: EnvironmentTools
) -> CommandPlan:
    """Não interpreta código fornecido pelo usuário e trabalha só em projetos válidos."""
    validar_template(spec.target, spec.language, spec.template_id)
    packages = validate_package_names(names)
    if not packages:
        raise ValueError("Nenhuma biblioteca foi selecionada.")

    project = Path(spec.destination).expanduser().resolve() / spec.name
    if not (project / "package.json").is_file():
        raise ValueError("Não foi encontrado package.json no projeto.")

    if spec.target == REACT_NATIVE:
        return _montar_cli("npx", ("expo", "install", *packages, "--npm"), project, tools)
    if spec.target == REACT_WEB:
        return _montar_cli("npm", ("install", *packages, "--no-audit", "--no-fund"), project, tools)
    raise ValueError("Plataforma não suportada.")


def pacotes_instalados(package_json: dict, packages: tuple[str, ...]) -> tuple[str, ...]:
    """Confere dependências do manifest, sem confundir saída zero com configuração pronta."""
    deps = package_json.get("dependencies") or {}
    dev = package_json.get("devDependencies") or {}
    if not isinstance(deps, dict) or not isinstance(dev, dict):
        return ()
    return tuple(name for name in packages if name in deps or name in dev)
