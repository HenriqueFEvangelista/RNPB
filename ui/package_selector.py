"""Componente reutilizável: pesquisa e seleção de bibliotecas para um projeto."""

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QVBoxLayout, QWidget,
)

from core.packages import CATEGORIES, PackageInfo, curated_packages
from core.templates import REACT_NATIVE


class PackageSelector(QWidget):
    search_requested = Signal(str, str)

    def __init__(self, target: str, parent: QWidget | None = None):
        super().__init__(parent)
        self._target = target
        self._selected: dict[str, PackageInfo] = {}
        self._results: tuple[PackageInfo, ...] = ()
        self._updating = False

        layout = QVBoxLayout(self)
        title = QLabel("Bibliotecas opcionais")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        note = QLabel(
            "Escolha bibliotecas para instalar depois de criar o projeto. "
            "A seleção é opcional e pacotes externos podem executar scripts de instalação."
        )
        note.setWordWrap(True)
        note.setObjectName("muted")
        layout.addWidget(note)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Pesquisar pacotes no npm...")
        self.search_input.setObjectName("packageSearch")
        layout.addWidget(self.search_input)

        filters = QHBoxLayout()
        self.category_combo = QComboBox()
        for category in CATEGORIES:
            self.category_combo.addItem(category)
        self.expo_go_only = QCheckBox("Somente compatíveis com Expo Go")
        filters.addWidget(self.category_combo)
        filters.addWidget(self.expo_go_only)
        filters.addStretch()
        layout.addLayout(filters)

        self.results = QListWidget()
        self.results.setObjectName("packageResults")
        self.results.setAlternatingRowColors(True)
        self.results.setMinimumHeight(170)
        layout.addWidget(self.results)

        self.source_label = QLabel("Sugestões locais (compatibilidade não verificada).")
        self.source_label.setObjectName("muted")
        self.source_label.setWordWrap(True)
        layout.addWidget(self.source_label)

        self.selected_label = QLabel("Nenhuma biblioteca selecionada.")
        self.selected_label.setWordWrap(True)
        layout.addWidget(self.selected_label)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(450)
        self._timer.timeout.connect(self._dispatch_search)
        self.search_input.textChanged.connect(self._on_search_changed)
        self.category_combo.currentIndexChanged.connect(self._display)
        self.expo_go_only.toggled.connect(self._display)
        self.results.itemChanged.connect(self._item_changed)

        self.set_target(target)

    @property
    def target(self) -> str:
        return self._target

    @property
    def selected_packages(self) -> tuple[PackageInfo, ...]:
        return tuple(self._selected.values())

    @property
    def selected_names(self) -> tuple[str, ...]:
        return tuple(self._selected)

    def set_target(self, target: str) -> None:
        if target == self._target and self._results:
            return
        curated_packages(target)  # valida destino
        self._target = target
        self._selected.clear()  # não transfere pacotes de plataformas diferentes
        self.expo_go_only.setVisible(target == REACT_NATIVE)
        self.expo_go_only.setChecked(False)
        self._timer.stop()
        self._results = curated_packages(target)
        self.source_label.setText("Sugestões locais. Compatibilidade a verificar na documentação.")
        self._display()
        if len(self.search_input.text().strip()) >= 2:
            self._timer.start()

    def _on_search_changed(self, value: str) -> None:
        self._timer.stop()
        if len(value.strip()) < 2:
            self._results = curated_packages(self._target)
            self.source_label.setText("Sugestões locais. Digite pelo menos 2 caracteres para pesquisar.")
            self._display()
        else:
            self.source_label.setText("Pesquisando…")
            self._timer.start()

    def _dispatch_search(self) -> None:
        query = self.search_input.text().strip()
        if len(query) >= 2:
            self.search_requested.emit(query, self._target)

    def apply_results(self, query: str, target: str, result) -> None:
        if query != self.search_input.text().strip() or target != self._target:
            return
        self._results = result.packages if result.packages else curated_packages(target)
        # Se a pesquisa trouxe metadados mais completos (ex.: Expo Go),
        # atualizar também os itens selecionados anteriormente pelo catálogo local.
        for package in result.packages:
            if package.name in self._selected:
                self._selected[package.name] = package
        if result.warning:
            label = result.warning + " "
            if not result.packages:
                label += "Exibindo sugestões locais."
        else:
            label = "Resultados das APIs." if result.packages else "Nenhum resultado remoto; sugestões locais."
        self.source_label.setText(label)
        self._display()

    def _display(self, *_unused) -> None:
        self._updating = True
        self.results.clear()
        category = self.category_combo.currentText()
        query = self.search_input.text().strip().casefold()
        for package in self._results:
            if category != "Todas" and package.category != category:
                continue
            if self._target == REACT_NATIVE and self.expo_go_only.isChecked() and package.expo_go is not True:
                continue
            if query and query not in (package.name + " " + package.description).casefold():
                continue
            label = package.name
            if package.version:
                label += f" · v{package.version}"
            if self._target == REACT_NATIVE:
                label += f" · {package.compatibility_label}"
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, package)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked if package.name in self._selected else Qt.CheckState.Unchecked)
            item.setToolTip(package.description or "Consulte a documentação antes de instalar.")
            self.results.addItem(item)
        self._updating = False
        self._refresh_count()

    def _item_changed(self, item: QListWidgetItem) -> None:
        if self._updating:
            return
        package = item.data(Qt.ItemDataRole.UserRole)
        if item.checkState() == Qt.CheckState.Checked:
            if len(self._selected) >= 30 and package.name not in self._selected:
                self._updating = True
                item.setCheckState(Qt.CheckState.Unchecked)
                self._updating = False
                self.source_label.setText("Limite de 30 bibliotecas atingido.")
                return
            self._selected[package.name] = package
        else:
            self._selected.pop(package.name, None)
        self._refresh_count()

    def _refresh_count(self) -> None:
        names = list(self._selected)
        self.selected_label.setText(
            f"{len(names)} selecionada(s): {', '.join(names)}"
            if names else "Nenhuma biblioteca selecionada."
        )
