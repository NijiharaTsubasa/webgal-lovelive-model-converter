import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from converter.bake_yohane import main, motion_references, relay_progress, select_models
from converter.yohane.source import YohaneModelSource


def model(name='CH_person_normal01', controller='CH_person_normal01_story'):
    return YohaneModelSource(name, name, Path('model.bundle'), 'model.prefab', 1,
                             controller, Path('story.bundle'), 'story.controller', (Path('model.bundle'),))


class BakeYohaneTests(unittest.TestCase):
    def test_requested_models_preserve_subset(self):
        one, two = model(), model('CH_person_other01')
        self.assertEqual(select_models([one, two], [two.name]), [two])
        with self.assertRaisesRegex(ValueError, 'Unknown Yohane'):
            select_models([one], ['missing'])

    def test_motion_reference_is_unique_per_controller(self):
        one, two = model(), model('CH_person_other01')
        three = model('CH_other_normal01', 'CH_other_normal01_story')
        self.assertEqual(motion_references([one, two, three]), [one, three])

    def test_empty_input_does_not_resolve_unity(self):
        with tempfile.TemporaryDirectory() as folder, \
             patch('sys.argv', ['bake_yohane', '--input', folder]), \
             patch('converter.bake_yohane.resolve_unity_editor') as editor:
            main()
        editor.assert_not_called()

    def test_relay_only_prints_progress_and_leaves_partial_line(self):
        with tempfile.TemporaryDirectory() as folder:
            log = Path(folder) / 'one.log'
            log.write_text('noise\n[YOHANE_PROGRESS] stage=face\npartial', encoding='utf-8')
            with patch('builtins.print') as output:
                offset = relay_progress(log, 0)
            output.assert_called_once_with('[YOHANE_PROGRESS] stage=face', flush=True)
            with log.open(encoding='utf-8') as stream:
                stream.seek(offset)
                self.assertEqual(stream.read(), 'partial')


if __name__ == '__main__':
    unittest.main()
