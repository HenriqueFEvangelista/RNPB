"""Busca segura de exemplos oficiais Expo e referências comunitárias Vite.

Nenhum repositório encontrado na pesquisa vira automaticamente um comando de
scaffold. Apenas exemplos da organização oficial Expo podem usar --example.
"""

from dataclasses import dataclass
import re
from threading import Lock
from time import monotonic

import requests

from core.templates import (
    JAVASCRIPT, TYPESCRIPT, REACT_NATIVE, REACT_WEB, TemplateSpec,
)

GITHUB_EXPO_EXAMPLES = "https://api.github.com/repos/expo/examples/contents"
GITHUB_REPOSITORY_SEARCH = "https://api.github.com/search/repositories"
CACHE_SECONDS = 600
_EXAMPLE_NAME = re.compile(r"with-[a-z0-9]+(?:-[a-z0-9]+)*\Z")
_REPO_NAME = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z")
_HEADERS = {"Accept": "application/vnd.github+json", "User-Agent": "RNPB-TemplateCatalog"}


@dataclass(frozen=True)
class TemplateSearchResult:
    templates: tuple[TemplateSpec, ...]
    warning: str = ""


def parse_expo_examples(payload: object) -> tuple[TemplateSpec, ...]:
    """Usa apenas diretórios na raiz do repositório oficial expo/examples."""
    if not isinstance(payload, list):
        raise ValueError("Resposta do catálogo oficial Expo inválida.")
    found: dict[str, TemplateSpec] = {}
    for entry in payload:
        if not isinstance(entry, dict):
            continue
        name = entry.get("name")
        if not isinstance(name, str) or not _EXAMPLE_NAME.fullmatch(name):
            continue
        canonical = f"https://github.com/expo/examples/tree/master/{name}"
        if (
            entry.get("type") != "dir"
            or entry.get("path") != name
            or entry.get("html_url") != canonical
        ):
            continue
        found[name] = TemplateSpec(
            id=name,
            label=name.removeprefix("with-").replace("-", " ").title() + " · Expo example",
            target=REACT_NATIVE,
            language=None,  # O exemplo escolhe sua própria linguagem.
            strategy="example",
            source="expo/examples",
            description=f"Exemplo oficial Expo: {name}. A linguagem é definida pelo exemplo.",
            url=canonical,
        )
    return tuple(sorted(found.values(), key=lambda item: item.label.casefold()))


def parse_github_references(payload: object) -> tuple[TemplateSpec, ...]:
    """Repositórios comunitários são referências, nunca executáveis."""
    if not isinstance(payload, dict) or not isinstance(payload.get("items"), list):
        raise ValueError("Resposta da pesquisa GitHub inválida.")
    found: list[TemplateSpec] = []
    for entry in payload["items"][:25]:
        if not isinstance(entry, dict) or entry.get("archived") or entry.get("fork"):
            continue
        fullname = entry.get("full_name")
        if not isinstance(fullname, str) or not _REPO_NAME.fullmatch(fullname):
            continue
        url = f"https://github.com/{fullname}"
        if entry.get("html_url") != url:
            continue
        description = entry.get("description")
        found.append(TemplateSpec(
            id=f"github:{fullname}",
            label=fullname,
            target=REACT_WEB,
            language=None,
            strategy="reference",
            source="github-community",
            description=str(description or "Template comunitário; compatibilidade não verificada.")[:220],
            url=url,
            installable=False,
        ))
        if len(found) >= 12:
            break
    return tuple(found)


class TemplateCatalogService:
    def __init__(self, http_get=None, clock=monotonic):
        self._get = http_get or requests.get
        self._clock = clock
        self._cache: dict[str, tuple[float, tuple[TemplateSpec, ...]]] = {}
        self._lock = Lock()

    def search(self, text: str, target: str, language: str) -> TemplateSearchResult:
        query = text.strip()
        if target not in (REACT_NATIVE, REACT_WEB) or language not in (JAVASCRIPT, TYPESCRIPT):
            raise ValueError("Plataforma ou linguagem inválida.")
        if len(query) > 100:
            raise ValueError("A pesquisa deve ter no máximo 100 caracteres.")
        if len(query) < 2:
            return TemplateSearchResult(())

        # O catálogo Expo é listado inteiro pela API, portanto é compartilhado
        # entre buscas e linguagens e filtrado localmente.
        key = "expo/examples" if target == REACT_NATIVE else f"vite:{query.casefold()}"
        with self._lock:
            cached = self._cache.get(key)
            if cached and self._clock() - cached[0] < CACHE_SECONDS:
                return TemplateSearchResult(self._filter(cached[1], query, target))

        try:
            if target == REACT_NATIVE:
                response = self._get(
                    GITHUB_EXPO_EXAMPLES, headers=_HEADERS, timeout=(4, 8),
                )
            else:
                response = self._get(
                    GITHUB_REPOSITORY_SEARCH,
                    params={
                        "q": f"vite react template {query} in:name,description",
                        "per_page": 15,
                    },
                    headers=_HEADERS, timeout=(4, 8),
                )
            response.raise_for_status()
            raw = response.json()
            items = (
                parse_expo_examples(raw) if target == REACT_NATIVE
                else parse_github_references(raw)
            )
        except (requests.RequestException, ValueError, TypeError) as error:
            return TemplateSearchResult(
                (), f"Catálogo online indisponível ({type(error).__name__}). "
                    "Os templates oficiais locais continuam disponíveis.",
            )

        with self._lock:
            self._cache[key] = (self._clock(), items)
        return TemplateSearchResult(self._filter(items, query, target))

    @staticmethod
    def _filter(
        items: tuple[TemplateSpec, ...], query: str, target: str,
    ) -> tuple[TemplateSpec, ...]:
        q = query.casefold()
        return tuple(
            item for item in items if item.target == target
            and q in (item.id + " " + item.label + " " + item.description).casefold()
        )[:40]
