import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from converter.bake_bangdream import main, select_template


class BangDreamBakerInputTests(unittest.TestCase):
    def test_template_uses_unity_verdict_and_keeps_later_candidates(self):
        bundles = [(f'{name}.assetbundle', Path(name)) for name in ('no-avatar', 'valid', 'another')]
        seen = []

        def probe(candidates, label):
            seen.append(candidates)
            return 'valid.assetbundle' if bundles[1] in candidates else ''

        self.assertEqual(select_template(bundles, 1, probe), bundles[1])
        self.assertEqual(seen, [[bundles[0]], [bundles[1]]])
        self.assertEqual(len(bundles), 3)

    def test_missing_or_unknown_template_still_fails(self):
        bundles = [('model.assetbundle', Path('model'))]
        with self.assertRaisesRegex(SystemExit, 'No bundled valid Humanoid'):
            select_template(bundles, 2, lambda entries, label: '')
        with self.assertRaisesRegex(RuntimeError, 'unknown Avatar template'):
            select_template(bundles, 2, lambda entries, label: 'outside.assetbundle')

    def test_bakes_each_available_role_without_requiring_other_directory(self):
        for role in ('head', 'costume'):
            with self.subTest(role=role), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                unity = root / 'Unity.exe'
                unity.write_bytes(b'stub')
                managed = root / 'Data/Managed'
                managed.mkdir(parents=True)
                (managed / 'UnityEditor.dll').touch()
                model = root / 'input' / role / 'one'
                model.parent.mkdir(parents=True)
                model.write_bytes(b'AB')
                commands = []

                def run(command, **kwargs):
                    commands.append(command)
                    if '-templateReport' in command:
                        report = Path(command[command.index('-templateReport') + 1])
                        report.write_text(json.dumps({'bundle': f'{role}__one.assetbundle'}), encoding='utf-8')
                    return SimpleNamespace(returncode=0)

                with patch.object(sys, 'argv', ['bake', '--unity', str(unity), '--input', str(root / 'input'),
                                               '--output', str(root / 'output'), '--models-only']), \
                        patch('converter.bake_bangdream.subprocess.run', side_effect=run):
                    main()
                self.assertEqual(len(commands), 2)
                self.assertEqual(commands[0][commands[0].index('-executeMethod') + 1], 'BakePipeline.FindAvatarTemplate')
                self.assertEqual(commands[1][commands[1].index('-executeMethod') + 1], 'BakePipeline.Run')
                self.assertEqual(list((root / 'output').iterdir()), [])

    def test_empty_input_skips_before_requiring_unity(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            unity = root / 'Unity.exe'
            with patch.object(sys, 'argv', ['bake', '--unity', str(unity), '--input', str(root / 'input')]), \
                    patch('converter.bake_bangdream.subprocess.run') as run:
                main()
            run.assert_not_called()


if __name__ == '__main__':
    unittest.main()
