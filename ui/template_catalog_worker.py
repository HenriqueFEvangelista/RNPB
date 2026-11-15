"""Pesquisa de templates executada fora da thread da interface."""

from PySide6.QtCore import QObject, QRunnable, Signal

from core.template_catalog import TemplateCatalogService


class TemplateCatalogSignals(QObject):
    finished = Signal(int, str, str, str, object)
    failed = Signal(int, str, str, str, str)


class TemplateCatalogWorker(QRunnable):
    def __init__(
        self, request_id: int, query: str, target: str, language: str,
        service: TemplateCatalogService,
    ):
        super().__init__()
        self.request_id = request_id
        self.query = query
        self.target = target
        self.language = language
        self.service = service
        self.signals = TemplateCatalogSignals()
        self.setAutoDelete(False)

    def run(self) -> None:
        try:
            result = self.service.search(self.query, self.target, self.language)
        except Exception as error:
            self.signals.failed.emit(
                self.request_id, self.query, self.target, self.language, str(error),
            )
        else:
            self.signals.finished.emit(
                self.request_id, self.query, self.target, self.language, result,
            )
