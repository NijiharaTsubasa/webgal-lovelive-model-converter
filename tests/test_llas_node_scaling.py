import unittest
from types import SimpleNamespace as NS
from unittest.mock import patch

from converter.llas.node_scaling import scaling_for_member


class LlasNodeScalingTests(unittest.TestCase):
    def make_face(self):
        def pointer(value):
            return NS(read=lambda: value)

        child = NS(key=2, m_Children=[])
        root = NS(key=1, m_Children=[pointer(child)])
        fields = {
            "scaleValues": [{"target": child, "scaledValue": dict(x=.927, y=.927, z=.927)}],
            "positionValues": [{"target": child, "scaledValue": dict(x=1, y=2, z=3)}],
            "rotationValues": [{"target": child, "scaledValue": dict(x=0, y=276.48, z=270)}],
            # This is camera data; it must not multiply the authored body scales.
            "heightScale": .92024,
        }
        component = NS(m_Script=True, m_GameObject=pointer(NS(transform=root)))
        reader = NS(type=NS(name="MonoBehaviour"), read=lambda: component,
                    read_typetree=lambda: fields)
        component.object_reader = reader
        return NS(root=pointer(NS(transform=root,m_Component=[NS(component=reader)])), name="member",
                  head_all=None, needs_merging_face=True, environment=NS(objects=[reader]))

    def plan(self, face, graft=True):
        with patch("converter.llas.node_scaling.component_pointer", side_effect=lambda obj: obj.component), \
             patch("converter.llas.node_scaling.object_id", side_effect=lambda obj: obj.key), \
             patch("converter.llas.node_scaling.game_object_transform", side_effect=lambda obj: obj.transform), \
             patch("converter.llas.node_scaling._class", return_value="LiveCoreMemberNodeScaling"), \
             patch("converter.llas.node_scaling._pointer", side_effect=lambda reader, obj: NS(read=lambda: obj)), \
             patch("converter.llas.node_scaling.needs_face_graft", return_value=graft):
            return scaling_for_member(face)

    def test_authored_trs_uses_hierarchy_paths_and_scaled_endpoints(self):
        plan = self.plan(self.make_face())
        self.assertEqual(plan["scaleValues"], [{"path": [0], "value": [.927, .927, .927]}])
        self.assertEqual(plan["positionValues"], [{"path": [0], "value": [1., 2., 3.]}])
        self.assertEqual(plan["rotationValues"], [{"path": [0], "value": [0., 276.48, 270.]}])
        self.assertEqual(set(plan), {"name", "scaleValues", "positionValues", "rotationValues"})

    def test_already_assembled_face_keeps_authored_transforms(self):
        plan = self.plan(self.make_face(), graft=False)
        for field in ("scaleValues", "positionValues", "rotationValues"):
            self.assertEqual(plan[field], [])

    def test_scaling_on_a_different_prefab_is_not_applied(self):
        face = self.make_face()
        face.environment.objects[0].read().m_GameObject = NS(read=lambda: NS(transform=NS(key=99)))
        plan = self.plan(face)
        self.assertEqual(plan["scaleValues"], [])


if __name__ == "__main__":
    unittest.main()
