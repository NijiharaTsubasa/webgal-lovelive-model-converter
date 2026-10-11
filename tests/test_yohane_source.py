import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from converter.yohane.source import BundleInfo, dependency_closure, discover_models, read_bundle


class YohaneSourceTests(unittest.TestCase):
    def test_empty_input_is_valid(self):
        with tempfile.TemporaryDirectory() as folder:
            self.assertEqual(discover_models(Path(folder)), [])
            self.assertEqual(discover_models(Path(folder) / 'missing'), [])

    def test_input_file_is_not_treated_as_empty_directory(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'file'
            path.touch()
            with self.assertRaises(NotADirectoryError):
                discover_models(path)

    def test_dependency_closure_uses_serialized_files_not_names(self):
        a, b = Path('random-a.bundle'), Path('random-b.bundle')
        bundles = [BundleInfo(a, ('cab-a',), ('cab-b', 'unity default resources'), ()),
                   BundleInfo(b, ('cab-b',), (), ())]
        self.assertEqual(dependency_closure((a,), bundles), (a, b))

    def test_missing_dependency_identifies_referring_bundle(self):
        root = Path('one.bundle')
        with self.assertRaisesRegex(FileNotFoundError, 'one.bundle.*cab-missing'):
            dependency_closure((root,), [BundleInfo(root, ('cab-one',), ('cab-missing',), ())])

    def test_encrypted_input_is_rejected_without_decryption(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'one.bundle'
            path.write_bytes(b'encrypted data')
            with self.assertRaisesRegex(ValueError, 'decrypted'):
                read_bundle(path)

    def test_recursive_discovery_accepts_compatible_character_controller(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            nested = directory / 'raw'
            nested.mkdir()
            model = nested / 'model.bundle'
            story = directory / 'story.bundle'
            model.touch()
            story.touch()
            prefab = 'CH_person_costume01'
            controller = 'CH_person_normal01_story'
            inventory = {
                model: BundleInfo(model, ('cab-model',), (),
                                  ((f'Assets/Character/{prefab}/{prefab}.prefab', 'GameObject', prefab, 1),), True),
                story: BundleInfo(story, ('cab-story',), (),
                                  ((f'Assets/Character/{controller}/{controller}.controller', 'AnimatorController', controller, 2),)),
            }
            with patch('converter.yohane.source.read_bundle', side_effect=inventory.__getitem__), \
                 patch('converter.yohane.source.UnityPy.load'), \
                 patch('converter.yohane.source.source_prefab'), \
                 patch('converter.yohane.source.has_human_avatar', return_value=True), \
                 patch('converter.yohane.source.controller_idle_clips', return_value=('idle',)):
                result = discover_models(directory)
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0].controller_name, controller)
            self.assertEqual(set(result[0].bundle_paths), {model, story})


if __name__ == '__main__':
    unittest.main()
