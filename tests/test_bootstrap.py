"""Real installer regression: recover an existing venv created without pip."""
import contextlib
import io
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import venv

import run as launcher
from setup_project import ensure_environment


class BootstrapTests(unittest.TestCase):
    def test_existing_environment_without_pip_is_repaired_and_reused(self):
        with tempfile.TemporaryDirectory(prefix='genshin-bootstrap-') as directory:
            root = Path(directory)
            venv.EnvBuilder(with_pip=False).create(root/'.venv')
            python = root/'.venv'/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
            before = subprocess.run([str(python),'-m','pip','--version'],capture_output=True)
            self.assertNotEqual(before.returncode,0)
            (root/'data').mkdir()
            sentinel = root/'data'/'manual-verification.csv'
            sentinel.write_text('SYNTHETIC USER DATA MUST SURVIVE\n')
            config = root/'config.local.json'
            config.write_text('{"synthetic_user_setting": true}\n')
            repaired = ensure_environment(root)
            after = subprocess.run([str(repaired),'-m','pip','--version'],capture_output=True,text=True)
            self.assertEqual(after.returncode,0,after.stderr)
            self.assertIn('pip ',after.stdout)
            with patch('setup_project.venv.EnvBuilder',side_effect=AssertionError('Must reuse existing venv')):
                self.assertEqual(ensure_environment(root),repaired)
            self.assertEqual(sentinel.read_text(),'SYNTHETIC USER DATA MUST SURVIVE\n')
            self.assertEqual(config.read_text(),'{"synthetic_user_setting": true}\n')
            # Pip is repaired, but Flask is intentionally not installed. Launcher must
            # explain how to finish setup without entering the app or downloading anything.
            error = io.StringIO()
            with patch.object(launcher,'__file__',str(root/'run.py')),patch('run.subprocess.call') as start,contextlib.redirect_stderr(error):
                self.assertEqual(launcher.main([]),1)
            start.assert_not_called()
            self.assertIn('flask',error.getvalue())
            self.assertIn('python setup_project.py',error.getvalue())

    def test_missing_environment_returns_setup_instruction(self):
        with tempfile.TemporaryDirectory() as directory:
            error=io.StringIO()
            with patch.object(launcher,'__file__',str(Path(directory)/'run.py')),contextlib.redirect_stderr(error):
                self.assertEqual(launcher.main([]),1)
            self.assertIn('python setup_project.py',error.getvalue())
