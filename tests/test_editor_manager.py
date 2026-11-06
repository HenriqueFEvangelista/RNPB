"""Testes do detector, validação e execução sem iniciar IDE real."""

import os
from pathlib import Path
from types import SimpleNamespace

import pytest

import core.editor_manager as module
from core.editor_manager import EditorLaunchError, EditorManager


def make_executable(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("#!/bin/sh\n", encoding="utf-8")
    path.chmod(path.stat().st_mode | 0o111)
    return path


def test_detecta_vscode_no_path(monkeypatch, tmp_path):
    code = make_executable(tmp_path / "code")
    monkeypatch.setattr(module.shutil, "which", lambda command, **_: str(code) if command == "code" else None)
    manager = EditorManager(platform_name="linux", environ={"PATH": str(tmp_path)})
    installation = manager.detect()["vscode"]
    assert installation.executable == code
    assert installation.source == "PATH"


def test_detecta_android_studio_no_windows_por_diretorio(tmp_path):
    studio = make_executable(tmp_path / "Program Files" / "Android" / "Android Studio"
                             / "bin" / "studio64.exe")
    manager = EditorManager(platform_name="win32", environ={
        "ProgramFiles": str(tmp_path / "Program Files"),
        "PATH": "",
    })
    assert manager.detect()["android-studio"].executable == studio


def test_windows_resolve_code_cmd_para_exe(monkeypatch, tmp_path):
    exe = make_executable(tmp_path / "Microsoft VS Code" / "Code.exe")
    make_executable(tmp_path / "Microsoft VS Code" / "bin" / "code.cmd")
    monkeypatch.setattr(module.shutil, "which", lambda command, **_: str(
        tmp_path / "Microsoft VS Code" / "bin" / "code.cmd"
    ) if command == "code" else None)
    manager = EditorManager(platform_name="win32", environ={"PATH": "custom"})
    assert manager.detect()["vscode"].executable == exe


def test_caminho_manual_tem_preferencia_e_valida_nome(tmp_path):
    custom = make_executable(tmp_path / "outro" / "Code.exe")
    manager = EditorManager(platform_name="win32", environ={"PATH": ""})
    manager.set_manual_path("vscode", str(custom))
    assert manager.detect()["vscode"].source == "manual"
    assert manager.detect()["vscode"].executable == custom
    with pytest.raises(ValueError, match="executável"):
        manager.set_manual_path("vscode", str(make_executable(tmp_path / "powershell.exe")))
    assert manager.detect()["vscode"].executable == custom


def test_editor_inexistente_nao_impede_outros(tmp_path):
    manager = EditorManager(platform_name="linux", environ={"PATH": "", "HOME": str(tmp_path)})
    assert not manager.detect()
    with pytest.raises(EditorLaunchError, match="não encontrado"):
        manager.open_project("vscode", tmp_path)


def test_abertura_passando_pasta_unica_sem_shell(monkeypatch, tmp_path):
    exe = make_executable(tmp_path / "code")
    directory = tmp_path / "meu projeto & testes"
    directory.mkdir()
    manager = EditorManager({"vscode": str(exe)}, platform_name="linux", environ={"PATH": ""})
    calls = []

    def fake_popen(args, **kwargs):
        calls.append((args, kwargs))
        return SimpleNamespace(pid=1234)

    monkeypatch.setattr(module.subprocess, "Popen", fake_popen)
    assert manager.open_project("vscode", directory).pid == 1234
    args, kwargs = calls[0]
    assert args == [str(exe), str(directory)]
    assert "shell" not in kwargs or kwargs["shell"] is False
    assert kwargs["close_fds"] is True


def test_falha_ao_iniciar_ide_nao_e_erro_de_projeto(monkeypatch, tmp_path):
    exe = make_executable(tmp_path / "code")
    manager = EditorManager({"vscode": str(exe)}, platform_name="linux", environ={"PATH": ""})
    def failure(*_args, **_kwargs):
        raise OSError("permissão recusada")
    monkeypatch.setattr(module.subprocess, "Popen", failure)
    with pytest.raises(EditorLaunchError, match="permissão recusada"):
        manager.open_project("vscode", tmp_path)


def test_nao_aceita_pasta_inexistente(tmp_path):
    manager = EditorManager(platform_name="linux", environ={"PATH": ""})
    with pytest.raises(EditorLaunchError, match="não existe"):
        manager.open_project("vscode", tmp_path / "inexistente")


def test_identificador_de_editor_invalido():
    with pytest.raises(ValueError, match="desconhecido"):
        EditorManager().set_manual_path("terminal", "bash")
