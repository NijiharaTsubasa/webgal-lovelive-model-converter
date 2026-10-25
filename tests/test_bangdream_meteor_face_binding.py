import math
import unittest
from types import SimpleNamespace as NS
from unittest.mock import patch

from converter.bangdream.meteor_face_binding import head_local_face_frame, finalize_body_face_frame
from converter.common.normalized_model import _trs_to_mat, _mat4_mul


class MeteorFaceBindingTests(unittest.TestCase):
    def assertVector(self, actual, expected):
        for a, b in zip(actual, expected):
            self.assertAlmostEqual(a, b, places=6)

    def test_nonuniform_parent_scale_and_sheared_world_do_not_change_direction(self):
        h = math.sqrt(0.5)
        source_root = _trs_to_mat([2, 3, 4], [0, 0, h, h], [2, 3, 4])
        angle = math.pi / 8
        source_child = _trs_to_mat([1, 2, 3], [math.sin(angle), 0, 0, math.cos(angle)], [1, 1, 1])
        world = _mat4_mul(source_root, source_child)
        # Genuine nonorthogonal world columns: column normalization alone is wrong.
        self.assertGreater(abs(sum(world[4 + i] * world[8 + i] for i in range(3))), 1)
        nodes = [{"rotation": [0, 0, 0, 1], "scale": [8, 2, 3], "children": [1]},
                 {"rotation": [0, h, 0, h], "scale": [5, 6, 7]}]
        result = head_local_face_frame(nodes, 1, [source_root, world])
        self.assertVector(result["up"], [-h, 0, -h])
        self.assertVector(result["forward"], [-h, 0, h])

    def test_same_rotations_give_original_local_axes_despite_different_scales(self):
        h = math.sqrt(0.5)
        nodes = [{"rotation": [h, 0, 0, h], "scale": [9, 2, 4]}]
        source = _trs_to_mat([9, 8, 7], [h, 0, 0, h], [2, 3, 5])
        result = head_local_face_frame(nodes, 0, [source])
        self.assertVector(result["up"], [0, 1, 0])
        self.assertVector(result["forward"], [0, 0, 1])

    def test_unrecovered_local_shear_is_rejected(self):
        matrix = _trs_to_mat([0, 0, 0], [0, 0, 0, 1], [1, 1, 1])
        matrix[4] = 0.3
        with self.assertRaisesRegex(ValueError, "shear"):
            head_local_face_frame([{}], 0, [matrix])

    def test_frame_is_body_only_and_requires_native_binding(self):
        exported = NS(standard_bones={"Head": 0}, builder=NS(document={"nodes": [{}]}),
                      node_mapping=NS(neutral_world=[_trs_to_mat([0, 0, 0], [0, 0, 0, 1], [1, 1, 1])]))
        with patch("converter.bangdream.meteor_face_binding.native_body_face_transform_available", return_value=True) as available:
            finalize_body_face_frame(exported, role="head", prefab_pointer=object())
            available.assert_not_called()
            self.assertNotIn("extras", exported.builder.document["nodes"][0])
            finalize_body_face_frame(exported, role="body", prefab_pointer=object())
            self.assertEqual(exported.builder.document["nodes"][0]["extras"]["meteorFaceFrame"],
                             {"up": [0, 1, 0], "forward": [0, 0, 1]})
        exported.builder.document["nodes"][0].pop("extras")
        with patch("converter.bangdream.meteor_face_binding.native_body_face_transform_available", return_value=False):
            finalize_body_face_frame(exported, role="body", prefab_pointer=object())
            self.assertNotIn("extras", exported.builder.document["nodes"][0])


if __name__ == "__main__":
    unittest.main()
