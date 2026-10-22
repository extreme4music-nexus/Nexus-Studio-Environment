"""Render synthetic UI data; never read user projects."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import argparse
from pathlib import Path
import sys
import tempfile
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'modules'))
from PySide6.QtWidgets import QApplication
from nse_runtime.composition import compose_workspace, make_studio_window

parser = argparse.ArgumentParser()
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--tab', choices=('brief', 'sessions', 'decisions'), default='brief')
args = parser.parse_args()
app = QApplication([])
with tempfile.TemporaryDirectory() as folder:
    runtime, service = compose_workspace(Path(folder)); runtime.start()
    try:
        project = service.create('Полноќни скици', 'Топол бас, органски ритам и простор за тишина.\n\nПочнуваме од една мелодија. Ја зачувуваме идејата, па ја развиваме заедно.')
        project = service.add_session(project.project_id, project.revision, 'Прва вечерна сесија', 'Го пробуваме мотивот на пијано. Оставаме простор меѓу фразите.')
        project = service.add_decision(project.project_id, project.revision, 'Да ја задржиме природната динамика на пијаното.', 'Автор', project.sessions[0].session_id)
        service.create('Нови хоризонти')
        window = make_studio_window(app, service)
        window.show_projects(service.list_projects()); window.show_project(project)
        window.tabs.setCurrentIndex(('brief', 'sessions', 'decisions').index(args.tab))
        window.show(); app.processEvents()
        if not window.grab().save(str(args.output)): raise RuntimeError('Preview export failed')
        window.close()
    finally: runtime.stop()
