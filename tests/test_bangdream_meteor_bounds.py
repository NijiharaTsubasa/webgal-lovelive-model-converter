import unittest
from types import SimpleNamespace as NS
from unittest.mock import patch

from converter.bangdream.meteor_bounds import attach_renderer_bounds


def vector(x, y, z):
    return NS(x=x, y=y, z=z)


def empty_box():
    return NS(m_Min=vector(float("inf"), float("inf"), float("inf")),
              m_Max=vector(-float("inf"), -float("inf"), -float("inf")))


class Pointer:
    def __init__(self, value=None, *, index=None):
        self.value, self.index = value, index

    def __bool__(self):
        return self.value is not None or self.index is not None

    def deref_parse_as_object(self):
        return self.value


def fixture():
    matrices = []
    def local_matrix(pointer, target):
        assert target is None
        matrix = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, pointer.index, 0, 0, 1]
        matrices.append(pointer)
        return matrix
    exported = NS(builder=NS(document={"nodes": [{} for _ in range(5)]}),
                  node_mapping=NS(node_index=lambda pointer: pointer.index, _local_matrix=local_matrix))
    mesh = NS(m_Name="source", m_BindPose=[object(), object()], m_BonesAABB=[
        NS(m_Min=vector(-2, 1, 0), m_Max=vector(4, 5, 8)),
        NS(m_Min=vector(10, 20, 30), m_Max=vector(12, 24, 36)),
    ])
    renderer = NS(object_reader=NS(path_id=-9123456789012345678),
                  m_Mesh=Pointer(mesh), m_Bones=[Pointer(index=2), Pointer(index=1)],
                  m_RootBone=Pointer(index=0), m_UpdateWhenOffscreen=False,
                  m_AABB=NS(m_Center=vector(1, 2, 3), m_Extent=vector(4, 5, 6)))
    return exported, renderer, matrices


class MeteorBoundsTests(unittest.TestCase):
    def test_preserves_original_bone_order_boxes_and_source_binding(self):
        exported, renderer, calls = fixture()
        attach_renderer_bounds(exported, [(renderer, 4)], role="head")
        result = exported.builder.document["nodes"][4]["extras"]["meteorBounds"]
        self.assertEqual(result["rendererId"], "-9123456789012345678")
        self.assertEqual([x["node"] for x in result["bones"]], ["head:2", "head:1"])
        self.assertEqual(result["bones"][0]["center"], [-1, 3, 4])
        self.assertEqual(result["bones"][0]["extents"], [3, 2, 4])
        self.assertEqual(result["bones"][1]["center"], [-11, 22, 33])
        self.assertEqual(result["root"]["bindMatrix"][12], 0)
        self.assertEqual(result["localBounds"], {"center": [-1, 2, 3], "extents": [4, 5, 6]})
        self.assertFalse(result["updateWhenOffscreen"])
        self.assertEqual(exported.builder.document["nodes"][2]["extras"]["meteorBoundsAnchor"], "head:2")
        self.assertEqual([p.index for p in calls], [2, 1, 0])

    def test_missing_root_uses_original_renderer_transform(self):
        exported, renderer, _ = fixture()
        renderer.m_RootBone = Pointer()
        renderer.m_GameObject = Pointer(NS())
        fallback = Pointer(index=3)
        with patch("converter.bangdream.meteor_bounds.game_object_transform", return_value=fallback):
            attach_renderer_bounds(exported, [(renderer, 4)], role="body")
        self.assertEqual(exported.builder.document["nodes"][4]["extras"]["meteorBounds"]["root"]["node"], "body:3")

    def test_array_mismatch_and_null_bone_are_rejected(self):
        exported, renderer, _ = fixture()
        renderer.m_Bones.pop()
        with self.assertRaisesRegex(ValueError, "do not correspond"):
            attach_renderer_bounds(exported, [(renderer, 4)], role="body")
        exported, renderer, _ = fixture()
        renderer.m_Bones[0] = Pointer()
        with self.assertRaisesRegex(ValueError, "null bone"):
            attach_renderer_bounds(exported, [(renderer, 4)], role="body")

    def test_unused_renderer_tail_does_not_create_or_remove_original_boxes(self):
        exported, renderer, _ = fixture()
        renderer.m_Bones.append(Pointer(index=3))
        decoded = NS(process=lambda: None, m_BoneIndices=[[0, 2, 99]], m_BoneWeights=[[1, 0, 0]])
        with patch("converter.bangdream.meteor_bounds.MeshHandler", return_value=decoded):
            attach_renderer_bounds(exported, [(renderer, 4)], role="body")
        boxes = exported.builder.document["nodes"][4]["extras"]["meteorBounds"]["bones"]
        self.assertEqual([x["node"] for x in boxes], ["body:2", "body:1"])
        exported, renderer, _ = fixture()
        renderer.m_Bones.append(Pointer(index=3))
        decoded.m_BoneWeights = [[0, 1, 0]]
        with patch("converter.bangdream.meteor_bounds.MeshHandler", return_value=decoded):
            with self.assertRaisesRegex(RuntimeError, "references bone"):
                attach_renderer_bounds(exported, [(renderer, 4)], role="body")

    def test_empty_bone_box_has_no_record_anchor_or_binding_matrix(self):
        exported, renderer, calls = fixture()
        renderer.m_Mesh.value.m_BonesAABB[0] = empty_box()
        attach_renderer_bounds(exported, [(renderer, 4)], role="head")
        nodes = exported.builder.document["nodes"]
        boxes = nodes[4]["extras"]["meteorBounds"]["bones"]
        self.assertEqual(boxes, [{"node": "head:1",
            "bindMatrix": [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 1],
            "center": [-11, 22, 33], "extents": [1, 2, 3]}])
        self.assertNotIn("meteorBoundsAnchor", nodes[2].get("extras", {}))
        self.assertEqual([p.index for p in calls], [1, 0])
        self.assertEqual([p.index for p in renderer.m_Bones], [2, 1])

    def test_mixed_boxes_keep_nonempty_source_order_and_values(self):
        baseline, baseline_renderer, _ = fixture()
        attach_renderer_bounds(baseline, [(baseline_renderer, 4)], role="body")
        expected = baseline.builder.document["nodes"][4]["extras"]["meteorBounds"]["bones"]
        exported, renderer, calls = fixture()
        mesh = renderer.m_Mesh.value
        mesh.m_BindPose.insert(1, object())
        mesh.m_BonesAABB.insert(1, empty_box())
        renderer.m_Bones.insert(1, Pointer(index=3))
        attach_renderer_bounds(exported, [(renderer, 4)], role="body")
        nodes = exported.builder.document["nodes"]
        self.assertEqual(nodes[4]["extras"]["meteorBounds"]["bones"], expected)
        self.assertNotIn("meteorBoundsAnchor", nodes[3].get("extras", {}))
        self.assertEqual([p.index for p in calls], [2, 1, 0])

    def test_empty_box_does_not_hide_null_bone_or_malformed_bounds(self):
        exported, renderer, _ = fixture()
        renderer.m_Mesh.value.m_BonesAABB[0] = empty_box()
        renderer.m_Bones[0] = Pointer()
        with self.assertRaisesRegex(ValueError, "null bone"):
            attach_renderer_bounds(exported, [(renderer, 4)], role="body")
        exported, renderer, _ = fixture()
        renderer.m_Mesh.value.m_BonesAABB[0] = empty_box()
        renderer.m_Mesh.value.m_BonesAABB[0].m_Max.x = 0
        with self.assertRaisesRegex(ValueError, "Non-finite"):
            attach_renderer_bounds(exported, [(renderer, 4)], role="body")

    def test_root_binding_survives_when_its_bone_box_is_empty(self):
        exported, renderer, calls = fixture()
        renderer.m_RootBone = renderer.m_Bones[0]
        renderer.m_Mesh.value.m_BonesAABB[0] = empty_box()
        attach_renderer_bounds(exported, [(renderer, 4)], role="head")
        nodes = exported.builder.document["nodes"]
        bounds = nodes[4]["extras"]["meteorBounds"]
        self.assertEqual(bounds["root"]["node"], "head:2")
        self.assertEqual(nodes[2]["extras"]["meteorBoundsAnchor"], "head:2")
        self.assertEqual([entry["node"] for entry in bounds["bones"]], ["head:1"])
        self.assertEqual([p.index for p in calls], [1, 2])

    def test_all_empty_bone_boxes_fail_before_publishing_renderer_bounds(self):
        exported, renderer, calls = fixture()
        renderer.m_Mesh.value.m_BonesAABB = [empty_box(), empty_box()]
        with self.assertRaisesRegex(ValueError, "no nonempty bone boxes"):
            attach_renderer_bounds(exported, [(renderer, 4)], role="body")
        nodes = exported.builder.document["nodes"]
        self.assertNotIn("meteorBounds", nodes[4].get("extras", {}))
        self.assertEqual(calls, [])
        self.assertNotIn("meteorBoundsAnchor", nodes[0].get("extras", {}))
        self.assertNotIn("meteorBoundsAnchor", nodes[1].get("extras", {}))
        self.assertNotIn("meteorBoundsAnchor", nodes[2].get("extras", {}))


if __name__ == "__main__":
    unittest.main()
