"""Physics conversion tests use tiny source-shaped fixtures, not asset dumps."""

import unittest
import math
from types import SimpleNamespace as NS
from UnityPy.classes import PPtr

from converter.common.physics import (
    capsule_endpoints, extract_model_physics, magica1_radius, magica2_radius,
)
from converter.common.unity import object_id


def vec(x=0., y=0., z=0.):
    return NS(x=x, y=y, z=z)


class Ptr:
    def __init__(self, value, kind="Transform"):
        self.value = value
        self.type = NS(name=kind)

    def read(self):
        return self.value

    def deref_parse_as_object(self):
        return self.value


class PhysicsFixture:
    def __init__(self):
        self.asset = object()
        self.nodes = []
        self.components = []

    def identity(self, obj):
        obj.object_reader = NS(assets_file=self.asset, path_id=id(obj))
        return obj

    def node(self, position):
        transform = self.identity(NS(index=len(self.nodes), position=position, m_Children=[], m_Father=None))
        go = NS(m_Component=[(0, Ptr(transform))])
        transform.m_GameObject = Ptr(go, "GameObject")
        self.nodes.append(transform)
        return transform

    def component(self, node, name, **fields):
        if name == "MagicaBoneCloth":
            fields.setdefault("meshData", Ptr(NS()))
        item = self.identity(NS(m_Script=Ptr(NS(m_ClassName=name)), m_Enabled=1,
                                m_GameObject=node.m_GameObject, **fields))
        self.components.append(Ptr(item, "MonoBehaviour"))
        node.m_GameObject.read().m_Component.append((0, self.components[-1]))
        return item

    def extract(self, core=(), missing=()):
        def node_index(node):
            if node.index in missing:
                raise ValueError("Source Transform is absent from the exported skeleton")
            return node.index

        mapping = NS(node_index=node_index,
                     point=lambda n, p, target_node=None: [
                         p[i] + n.position[i] - self.nodes[node_index(n) if target_node is None else target_node].position[i]
                         for i in range(3)],
                     radius=lambda n, r, target_node=None: r,
                     direction=lambda n, d: d,
                     normal=lambda n, d: d,
                     canonical_world=[[1,0,0,0, 0,1,0,0, 0,0,1,0, *node.position,1] for node in self.nodes],
                     source_nodes={object_id(node): node.index for node in self.nodes if node.index not in missing},
                     source_world=[[1,0,0,0, 0,1,0,0, 0,0,1,0, *node.position,1] for node in self.nodes])
        return extract_model_physics(NS(objects=self.components),
                                    NS(node_mapping=mapping, standard_bones={str(i): i for i in core}))


class PhysicsExportTests(unittest.TestCase):
    def test_unity_spring_bone_exports_declared_collision_geometry(self):
        f = PhysicsFixture()
        bone, child, leg = [f.node(p) for p in ([0, 0, 0], [0, -1, 0], [.1, 0, 0])]
        bone.m_Children = [Ptr(child)]
        capsule = f.component(leg, 'SpringCapsuleCollider', radius=.1, height=.7, linkedRenderer=None)
        sphere = f.component(leg, 'SpringSphereCollider', radius=.2, linkedRenderer=None)
        spring = f.component(bone, 'SpringBone', explicitlyChild=None, radius=.025,
                    sphereColliders=[Ptr(sphere)], capsuleColliders=[Ptr(capsule)], panelColliders=[])
        result = f.extract()
        self.assertIsNotNone(result)
        self.assertEqual(result['springs'][0]['tail'], [0, -1, 0])
        self.assertEqual(result['springs'][0]['colliders'], [0, 1])
        self.assertEqual(result['colliders'][1]['offset'], [0, 0, 0])
        self.assertEqual(result['colliders'][1]['tail'], {'node': 2, 'offset': [0, .7, 0]})
        self.assertEqual(result['colliders'][1]['radius'], .1)
        spring.radius = -.025
        self.assertEqual(f.extract()['springs'][0]['radius'], .025)

    def test_spring_bone_multichild_uses_average_direction_and_length_ignoring_pivots(self):
        f = PhysicsFixture()
        bone, a, b, pivot = [f.node(p) for p in ([1,2,3], [3,2,3], [1,3,3], [90,80,70])]
        bone.m_Children = [Ptr(a), Ptr(b), Ptr(pivot)]
        f.component(pivot, 'SpringBonePivot')
        spring = f.component(bone, 'SpringBone', explicitlyChild=None, radius=.02,
                             sphereColliders=[], capsuleColliders=[], panelColliders=[])
        tail = f.extract()['springs'][0]['tail']
        for actual, expected in zip(tail, [3/math.sqrt(5), 1.5/math.sqrt(5), 0]):
            self.assertAlmostEqual(actual, expected)
        spring.explicitlyChild = Ptr(b)
        self.assertEqual(f.extract()['springs'][0]['tail'], [0,1,0])
        # Explicit child is only consulted for multiple valid children.
        bone.m_Children = [Ptr(a), Ptr(pivot)]
        self.assertEqual(f.extract()['springs'][0]['tail'], [2,0,0])

    def test_spring_bone_panel_and_disabled_source_components(self):
        f = PhysicsFixture()
        bone, child = f.node([0,0,0]), f.node([0,-1,0])
        bone.m_Children = [Ptr(child)]
        panel = f.component(bone, 'SpringPanelCollider', width=2., height=4., linkedRenderer=None)
        hidden = f.component(bone, 'SpringSphereCollider', radius=.2, linkedRenderer=Ptr(NS(m_Enabled=0)))
        tiny = f.component(bone, 'SpringCapsuleCollider', radius=.0001, height=2., linkedRenderer=None)
        spring = f.component(bone, 'SpringBone', explicitlyChild=None, radius=.02,
                             sphereColliders=[Ptr(hidden)], capsuleColliders=[Ptr(tiny)], panelColliders=[Ptr(panel)])
        result = f.extract()
        self.assertEqual(result['colliders'], [{'shape':'panel','node':0,'offset':[0,0,0],
                                               'halfAxes':[[1.,0.,0.],[0.,2.,0.]]}])
        self.assertEqual(result['springs'][0]['colliders'], [0])
        spring.m_Enabled = 0
        self.assertIsNone(f.extract())

    def test_spring_bone_nearly_cancelling_children_follow_unity_normalize_threshold(self):
        f = PhysicsFixture()
        bone, a, b = [f.node(p) for p in ([0,0,0], [1,0,0], [-1 + 1.5e-5,0,0])]
        bone.m_Children = [Ptr(a), Ptr(b)]
        f.component(bone, 'SpringBone', explicitlyChild=None, radius=.02,
                    sphereColliders=[], capsuleColliders=[], panelColliders=[])
        self.assertIsNone(f.extract())
        b.position[0] = -1 + 5e-5
        self.assertAlmostEqual(f.extract()['springs'][0]['tail'][0], 1 - 2.5e-5)

    def test_spring_manager_ground_is_bound_to_model_root_not_animated_bone(self):
        f = PhysicsFixture()
        root, bone, child = [f.node(p) for p in ([0,1,0], [0,2,0], [0,2.5,0])]
        root.m_Children, bone.m_Children = [Ptr(bone)], [Ptr(child)]
        bone.m_Father, child.m_Father = Ptr(root), Ptr(bone)
        # The stored manager bone list is not authoritative: Awake discovers
        # the entire manager subtree again, including bones absent from it.
        f.component(bone, 'SpringManager', collideWithGround=True, groundHeight=.25, springBones=[])
        f.component(bone, 'SpringBone', explicitlyChild=None, radius=.02,
                    sphereColliders=[], capsuleColliders=[], panelColliders=[])
        result = f.extract()
        self.assertEqual(result['colliders'], [{'shape':'plane', 'node':0,
                                               'offset':[0,-.75,0], 'normal':[0,1,0]}])
        self.assertEqual(result['springs'][0]['colliders'], [0])

    def test_magica1_length_is_half_external_length(self):
        source = NS(center=vec(), axis=0, length=.5, startRadius=.1, endRadius=.2)
        start, end, radius = capsule_endpoints(source, magica2=False)
        self.assertEqual(start, [.4, 0., 0.])
        self.assertEqual(end, [-.3, 0., 0.])
        self.assertEqual(radius, .2)

    def test_magica2_separate_radius_disabled_and_reverse_axis(self):
        source = NS(center=vec(1, 2, 3), size=vec(.1, .9, 1), direction=1,
                    alignedOnCenter=True, radiusSeparation=False, reverseDirection=True)
        start, end, radius = capsule_endpoints(source, magica2=True)
        self.assertEqual(start, [1., 1.6, 3.])
        self.assertEqual(end, [1., 2.4, 3.])
        self.assertEqual(radius, .1)

    def test_magica2_start_pivot(self):
        source = NS(center=vec(), size=vec(.1, .2, 1), direction=2,
                    alignedOnCenter=False, radiusSeparation=True, reverseDirection=False)
        start, end, radius = capsule_endpoints(source, magica2=True)
        self.assertEqual(start, [0., 0., 0.])
        self.assertAlmostEqual(end[2], -.7)
        self.assertEqual(radius, .2)

    def test_llas_uses_declared_child_and_two_node_collider(self):
        f = PhysicsFixture()
        bone, child, leg, knee = [f.node(p) for p in ([0, 0, 0], [0, -1, 0], [.1, 0, 0], [.1, -.5, 0])]
        end = f.component(knee, "SwingCollider", radius=.1, offset=vec(), sibling=None)
        collider = f.component(leg, "SwingCollider", radius=.2, offset=vec(0, .01, 0), sibling=Ptr(end))
        f.component(bone, "SwingBone", child=Ptr(child), radius=.02,
                    colliders=[Ptr(collider), Ptr(collider)])
        result = f.extract()
        self.assertEqual(len(result["colliders"]), 1)
        self.assertEqual(result["colliders"][0]["shape"], "capsule")
        self.assertEqual(result["colliders"][0]["tail"], {"node": 3, "offset": [0., 0., 0.]})
        self.assertEqual(result["springs"][0]["tail"], [0., -1., 0.])
        self.assertEqual(result["springs"][0]["colliders"], [0])

    def test_core_humanoid_nodes_never_driven(self):
        f = PhysicsFixture()
        bone, child = f.node([0, 0, 0]), f.node([0, 1, 0])
        f.component(bone, "SwingBone", child=Ptr(child), radius=.02, colliders=[])
        self.assertIsNone(f.extract(core=[0]))

    def test_models_without_physics_emit_nothing(self):
        f = PhysicsFixture()
        self.assertIsNone(f.extract())

    def test_magica_chain_uses_real_children_and_plane(self):
        f = PhysicsFixture()
        root, mid, end, plane_node = [f.node(p) for p in ([0, 0, 0], [0, -.5, 0], [0, -1, 0], [0, 0, 0])]
        root.m_Children = [Ptr(mid)]
        mid.m_Children = [Ptr(end)]
        plane = f.component(plane_node, "MagicaPlaneCollider", center=vec())
        f.component(root, "MagicaCloth", serializeData=NS(clothType=1, rootBones=[Ptr(root)],
                    radius=NS(value=.03, useCurve=False), colliderCollisionConstraint=NS(colliderList=[Ptr(plane), None])),
                    serializeData2=NS(selectionData=NS(positions=[vec(),vec(0,-.5,0),vec(0,-1,0)],
                        attributes=[NS(Value=1),NS(Value=2),NS(Value=2)],maxConnectionDistance=.5)))
        result = f.extract()
        self.assertEqual([s["node"] for s in result["springs"]], [0, 1])
        self.assertEqual(result["colliders"], [{"shape": "plane", "node": 3,
                         "offset": [0., 0., 0.], "normal": [0., 1., 0.]}])

    def test_bezier_parameter_matches_native_midpoint_control(self):
        parameter = NS(startValue=.05, endValue=.075, useEndValue=True,
                       useCurveValue=False, curveValue=0)
        self.assertAlmostEqual(magica1_radius(parameter, 1/6), .05416666666666667)
        parameter.useCurveValue, parameter.curveValue = True, 1
        self.assertAlmostEqual(magica1_radius(parameter, .5), .05625)
        parameter.curveValue = -1
        self.assertAlmostEqual(magica1_radius(parameter, .5), .06875)
        parameter.useEndValue = False
        self.assertAlmostEqual(magica1_radius(parameter, .5), .05)

    def test_magica2_unweighted_curve_and_runtime_lut(self):
        curve = NS(m_Curve=[NS(time=0,value=0,inSlope=0,outSlope=0,weightedMode=0),
                           NS(time=1,value=1,inSlope=0,outSlope=0,weightedMode=0)])
        parameter = NS(value=.1, useCurve=True, curve=curve)
        self.assertAlmostEqual(magica2_radius(parameter, .5), .05)
        self.assertAlmostEqual(magica2_radius(parameter, 0), 0)
        self.assertAlmostEqual(magica2_radius(parameter, 1), .1)
        curve.m_Curve[0].weightedMode = 1
        with self.assertRaisesRegex(ValueError, 'Unity sampling'):
            magica2_radius(parameter, .5)

    def test_magica1_child_particle_radius_and_fixed_child(self):
        f = PhysicsFixture()
        root, fixed, moving = [f.node(p) for p in ([0,0,0],[0,-.5,0],[0,-1,0])]
        root.m_Children=[Ptr(fixed)]
        fixed.m_Children=[Ptr(moving)]
        f.component(root, 'MagicaBoneCloth',
            clothTarget=NS(rootList=[Ptr(root)]),
            clothParams=NS(useCollision=False,radius=NS(startValue=.01,endValue=.03,useEndValue=True,
                                                       curveValue=0,useCurveValue=False)),
            teamData=NS(colliderList=[]),useTransformList=[Ptr(root),Ptr(fixed),Ptr(moving)],
            clothData=Ptr(NS(useVertexList=[0,1,2],vertexDepthList=[0,0,.5],selectionData=[2,2,1])))
        springs=f.extract()['springs']
        self.assertEqual(len(springs),1)
        self.assertEqual(springs[0]['node'],1)
        self.assertAlmostEqual(springs[0]['radius'],.02)

    def test_magica1_null_build_data_does_not_create_physics(self):
        # Source 014_cos_birthday_2021 has an enabled magica_scloth with null
        # clothData/meshData and no useTransformList. Native VerifyData rejects
        # it before runtime setup; a configured root alone is not built physics.
        for missing in ("clothData", "meshData"):
            with self.subTest(missing=missing):
                f = PhysicsFixture()
                root, tip = f.node([0, 0, 0]), f.node([0, -1, 0])
                root.m_Children = [Ptr(tip)]
                fields = {"clothData": Ptr(NS(useVertexList=[0, 1], vertexDepthList=[0, 1], selectionData=[2, 1])),
                          "meshData": Ptr(NS())}
                fields[missing] = PPtr(m_FileID=0, m_PathID=0, assetsfile=f.asset)
                f.component(root, "MagicaBoneCloth", **fields,
                    clothParams=NS(useCollision=False, radius=NS(startValue=.02, useEndValue=False,
                        useCurveValue=False, curveValue=0)), teamData=NS(colliderList=[]),
                    clothTarget=NS(rootList=[Ptr(root)]), useTransformList=[Ptr(root), Ptr(tip)])
                self.assertIsNone(f.extract())

    def test_magica1_nonnull_broken_build_reference_still_fails(self):
        class BrokenPtr(Ptr):
            def read(self):
                raise ValueError("non-null source build reference is missing")

        for broken in ("clothData", "meshData"):
            with self.subTest(broken=broken):
                f = PhysicsFixture()
                root = f.node([0, 0, 0])
                fields = {"clothData": Ptr(NS(useVertexList=[], vertexDepthList=[], selectionData=[])),
                          "meshData": Ptr(NS())}
                fields[broken] = BrokenPtr(NS())
                f.component(root, "MagicaBoneCloth", **fields,
                    clothParams=NS(useCollision=False), teamData=NS(colliderList=[]),
                    clothTarget=NS(rootList=[]), useTransformList=[])
                with self.assertRaisesRegex(ValueError, "non-null source build reference"):
                    f.extract()

    def test_physics_only_uses_components_attached_to_exported_prefab(self):
        f = PhysicsFixture()
        own_root, own_tip, other_root, other_tip = [
            f.node(p) for p in ([0,0,0], [0,-1,0], [0,0,0], [0,-1,0])
        ]
        for root, tip in [(other_root, other_tip), (own_root, own_tip)]:
            root.m_Children = [Ptr(tip)]
            f.component(root, 'MagicaBoneCloth',
                clothTarget=NS(rootList=[Ptr(root)]),
                clothParams=NS(useCollision=False, radius=NS(startValue=.02, useEndValue=False,
                    useCurveValue=False, curveValue=0)),
                teamData=NS(colliderList=[]), useTransformList=[Ptr(root), Ptr(tip)],
                clothData=Ptr(NS(useVertexList=[0,1], vertexDepthList=[0,1], selectionData=[2,1])))
        result = f.extract(missing=[other_root.index, other_tip.index])
        self.assertEqual([s['node'] for s in result['springs']], [own_root.index])
        self.assertEqual(result['springs'][0]['tail'], [0., -1., 0.])

    def test_exported_component_with_missing_physics_particle_still_fails(self):
        f = PhysicsFixture()
        root, mid, tip = [f.node(p) for p in ([0,0,0], [0,-.5,0], [0,-1,0])]
        root.m_Children, mid.m_Children = [Ptr(mid)], [Ptr(tip)]
        f.component(root, 'MagicaBoneCloth',
            clothTarget=NS(rootList=[Ptr(root)]),
            clothParams=NS(useCollision=False, radius=NS(startValue=.02, useEndValue=False,
                useCurveValue=False, curveValue=0)),
            teamData=NS(colliderList=[]), useTransformList=[Ptr(root), Ptr(mid), Ptr(tip)],
            clothData=Ptr(NS(useVertexList=[0,1,2], vertexDepthList=[0,.5,1], selectionData=[2,1,1])))
        with self.assertRaisesRegex(ValueError, 'absent from the exported skeleton'):
            f.extract(missing=[mid.index])

    def test_taper_subdivision_retains_thin_end_and_index_associations(self):
        f = PhysicsFixture()
        bone,child,collider_node=[f.node(p) for p in ([0,0,0],[0,-1,0],[0,0,0])]
        collider=f.component(collider_node,'MagicaCapsuleCollider',center=vec(),axis=0,
                             length=.4,startRadius=.15,endRadius=.05)
        f.component(bone,'SwingBone',child=Ptr(child),radius=.02,colliders=[Ptr(collider)])
        result=f.extract()
        self.assertGreaterEqual(len(result['colliders']),20)
        self.assertLessEqual(result['colliders'][-1]['radius'],.05500001)
        self.assertEqual(result['springs'][0]['colliders'],list(range(len(result['colliders']))))


if __name__ == "__main__":
    unittest.main()
