import contextlib
import io
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import convert
from converter import pipeline


class ConversionCliHelpTests(unittest.TestCase):
    def test_selected_game_help_skips_conversion_and_index_refresh(self):
        with patch.object(sys, 'argv', ['convert', '--game', 'hasunosora', '--help']), \
                patch.object(convert, '_run_game', return_value=0) as run, \
                patch.object(convert, '_merge_top_level_index') as merge:
            self.assertEqual(convert.main(Path('workspace')), 0)
        run.assert_called_once_with('hasunosora', Path('workspace'), extra_args=['--help'])
        merge.assert_not_called()

    def test_selected_game_arguments_reach_child(self):
        with patch.object(sys, 'argv', ['convert', '--game', 'llas', '--model', 'member', '--input', 'source']), \
                patch.object(convert, '_run_game', return_value=0) as run, \
                patch.object(convert, '_merge_top_level_index', return_value=0):
            self.assertEqual(convert.main(Path('workspace')), 0)
        run.assert_called_once_with('llas', Path('workspace'), clean=False,
                                   extra_args=['--model', 'member', '--input', 'source'])

    def test_unscoped_game_arguments_fail_before_any_stage(self):
        with patch.object(sys, 'argv', ['convert', '--model', 'member']), \
                patch.object(convert, '_run_game') as run, contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as error:
                convert.main()
        self.assertEqual(error.exception.code, 2)
        run.assert_not_called()

    def test_top_level_help_does_not_run_or_write(self):
        with patch.object(sys, 'argv', ['convert', '--help']), \
                patch.object(convert, '_run_game') as run, \
                patch.object(convert, '_merge_top_level_index') as merge, \
                contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(convert.main(), 0)
        self.assertIn('--game GAME --help', output.getvalue())
        run.assert_not_called()
        merge.assert_not_called()

    def test_pipeline_help_never_starts_baking(self):
        for flags in ([], ['--game', 'bangdream'], ['--game', 'bangdream', '--bake-only']):
            with self.subTest(flags=flags), patch.object(sys, 'argv', ['pipeline', *flags, '--help']), \
                    patch.object(pipeline.subprocess, 'call') as call, \
                    contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(SystemExit) as error:
                    pipeline.main()
                self.assertEqual(error.exception.code, 0)
                call.assert_not_called()

    def test_bangdream_full_stage_order_and_failure_stop(self):
        with patch.object(sys, 'argv', ['pipeline', '--game', 'bangdream']), \
                patch.object(pipeline.subprocess, 'call', side_effect=[0, 7]) as call:
            self.assertEqual(pipeline.main(), 7)
        self.assertEqual([c.args[0][1:] for c in call.call_args_list], [
            ['-m', 'converter.bake_bangdream', '--models-only'],
            ['-m', 'converter.bake_bangdream_motion'],
        ])

    def test_full_pipeline_preserves_baking_then_clean_conversion(self):
        with patch.object(sys, 'argv', ['pipeline']), \
                patch.object(pipeline.subprocess, 'call', return_value=0) as call:
            self.assertEqual(pipeline.main(), 0)
        self.assertEqual([c.args[0][1:] for c in call.call_args_list], [
            ['-m', 'converter.bake_hasunosora'],
            ['-m', 'converter.bake_bangdream', '--models-only'],
            ['-m', 'converter.bake_bangdream_motion'],
            ['-m', 'converter.bake_llas'],
            ['-m', 'converter.bake_yohane'],
            ['convert.py', '--clean'],
        ])


if __name__ == '__main__':
    unittest.main()
