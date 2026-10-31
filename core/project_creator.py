"""Regras e planejamento da criação de projetos, sem dependências de Qt."""

from dataclasses import dataclass
from pathlib import Path
import re
import sys

from core.environment import EnvironmentTools


_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_-]{0,62}$")
_WINDOWS_RESERVED = {
    "con", "prn", "aux", "nul", *(f"com{i}" for i in range(1, 10)),
    *(f"lpt{i}" for i in range(1, 10))
}


@dataclass(frozen=True)
class CommandPlan:
    program: str
    arguments: tuple[str, ...]
    working_directory: str


def validar_projeto(nome: str, pasta: str) -> Path:
    """Retorna o destino esperado; lança ValueError se a criação for insegura."""
    if not _NAME_PATTERN.fullmatch(nome) or nome.casefold() in _WINDOWS_RESERVED:
        raise ValueError(
            "Nome inválido: use de 1 a 63 caracteres, iniciando com letra minúscula; "
            "depois use apenas letras minúsculas, números, '-' ou '_'."
        )
    if not pasta.strip():
        raise ValueError("Escolha uma pasta de destino.")
    raiz = Path(pasta).expanduser()
    if not raiz.is_dir():
        raise ValueError("A pasta de destino não existe ou não é um diretório.")
    destino = raiz / nome
    if destino.exists() or destino.is_symlink():
        raise ValueError(f"A pasta do projeto já existe: {destino}")
    return destino


def montar_comando_expo(nome: str, pasta: str, tools: EnvironmentTools) -> CommandPlan:
    """Cria o plano de CLI para o único template atualmente suportado: Expo blank."""
    validar_projeto(nome, pasta)

    arguments = ("create-expo-app@latest", nome, "--template", "blank", "--yes")

    # Evita iniciar o shim npx.cmd via interpretador Windows quando o CLI real
    # do npm está disponível. O nome é validado antes de compor os argumentos.
    if sys.platform == "win32":
        candidates = (
            Path(tools.npx).parent / "node_modules" / "npm" / "bin" / "npx-cli.js",
            Path(tools.node).parent / "node_modules" / "npm" / "bin" / "npx-cli.js",
        )
        for cli in candidates:
            if cli.is_file():
                return CommandPlan(tools.node, (str(cli), *arguments), str(Path(pasta).resolve()))

    return CommandPlan(tools.npx, arguments, str(Path(pasta).resolve()))
