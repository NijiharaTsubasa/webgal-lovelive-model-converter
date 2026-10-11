"""Facial controls from sampled source clips, independent of game assets."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from converter.yohane.face import export_face


class YohaneFaceTests(unittest.TestCase):
    def test_delayed_blink_peak_and_original_state_permissions(self):
        def sample(face, time, close):
            return {'face': face, 'eye': 'f_normal', 'mouth': 'f_normal', 'time': time,
                    'meshes': [{'node': 'head', 'targets': ['normal', 'eye_close'],
                                'weights': [100, close]}]}

        data = {'poses': [sample(name, 0, 0) for name in
                          ('f_normal', 'f_surprise', 'f_happy')],
                'isolatedClips': [sample('f_eye_close', 0, 0),
                                  sample('f_eye_close', .1, 0),
                                  sample('f_eye_close', .5, 0),
                                  sample('f_eye_close', 2.5, 100),
                                  sample('f_eye_close_over', 2.5, 120)]}
        controls = {'f_normal': {'blink': 'f_eye_close', 'speech': None},
                    'f_surprise': {'blink': 'f_eye_close_over', 'speech': None},
                    'f_happy': {'blink': 'f_normal', 'speech': None}}
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'face.json'
            path.write_text(json.dumps(data), encoding='utf-8')
            with patch('converter.yohane.face.controller_controls', return_value=controls):
                result = export_face(path, object())
        states = {state['name']: state for state in result['expressionGroups'][0]['states']}
        self.assertEqual(states['normal']['controls']['blink'], {'eye.close': 1})
        self.assertEqual(states['surprise']['controls']['blink'], {'eye.close': 1.2})
        self.assertNotIn('controls', states['happy'])
        close = next(pose for pose in result['morphPoses'] if pose['name'] == 'eye.close')
        self.assertEqual(close['targets'], {'head': {'eye_close': 1}})


if __name__ == '__main__':
    unittest.main()
