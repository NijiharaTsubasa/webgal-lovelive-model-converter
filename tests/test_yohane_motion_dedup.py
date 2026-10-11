"""Yohane duplicate selection and model-reference regression tests."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from converter.common.motion_binary import encode_motion
from converter.yohane.motion_dedup import deduplicate_motions, resolve_default_motion


def action(name, value=0, speed=1):
    return {'type': 'motion', 'name': name, 'description': name,
            'clips': [{'id': name, 'name': name, 'duration': 1,
                       'sampleRate': 1, 'frames': 2,
                       'tracks': [{'bone': 'Hips', 'rotation': [value, 0, 0, 1] * 2}]}],
            'program': {'layers': [{'id': 'base', 'initialState': name,
                                   'states': [{'id': name, 'clip': name,
                                               'speed': speed, 'loop': True, 'transitions': []}]}]}}


class YohaneMotionDedupTests(unittest.TestCase):
    def write_action(self, root, controller, name, payload):
        path = root / 'motion' / 'yohane' / controller / f'{name}.motionbin'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(encode_motion(payload))
        return path

    def test_normal_priority_unique_variants_and_references(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            normal = 'CH_chika_normal01_story'
            other = 'CH_chika_dinosaur01_story'
            third = 'CH_chika_swimsuit01_story'
            self.write_action(root, normal, 'idle', action('idle'))
            self.write_action(root, other, 'idle', action('idle', value=2e-6))
            self.write_action(root, other, 'angry', action('angry', value=.2))
            self.write_action(root, third, 'angry', action('angry', value=.2))
            self.write_action(root, third, 'run', action('run', speed=2))
            # Identical data for another character must retain its own motion.
            self.write_action(root, 'CH_dia_normal01_story', 'idle', action('idle'))
            config = root / 'yohane' / 'CH_chika_dinosaur01' / 'config.json'
            config.parent.mkdir(parents=True)
            config.write_text(json.dumps({'components': [{'defaultMotion': f'yohane/{other}/idle'}]}), encoding='utf-8')
            mapping = deduplicate_motions(root)
            self.assertEqual(mapping, {f'yohane/{other}/idle': f'yohane/{normal}/idle',
                                       f'yohane/{third}/angry': f'yohane/{other}/angry'})
            self.assertEqual(len(list((root / 'motion').rglob('*.motionbin'))), 4)
            self.assertEqual(json.loads(config.read_text())['components'][0]['defaultMotion'],
                             f'yohane/{normal}/idle')
            self.assertEqual(resolve_default_motion(root, other, 'idle', action('idle')),
                             f'yohane/{normal}/idle')
            self.assertEqual(deduplicate_motions(root), {})

    def test_without_normal_and_identical_actions_with_different_names(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            first = 'CH_ruby_fairy01_story'
            second = 'CH_ruby_petitedevil01_story'
            original = action('run')
            duplicate = action('walk')
            self.write_action(root, second, 'run', original)
            self.write_action(root, first, 'walk', duplicate)
            self.write_action(root, first, 'run', original)
            self.assertEqual(deduplicate_motions(root), {
                f'yohane/{first}/walk': f'yohane/{first}/run',
                f'yohane/{second}/run': f'yohane/{first}/run'})
            self.assertFalse((root / 'motion' / 'yohane' / second).exists())
            self.assertEqual(original, action('run'))

    def test_playback_and_track_differences_are_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            controller = 'CH_you_normal01_story'
            baseline = action('idle')
            variants = [action('pose', value=1e-4), action('speed', speed=2)]
            duration = copy.deepcopy(baseline)
            duration['clips'][0]['duration'] = 2
            variants.append(duration)
            transition = copy.deepcopy(baseline)
            transition['program']['layers'][0]['states'][0]['transitions'] = [
                {'to': 'idle', 'duration': .2, 'exitTime': 1}]
            variants.append(transition)
            bone = copy.deepcopy(baseline)
            bone['clips'][0]['tracks'][0]['bone'] = 'Spine'
            variants.append(bone)
            self.write_action(root, controller, 'idle', baseline)
            for index, payload in enumerate(variants):
                self.write_action(root, controller, f'variant-{index}', payload)
            self.assertEqual(deduplicate_motions(root), {})


if __name__ == '__main__':
    unittest.main()
