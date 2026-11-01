"""Detecção de dependências locais para os geradores do RNPB."""

from dataclasses import dataclass
import shutil


@dataclass(frozen=True)
class EnvironmentTools:
    node: str
    npm: str
    npx: str


def verificar_ambiente() -> tuple[bool, str, EnvironmentTools | None]:
    """Valida somente a presença dos comandos; a execução valida erros reais."""
    node = shutil.which("node")
    npm = shutil.which("npm") or shutil.which("npm.cmd")
    npx = shutil.which("npx") or shutil.which("npx.cmd")

    missing = [
        name
        for name, executable in (("Node.js", node), ("npm", npm), ("npx", npx))
        if not executable
    ]
    if missing:
        return False, f"Ferramentas não encontradas: {', '.join(missing)}. Instale o Node.js e confira o PATH.", None
    return True, "Ambiente OK: Node.js, npm e npx encontrados.", EnvironmentTools(node, npm, npx)
