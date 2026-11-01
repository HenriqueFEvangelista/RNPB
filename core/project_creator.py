"""Planejamento validado de comandos Vite/Expo, independente da interface Qt."""

from dataclasses import dataclass
from pathlib import Path
import re
import sys

from core.environment import EnvironmentTools
from core.templates import REACT_NATIVE, REACT_WEB, validar_template


_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_-]{0,62}$")
_WINDOWS_RESERVED = {
    "con", "prn", "aux", "nul", *(f"com{i}" for i in range(1, 10)),
    *(f"lpt{i}" for i in range(1, 10)),
}


@dataclass(frozen=True)
class ProjectSpec:
    name: str
    destination: str
    target: str
    language: str
    template_id: str


@dataclass(frozen=True)
class CommandPlan:
    program: str
    arguments: tuple[str, ...]
    working_directory: str


def validar_projeto(nome: str, pasta: str) -> Path:
    """Valida o nome e a pasta de destino sem sobrescrever projetos existentes."""
    if not _NAME_PATTERN.fullmatch(nome) or nome.casefold() in _WINDOWS_RESERVED:
        raise ValueError(
            "Nome inválido: use de 1 a 63 caracteres, iniciando com letra minúscula; "
            "depois use apenas letras minúsculas, números, '-' ou '_'."
        )
    if not pasta.strip():
        raise ValueError("Escolha uma pasta de destino.")
    raiz = Path(pasta).expanduser().resolve()
    if not raiz.is_dir():
        raise ValueError("A pasta de destino não existe ou não é um diretório.")
    destino = raiz / nome
    if destino.exists() or destino.is_symlink():
        raise ValueError(f"A pasta do projeto já existe: {destino}")
    return destino


def _montar_cli(comando: str, argumentos: tuple[str, ...], pasta: Path, tools: EnvironmentTools) -> CommandPlan:
    """Em Windows, prefere invocar os scripts npm/npx via node.exe, sem shell."""
    executavel = tools.npx if comando == "npx" else tools.npm
    if sys.platform == "win32":
        cli_file = "npx-cli.js" if comando == "npx" else "npm-cli.js"
        candidates = (
            Path(executavel).parent / "node_modules" / "npm" / "bin" / cli_file,
            Path(tools.node).parent / "node_modules" / "npm" / "bin" / cli_file,
        )
        for cli in candidates:
            if cli.is_file():
                return CommandPlan(tools.node, (str(cli), *argumentos), str(pasta))
    return CommandPlan(executavel, argumentos, str(pasta))


def montar_comando(spec: ProjectSpec, tools: EnvironmentTools) -> CommandPlan:
    """Retorna o comando de geração somente para templates do catálogo validado."""
    validar_template(spec.target, spec.language, spec.template_id)
    destino = validar_projeto(spec.name, spec.destination)
    raiz = destino.parent

    if spec.target == REACT_NATIVE:
        args = ("create-expo-app@latest", spec.name, "--template", spec.template_id, "--yes")
    else:
        # create-vite é apenas o scaffold; instalação acontece em outra etapa.
        args = ("create-vite@latest", spec.name, "--template", spec.template_id, "--no-interactive")
    return _montar_cli("npx", args, raiz, tools)


def montar_comando_instalacao(spec: ProjectSpec, tools: EnvironmentTools) -> CommandPlan:
    """Instala as dependências do Vite após a geração dos arquivos."""
    validar_template(spec.target, spec.language, spec.template_id)
    if spec.target != REACT_WEB:
        raise ValueError("Instalação adicional só é necessária para React Web/Vite.")
    caminho = Path(spec.destination).expanduser().resolve() / spec.name
    if not (caminho / "package.json").is_file():
        raise ValueError("O projeto Vite não contém package.json para instalar dependências.")
    return _montar_cli("npm", ("install", "--no-audit", "--no-fund"), caminho, tools)


def montar_comando_expo(nome: str, pasta: str, tools: EnvironmentTools) -> CommandPlan:
    """Compatibilidade com o fluxo Expo blank JS da primeira etapa."""
    from core.templates import JAVASCRIPT

    return montar_comando(ProjectSpec(nome, pasta, REACT_NATIVE, JAVASCRIPT, "blank"), tools)
