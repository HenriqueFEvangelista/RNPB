import sys

import pytest

pytest.importorskip("PySide6")

from core.process_runner import ProcessRunner
from core.project_creator import CommandPlan


def test_qprocess_sucesso(qtbot, tmp_path):
    runner = ProcessRunner()
    results = []
    logs = []
    runner.completed.connect(lambda status, code: results.append((status, code)))
    runner.output.connect(logs.append)

    plan = CommandPlan(sys.executable, ("-c", "print('ok')"), str(tmp_path))
    with qtbot.waitSignal(runner.completed, timeout=10000):
        assert runner.run(plan)
        assert runner.is_running
        assert not runner.run(plan)

    assert results == [("success", 0)]
    assert "ok" in "".join(logs)
    assert not runner.is_running


def test_qprocess_falha(qtbot, tmp_path):
    runner = ProcessRunner()
    results = []
    runner.completed.connect(lambda status, code: results.append((status, code)))
    plan = CommandPlan(sys.executable, ("-c", "raise SystemExit(7)"), str(tmp_path))
    with qtbot.waitSignal(runner.completed, timeout=10000):
        runner.run(plan)
    assert results == [("failed", 7)]


def test_qprocess_cancelamento(qtbot, tmp_path):
    runner = ProcessRunner()
    results = []
    runner.completed.connect(lambda status, code: results.append((status, code)))
    plan = CommandPlan(
        sys.executable, ("-c", "import time; time.sleep(30)"), str(tmp_path)
    )
    with qtbot.waitSignal(runner.started, timeout=10000):
        runner.run(plan)
    with qtbot.waitSignal(runner.completed, timeout=10000):
        runner.cancel()
    assert results[0][0] == "cancelled"



def test_qprocess_reutilizado_para_geracao_e_instalacao(qtbot, tmp_path):
    """O segundo processo inicia a partir do sinal de término do primeiro."""
    runner = ProcessRunner()
    results = []

    def on_completed(status, code):
        results.append((status, code))
        if len(results) == 1:
            assert runner.run(CommandPlan(
                sys.executable, ("-c", "print('install')"), str(tmp_path)
            ))

    runner.completed.connect(on_completed)
    assert runner.run(CommandPlan(
        sys.executable, ("-c", "print('generate')"), str(tmp_path)
    ))
    qtbot.waitUntil(lambda: len(results) == 2, timeout=10000)
    assert results == [("success", 0), ("success", 0)]
