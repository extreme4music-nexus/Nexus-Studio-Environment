"""Read-only views over the selected immutable Project; no storage calls."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QListWidgetItem, QTextEdit, QLabel


class RecordBrowser(QWidget):
    def __init__(self, kind):
        super().__init__()
        self.kind = kind
        self.project_id = None
        self.records = {}
        self.sessions = {}
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        self.hint = QLabel('Избери проект за преглед.')
        self.hint.setWordWrap(True)
        layout.addWidget(self.hint)
        self.items = QListWidget()
        self.items.setAccessibleName('Сесии' if kind == 'sessions' else 'Одлуки')
        self.items.setMaximumHeight(100)
        self.items.currentItemChanged.connect(self.show_record)
        layout.addWidget(self.items)
        self.detail = QTextEdit()
        self.detail.setReadOnly(True)
        self.detail.setMinimumHeight(150)
        self.detail.setAcceptRichText(False)
        self.detail.setAccessibleName('Детали за сесија' if kind == 'sessions' else 'Детали за одлука')
        layout.addWidget(self.detail, 1)

    def set_project(self, project):
        current = self.items.currentItem()
        previous = current.data(Qt.ItemDataRole.UserRole) if current and self.project_id == project.project_id else None
        self.project_id = project.project_id
        self.sessions = {s.session_id: s for s in project.sessions}
        values = project.sessions if self.kind == 'sessions' else project.decisions
        field = 'session_id' if self.kind == 'sessions' else 'decision_id'
        self.records = {getattr(record, field): record for record in values}
        self.items.clear()
        self.detail.clear()
        label = 'сесии' if self.kind == 'sessions' else 'одлуки'
        self.hint.setText(f'{label.capitalize()}: {len(values)} · Само за преглед' if values else f'Во овој проект сè уште нема {label}.')
        selected = None
        for record in values:
            title = record.title if self.kind == 'sessions' else record.text
            title = ' '.join(title.split())
            item = QListWidgetItem(title[:100] + ('…' if len(title) > 100 else ''))
            identifier = getattr(record, field)
            item.setData(Qt.ItemDataRole.UserRole, identifier)
            self.items.addItem(item)
            if identifier == previous:
                selected = item
        if values:
            self.items.setCurrentItem(selected or self.items.item(0))

    def show_record(self, item, previous=None):
        if item is None:
            self.detail.clear()
            return
        record = self.records[item.data(Qt.ItemDataRole.UserRole)]
        if self.kind == 'sessions':
            text = f'{record.title}\n\nСоздадена: {record.created_at}\n\n{record.summary}'
        else:
            statuses = {'accepted': 'Прифатена', 'proposed': 'Предложена', 'rejected': 'Одбиена'}
            session = self.sessions.get(record.session_id)
            linked = session.title if session else 'Општа одлука за проектот'
            text = (f'{record.text}\n\nСтатус: {statuses[record.status]}'
                    f'\nИзвор: {record.source}\nСоздадена: {record.created_at}\nСесија: {linked}')
        # Plain text prevents project content from being interpreted as HTML or links.
        self.detail.setPlainText(text)
