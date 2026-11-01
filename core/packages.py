"""Modelos e regras de pacotes: dados externos nunca autorizam comandos arbitrários."""

from dataclasses import dataclass, replace
import re

from core.templates import REACT_NATIVE, REACT_WEB

_PACKAGE = re.compile(r"^(?:@[a-z0-9][a-z0-9._-]*/)?[a-z0-9][a-z0-9._-]*$")
CATEGORIES = ("Todas", "Rede", "Estado", "Interface", "Armazenamento", "Navegação", "Outras")


@dataclass(frozen=True)
class PackageInfo:
    name: str
    description: str = ""
    version: str = ""
    category: str = "Outras"
    source: str = "local"  # local | npm | directory
    expo_go: bool | None = None
    android: bool | None = None
    ios: bool | None = None
    web: bool | None = None

    @property
    def compatibility_label(self) -> str:
        if self.expo_go is True:
            return "Expo Go: informado como compatível"
        if self.expo_go is False:
            return "Expo Go: informado como incompatível"
        return "Expo Go: não verificado"


def validate_package_names(names) -> tuple[str, ...]:
    """Aceita identificadores npm simples; bloqueia versões/URLs/flags/scripts."""
    result = []
    for name in names:
        if not isinstance(name, str) or len(name) > 214 or not _PACKAGE.fullmatch(name):
            raise ValueError(f"Nome de biblioteca inválido: {name!r}")
        if name not in result:
            result.append(name)
    if len(result) > 30:
        raise ValueError("Selecione no máximo 30 bibliotecas por projeto.")
    return tuple(result)


# Sugestões iniciais são apenas uma lista; compatibilidade só é afirmada com
# metadados do RN Directory. A instalação pode executar scripts de terceiros.
CURATED = {
    REACT_WEB: (
        PackageInfo("axios", "Cliente HTTP", category="Rede"),
        PackageInfo("zustand", "Gerenciamento de estado", category="Estado"),
        PackageInfo("react-router-dom", "Rotas no navegador", category="Navegação"),
        PackageInfo("lucide-react", "Ícones SVG para React", category="Interface"),
        PackageInfo("react-hook-form", "Formulários", category="Interface"),
    ),
    REACT_NATIVE: (
        PackageInfo("axios", "Cliente HTTP", category="Rede"),
        PackageInfo("zustand", "Gerenciamento de estado", category="Estado"),
        PackageInfo("expo-sqlite", "Banco de dados SQLite", category="Armazenamento"),
        PackageInfo("expo-image", "Imagens e cache", category="Interface"),
        PackageInfo("@react-native-async-storage/async-storage", "Armazenamento local", category="Armazenamento"),
    ),
}


def curated_packages(target: str) -> tuple[PackageInfo, ...]:
    if target not in CURATED:
        raise ValueError("Plataforma desconhecida.")
    return CURATED[target]


def category_for(name: str, target: str) -> str:
    for package in curated_packages(target):
        if package.name == name:
            return package.category
    return "Outras"


def parse_npm(payload: dict, target: str) -> tuple[PackageInfo, ...]:
    """Lê somente campos esperados do npm Registry."""
    if not isinstance(payload, dict) or not isinstance(payload.get("objects"), list):
        raise ValueError("Formato de resposta inválido do npm Registry.")
    items = []
    for obj in payload["objects"]:
        if not isinstance(obj, dict):
            continue
        pkg = obj.get("package")
        if not isinstance(pkg, dict):
            continue
        name = pkg.get("name")
        if not isinstance(name, str) or not _PACKAGE.fullmatch(name):
            continue
        items.append(PackageInfo(
            name=name, description=str(pkg.get("description") or "")[:220],
            version=str(pkg.get("version") or ""), source="npm",
            category=category_for(name, target),
        ))
    return tuple(items)


def parse_directory(payload: dict) -> tuple[PackageInfo, ...]:
    """Lê indicadores do RN Directory, preservando desconhecido como None."""
    if not isinstance(payload, dict) or not isinstance(payload.get("libraries"), list):
        raise ValueError("Formato de resposta inválido do React Native Directory.")
    items = []
    for obj in payload["libraries"]:
        if not isinstance(obj, dict):
            continue
        name = obj.get("npmPkg")
        if not isinstance(name, str) or not _PACKAGE.fullmatch(name):
            continue
        github = obj.get("github") or {}
        github = github if isinstance(github, dict) else {}
        meta = obj.get("npm") or {}
        meta = meta if isinstance(meta, dict) else {}
        desc = github.get("description") or ""
        indicator = lambda key: obj.get(key) if type(obj.get(key)) is bool else None
        items.append(PackageInfo(
            name=name, description=str(desc)[:220],
            version=str(meta.get("latestRelease") or ""),
            category=category_for(name, REACT_NATIVE),
            source="directory",
            expo_go=indicator("expoGo"),
            android=indicator("android"),
            ios=indicator("ios"),
            web=indicator("web"),
        ))
    return tuple(items)


def merge_packages(directory: tuple[PackageInfo, ...], npm: tuple[PackageInfo, ...]) -> tuple[PackageInfo, ...]:
    """RN Directory tem precedência para a compatibilidade, npm pode enriquecer texto."""
    indexed = {item.name: item for item in directory}
    for item in npm:
        existing = indexed.get(item.name)
        if existing is None:
            indexed[item.name] = item
        elif existing.source == "directory":
            indexed[item.name] = replace(
                existing, description=existing.description or item.description,
                version=existing.version or item.version,
            )
    return tuple(indexed.values())
