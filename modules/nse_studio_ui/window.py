"""UI-thread widgets with one serialized background WorkspacePort operation."""
from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Qt
from PySide6.QtWidgets import (QWidget, QLabel, QPushButton, QLineEdit, QTextEdit,
    QListWidget, QListWidgetItem, QHBoxLayout, QVBoxLayout, QMessageBox, QInputDialog, QTabWidget)
from nse_contracts.workspace import WorkspacePort, WorkspaceError
from .activity import RecordBrowser


class Signals(QObject):
    finished = Signal(object, object)


class Operation(QRunnable):
    def __init__(self, function):
        super().__init__()
        self.function = function
        self.signals = Signals()

    def run(self):
        try:
            result = self.function()
        except Exception as exc:
            self.signals.finished.emit(None, exc)
        else:
            self.signals.finished.emit(result, None)


class StudioWindow(QWidget):
    def __init__(self, workspace: WorkspacePort):
        super().__init__()
        self.workspace = workspace
        self.project = None
        self.busy = False
        self.pool = QThreadPool(self)
        self.pool.setMaxThreadCount(1)
        self.setWindowTitle('Nexus Studio Environment · Projects')
        self.resize(1180, 760)
        self.setMinimumSize(850, 620)
        outer = QHBoxLayout(self)
        outer.setContentsMargins(28, 28, 28, 28)
        outer.setSpacing(28)
        left = QVBoxLayout()
        brand = QLabel('NEXUS'); brand.setObjectName('brand')
        left.addWidget(brand)
        left.addWidget(QLabel('STUDIO ENVIRONMENT'))
        left.addSpacing(24)
        left.addWidget(QLabel('ПРОЕКТИ'))
        self.projects = QListWidget()
        self.projects.setMinimumWidth(260)
        self.projects.itemClicked.connect(self.open_item)
        left.addWidget(self.projects)
        self.new = QPushButton('+ Нов проект')
        self.new.clicked.connect(self.create_dialog)
        self.refresh = QPushButton('Освежи список')
        self.refresh.clicked.connect(self.refresh_projects)
        left.addWidget(self.new); left.addWidget(self.refresh)
        future = QLabel('Следни модули\nNexus · NeuraFS · Audio · Music\nВо подготовка')
        future.setObjectName('muted'); left.addWidget(future)
        outer.addLayout(left, 1)
        right = QVBoxLayout(); right.setSpacing(14)
        title = QLabel('Простор за твојата следна идеја'); title.setObjectName('heading')
        right.addWidget(title)
        subtitle = QLabel('Проектот ги чува насоката, сесиите и одлуките.'); subtitle.setObjectName('muted')
        right.addWidget(subtitle); right.addSpacing(18)
        right.addWidget(QLabel('Име на проект'))
        self.name = QLineEdit(); self.name.setAccessibleName('Име на проект')
        right.addWidget(self.name)
        right.addWidget(QLabel('Содржина на проектот'))
        self.brief = QTextEdit(); self.brief.setAcceptRichText(False)
        self.brief.setAccessibleName('Креативна насока')
        self.brief.setPlaceholderText('Каква музика сакаш да создадеш?')
        self.tabs = QTabWidget()
        self.tabs.setAccessibleName('Содржина на проект')
        self.tabs.addTab(self.brief, 'Креативна насока')
        self.sessions = RecordBrowser('sessions')
        self.decisions = RecordBrowser('decisions')
        self.tabs.addTab(self.sessions, 'Сесии')
        self.tabs.addTab(self.decisions, 'Одлуки')
        right.addWidget(self.tabs, 1)
        self.details = QLabel('Избери проект или создај нов.'); self.details.setWordWrap(True)
        self.details.setObjectName('muted'); right.addWidget(self.details)
        actions = QHBoxLayout()
        self.reload = QPushButton('Вчитај повторно'); self.reload.clicked.connect(self.reload_project)
        self.save = QPushButton('Зачувај измени'); self.save.setObjectName('primary')
        self.save.clicked.connect(self.save_project)
        actions.addWidget(self.reload); actions.addStretch(); actions.addWidget(self.save)
        right.addLayout(actions)
        self.status = QLabel('Подготвено'); self.status.setWordWrap(True)
        self.status.setAccessibleName('Статус'); right.addWidget(self.status)
        outer.addLayout(right, 3)
        self.name.textChanged.connect(self.update_controls)
        self.brief.textChanged.connect(self.update_controls)
        self.update_controls()

    @property
    def dirty(self):
        return self.project is not None and (self.name.text() != self.project.name or
            self.brief.toPlainText() != self.project.creative_brief)

    def confirm_discard(self):
        return not self.dirty or QMessageBox.question(self, 'Незачувани измени',
            'Да ги отфрлам незачуваните измени?', QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No) == QMessageBox.Yes

    def update_controls(self):
        for widget in (self.new, self.refresh, self.projects): widget.setEnabled(not self.busy)
        for widget in (self.name, self.brief, self.reload):
            widget.setEnabled(not self.busy and self.project is not None)
        self.save.setEnabled(not self.busy and self.dirty and bool(self.name.text().strip()))

    def submit(self, function, success):
        if self.busy: return
        self.busy = True
        self.status.setText('Се обработува…')
        self.update_controls()
        operation = Operation(function)
        self.operation = operation
        def finished(result, error):
            self.busy = False
            if error is None:
                success(result)
                self.status.setText('Завршено · податоците се зачувани во Workspace')
            else:
                code = error.code.value if isinstance(error, WorkspaceError) else 'operation_failed'
                self.status.setText(f'Неуспешно: {code}. Текстот останува во уредувачот. '
                    'При конфликт вчитај повторно кога ќе ги зачуваш своите белешки.')
            self.update_controls()
        operation.signals.finished.connect(finished, Qt.ConnectionType.QueuedConnection)
        self.pool.start(operation)

    def refresh_projects(self):
        self.submit(self.workspace.list_projects, self.show_projects)

    def show_projects(self, projects):
        self.projects.clear()
        for project in projects:
            item = QListWidgetItem(project.name)
            item.setData(Qt.ItemDataRole.UserRole, project.project_id)
            self.projects.addItem(item)

    def show_project(self, project):
        self.project = project
        self.name.setText(project.name)
        self.brief.setPlainText(project.creative_brief)
        self.sessions.set_project(project)
        self.decisions.set_project(project)
        self.details.setText(f'Ревизија {project.revision}  ·  Сесии {len(project.sessions)}'
            f'  ·  Одлуки {len(project.decisions)}  ·  Ресурси {len(project.assets)}\n'
            f'Последна промена: {project.updated_at}')
        for index in range(self.projects.count()):
            item = self.projects.item(index)
            if item.data(Qt.ItemDataRole.UserRole) == project.project_id:
                item.setText(project.name)
                self.projects.setCurrentItem(item)
        self.update_controls()

    def open_item(self, item):
        if self.confirm_discard():
            identifier = item.data(Qt.ItemDataRole.UserRole)
            self.submit(lambda: self.workspace.open(identifier), self.show_project)

    def create_dialog(self):
        if not self.confirm_discard(): return
        name, ok = QInputDialog.getText(self, 'Нов проект', 'Име на проект:')
        if ok and name.strip(): self.create_project(name.strip())

    def create_project(self, name):
        def created(project):
            item = QListWidgetItem(project.name)
            item.setData(Qt.ItemDataRole.UserRole, project.project_id)
            self.projects.addItem(item)
            self.show_project(project)
        self.submit(lambda: self.workspace.create(name), created)

    def save_project(self):
        if self.project is None or not self.dirty or not self.name.text().strip(): return
        identifier, revision = self.project.project_id, self.project.revision
        name, brief = self.name.text(), self.brief.toPlainText()
        self.submit(lambda: self.workspace.update(identifier, revision, name=name,
            creative_brief=brief), self.show_project)

    def reload_project(self):
        if self.project is not None and self.confirm_discard():
            identifier = self.project.project_id
            self.submit(lambda: self.workspace.open(identifier), self.show_project)

    def closeEvent(self, event):
        if self.busy:
            self.status.setText('Почекај тековната операција да заврши пред затворање.')
            event.ignore()
        elif self.confirm_discard(): event.accept()
        else: event.ignore()
