"""Workers Qt para HTTP: nunca atualizam widgets fora da thread da interface."""

from PySide6.QtCore import QObject, QRunnable, Signal

from core.package_catalog import CatalogService


class CatalogSignals(QObject):
    finished = Signal(int, str, str, object)
    failed = Signal(int, str, str, str)


class CatalogWorker(QRunnable):
    def __init__(self, request_id: int, query: str, target: str, service: CatalogService):
        super().__init__()
        self.request_id = request_id
        self.query = query
        self.target = target
        self.service = service
        self.signals = CatalogSignals()
        self.setAutoDelete(False)

    def run(self) -> None:
        try:
            result = self.service.search(self.query, self.target)
        except Exception as error:
            self.signals.failed.emit(self.request_id, self.query, self.target, str(error))
        else:
            self.signals.finished.emit(self.request_id, self.query, self.target, result)
