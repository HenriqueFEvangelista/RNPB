"""Página de configuração de IDEs e preferências persistentes do usuário."""

from pathlib import Path

from PySide6.QtCore import QSettings, Signal
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QFileDialog, QHBoxLayout, QLabel,
    QMessageBox, QPushButton, QVBoxLayout, QWidget,
)

from core.editor_manager import EDITOR_NAMES, EditorManager


class EditorSettingsView(QWidget):
    settings_changed = Signal()

    def __init__(
        self, manager: EditorManager, settings: QSettings, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self.manager = manager
        self.settings = settings
        self._detected = {}

        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        title = QLabel("Editores")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        description = QLabel(
            "Escolha a IDE para abrir seus projetos. A detecção é automática; "
            "caso necessário, selecione o executável manualmente."
        )
        description.setWordWrap(True)
        description.setObjectName("muted")
        layout.addWidget(description)

        self.editor_combo = QComboBox()
        self.editor_combo.setAccessibleName("Editor preferido")
        layout.addWidget(QLabel("Editor preferido"))
        layout.addWidget(self.editor_combo)

        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        self.status_label.setObjectName("muted")
        layout.addWidget(self.status_label)

        self.auto_checkbox = QCheckBox("Abrir automaticamente após criar o projeto")
        self.auto_checkbox.setChecked(self._bool_setting("editors/auto_open"))
        self.auto_checkbox.toggled.connect(self._save_auto_open)
        layout.addWidget(self.auto_checkbox)

        controls = QHBoxLayout()
        self.browse_button = QPushButton("Localizar executável…")
        self.clear_button = QPushButton("Remover caminho manual")
        self.refresh_button = QPushButton("Detectar novamente")
        controls.addWidget(self.browse_button)
        controls.addWidget(self.clear_button)
        controls.addWidget(self.refresh_button)
        layout.addLayout(controls)
        note = QLabel(
            "A abertura usa a pasta raiz do projeto (inclusive no Expo). "
            "Instalar uma IDE ou iniciar um emulador não é responsabilidade do RNPB."
        )
        note.setObjectName("muted")
        note.setWordWrap(True)
        layout.addWidget(note)
        layout.addStretch()

        self.editor_combo.currentIndexChanged.connect(self._selection_changed)
        self.browse_button.clicked.connect(self.choose_executable)
        self.clear_button.clicked.connect(self.clear_manual_path)
        self.refresh_button.clicked.connect(self.refresh_editors)
        self.refresh_editors()

    def _bool_setting(self, key: str) -> bool:
        value = self.settings.value(key, False)
        return value is True or str(value).lower() in ("true", "1")

    def selected_editor_id(self) -> str:
        return self.editor_combo.currentData() or "vscode"

    def selected_installation(self):
        return self.manager.detect().get(self.selected_editor_id())

    def should_auto_open(self) -> bool:
        return self.auto_checkbox.isChecked() and self.selected_installation() is not None

    def refresh_editors(self) -> None:
        self._detected = self.manager.detect()
        preferred = self.editor_combo.currentData() or self.settings.value(
            "editors/preferred", "vscode"
        )
        self.editor_combo.blockSignals(True)
        self.editor_combo.clear()
        for editor_id, name in EDITOR_NAMES.items():
            suffix = " — detectado" if editor_id in self._detected else " — não encontrado"
            self.editor_combo.addItem(name + suffix, editor_id)
        selected_index = self.editor_combo.findData(preferred)
        self.editor_combo.setCurrentIndex(max(0, selected_index))
        self.editor_combo.blockSignals(False)
        self._selection_changed()

    def _selection_changed(self, *_args) -> None:
        editor_id = self.selected_editor_id()
        self.settings.setValue("editors/preferred", editor_id)
        installation = self._detected.get(editor_id)
        self.auto_checkbox.setEnabled(installation is not None)
        self.clear_button.setEnabled(bool(self.manager.manual_paths.get(editor_id)))
        if installation:
            self.status_label.setText(
                f"Detectado via {installation.source}: {installation.executable}"
            )
        else:
            self.status_label.setText(
                f"{EDITOR_NAMES[editor_id]} não encontrado. "
                "Utilize 'Localizar executável…' para configurar manualmente."
            )
        self.settings_changed.emit()

    def _save_auto_open(self, checked: bool) -> None:
        self.settings.setValue("editors/auto_open", bool(checked))
        self.settings_changed.emit()

    def choose_executable(self) -> None:
        editor_id = self.selected_editor_id()
        path, _ = QFileDialog.getOpenFileName(
            self, f"Localizar executável do {EDITOR_NAMES[editor_id]}",
            str(Path.home()), "Executáveis (*.exe);;Todos os arquivos (*)",
        )
        if not path:
            return
        try:
            self.manager.set_manual_path(editor_id, path)
        except ValueError as exc:
            QMessageBox.warning(self, "Editor inválido", str(exc))
            return
        self.settings.setValue(f"editors/{editor_id}/path", path)
        self.refresh_editors()

    def clear_manual_path(self) -> None:
        editor_id = self.selected_editor_id()
        self.manager.clear_manual_path(editor_id)
        self.settings.remove(f"editors/{editor_id}/path")
        self.refresh_editors()
