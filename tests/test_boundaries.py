import ast
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class BoundaryTests(unittest.TestCase):
    def test_no_implementation_cross_imports(self):
        for package in (ROOT / 'modules').glob('nse_*'):
            for file in package.rglob('*.py'):
                tree = ast.parse(file.read_text(encoding='utf-8'))
                for node in ast.walk(tree):
                    names = ([a.name for a in node.names] if isinstance(node, ast.Import)
                             else [node.module or ''] if isinstance(node, ast.ImportFrom) else [])
                    for name in names:
                        target = name.split('.')[0]
                        allowed = {package.name, 'nse_contracts'}
                        # Only the explicit composition root may import implementations.
                        composition_root = file == ROOT/'modules/nse_runtime/composition.py'
                        self.assertTrue(not target.startswith('nse_') or target in allowed or composition_root,
                                        f'{file}: forbidden import {target}')

    def test_no_legacy_imports(self):
        forbidden = {'nexus_foundation', 'neural_governor', 'latent_engram_stream',
                     'GeneralDualModelAgent', 'cognitive_fusion_engine', 'sensory_cortex'}
        for file in (ROOT/'modules').glob('nse_*/**/*.py'):
            tree = ast.parse(file.read_text(encoding='utf-8'))
            for node in ast.walk(tree):
                names = ([a.name for a in node.names] if isinstance(node, ast.Import)
                         else [node.module or ''] if isinstance(node, ast.ImportFrom) else [])
                for name in names:
                    self.assertNotIn(name.split('.')[0], forbidden, str(file))

    def test_references_ignored(self):
        for module in ('neurafs', 'nexus_core'):
            result = subprocess.run(['git', 'check-ignore', f'modules/{module}/reference/legacy/probe.py'],
                                    cwd=ROOT, capture_output=True)
            self.assertEqual(result.returncode, 0)
