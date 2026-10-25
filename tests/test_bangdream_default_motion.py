import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from converter.bangdream import build_package_config
from converter.bangdream.default_motion import DefaultMotions


class DefaultMotionTests(unittest.TestCase):
    def test_default_paths_and_michelle_composition_group(self):
        with tempfile.TemporaryDirectory() as tmp:
            defaults = DefaultMotions(Path(tmp), None)
            for name, character, group in [
                ('000_cos_monthly_2023_3', '001', 'garupa'),
                ('015_cos_live_default', '015', 'garupa-michelle'),
                ('015_cos_party_another1', '015', 'garupa-michelle'),
                ('037_cos_live_default', '037', 'garupa'),
                ('601_cos_live_default', '601', 'garupa'),
            ]:
                config = build_package_config(name, [{'role': 'body'}], defaults=defaults.get(name))
                component = config['components'][0]
                self.assertEqual(component['group'], group)
                self.assertEqual(component['motionGroup'], 'garupa')
                self.assertEqual(component['defaultMotion'], f'garupa/characterunique/ch{character}/001')

    def test_first_frame_uses_the_same_entry_clip_as_motion_playback(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / 'input/motions/characterunique/ch037/001'
            source.parent.mkdir(parents=True)
            source.touch()
            baked = root / 'baked/bangdream/motion_000001.baked.json'
            baked.parent.mkdir(parents=True)
            clips = [{'name': name, 'frames': 2, 'tracks': [
                {'bone': 'Hips', 'rotation': [value, 0, 0, 1, 0, 0, 0, 1],
                 'translation': [1, 2, 3, 4, 5, 6]},
            ]} for name, value in [('move_lp', .2), ('move_in', .3)]]
            baked.write_text(json.dumps({'schemaVersion': 8, 'clips': clips}), encoding='utf-8')
            with patch('converter.bangdream.default_motion.controller_program', return_value=None) as program:
                defaults = DefaultMotions(root / 'input', root / 'baked')
                first = defaults.get('037_cos_live_default')
                second = defaults.get('037_cos_other_another2')
            self.assertEqual(first['idlePose'], {'tracks': [
                {'bone': 'Hips', 'rotation': [.3, 0, 0, 1], 'translation': [1, 2, 3]},
            ]})
            self.assertEqual(first, second)
            program.assert_called_once()

    def test_subset_without_default_motion_keeps_default_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            defaults = DefaultMotions(Path(tmp), Path(tmp))
            self.assertEqual(defaults.get('001_cos_live_default'),
                             {'defaultMotion': 'garupa/characterunique/ch001/001'})
