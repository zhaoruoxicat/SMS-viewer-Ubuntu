"""Exercise the actual Debian archive, rather than checking template text."""

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which('dpkg-deb'), 'Debian packaging tools are required')
class DebianPackageTests(unittest.TestCase):
    def test_build_contains_runnable_app_and_declares_native_dependencies(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'dist'
            subprocess.run(['python3', str(ROOT / 'build_deb.py'), '--output-dir', str(output)],
                           check=True, capture_output=True, text=True)
            archives = list(output.glob('*.deb'))
            self.assertEqual(len(archives), 1)
            archive = archives[0]
            metadata = subprocess.check_output(
                ['dpkg-deb', '--field', str(archive)], text=True)
            self.assertIn('Package: sms-forward-client\n', metadata)
            self.assertIn('Architecture: all\n', metadata)
            for dependency in ('python3-pyside6.qtcore', 'python3-pyside6.qtgui',
                               'python3-pyside6.qtwidgets', 'python3-pyside6.qtnetwork'):
                self.assertIn(dependency, metadata)
            extracted = Path(directory) / 'extracted'
            subprocess.run(['dpkg-deb', '--extract', str(archive), str(extracted)], check=True)
            application = extracted / 'usr/share/sms-forward-client'
            self.assertTrue((application / 'sms_client/__main__.py').is_file())
            self.assertEqual((application / 'logo.png').read_bytes(), (ROOT / 'logo.png').read_bytes())
            self.assertEqual((extracted / 'usr/share/pixmaps/sms-forward-client.png').read_bytes(),
                             (ROOT / 'logo.png').read_bytes())
            launcher = extracted / 'usr/bin/sms-forward-client'
            self.assertTrue(os.access(launcher, os.X_OK))
            subprocess.run(['bash', '-n', str(launcher)], check=True)
            self.assertTrue((extracted / 'usr/share/applications/sms-forward-client.desktop').is_file())
            if shutil.which('desktop-file-validate'):
                subprocess.run(['desktop-file-validate', str(extracted / 'usr/share/applications/sms-forward-client.desktop')], check=True)
            environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', QT_QPA_PLATFORM='offscreen')
            version = subprocess.check_output(['/usr/bin/python3', '-m', 'sms_client', '--version'],
                                               cwd=application, env=environment, text=True)
            self.assertEqual(version.strip(), '1.0.3')
            all_paths = [str(path.relative_to(extracted)) for path in extracted.rglob('*')]
            self.assertFalse(any('__pycache__' in path or path.endswith('.pyc') for path in all_paths))
            self.assertFalse(any('config.json' in path or '/tests/' in path or '.venv' in path for path in all_paths))
            listing = subprocess.check_output(['dpkg-deb', '--contents', str(archive)], text=True)
            self.assertIn('root/root', listing)
            self.assertTrue((output / 'SHA256SUMS').is_file())


if __name__ == '__main__':
    unittest.main()
