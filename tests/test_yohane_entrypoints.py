import json
import shlex
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
from types import SimpleNamespace

import convert
from converter.common import normalized_model
from converter import pipeline


class YohaneEntrypointTests(unittest.TestCase):
    def test_yohane_registered_for_conversion_and_full_baking(self):
        root = Path(__file__).parents[1]
        scripts = json.loads((root / 'package.json').read_text(encoding='utf-8'))['scripts']
        self.assertIn('yohane', convert.GAMES)
        for name in ('convert:full', 'convert:full:yohane'):
            command = shlex.split(scripts[name])
            self.assertEqual(command[:3], ['python', '-m', 'converter.pipeline'])
            with self.subTest(command=name), patch.object(sys, 'argv', ['pipeline', *command[3:]]), \
                    patch.object(pipeline.subprocess, 'call', return_value=0) as call:
                self.assertEqual(pipeline.main(), 0)
            stages = [entry.args[0][1:] for entry in call.call_args_list]
            self.assertIn(['-m', 'converter.bake_yohane'], stages)
            self.assertLess(stages.index(['-m', 'converter.bake_yohane']), len(stages) - 1)
            self.assertEqual(stages[-1], ['convert.py', '--clean'] +
                             (['--game', 'yohane'] if name.endswith(':yohane') else []))
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
