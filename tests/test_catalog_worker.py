"""Verifica que a consulta HTTP é encaminhada a uma thread Qt."""

import threading

import pytest
pytest.importorskip("PySide6")

from PySide6.QtCore import QThreadPool

from core.package_catalog import CatalogResult
from core.packages import PackageInfo
from core.templates import REACT_WEB
from ui.catalog_worker import CatalogWorker


class FakeCatalog:
    def __init__(self):
        self.thread_id = None

    def search(self, text, target):
        self.thread_id = threading.get_ident()
        assert text == "axios"
        assert target == REACT_WEB
        return CatalogResult((PackageInfo("axios", source="npm"),))


def test_worker_runs_off_ui_thread_and_emits_result(qtbot):
    main_thread = threading.get_ident()
    service = FakeCatalog()
    pool = QThreadPool()
    pool.setMaxThreadCount(1)
    worker = CatalogWorker(17, "axios", REACT_WEB, service)
    result = []
    worker.signals.finished.connect(
        lambda seq, query, target, data: result.append((seq, query, target, data))
    )
    with qtbot.waitSignal(worker.signals.finished, timeout=10000):
        pool.start(worker)
    assert service.thread_id != main_thread
    assert result[0][:3] == (17, "axios", REACT_WEB)
    assert result[0][3].packages[0].name == "axios"
    pool.waitForDone(10000)
