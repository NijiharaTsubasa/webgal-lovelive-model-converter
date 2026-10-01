import unittest
import math
from types import SimpleNamespace

from converter.common.normalized_model import (
    FaceBonesCopierAdapter,
    _lowest_common_node_ancestor,
    _deduplicate_skin_joints,
    _singular_branch_redirect,
    _attach_copied_face_helpers,
    _node_world_matrices,
    _trs_to_mat,
    _mat4_mul,
)


class Pointer:
    def __init__(self, target):
        self.target = target

    def __bool__(self):
        return True

    def deref_parse_as_object(self):
        return self.target


def target(path_id):
    return SimpleNamespace(
        object_reader=SimpleNamespace(assets_file=object(), path_id=path_id)
    )


class FaceBonesCopierAdapterTests(unittest.TestCase):
    def test_local_rotation_copy_preserves_face_eye_spacing_scale_and_helpers(self):
        angle = math.radians(23)
        rotation = [0, math.sin(angle / 2), 0, math.cos(angle / 2)]
        identity = [0, 0, 0, 1]
        def node(position, children=(), quaternion=identity, scale=(1, 1, 1)):
            return {"matrix": _trs_to_mat(position, quaternion, list(scale)), "children": list(children)}
        nodes = [
            node([0, 0, 0], [1, 5]),
            node([0, 1, 0], [2]), node([0, 1, 0], [3]),
            node([.03, 0, 0], [4]), node([0, 0, 0], quaternion=rotation),
            node([0, 0, 0], [6]), node([0, 1, 0], [7]),
            node([.04, 0, 0], [8]), node([0, 0, 0], [9], scale=(2, 3, 4)),
            node([0, .01, 0]),
        ]
        parents = [-1, 0, 1, 2, 3, 0, 5, 6, 7, 8]
        canonical = _node_world_matrices(nodes)
        neutral = [list(value) for value in canonical]
        scales = [[1, 1, 1] for _ in nodes]
        scales[8] = [2, 3, 4]
        keys = {(1, index): index for index in (5, 6, 8)}
        redirects = {(1, 5): 1, (1, 6): 2, (1, 8): 4}
        _attach_copied_face_helpers(nodes, keys, redirects, frozenset(keys),
                                   canonical, neutral, parents, scales, frozenset({(1, 6), (1, 8)}))
        expected = _trs_to_mat([.04, 2, 0], rotation, [2, 3, 4])
        for actual, value in zip(neutral[8], expected):
            self.assertAlmostEqual(actual, value, places=9)
        expected_helper = _mat4_mul(expected, _trs_to_mat([0, .01, 0], identity, [1, 1, 1]))
        for actual, value in zip(_node_world_matrices(nodes)[9], expected_helper):
            self.assertAlmostEqual(actual, value, places=9)

    def test_duplicate_face_rig_targets_redirect_to_standard_humanoid_bones(self):
        face_head = target(101)
        face_neck = target(102)
        component = SimpleNamespace(
            m_Script=Pointer(SimpleNamespace(m_ClassName="FaceBonesCopier")),
            head=Pointer(face_head),
            neck=Pointer(face_neck),
        )
        reader = SimpleNamespace(
            type=SimpleNamespace(name="MonoBehaviour"),
            read=lambda: component,
        )
        adapter = FaceBonesCopierAdapter(SimpleNamespace(objects=[reader]))

        redirects = adapter.bone_redirects({"Head": 9, "Neck": 8})

        self.assertEqual(redirects[(id(face_head.object_reader.assets_file), 101)], 9)
        self.assertEqual(redirects[(id(face_neck.object_reader.assets_file), 102)], 8)

    def test_skin_skeleton_uses_the_lowest_common_joint_ancestor(self):
        nodes = [
            {"children": [1, 4]},
            {"children": [2, 3]},
            {},
            {},
            {},
        ]

        self.assertEqual(_lowest_common_node_ancestor([2, 3], nodes), 1)
        self.assertEqual(_lowest_common_node_ancestor([2, 4], nodes), 0)

    def test_skin_helper_below_collapsed_dummy_redirects_to_humanoid_ancestor(self):
        bones = [
            {"parentIndex": -1, "scale": [1, 1, 1]},
            {"parentIndex": 0, "scale": [1e-12, 1, 1]},
            {"parentIndex": 1, "scale": [1, 17389, 48661]},
        ]

        self.assertEqual(_singular_branch_redirect(bones, 2, {0}), 0)
        self.assertIsNone(_singular_branch_redirect(bones, 0, {0}))

    def test_redirected_skin_joints_are_deduplicated_and_vertex_slots_remapped(self):
        nodes, joints, weights = _deduplicate_skin_joints(
            [7, 9, 7, 12],
            [[0, 1, 2, 3], [2, 2, 1, 0]],
            [[0.1, 0.2, 0.3, 0.4], [0.25, 0.25, 0.5, 0]],
        )

        self.assertEqual(nodes, [7, 9, 12])
        self.assertEqual(joints, [[0, 1, 2, 0], [0, 1, 0, 0]])
        self.assertEqual(weights, [[0.4, 0.2, 0.4, 0], [0.5, 0.5, 0, 0]])


if __name__ == "__main__":
    unittest.main()
