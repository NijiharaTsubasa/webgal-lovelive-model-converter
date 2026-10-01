import contextlib
import io
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from converter import bake_llas, convert_llas
from converter.llas import convert_all
from converter.llas.source_inventory import SourceInventory, active_sources, scan_sources


class CliOutput(io.StringIO):
    def reconfigure(self, **kwargs):
        pass


class LlasEmptyInputTests(unittest.TestCase):
    def setUp(self):
        active_sources.cache_clear()
        scan_sources.cache_clear()

    def tearDown(self):
        active_sources.cache_clear()
        scan_sources.cache_clear()

    def run_cli(self, module, arguments):
        output = CliOutput()
        with patch.object(sys, 'argv', ['command', *arguments]), contextlib.redirect_stdout(output):
            module.main()
        return output.getvalue()

    def test_missing_gitignore_and_database_only_inputs_are_empty(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            placeholder = root / 'placeholder'
            placeholder.mkdir()
            (placeholder / '.gitignore').write_text('*\n!.gitignore\n', encoding='utf-8')
            database_only = root / 'database-only'
            (database_only / 'db').mkdir(parents=True)
            with contextlib.closing(sqlite3.connect(database_only / 'db' / 'asset_a_ja.db')):
                pass
            with patch('converter.llas.source_inventory.UnityPy.load') as load:
                for source in (root / 'missing', placeholder, database_only):
                    with self.subTest(source=source):
                        inventory = active_sources(source)
                        self.assertEqual(inventory.models, ())
                        self.assertEqual(inventory.motions, ())
                load.assert_not_called()

    def test_classification_scan_still_rejects_missing_explicit_path(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(FileNotFoundError):
                scan_sources(Path(temporary) / 'missing')

    def test_empty_bake_skips_unity_and_preserves_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / 'baked'
            output.mkdir()
            marker = output / 'keep.txt'
            marker.write_text('retained', encoding='utf-8')
            for selection in ([], ['--models-only'], ['--motions-only']):
                with self.subTest(selection=selection), patch.object(bake_llas, '_run_unity') as run:
                    result = self.run_cli(bake_llas, [
                        '--input', str(root / 'missing'), '--unity', str(root / 'missing-unity'),
                        '--output', str(output), *selection,
                    ])
                    self.assertIn('输入为空', result)
                    run.assert_not_called()
                    self.assertEqual(marker.read_text(encoding='utf-8'), 'retained')

    def test_empty_clean_conversion_preserves_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / 'output'
            output.mkdir()
            marker = output / 'keep.txt'
            marker.write_text('retained', encoding='utf-8')
            with patch.object(convert_llas, 'convert_all') as convert:
                result = self.run_cli(convert_llas, [
                    '--input', str(root / 'missing'), '--output', str(output), '--clean',
                ])
                convert.assert_not_called()
            self.assertIn('输入为空', result)
            self.assertEqual(marker.read_text(encoding='utf-8'), 'retained')

    def test_empty_conversion_api_does_not_create_output(self):
        with tempfile.TemporaryDirectory() as temporary, contextlib.redirect_stdout(CliOutput()) as output:
            root = Path(temporary)
            self.assertEqual(convert_all(root / 'missing', root / 'output', root / 'baked'), ([], []))
            self.assertIn('输入为空', output.getvalue())
            self.assertFalse((root / 'output').exists())

    def test_motion_only_input_still_requires_model(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            motion = root / 'motion'
            inventory = SourceInventory((), (motion,), {}, {motion: 'idle'}, {}, {})
            with patch.object(bake_llas, 'active_sources', return_value=inventory):
                with self.assertRaisesRegex(SystemExit, 'model is required'):
                    self.run_cli(bake_llas, ['--input', str(root), '--unity', str(root / 'absent')])
            with patch.object(convert_llas, 'active_sources', return_value=inventory):
                with self.assertRaisesRegex(SystemExit, 'require a character model'):
                    self.run_cli(convert_llas, ['--input', str(root), '--clean'])
            with patch('converter.llas.active_sources', return_value=inventory):
                with self.assertRaisesRegex(RuntimeError, 'require a character model'):
                    convert_all(root, root / 'output', root / 'baked')

    def test_explicit_unknown_model_does_not_silently_skip(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for module in (bake_llas, convert_llas):
                with self.subTest(module=module.__name__), self.assertRaisesRegex(ValueError, 'got 0'):
                    self.run_cli(module, ['--input', str(root), '--model', 'not-present'])
            with self.assertRaisesRegex(ValueError, 'got 0'):
                convert_all(root, root / 'output', root / 'baked', model_names=['not-present'])

    def test_model_only_motion_bake_skips_missing_unity(self):
        model = Path('member')
        inventory = SourceInventory((model,), (), {model: 'a_member'}, {}, {}, {})
        with patch.object(bake_llas, 'active_sources', return_value=inventory), \
                patch.object(bake_llas, '_run_unity') as run:
            self.assertIn('输入为空', self.run_cli(bake_llas, ['--motions-only', '--unity', 'absent']))
            run.assert_not_called()

    def test_motion_only_model_bake_skips_missing_unity(self):
        motion = Path('motion')
        inventory = SourceInventory((), (motion,), {}, {motion: 'idle'}, {}, {})
        with patch.object(bake_llas, 'active_sources', return_value=inventory), \
                patch.object(bake_llas, '_run_unity') as run:
            self.assertIn('输入为空', self.run_cli(bake_llas, ['--models-only', '--unity', 'absent']))
            run.assert_not_called()

    def test_bad_bundle_and_permission_errors_are_not_empty_input(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'bad').write_bytes(b'UnityFS\0broken')
            with patch('converter.llas.source_inventory.UnityPy.load', side_effect=ValueError('bad AB')):
                with self.assertRaisesRegex(ValueError, 'bad AB'):
                    active_sources(root)
            active_sources.cache_clear()
            with patch.object(Path, 'stat', side_effect=PermissionError('denied')):
                with self.assertRaises(PermissionError):
                    active_sources(root)


if __name__ == '__main__':
    unittest.main()
