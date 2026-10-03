import ast
import json
import tempfile
import unittest
from pathlib import Path

from convert import _merge_top_level_index


class ConverterOutputTests(unittest.TestCase):
    def test_converter_has_no_runtime_repository_dependency(self):
        root = Path(__file__).parents[1] / 'converter'
        for source in root.rglob('*.py'):
            tree = ast.parse(source.read_text(encoding='utf-8'))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    self.assertNotIn('dependency_packages', node.module or '', str(source))
                elif isinstance(node, ast.Name):
                    self.assertNotEqual(node.id, 'copy_dependency_package', str(source))

    def test_preview_catalog_excludes_old_runtime_outputs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / 'output_packages'
            for folder, component in [
                ('llas/example', {'type': 'model', 'name': 'example', 'role': 'integrated', 'model': 'model.glb',
                                  'preview': 'data:image/webp;base64,UklGRg=='}),
                ('runtime/llas_runtime', {'type': 'shader', 'name': 'llas-member'}),
            ]:
                target = output / folder
                target.mkdir(parents=True)
                (target / 'config.json').write_text(json.dumps({'components': [component]}), encoding='utf-8')
            _merge_top_level_index(root)
            catalog = json.loads((output / 'config.json').read_text(encoding='utf-8'))
            self.assertEqual([entry['name'] for entry in catalog['components']], ['example'])
            self.assertNotIn('preview', catalog['components'][0])
            source = json.loads((output / 'llas/example/config.json').read_text(encoding='utf-8'))
            self.assertIn('preview', source['components'][0])
            index = json.loads((output / 'index.json').read_text(encoding='utf-8'))
            self.assertEqual(index['configs'], ['llas/example/config.json'])
            self.assertTrue((output / 'runtime/llas_runtime/config.json').exists())
