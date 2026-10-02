import math
import unittest
from types import SimpleNamespace as NS
from unittest.mock import patch

import converter.common.normalized_model as nm


def matrix(position=(0, 0, 0), degrees=0, scale=(1, 1, 1)):
    angle = math.radians(degrees) / 2
    return nm._trs_to_mat(
        list(position), [0, 0, math.sin(angle), math.cos(angle)], list(scale),
    )


def unity_matrix(gltf):
    signs = [-1, 1, 1, 1]
    return NS(**{
        f'e{row}{column}': gltf[column * 4 + row] * signs[row] * signs[column]
        for row in range(4) for column in range(4)
    })


def skin_point(matrices, weights, point):
    transformed = [nm._mat4_transform_point(value, point) for value in matrices]
    return [sum(weight * value[axis] for weight, value in zip(weights, transformed))
            for axis in range(3)]


class Pointer:
    def __init__(self, value):
        self.value = value

    def deref_parse_as_object(self):
        return self.value


class Builder:
    def __init__(self):
        self.document = {
            'nodes': [{'name': 'root', 'children': [1, 2]},
                      {'name': 'joint1'}, {'name': 'joint2'}],
            'skins': [], 'meshes': [], 'scenes': [{'nodes': [0]}],
        }
        self.values = []
        self.include_vertex_colors = False

    def add_accessor(self, values, *args, **kwargs):
        self.values.append(values)
        return len(self.values) - 1

    def add_material(self, value):
        return 0


class SourceSkinTests(unittest.TestCase):
    def assertVectorClose(self, actual, expected):
        self.assertEqual(len(actual), len(expected))
        for component, value in zip(actual, expected):
            self.assertAlmostEqual(component, value, places=11)

    def export(self, *, redirected=False, copied=False, transformed=False,
               round_trip=False):
        bones = [NS(object_reader=NS(assets_file=object(), path_id=index))
                 for index in (1, 2)]
        keys = [nm.object_id(bone) for bone in bones]
        inverse_binds = [matrix((-.1, 0, 0), -13), matrix((.2, .1, 0), 29)]
        morph = NS(
            channels=[NS(name='lift', frameIndex=0, frameCount=1)],
            shapes=[NS(firstVertex=0, vertexCount=1)],
            vertices=[NS(index=0, vertex=NS(x=.03, y=.01, z=-.02))],
        )
        mesh = NS(m_Name='body', m_Shapes=morph)
        renderer = NS(m_Mesh=Pointer(mesh), m_Bones=[Pointer(bone) for bone in bones],
                      m_Materials=[])
        decoded = NS(
            process=lambda: None,
            m_Vertices=[(.1, .2, .3)], m_Normals=[(.6, .8, 0)],
            m_Tangents=[(.8, -.6, 0, -1)], m_BoneIndices=[[0, 1]],
            m_BoneWeights=[[.4, .6]], m_UV0=[],
            get_triangles=lambda: [[(0, 0, 0)]],
        )
        canonical = [matrix((.3, .1, 0), 11), matrix((0, .3, 0), 15),
                     matrix((.1, .4, 0), -22)]
        neutral = [matrix(), matrix((.2, .3, 0), -34), matrix((.3, .5, 0), 43)]
        source = [matrix(), matrix((.1, .2, 0), 12), matrix((.2, .6, 0), -4)]
        if transformed:
            # Unit conversion and a rotated, translated root must be carried
            # exactly once; attachment space does not enter glTF skinning.
            root = matrix((2, -.5, 1), 32, (.01, .01, .01))
            canonical = [nm._mat4_mul(root, value) for value in canonical]
            neutral = [nm._mat4_mul(root, value) for value in neutral]
            source = [nm._mat4_mul(root, value) for value in source]
            canonical[1] = nm._mat4_mul(canonical[1], matrix(scale=(2, .8, 1.1)))
            neutral[2] = nm._mat4_mul(neutral[2], matrix(scale=(.9, 1.2, .7)))
        if round_trip:
            canonical = [matrix(), matrix(), matrix()]
            neutral = [matrix(), matrix(degrees=45), matrix(degrees=-45)]
            inverse_binds = [matrix(), matrix()]
            decoded.m_Vertices = [(-1, 0, 0)]
            decoded.m_BoneWeights = [[.5, .5]]
        redirects = {keys[1]: 1} if redirected else {}
        copies = frozenset([keys[1]]) if copied else frozenset()
        if redirected:
            renderer.m_Bones = [Pointer(bones[1])]
            mesh.m_BindPose = [unity_matrix(inverse_binds[1])]
            decoded.m_BoneIndices = [[0]]
            decoded.m_BoneWeights = [[1.0]]
        else:
            mesh.m_BindPose = [unity_matrix(value) for value in inverse_binds]
        builder = Builder()
        with patch.object(nm, 'MeshHandler', return_value=decoded):
            nm._add_normalized_renderer(
                renderer, 0, builder, dict(zip(keys, [1, 2])), canonical,
                neutral, source, redirects, copies,
            )
        return builder, canonical, neutral, source, inverse_binds

    def test_source_attributes_and_morph_share_mesh_coordinates(self):
        builder, *_ = self.export()
        primitive = builder.document['meshes'][0]['primitives'][0]
        self.assertEqual(builder.values[primitive['attributes']['POSITION']], [(-.1, .2, .3)])
        self.assertEqual(builder.values[primitive['attributes']['NORMAL']], [(-.6, .8, 0)])
        self.assertEqual(builder.values[primitive['attributes']['TANGENT']], [(-.8, -.6, 0, 1)])
        self.assertEqual(builder.values[primitive['targets'][0]['POSITION']], [[-.03, .01, -.02]])
        self.assertEqual(builder.document['scenes'][0]['nodes'], [0, 3])
        self.assertEqual(builder.document['nodes'][3], {'name': 'body Renderer', 'mesh': 0, 'skin': 0})

    def test_single_source_lbs_at_reference_and_non_endpoint_motion_with_morph(self):
        for transformed in (False, True):
            builder, canonical, neutral, _, inverse_binds = self.export(transformed=transformed)
            skin = builder.document['skins'][0]
            new_binds = builder.values[skin['inverseBindMatrices']]
            primitive = builder.document['meshes'][0]['primitives'][0]
            position = builder.values[primitive['attributes']['POSITION']][0]
            morph = builder.values[primitive['targets'][0]['POSITION']][0]
            weights = builder.values[primitive['attributes']['WEIGHTS_0']][0][:2]
            for morph_weight in (0, .37, 1):
                actual_vertex = [value + delta * morph_weight for value, delta in zip(position, morph)]
                source_vertex = [-.1 - .03 * morph_weight, .2 + .01 * morph_weight,
                                 .3 - .02 * morph_weight]
                for angles in ((0, 0), (24, -41), (117, -83)):
                    with self.subTest(transformed=transformed, morph=morph_weight, angles=angles):
                        deltas = [matrix(degrees=degrees) for degrees in angles]
                        direct = [nm._mat4_mul(nm._mat4_mul(delta, neutral[index + 1]), inverse_binds[index])
                                  for index, delta in enumerate(deltas)]
                        actual = [nm._mat4_mul(nm._mat4_mul(delta, canonical[index + 1]), new_binds[index])
                                  for index, delta in enumerate(deltas)]
                        self.assertVectorClose(skin_point(actual, weights, actual_vertex),
                                               skin_point(direct, weights, source_vertex))

    def test_opposite_bone_rotations_can_return_mixed_vertex_to_source_pose(self):
        builder, canonical, _, _, _ = self.export(round_trip=True)
        skin = builder.document['skins'][0]
        binds = builder.values[skin['inverseBindMatrices']]
        primitive = builder.document['meshes'][0]['primitives'][0]
        position = builder.values[primitive['attributes']['POSITION']][0]
        posed = [nm._mat4_mul(nm._mat4_mul(matrix(degrees=degrees), canonical[index + 1]), binds[index])
                 for index, degrees in enumerate((-45, 45))]
        self.assertVectorClose(skin_point(posed, [.5, .5], position), [1, 0, 0])

    def test_redirect_preserves_source_offset_and_copy_uses_adjusted_neutral(self):
        for copied in (False, True):
            builder, canonical, neutral, source, inverse_binds = self.export(redirected=True, copied=copied)
            effective = neutral[2] if copied else nm._mat4_mul(
                nm._mat4_mul(neutral[1], nm._mat4_inverse(source[1])), source[2],
            )
            expected = nm._mat4_mul(
                nm._mat4_mul(nm._mat4_inverse(canonical[1]), effective), inverse_binds[1],
            )
            skin = builder.document['skins'][0]
            self.assertEqual(skin['joints'], [1])
            self.assertVectorClose(builder.values[skin['inverseBindMatrices']][0], expected)

    def test_equal_offsets_merge_and_different_offsets_fail_without_nodes(self):
        nodes = [{'name': 'root'}, {'name': 'joint'}]
        identity = matrix()
        joints, binds, indices, weights = nm._resolve_skin_bindings(
            nodes, [1, 1], [identity, identity], [[0, 1, 0, 0]], [[.4, .6, 0, 0]],
        )
        self.assertEqual((joints, indices, weights), ([1], [[0, 0, 0, 0]], [[1, 0, 0, 0]]))
        self.assertEqual(binds, [identity])
        with self.assertRaisesRegex(ValueError, "'joint'.*distinct source bind offsets"):
            nm._resolve_skin_bindings(
                nodes, [1, 1], [identity, matrix((.01, 0, 0))], [[0, 1]], [[.4, .6]],
            )
        self.assertEqual(len(nodes), 2)

    def test_zero_weight_slots_do_not_reference_a_skin_joint(self):
        joints, _, indices, weights = nm._resolve_skin_bindings(
            [{'name': 'joint'}], [0], [matrix()], [[0, 999, 999, 999]], [[1, 0, 0, 0]],
        )
        self.assertEqual((joints, indices, weights), ([0], [[0, 0, 0, 0]], [[1, 0, 0, 0]]))


if __name__ == '__main__':
    unittest.main()
