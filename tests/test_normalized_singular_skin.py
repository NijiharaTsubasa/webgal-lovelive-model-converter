import math
import struct
import unittest
from types import SimpleNamespace as NS
from unittest.mock import patch

import converter.common.normalized_model as nm


def matrix(position=(0, 0, 0), degrees=0, scale=(1, 1, 1)):
    angle = math.radians(degrees) / 2
    return nm._trs_to_mat(list(position), [0, 0, math.sin(angle), math.cos(angle)], list(scale))


def float32(values):
    return list(struct.unpack('<' + 'f' * len(values), struct.pack('<' + 'f' * len(values), *values)))


def unity_matrix(values):
    signs = (-1, 1, 1, 1)
    return NS(**{f'e{row}{column}': values[column * 4 + row] * signs[row] * signs[column]
                 for row in range(4) for column in range(4)})


class Pointer:
    def __init__(self, value):
        self.value = value

    def deref_parse_as_object(self):
        return self.value


class Builder:
    def __init__(self):
        self.document = {'nodes': [], 'skins': [], 'meshes': [], 'scenes': [{'nodes': []}]}
        self.values = []
        self.include_vertex_colors = False

    def add_accessor(self, values, value_type, component_type, **kwargs):
        self.values.append([float32(v) for v in values] if component_type == 5126 else values)
        return len(self.values) - 1

    def add_material(self, value):
        return 0


class SingularSkinTests(unittest.TestCase):
    def fixture(self):
        # A weighted auxiliary joint under a near-zero-scale parent is still a
        # distinct source joint. Its ordinary local transform must survive.
        bones = []
        definitions = [
            ('root', -1, (0, 0, 0), 0, (1, 1, 1)),
            ('LeftUpperArm', 0, (.2, 1.1, .1), 37, (1, 1, 1)),
            ('LArm_Twist_dmy', 1, (0, 0, 0), -19, (1e-12, 1, 1)),
            ('LArm_Twist', 2, (2.7e-8, 0, 0), 0, (1, 1, 1)),
        ]
        transforms = []
        assets = object()
        for index, (name, parent, position, degrees, scale) in enumerate(definitions):
            angle = math.radians(degrees) / 2
            rotation = [0, 0, math.sin(angle), math.cos(angle)]
            bones.append(dict(name=name, originalName=name, parentIndex=parent,
                              hierarchyPath=[0] * index, isHumanoidCore=index == 1,
                              translation=list(position), rotation=rotation, scale=list(scale),
                              sourceUnityEulerAngles=[0, 0, -degrees]))
            transforms.append(NS(
                object_reader=NS(assets_file=assets, path_id=index),
                m_LocalPosition=NS(x=-position[0], y=position[1], z=position[2]),
                m_LocalRotation=NS(x=0, y=0, z=-rotation[2], w=rotation[3]),
                m_LocalScale=NS(x=scale[0], y=scale[1], z=scale[2]),
                m_Children=[], m_GameObject=Pointer(NS(m_Name=name, m_Component=[]))))
        for parent, child in zip(transforms, transforms[1:]):
            parent.m_Children.append(Pointer(child))
        canonical = nm._world_matrices(bones)
        for bone, world in zip(bones, canonical):
            bone['neutralWorldMatrix'] = world
        skeleton = dict(schemaVersion=4, producer='unity-humanoid-normalizer',
                        coordinateSystem='gltf-yup-zfwd-right-handed', pose='mecanim-zero-muscles',
                        rootIndex=0, humanScale=1, bones=bones)
        builder = Builder()
        with patch.object(nm, 'GlbBuilder', return_value=builder), \
                patch.object(nm, 'game_object_transform', return_value=transforms[0]):
            result = nm.export_normalized_model(NS(objects=[]), Pointer(object()), skeleton,
                                                nm.NormalizedModelAdapter())
        return builder, result, transforms, canonical

    def test_near_singular_auxiliary_keeps_own_joint_and_local_transform(self):
        builder, result, transforms, _ = self.fixture()
        mapping = result.node_mapping
        self.assertEqual(mapping.node_index(transforms[1]), 1)
        self.assertEqual(mapping.node_index(transforms[3]), 3)
        self.assertEqual(mapping.redirects, {})
        self.assertEqual(builder.document['nodes'][3]['translation'], [2.7e-8, 0, 0])
        self.assertEqual(builder.document['nodes'][3]['scale'], [1, 1, 1])
        self.assertEqual(builder.document['nodes'][2]['children'], [3])

    def test_float32_skinning_preserves_mixed_vertices_at_non_endpoint_rotations(self):
        builder, result, transforms, canonical = self.fixture()
        # The source inverse bind legitimately cancels its parent's 1e-12
        # scale. Do not replace that weighted joint with the core ancestor.
        source_binds = [nm._mat4_inverse(canonical[i]) for i in (1, 3)]
        mesh = NS(m_Name='body', m_BindPose=[unity_matrix(v) for v in source_binds])
        renderer = NS(m_Mesh=Pointer(mesh), m_Bones=[Pointer(transforms[i]) for i in (1, 3)],
                      m_Materials=[])
        decoded = NS(process=lambda: None, m_Vertices=[(-.3, 1.15, .17)],
                     m_Normals=[], m_Tangents=[], m_UV0=[], m_BoneIndices=[[0, 1]],
                     m_BoneWeights=[[.37, .63]], get_triangles=lambda: [[(0, 0, 0)]])
        mapping = result.node_mapping
        with patch.object(nm, 'MeshHandler', return_value=decoded), \
                patch.object(nm, 'mesh_morphs', return_value=([], [])):
            nm._add_normalized_renderer(renderer, 0, builder, mapping.source_nodes,
                                        canonical, canonical, canonical, mapping.redirects,
                                        frozenset())
        skin = builder.document['skins'][0]
        self.assertEqual(skin['joints'], [1, 3])
        self.assertFalse(any('__skin_binding' in n['name'] for n in builder.document['nodes']))
        ibms = builder.values[skin['inverseBindMatrices']]
        primitive = builder.document['meshes'][0]['primitives'][0]
        point = builder.values[primitive['attributes']['POSITION']][0]
        weights = builder.values[primitive['attributes']['WEIGHTS_0']][0][:2]
        for angle in (0, 23, 71, -119):
            with self.subTest(angle=angle):
                delta = matrix(degrees=angle)
                expected = [0., 0., 0.]
                actual = [0., 0., 0.]
                for index, node in enumerate(skin['joints']):
                    source = nm._mat4_mul(nm._mat4_mul(delta, canonical[node]), source_binds[index])
                    # Three.js multiplies in JS doubles and uploads bone
                    # matrices as float32 before GPU weighted skinning.
                    exported = float32(nm._mat4_mul(nm._mat4_mul(delta, canonical[node]), ibms[index]))
                    for accumulator, transform in ((expected, source), (actual, exported)):
                        vertex = nm._mat4_transform_point(transform, point)
                        for axis in range(3):
                            accumulator[axis] += vertex[axis] * weights[index]
                self.assertLess(math.dist(actual, expected), 2e-6)


if __name__ == '__main__':
    unittest.main()
