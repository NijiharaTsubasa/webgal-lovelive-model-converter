"""Physics geometry follows the same source-to-canonical seam as skinning."""

import math
import unittest
from types import SimpleNamespace

from converter.common.normalized_model import NormalizedNodeMapping, _trs_to_mat
from converter.common.unity import object_id


def matrix(position=(0, 0, 0), rotation=(0, 0, 0, 1), scale=(1, 1, 1)):
    return _trs_to_mat(list(position), list(rotation), list(scale))


class PhysicsMappingTests(unittest.TestCase):
    def setUp(self):
        asset = object()
        self.sources = [SimpleNamespace(object_reader=SimpleNamespace(
            assets_file=asset, path_id=index + 1)) for index in range(3)]

    def mapping(self, canonical, neutral=None, original=None, redirects=None):
        return NormalizedNodeMapping(
            {object_id(source): index for index, source in enumerate(self.sources[:len(canonical)])},
            canonical, neutral or canonical, original or canonical, redirects or {},
        )

    def assertVector(self, actual, expected):
        for left, right in zip(actual, expected):
            self.assertAlmostEqual(left, right, places=10)

    def test_auxiliary_node_preserves_its_local_frame_and_reflects_x(self):
        world = matrix((3, 4, 5), (0, 0, math.sqrt(0.5), math.sqrt(0.5)), (2, 2, 2))
        mapping = self.mapping([world])
        self.assertEqual(mapping.node_index(self.sources[0]), 0)
        self.assertVector(mapping.point(self.sources[0], (1, 2, 3)), (-1, 2, 3))
        self.assertVector(mapping.direction(self.sources[0], (1, 2, 3)), (-1, 2, 3))
        self.assertAlmostEqual(mapping.radius_scale(self.sources[0]), 1)

    def test_core_axis_change_is_applied_after_reflection(self):
        canonical = matrix((4, 5, 6), (0, 0, math.sqrt(0.5), math.sqrt(0.5)))
        neutral = matrix((4, 5, 6))
        mapping = self.mapping([canonical], [neutral])
        self.assertVector(mapping.point(self.sources[0], (0, 1, 0)), (1, 0, 0))
        self.assertVector(mapping.direction(self.sources[0], (1, 0, 0)), (0, 1, 0))
        self.assertAlmostEqual(mapping.radius(self.sources[0], 0.2), 0.2)

    def test_explicit_target_and_directions_ignore_translation(self):
        mapping = self.mapping([matrix((3, 0, 0)), matrix((1, 0, 0))])
        self.assertVector(mapping.point(self.sources[0], (0, 0, 0), 1), (2, 0, 0))
        self.assertVector(mapping.direction(self.sources[0], (0, 1, 0), 1), (0, 1, 0))

    def test_radius_uses_local_relative_scale_not_world_scale_twice(self):
        mapping = self.mapping([matrix(scale=(2, 2, 2))], [matrix(scale=(6, 8, 10))])
        self.assertAlmostEqual(mapping.radius_scale(self.sources[0]), 5)
        self.assertAlmostEqual(mapping.radius(self.sources[0], 0.02), 0.1)
        self.assertVector(mapping.point(self.sources[0], (1, 1, 1)), (-3, 4, 5))

    def test_radius_bounds_shear_not_only_axis_lengths(self):
        shear = matrix()
        shear[4] = 1
        mapping = self.mapping([matrix()], [shear])
        self.assertAlmostEqual(mapping.radius_scale(self.sources[0]), (1 + math.sqrt(5)) / 2)

    def test_redirect_matches_exported_skin_neutral_offset(self):
        mapping = self.mapping(
            [matrix((3, 0, 0)), matrix((5, 0, 0))],
            [matrix((3, 0, 0)), matrix((99, 0, 0))],
            [matrix((1, 0, 0)), matrix((5, 0, 0))],
            {object_id(self.sources[1]): 0},
        )
        self.assertEqual(mapping.node_index(self.sources[1]), 0)
        self.assertVector(mapping.point(self.sources[1], (0, 0, 0)), (4, 0, 0))

    def test_transform_pointer_is_resolved(self):
        mapping = self.mapping([matrix()])
        pointer = SimpleNamespace(deref_parse_as_object=lambda: self.sources[0])
        self.assertEqual(mapping.node_index(pointer), 0)

    def test_plane_normal_uses_inverse_transpose(self):
        mapping = self.mapping([matrix()], [matrix(scale=(2, 1, 1))])
        expected = [-1 / math.sqrt(5), 2 / math.sqrt(5), 0]
        self.assertVector(mapping.normal(self.sources[0], (1, 1, 0)), expected)
        with self.assertRaisesRegex(ValueError, "nonzero"):
            mapping.normal(self.sources[0], (0, 0, 0))

    def test_unmapped_transform_and_invalid_inputs_fail(self):
        mapping = self.mapping([matrix()])
        with self.assertRaisesRegex(ValueError, "absent"):
            mapping.node_index(self.sources[1])
        with self.assertRaisesRegex(ValueError, "Expected a source"):
            mapping.node_index(None)
        with self.assertRaisesRegex(ValueError, "target node"):
            mapping.point(self.sources[0], (0, 0, 0), 3)
        with self.assertRaisesRegex(ValueError, "three-component"):
            mapping.point(self.sources[0], (0, float('nan'), 0))
        with self.assertRaisesRegex(ValueError, "nonnegative"):
            mapping.radius(self.sources[0], -1)


if __name__ == '__main__':
    unittest.main()
