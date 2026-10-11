import json
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
from types import SimpleNamespace

import convert
from converter.common import normalized_model


class YohaneEntrypointTests(unittest.TestCase):
    def test_yohane_registered_for_conversion_and_full_baking(self):
        root = Path(__file__).parents[1]
        scripts = json.loads((root / 'package.json').read_text(encoding='utf-8'))['scripts']
        self.assertIn('yohane', convert.GAMES)
        self.assertIn('npm run bake:yohane', scripts['convert:full'])
        self.assertEqual(scripts['convert:full:yohane'],
                         'npm run bake:yohane && npm run convert:yohane:clean')
        self.assertIn('--models-only', scripts['bake:yohane:models'])
        self.assertIn('--motions-only', scripts['bake:yohane:motions'])

    def test_material_adapter_receives_current_builder_before_export(self):
        bone = {'name': 'root', 'translation': [0, 0, 0], 'rotation': [0, 0, 0, 1],
                'scale': [1, 1, 1], 'parentIndex': -1, 'isHumanoidCore': False,
                'neutralWorldMatrix': normalized_model._trs_to_mat([0, 0, 0], [0, 0, 0, 1], [1, 1, 1]),
                'hierarchyPath': []}
        transform = SimpleNamespace(m_Children=[])
        adapter = Mock()
        adapter.bind_builder.side_effect = RuntimeError('bound current builder')
        with patch.object(normalized_model, '_validate_skeleton'), \
                patch.object(normalized_model, 'game_object_transform', return_value=transform), \
                patch.object(normalized_model, 'object_id', return_value=(1, 1)), \
                patch.object(normalized_model, '_source_world_matrices', return_value=[bone['neutralWorldMatrix']]), \
                self.assertRaisesRegex(RuntimeError, 'bound current builder'):
            normalized_model.export_normalized_model(None, Mock(),
                                                    {'bones': [bone], 'rootIndex': 0}, adapter)
        builder = adapter.bind_builder.call_args.args[0]
        self.assertIsInstance(builder, normalized_model.GlbBuilder)
        self.assertEqual(builder.document['nodes'][0]['name'], 'root')


if __name__ == '__main__':
    unittest.main()
