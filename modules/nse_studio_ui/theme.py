"""Shared logical pixel tokens and bundled Cyrillic font."""
from pathlib import Path
from PySide6.QtGui import QFontDatabase
TOKENS = {'background': '#11151c', 'panel': '#1b222d', 'text': '#e7edf5',
          'muted': '#aab9cb', 'accent': '#edba72', 'border': '#354153'}


def apply_theme(app):
    app.setStyle('Fusion')
    font_id = QFontDatabase.addApplicationFont(str(Path(__file__).parent/'assets/NotoSans.ttf'))
    if font_id < 0:
        raise RuntimeError('Bundled Studio font could not be loaded')
    app.setStyleSheet('''
        QWidget { background:#11151c; color:#e7edf5; font-family:"Noto Sans"; font-size:14px; }
        QLabel#brand { font-size:28px; font-weight:700; color:#edba72; }
        QLabel#heading { font-size:24px; font-weight:600; }
        QLabel#muted { color:#aab9cb; }
        QListWidget, QLineEdit, QTextEdit { background:#1b222d; border:1px solid #354153;
            border-radius:6px; padding:10px; selection-background-color:#405575; }
        QListWidget::item { padding:14px; border-bottom:1px solid #354153; }
        QListWidget::item:selected { background:#405575; }
        QPushButton { background:#283443; border:1px solid #52627a; border-radius:6px;
            padding:10px 18px; }
        QPushButton:hover { border-color:#edba72; }
        QPushButton:focus { border:2px solid #edba72; }
        QPushButton#primary { background:#edba72; color:#11151c; font-weight:600; }
        QPushButton:disabled { color:#778496; background:#202833; }
        QPushButton#primary:disabled { color:#778496; background:#202833; }
    ''')
