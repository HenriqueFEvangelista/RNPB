"""Consulta npm Registry + React Native Directory com fallback e cache em memória."""

from dataclasses import dataclass
from threading import Lock
from time import monotonic

import requests

from core.packages import PackageInfo, merge_packages, parse_directory, parse_npm
from core.templates import REACT_NATIVE, REACT_WEB

NPM_SEARCH = "https://registry.npmjs.org/-/v1/search"
DIRECTORY_SEARCH = "https://reactnative.directory/api/libraries"
CACHE_SECONDS = 600


@dataclass(frozen=True)
class CatalogResult:
    packages: tuple[PackageInfo, ...]
    warning: str = ""


class CatalogService:
    def __init__(self, http_get=None, clock=monotonic):
        self._get = http_get or requests.get
        self._clock = clock
        self._cache: dict[tuple[str, str], tuple[float, CatalogResult]] = {}
        self._lock = Lock()

    def search(self, text: str, target: str) -> CatalogResult:
        query = text.strip()
        if target not in (REACT_WEB, REACT_NATIVE):
            raise ValueError("Plataforma inválida.")
        if len(query) > 100:
            raise ValueError("A busca deve ter até 100 caracteres.")
        if len(query) < 2:
            return CatalogResult(())

        key = (query.casefold(), target)
        with self._lock:
            cached = self._cache.get(key)
            if cached and self._clock() - cached[0] < CACHE_SECONDS:
                return cached[1]

        npm = ()
        directory = ()
        warnings = []
        try:
            response = self._get(NPM_SEARCH, params={"text": query, "size": 20}, timeout=(4, 8))
            response.raise_for_status()
            npm = parse_npm(response.json(), target)
        except (requests.RequestException, ValueError, TypeError) as error:
            warnings.append(f"npm indisponível ({type(error).__name__}).")

        if target == REACT_NATIVE:
            try:
                response = self._get(
                    DIRECTORY_SEARCH, params={"search": query, "limit": 20, "skipTools": "true"},
                    timeout=(4, 8),
                )
                response.raise_for_status()
                directory = parse_directory(response.json())
            except (requests.RequestException, ValueError, TypeError) as error:
                warnings.append(f"React Native Directory indisponível ({type(error).__name__}).")

        packages = merge_packages(directory, npm) if target == REACT_NATIVE else npm
        result = CatalogResult(packages, " ".join(warnings))
        # Falhas totais não são armazenadas como respostas válidas.
        if packages:
            with self._lock:
                self._cache[key] = (self._clock(), result)
        return result
