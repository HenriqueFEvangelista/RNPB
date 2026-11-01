"""Adaptador Qt assíncrono para execução de CLIs e exibição de seus logs."""

import codecs

from PySide6.QtCore import QObject, QProcess, QTimer, Signal

from core.project_creator import CommandPlan


class ProcessRunner(QObject):
    output = Signal(str)
    started = Signal()
    completed = Signal(str, int)  # success | failed | cancelled, exit code

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        self._process = QProcess(self)
        self._process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self._process.started.connect(self.started.emit)
        self._process.readyReadStandardOutput.connect(self._read_output)
        self._process.errorOccurred.connect(self._error_occurred)
        self._process.finished.connect(self._finished)
        self._decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
        self._active = False
        self._cancel_requested = False

    @property
    def is_running(self) -> bool:
        return self._active

    def run(self, plan: CommandPlan) -> bool:
        if self._active:
            return False
        self._active = True
        self._cancel_requested = False
        self._decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
        self._process.setWorkingDirectory(plan.working_directory)
        self._process.start(plan.program, list(plan.arguments))
        return True

    def cancel(self) -> None:
        if not self._active:
            return
        self._cancel_requested = True
        self.output.emit("\nCancelamento solicitado...\n")
        if self._process.state() != QProcess.ProcessState.NotRunning:
            self._process.terminate()
            QTimer.singleShot(3000, self._force_kill)

    def _force_kill(self) -> None:
        if self._active and self._process.state() != QProcess.ProcessState.NotRunning:
            self._process.kill()

    def _read_output(self) -> None:
        data = bytes(self._process.readAllStandardOutput())
        if data:
            chunk = self._decoder.decode(data)
            if chunk:
                self.output.emit(chunk)

    def _error_occurred(self, error: QProcess.ProcessError) -> None:
        if not self._active:
            return
        if error == QProcess.ProcessError.FailedToStart:
            self.output.emit(f"\nErro ao iniciar o processo: {self._process.errorString()}\n")
            self._complete("cancelled" if self._cancel_requested else "failed", -1)
        elif not self._cancel_requested:
            self.output.emit(f"\nErro de processo: {self._process.errorString()}\n")

    def _finished(self, exit_code: int, exit_status: QProcess.ExitStatus) -> None:
        if not self._active:
            return
        self._read_output()
        final_text = self._decoder.decode(b"", final=True)
        if final_text:
            self.output.emit(final_text)
        if self._cancel_requested:
            status = "cancelled"
        elif exit_code == 0 and exit_status == QProcess.ExitStatus.NormalExit:
            status = "success"
        else:
            status = "failed"
        self._complete(status, exit_code)

    def _complete(self, status: str, exit_code: int) -> None:
        if not self._active:
            return
        self._active = False
        self.completed.emit(status, exit_code)
