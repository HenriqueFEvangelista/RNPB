"""Catálogo local de templates oficiais e combinações de linguagem aceitas."""

from dataclasses import dataclass


REACT_WEB = "react-web"
REACT_NATIVE = "react-native"
JAVASCRIPT = "javascript"
TYPESCRIPT = "typescript"


@dataclass(frozen=True)
class TemplateSpec:
    id: str
    label: str
    target: str
    language: str


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


def validar_template(target: str, language: str, template_id: str) -> TemplateSpec:
    for template in opcoes_templates(target, language):
        if template.id == template_id:
            return template
    raise ValueError("Template incompatível com a plataforma ou linguagem selecionada.")
