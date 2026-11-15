"""Catálogo local de templates oficiais e combinações de linguagem aceitas."""

from dataclasses import dataclass
import re


REACT_WEB = "react-web"
REACT_NATIVE = "react-native"
JAVASCRIPT = "javascript"
TYPESCRIPT = "typescript"


@dataclass(frozen=True)
class TemplateSpec:
    id: str
    label: str
    target: str
    language: str | None
    strategy: str = "template"  # template, example ou reference
    source: str = "official"
    description: str = ""
    url: str = ""
    installable: bool = True


# Manter IDs alinhados com os geradores oficiais (Vite/Expo).
TEMPLATES = (
    TemplateSpec("blank", "Blank · mínimo", REACT_NATIVE, JAVASCRIPT),
    TemplateSpec("blank-typescript", "Blank · TypeScript", REACT_NATIVE, TYPESCRIPT),
    TemplateSpec("default", "Default · Expo Router", REACT_NATIVE, TYPESCRIPT),
    TemplateSpec("tabs", "Tabs · Expo Router", REACT_NATIVE, TYPESCRIPT),
    TemplateSpec("react", "React · padrão", REACT_WEB, JAVASCRIPT),
    TemplateSpec("react-compiler", "React Compiler", REACT_WEB, JAVASCRIPT),
    TemplateSpec("react-ts", "React · TypeScript", REACT_WEB, TYPESCRIPT),
    TemplateSpec("react-compiler-ts", "React Compiler · TypeScript", REACT_WEB, TYPESCRIPT),
)


def opcoes_templates(target: str, language: str) -> tuple[TemplateSpec, ...]:
    if target not in (REACT_WEB, REACT_NATIVE):
        raise ValueError("Plataforma não suportada.")
    if language not in (JAVASCRIPT, TYPESCRIPT):
        raise ValueError("Linguagem não suportada.")
    return tuple(item for item in TEMPLATES if item.target == target and item.language == language)


_EXAMPLE_ID = re.compile(r"with-[a-z0-9]+(?:-[a-z0-9]+)*\Z")


def _official_expo_example(item: TemplateSpec) -> bool:
    """Apenas diretórios do catálogo oficial Expo autorizam --example."""
    return (
        item.strategy == "example"
        and item.target == REACT_NATIVE
        and item.language is None
        and item.source == "expo/examples"
        and item.installable
        and isinstance(item.id, str)
        and _EXAMPLE_ID.fullmatch(item.id) is not None
        and item.url == f"https://github.com/expo/examples/tree/master/{item.id}"
    )


def validar_template(
    target: str, language: str, template_id: str,
    external: tuple[TemplateSpec, ...] = (),
) -> TemplateSpec:
    """Valida templates locais ou exemplos oficiais aprovados pelo catálogo."""
    for template in opcoes_templates(target, language):
        if template.id == template_id:
            return template
    for item in external:
        if (
            isinstance(item, TemplateSpec)
            and item.id == template_id
            and item.target == target
            and (item.language is None or item.language == language)
            and _official_expo_example(item)
        ):
            return item
    raise ValueError("Template incompatível com a plataforma ou linguagem selecionada.")
