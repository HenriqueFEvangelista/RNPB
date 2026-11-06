"""Detecção e abertura segura de editores locais, sem dependência de Qt."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

EDITOR_NAMES = {
    "vscode": "Visual Studio Code",
    "android-studio": "Android Studio",
}

_ALLOWED_BASENAMES = {
    "vscode": {"code.exe", "code-insiders.exe", "code"},
    "android-studio": {"studio64.exe", "studio.exe", "studio.sh", "studio"},
}


class EditorLaunchError(RuntimeError):
    """Editor indisponível, diretório inválido ou falha ao iniciá-lo."""


@dataclass(frozen=True)
class EditorInstallation:
    editor_id: str
    name: str
    executable: Path
    source: str


class EditorManager:
    """Gerencia caminhos locais conhecidos, preferências manuais e lançamento.

    Não executa shell, não procura recursivamente discos e não instala IDEs.
    A persistência das preferências é responsabilidade da camada de interface.
    """

    def __init__(
        self,
        manual_paths: Mapping[str, str] | None = None,
        *,
        platform_name: str | None = None,
        environ: Mapping[str, str] | None = None,
    ) -> None:
        self.manual_paths = dict(manual_paths or {})
        self.platform_name = platform_name or sys.platform
        self.environ = dict(os.environ if environ is None else environ)

    def set_manual_path(self, editor_id: str, executable: str) -> EditorInstallation:
        """Valida um caminho selecionado pelo usuário antes de salvá-lo."""
        self._validate_id(editor_id)
        found = self._candidate(editor_id, executable, "manual")
        if found is None:
            raise ValueError(
                f"Selecione o executável do {EDITOR_NAMES[editor_id]} "
                "(não um atalho, comando ou outra aplicação)."
            )
        self.manual_paths[editor_id] = str(found.executable)
        return found

    def clear_manual_path(self, editor_id: str) -> None:
        self._validate_id(editor_id)
        self.manual_paths.pop(editor_id, None)

    def detect(self) -> dict[str, EditorInstallation]:
        """Retorna somente editores encontrados, com caminho validado."""
        found: dict[str, EditorInstallation] = {}
        for editor_id in EDITOR_NAMES:
            candidates: list[tuple[str, str]] = []
            manual = self.manual_paths.get(editor_id)
            if manual:
                candidates.append((manual, "manual"))

            candidates.extend((candidate, "registro") for candidate in self._registry_paths(editor_id))
            candidates.extend((candidate, "PATH") for candidate in self._path_candidates(editor_id))
            candidates.extend((candidate, "instalação conhecida") for candidate in self._known_paths(editor_id))

            for candidate, source in candidates:
                installation = self._candidate(editor_id, candidate, source)
                if installation is not None:
                    found[editor_id] = installation
                    break
        return found

    def open_project(self, editor_id: str, project_directory: str | Path):
        """Abre a raiz do projeto, inclusive para Expo sem pasta android/."""
        self._validate_id(editor_id)
        directory = Path(project_directory).expanduser().resolve()
        if not directory.is_dir():
            raise EditorLaunchError("A pasta do projeto não existe ou não é um diretório.")
        installation = self.detect().get(editor_id)
        if installation is None:
            raise EditorLaunchError(
                f"{EDITOR_NAMES[editor_id]} não encontrado. Configure o executável em Editores."
            )
        # A pasta é um argumento único: não há shell nem interpolação de comandos.
        try:
            return subprocess.Popen(
                [str(installation.executable), str(directory)],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                close_fds=True,
            )
        except OSError as exc:
            raise EditorLaunchError(
                f"Não foi possível abrir {installation.name}: {exc}"
            ) from exc

    @staticmethod
    def _validate_id(editor_id: str) -> None:
        if editor_id not in EDITOR_NAMES:
            raise ValueError(f"Editor desconhecido: {editor_id}")

    def _candidate(self, editor_id: str, raw: str, source: str) -> EditorInstallation | None:
        if not raw:
            return None
        path = Path(raw).expanduser()
        # A instalação padrão do VS Code no Windows publica code.cmd no PATH.
        # Executamos Code.exe diretamente, sem recorrer ao cmd.exe/shell.
        if self.platform_name == "win32" and path.name.casefold() in (
            "code.cmd", "code-insiders.cmd"
        ):
            exe = "Code - Insiders.exe" if path.name.casefold() == "code-insiders.cmd" else "Code.exe"
            path = path.parent.parent / exe

        if path.name.casefold() not in _ALLOWED_BASENAMES[editor_id]:
            return None
        if self.platform_name == "win32" and path.suffix.lower() != ".exe":
            return None
        if not path.is_file():
            return None
        if self.platform_name != "win32" and not os.access(path, os.X_OK):
            return None
        return EditorInstallation(editor_id, EDITOR_NAMES[editor_id], path.resolve(), source)

    def _path_candidates(self, editor_id: str) -> list[str]:
        commands = (
            ("code", "code.exe", "code.cmd") if editor_id == "vscode"
            else ("studio", "studio64.exe", "studio.exe", "studio.sh")
        )
        candidates = []
        for command in commands:
            found = shutil.which(command, path=self.environ.get("PATH", ""))
            if found:
                candidates.append(found)
        return candidates

    def _known_paths(self, editor_id: str) -> list[str]:
        if self.platform_name == "win32":
            local = self.environ.get("LOCALAPPDATA")
            program_files = self.environ.get("ProgramFiles")
            program_files_x86 = self.environ.get("ProgramFiles(x86)")
            bases = [(key, value) for key, value in (
                ("local", local), ("system", program_files), ("x86", program_files_x86)
            ) if value]
            paths = []
            for kind, base in bases:
                directory = Path(base)
                if editor_id == "vscode":
                    location = ("Programs/Microsoft VS Code" if kind == "local"
                                else "Microsoft VS Code")
                    paths.append(str(directory / location / "Code.exe"))
                else:
                    location = ("Programs/Android Studio" if kind == "local"
                                else "Android/Android Studio")
                    paths.append(str(directory / location / "bin/studio64.exe"))
            return paths
        home = Path(self.environ.get("HOME", str(Path.home())))
        if editor_id == "vscode":
            return ["/usr/bin/code", "/usr/local/bin/code", str(home / ".local/bin/code")]
        return [
            "/opt/android-studio/bin/studio.sh",
            str(home / ".local/share/JetBrains/Toolbox/scripts/studio"),
            "/Applications/Android Studio.app/Contents/MacOS/studio",
        ]

    def _registry_paths(self, editor_id: str) -> list[str]:
        if self.platform_name != "win32":
            return []
        try:
            import winreg
        except ImportError:
            return []
        filenames = ("Code.exe",) if editor_id == "vscode" else ("studio64.exe", "studio.exe")
        found = []
        for root in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
            for filename in filenames:
                try:
                    with winreg.OpenKey(
                        root, rf"Software\Microsoft\Windows\CurrentVersion\App Paths\{filename}"
                    ) as key:
                        value, _ = winreg.QueryValueEx(key, None)
                        if isinstance(value, str):
                            found.append(value.strip('"'))
                except OSError:
                    continue
        return found
