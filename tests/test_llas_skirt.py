import unittest
from types import SimpleNamespace as NS

from converter.llas.skirt import build_skirt_behavior, skirt_flags, source_frame
from tests.test_physics_export import PhysicsFixture, Ptr, vec
from converter.common.unity import object_id


class LlasSkirtTests(unittest.TestCase):
    def test_source_flags_and_second_segment_exclusion(self):
        cases = {'SkirtA1_Dyna': 7, 'SkirtE1_Dyna': 3, 'LeftSkirtC1_Dyna': 1,
                 'RightSkirtD1_Dyna': 2, 'LeftSkirtB2_Dyna': 0, 'Hair': 0,
                 'SkirtA1_Dyna_extra': 7, 'OtherSkirtA1_Dyna': 0}
        for name, expected in cases.items():
            self.assertEqual(skirt_flags(name), expected)

    def test_source_axes_preserve_handedness_and_offset(self):
        mapping = NS(direction=lambda _, p: [-p[0], p[1], p[2]],
                     point=lambda _, p: [.1 - p[0], .2 + p[1], .3 + p[2]])
        self.assertEqual(source_frame(mapping, None), [-1,0,0,0, 0,1,0,0, 0,0,1,0, .1,.2,.3,1])

    def test_manager_rebuilds_knees_and_exports_native_defaults_without_inputs(self):
        f = PhysicsFixture()
        root, left, right, bone, child = [f.node(p) for p in
                                         ([0,0,0], [0,0,0], [0,0,0], [0,0,0], [-.2,0,0])]
        names = ['root', 'LeftUpLeg', 'RightUpLeg', 'SkirtA1_Dyna', 'tip']
        for n, name in zip(f.nodes, names):
            n.m_GameObject.read().m_Name = name
        root.m_Children = [Ptr(left), Ptr(right), Ptr(bone)]
        bone.m_Children = [Ptr(child)]; bone.m_Father = Ptr(root)
        spring = f.component(bone, 'SwingBone', child=Ptr(child), boneAxis=vec(-1,0,0),
                             skirtSafeEnable=1, skirtLimitDotMin=-.975, skirtLimitDotMax=0,
                             skirtRotDegMax=30, kneeSpaceOffsetMax=.2)
        f.component(root, 'SwingBoneManager', bones=[Ptr(spring)], kneeTransforms=[])
        matrices = [[1,0,0,0, 0,1,0,0, 0,0,1,0, *node.position,1] for node in f.nodes]
        mapping = NS(source_nodes={object_id(n): n.index for n in f.nodes}, source_world=matrices,
                     node_index=lambda n: n.index, direction=lambda n,p: [-p[0],p[1],p[2]],
                     point=lambda n,p: [-p[0],p[1],p[2]])
        exported = NS(node_mapping=mapping, builder=NS(document={'nodes': [{'name': n} for n in names]}))
        result = build_skirt_behavior(NS(objects=f.components), exported)
        manager = result['parameters']['managers'][0]
        self.assertEqual([k['node'] for k in manager['knees']], ['LeftUpLeg','RightUpLeg'])
        b = manager['bones'][0]
        self.assertEqual(b['knees'], [0,1]); self.assertAlmostEqual(b['length'], .2)
        self.assertEqual(b['kneeSpaceOffset'], .02)
        spring.kneeSpaceOffsetFront = .07
        self.assertEqual(build_skirt_behavior(NS(objects=f.components), exported)['parameters']['managers'][0]
                         ['bones'][0]['kneeSpaceOffset'], .07)
        spring.skirtSafeEnable = 0
        self.assertIsNone(build_skirt_behavior(NS(objects=f.components), exported))

    def test_collision_edges_export_actual_sibling_references(self):
        f = PhysicsFixture()
        a, at, b, bt, leg = [f.node(p) for p in ([0,0,0], [-.2,0,0], [0,0,0], [.2,0,0], [0,0,0])]
        collider = f.component(leg, 'SwingCollider', radius=.1, offset=vec(), sibling=None)
        ca = f.component(a, 'SwingBone', child=Ptr(at), radius=.02, colliders=[Ptr(collider)])
        cb = f.component(b, 'SwingBone', child=Ptr(bt), radius=.03, colliders=[Ptr(collider)], sibling=Ptr(ca))
        ca.sibling = Ptr(cb)
        data = f.extract()
        self.assertEqual(data['collisionEdges'], [{'springs':[0,1], 'colliders':[0]}])


if __name__ == '__main__':
    unittest.main()
