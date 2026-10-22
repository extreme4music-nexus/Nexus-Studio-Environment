import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import sys
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'modules'))
try:
    from PySide6.QtWidgets import QApplication
except ImportError:
    if os.environ.get('NSE_UI_REQUIRED') == '1':
        raise
    QApplication = None


@unittest.skipIf(QApplication is None, 'Install the ui extra for desktop checks')
class StudioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        from nse_runtime.composition import compose_workspace, make_studio_window
        self.temp = tempfile.TemporaryDirectory()
        self.runtime, self.service = compose_workspace(Path(self.temp.name))
        self.runtime.start()
        self.window = make_studio_window(self.app, self.service)
        self.window.show()

    def wait(self):
        deadline = time.monotonic() + 10
        while self.window.busy and time.monotonic() < deadline:
            self.app.processEvents()
            time.sleep(.005)
        self.assertFalse(self.window.busy, 'Background operation did not finish')

    def tearDown(self):
        self.wait()
        with patch.object(self.window, 'confirm_discard', return_value=True): self.window.close()
        self.runtime.stop()
        self.temp.cleanup()

    def create(self):
        self.window.create_project('Мој проект')
        self.wait()
        self.assertEqual(self.window.project.name, 'Мој проект')

    def test_create_edit_save_reopen(self):
        self.create()
        self.window.brief.setPlainText('Љубов, ритам и тишина')
        self.assertTrue(self.window.dirty)
        self.window.save.click(); self.wait()
        self.assertFalse(self.window.dirty)
        project = self.service.open(self.window.project.project_id)
        self.assertEqual(project.creative_brief, 'Љубов, ритам и тишина')
        self.assertEqual(project.revision, 2)
        self.window.refresh.click(); self.wait()
        self.assertEqual(self.window.projects.count(), 1)

    def test_conflict_preserves_editor(self):
        self.create()
        self.service.update(self.window.project.project_id, 1, creative_brief='External')
        self.window.brief.setPlainText('Unsaved local')
        self.window.save.click(); self.wait()
        self.assertTrue(self.window.dirty)
        self.assertEqual(self.window.brief.toPlainText(), 'Unsaved local')
        self.assertIn('revision_conflict', self.window.status.text())
        self.assertEqual(self.service.open(self.window.project.project_id).creative_brief, 'External')

    def test_discard_cancel_and_blank_name(self):
        self.create()
        self.window.name.setText('')
        self.assertFalse(self.window.save.isEnabled())
        with patch.object(self.window, 'confirm_discard', return_value=False):
            self.window.reload_project()
            self.assertFalse(self.window.close())
        self.assertEqual(self.window.name.text(), '')

    def test_worker_is_background_and_busy_close_rejected(self):
        from threading import Event, get_ident
        gate = Event(); main = get_ident(); threads = []
        def work():
            threads.append(get_ident()); gate.wait(2); return ()
        callbacks = []
        self.window.submit(work, lambda result: callbacks.append(get_ident()))
        self.assertFalse(self.window.close())
        self.assertFalse(self.window.new.isEnabled())
        gate.set(); self.wait()
        self.assertNotEqual(threads[0], main)
        self.assertEqual(callbacks, [main])

    def test_io_error_hides_raw_details(self):
        def fail(): raise OSError('private credential should never be displayed')
        self.window.submit(fail, lambda result: None); self.wait()
        self.assertIn('operation_failed', self.window.status.text())
        self.assertNotIn('credential', self.window.status.text())

    def test_bundled_font_has_macedonian_glyphs(self):
        from PySide6.QtGui import QFont, QRawFont
        font = QRawFont.fromFont(QFont('Noto Sans', 14))
        self.assertTrue(font.isValid())
        self.assertTrue(all(font.supportsCharacter(ord(c)) for c in 'ЃѓЌќЉљЊњЏџЅѕ'))

    def populated(self):
        self.create()
        project = self.service.add_session(self.window.project.project_id, 1, 'Прва сесија', 'Ќе пробаме тивок вовед.')
        project = self.service.add_session(project.project_id, project.revision, 'Втора сесија', '<b>Буквален текст</b>\n' + 'Долг опис ' * 1000)
        project = self.service.add_decision(project.project_id, project.revision, 'Остануваме во 6/8', 'Корисник', project.sessions[0].session_id)
        project = self.service.add_decision(project.project_id, project.revision, '<script>Нема извршување</script>', 'Лична белешка', status='proposed')
        project = self.service.add_decision(project.project_id, project.revision, 'Без тапани', 'Корисник', status='rejected')
        self.window.reload.click(); self.wait()
        return project

    def test_activity_details_statuses_and_literal_text(self):
        project = self.populated()
        self.assertEqual(self.window.sessions.items.count(), 2)
        self.assertEqual(self.window.decisions.items.count(), 3)
        self.assertIn('Ќе пробаме', self.window.sessions.detail.toPlainText())
        self.window.sessions.items.setCurrentRow(1)
        self.assertIn('<b>Буквален текст</b>', self.window.sessions.detail.toPlainText())
        self.assertIn('Долг опис ' * 1000, self.window.sessions.detail.toPlainText())
        self.assertTrue(self.window.sessions.detail.isReadOnly())
        detail = self.window.decisions.detail.toPlainText()
        for value in ('6/8', 'Прифатена', 'Корисник', 'Прва сесија', project.decisions[0].created_at):
            self.assertIn(value, detail)
        self.window.decisions.items.setCurrentRow(1)
        for value in ('<script>Нема извршување</script>', 'Предложена', 'Општа одлука'):
            self.assertIn(value, self.window.decisions.detail.toPlainText())
        self.window.decisions.items.setCurrentRow(2)
        self.assertIn('Одбиена', self.window.decisions.detail.toPlainText())

    def test_browsing_preserves_dirty_text_and_does_not_write(self):
        project = self.populated()
        self.window.brief.setPlainText('Незачувана насока')
        for tab in (1, 2, 0):
            self.window.tabs.setCurrentIndex(tab)
        self.window.sessions.items.setCurrentRow(1)
        self.assertTrue(self.window.dirty)
        self.assertEqual(self.window.brief.toPlainText(), 'Незачувана насока')
        self.assertEqual(self.service.open(project.project_id), project)
        self.window.save.click(); self.wait()
        self.assertEqual(self.window.sessions.items.currentRow(), 1)
        self.assertEqual(self.window.sessions.items.count(), 2)
        self.assertEqual(self.window.project.decisions, project.decisions)

    def test_activity_empty_states_and_project_isolation(self):
        from PySide6.QtCore import Qt
        project = self.populated()
        self.window.create_project('Празен проект'); self.wait()
        self.assertEqual(self.window.sessions.items.count(), 0)
        self.assertEqual(self.window.decisions.items.count(), 0)
        self.assertEqual(self.window.sessions.detail.toPlainText(), '')
        self.assertEqual(self.window.decisions.detail.toPlainText(), '')
        self.assertIn('нема сесии', self.window.sessions.hint.text())
        self.assertIn('нема одлуки', self.window.decisions.hint.text())
        item = next(self.window.projects.item(i) for i in range(self.window.projects.count())
                    if self.window.projects.item(i).data(Qt.ItemDataRole.UserRole) == project.project_id)
        self.window.open_item(item); self.wait()
        self.assertEqual(self.window.decisions.items.count(), 3)

    def test_activity_keyboard_navigation(self):
        from PySide6.QtCore import Qt
        from PySide6.QtTest import QTest
        self.populated()
        self.window.tabs.setCurrentIndex(1)
        self.window.sessions.items.setFocus()
        QTest.keyClick(self.window.sessions.items, Qt.Key.Key_Down)
        self.assertEqual(self.window.sessions.items.currentRow(), 1)
        self.assertIn('Буквален текст', self.window.sessions.detail.toPlainText())
