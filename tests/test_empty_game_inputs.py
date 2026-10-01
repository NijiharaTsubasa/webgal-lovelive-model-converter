import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import convert
from converter.bake_bangdream import main as bake_bangdream
from converter.bake_bangdream_motion import main as bake_bangdream_motion
from converter.bake_hasunosora import main as bake_hasunosora
from converter.bangdream import discover_bundle_inputs
from converter.bangdream.motion import discover_motion_bundles
from converter.convert_bangdream import main as convert_bangdream
from converter.hasunosora import convert as convert_hasunosora
from converter.hasunosora.source import discover_inputs


class EmptyGameInputTests(unittest.TestCase):
    def test_bakers_skip_missing_and_placeholder_only_inputs_before_unity(self):
        for baker in (bake_hasunosora, bake_bangdream, bake_bangdream_motion):
            for placeholders in (False, True):
                with self.subTest(baker=baker.__module__, placeholders=placeholders), \
                        tempfile.TemporaryDirectory() as folder:
                    root = Path(folder)
                    source = root / 'input'
                    if placeholders:
                        for relative in ('', 'head', 'costume', 'motions/charactertype'):
                            directory = source / relative
                            directory.mkdir(parents=True, exist_ok=True)
                            (directory / '.gitignore').write_text('*\n', encoding='utf-8')
                    output = io.StringIO()
                    with patch.object(sys, 'argv', ['bake', '--input', str(source),
                                                  '--unity', str(root / 'missing-Unity.exe')]), \
                            contextlib.redirect_stdout(output), patch('subprocess.run') as run:
                        baker()
                    self.assertIn('输入为空', output.getvalue())
                    run.assert_not_called()

    def test_bangdream_hidden_files_are_not_resources(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for relative in ('head', 'costume', 'motions/characterunique/.hidden', 'motions/charactertype'):
                directory = root / relative
                directory.mkdir(parents=True)
                (directory / '.gitignore').touch()
            (root / 'motions/characterunique/.hidden/ignored').touch()
            self.assertEqual(discover_bundle_inputs(root), [])
            self.assertEqual(discover_motion_bundles(root), [])

    def test_invalid_input_path_and_permission_errors_are_not_empty(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            wrong = root / 'file'
            wrong.touch()
            for discover in (discover_inputs, discover_bundle_inputs, discover_motion_bundles):
                with self.subTest(discover=discover.__name__), self.assertRaises(NotADirectoryError):
                    discover(wrong)
                with patch.object(Path, 'stat', side_effect=PermissionError('denied')), \
                        self.assertRaises(PermissionError):
                    discover(root)

    def test_empty_clean_conversion_preserves_existing_outputs(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            output = root / 'output'
            for game in ('hasunosora', 'bangdream'):
                directory = output / game
                directory.mkdir(parents=True)
                (directory / 'keep.txt').write_text('existing output', encoding='utf-8')
            convert_hasunosora(root / 'input_hasunosora', output, None, True)
            with patch.object(sys, 'argv', ['convert', '--input', str(root / 'input_bangdream'),
                                           '--output', str(output / 'bangdream'), '--clean']):
                convert_bangdream()
            for game in ('hasunosora', 'bangdream'):
                self.assertEqual((output / game / 'keep.txt').read_text(encoding='utf-8'), 'existing output')

    def test_hasunosora_dependency_only_input_is_empty(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'dependency.assetbundle').touch()
            convert_hasunosora(root, root / 'output', None, True)
            self.assertFalse((root / 'output').exists())

    def test_hasunosora_motion_without_reference_still_fails(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'mot_current.assetbundle').touch()
            with patch.object(sys, 'argv', ['bake', '--input', str(root)]), \
                    self.assertRaisesRegex(SystemExit, 'reference bundle'):
                bake_hasunosora()

    def test_hasunosora_models_only_conversion_ignores_motion_only_input(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'mot_current.assetbundle').touch()
            convert_hasunosora(root, root / 'output', None, True, models_only=True)
            self.assertFalse((root / 'output').exists())

    def test_hasunosora_model_only_full_bake_does_not_require_motions(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / '3d_costume_001.assetbundle').touch()
            unity = root / 'Unity.exe'
            unity.touch()
            with patch.object(sys, 'argv', ['bake', '--input', str(root), '--unity', str(unity),
                                           '--output', str(root / 'baked')]), \
                    patch('converter.bake_hasunosora.bundle_metadata', return_value=('3d_costume_001', [])), \
                    patch('converter.bake_hasunosora.run_batch') as run:
                bake_hasunosora()
            run.assert_called_once()
            self.assertTrue(run.call_args.kwargs['models_only'])

    def test_top_level_empty_conversion_builds_empty_catalog(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with patch.object(sys, 'argv', ['convert', '--clean']):
                self.assertEqual(convert.main(root), 0)
            self.assertEqual(json.loads((root / 'output_packages/config.json').read_text(encoding='utf-8')),
                             {'components': []})


if __name__ == '__main__':
    unittest.main()
