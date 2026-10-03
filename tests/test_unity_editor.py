import importlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from converter.common import unity_editor


class UnityEditorDiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.appdata = self.root / 'appdata'
        self.registry = self.appdata / 'UnityHub' / 'editors-v2.json'
        self.registry.parent.mkdir(parents=True)
        self.env = patch.dict(os.environ, {'APPDATA': str(self.appdata), 'PATH': ''}, clear=True)
        self.env.start()
        self.addCleanup(self.env.stop)
        for name in ('run', 'Popen'):
            process_patch = patch(f'subprocess.{name}', side_effect=AssertionError('Discovery must not launch programs'))
            process_patch.start()
            self.addCleanup(process_patch.stop)

    def executable(self, folder, *, editor=True, mac=False):
        path = self.root / folder / ('MacOS/Unity' if mac else 'Unity.exe')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()
        if editor:
            managed = path.parent.parent / 'Managed' if mac else path.parent / 'Data' / 'Managed'
            managed.mkdir(parents=True)
            (managed / 'UnityEditor.dll').touch()
        return path

    def hub(self, entries):
        self.registry.write_text(json.dumps({'data': entries}), encoding='utf-8')

    def entry(self, executable, version='2022.3.62f2'):
        return {'version': version, 'location': [str(executable)]}

    def assert_resolution_error(self, explicit=None):
        with self.assertRaises(SystemExit) as caught:
            unity_editor.resolve_unity_editor(explicit)
        self.assertRegex(str(caught.exception), r'Unity|UNITY_EDITOR|Editor')

    def test_path_skips_cli_before_real_editor(self):
        cli = self.executable('cli', editor=False)
        editor = self.executable('editor')
        os.environ['PATH'] = os.pathsep.join([str(cli.parent), str(editor.parent)])
        self.assertEqual(unity_editor.default_unity_editor(), editor)
        self.assertEqual(unity_editor.resolve_unity_editor(None), editor)

    def test_cli_on_path_uses_hub_editor(self):
        cli = self.executable('cli', editor=False)
        editor = self.executable('hub-editor')
        os.environ['PATH'] = str(cli.parent)
        self.hub([self.entry(editor)])
        self.assertEqual(unity_editor.default_unity_editor(), editor)

    def test_only_cli_reports_no_editor_without_running_cli(self):
        cli = self.executable('cli', editor=False)
        os.environ['PATH'] = str(cli.parent)
        self.assertIsNone(unity_editor.default_unity_editor())
        self.assert_resolution_error()

    def test_environment_editor_precedes_path_and_hub(self):
        selected = self.executable('environment-editor')
        other = self.executable('other-editor')
        os.environ.update(UNITY_EDITOR=str(selected), PATH=str(other.parent))
        self.hub([self.entry(other)])
        self.assertEqual(unity_editor.default_unity_editor(), selected)
        self.assertEqual(unity_editor.resolve_unity_editor(None), selected)

    def test_invalid_environment_does_not_silently_fall_back(self):
        other = self.executable('other-editor')
        cli = self.executable('cli', editor=False)
        os.environ['PATH'] = str(other.parent)
        self.hub([self.entry(other)])
        for invalid in (self.root / 'missing.exe', cli):
            with self.subTest(invalid=invalid):
                os.environ['UNITY_EDITOR'] = str(invalid)
                self.assertEqual(unity_editor.default_unity_editor(), invalid)
                self.assert_resolution_error()

    def test_explicit_editor_precedes_environment(self):
        explicit = self.executable('explicit-editor')
        os.environ['UNITY_EDITOR'] = str(self.root / 'missing.exe')
        self.assertEqual(unity_editor.resolve_unity_editor(explicit), explicit)

    def test_invalid_explicit_editor_does_not_fall_back(self):
        other = self.executable('environment-editor')
        cli = self.executable('cli', editor=False)
        os.environ['UNITY_EDITOR'] = str(other)
        for invalid in (self.root / 'missing.exe', cli):
            with self.subTest(invalid=invalid):
                self.assert_resolution_error(invalid)

    def test_hub_ignores_stale_path_and_cli(self):
        cli = self.executable('cli', editor=False)
        expected = self.executable('hub-editor')
        self.hub([
            self.entry(self.root / 'uninstalled' / 'Unity.exe'),
            self.entry(cli),
            self.entry(expected),
        ])
        self.assertEqual(unity_editor.default_unity_editor(), expected)

    def test_hub_accepts_installed_version_without_project_version_filter(self):
        editor = self.executable('newer-editor')
        self.hub([self.entry(editor, '6000.0.99f1')])
        self.assertEqual(unity_editor.default_unity_editor(), editor)
        self.assertEqual(unity_editor.resolve_unity_editor(None), editor)

    def test_malformed_hub_json_is_ignored(self):
        self.registry.write_text('{broken JSON', encoding='utf-8')
        self.assertIsNone(unity_editor.default_unity_editor())
        self.assert_resolution_error()

    def test_editor_mac_bundle_layout(self):
        editor = self.executable('Unity.app/Contents', mac=True)
        os.environ['PATH'] = str(editor.parent)
        self.assertEqual(unity_editor.default_unity_editor(), editor)
        self.assertEqual(unity_editor.resolve_unity_editor(editor), editor)

    def test_import_without_editor_does_not_require_resolving_one(self):
        importlib.reload(unity_editor)
        # Importing the helper, including from CLI --help paths, must remain lazy.
        self.assertIsNone(unity_editor.default_unity_editor())
        self.assert_resolution_error()


if __name__ == '__main__':
    unittest.main()
