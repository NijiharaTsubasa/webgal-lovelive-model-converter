import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import call, patch

from converter.llas.face_batch import bake_faces_and_boards


class FaceBatchTests(unittest.TestCase):
    def test_each_model_is_loaded_once_and_sent_to_one_baker(self):
        models = [Path('ordinary-a'), Path('board'), Path('ordinary-b')]
        faces = [SimpleNamespace(needs_merging_face=True),
                 SimpleNamespace(needs_merging_face=False),
                 SimpleNamespace(needs_merging_face=True)]
        with patch('converter.llas.face_batch.load_member_with_face', side_effect=faces) as load, \
             patch('converter.llas.face_batch.bake_face') as ordinary, \
             patch('converter.llas.face_batch.bake_board_face') as board:
            bake_faces_and_boards(models, 'baked', 'unity', 'project', {'cab': ()})
        self.assertEqual(load.call_args_list,
                         [call(model, cab_paths={'cab': ()}) for model in models])
        self.assertEqual([item.args[0] for item in ordinary.call_args_list], [faces[0], faces[2]])
        self.assertEqual(board.call_args.args[:2], (faces[1], models[1]))
        self.assertEqual(board.call_count, 1)


if __name__ == '__main__':
    unittest.main()
