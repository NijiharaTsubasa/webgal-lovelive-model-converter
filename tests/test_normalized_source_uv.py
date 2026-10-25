import inspect
import struct
import unittest
from types import SimpleNamespace as Object
from unittest.mock import patch

from converter.common.glb import GlbBuilder
import converter.common.normalized_model as nm


class Pointer:
    def __init__(self, value):
        self.value = value

    def deref_parse_as_object(self):
        return self.value


def float32(value):
    return struct.unpack('<f', struct.pack('<f', value))[0]


class SourceUvTests(unittest.TestCase):
    def export(self, channels=(), **uvs):
        builder = GlbBuilder()
        builder.document['nodes'].append({'name': 'root'})
        builder.document['scenes'][0]['nodes'].append(0)
        builder.source_uv_channels = channels
        # Only material decoding is irrelevant to this geometry fixture. The
        # real accessor encoder, binary buffer and renderer export remain used.
        builder.add_material = lambda pointer: 0
        decoded = Object(process=lambda: None,
            m_Vertices=[(0,0,0), (1,0,0), (0,1,0)],
            m_Normals=[], m_Tangents=[], m_BoneIndices=[], m_BoneWeights=[],
            m_UV0=[], get_triangles=lambda: [[(0,1,2)]])
        for key, value in uvs.items():
            setattr(decoded, key, value)
        mesh = Object(m_Name='uv-controls', m_BindPose=[])
        renderer = Object(m_Materials=[])
        identity = nm._trs_to_mat([0,0,0], [0,0,0,1], [1,1,1])
        with patch.object(nm, 'MeshHandler', return_value=decoded), \
                patch.object(nm, 'mesh_morphs', return_value=([],[])):
            nm._add_normalized_renderer(renderer, 0, builder, {}, [identity],
                [identity], [identity], {}, frozenset(), mesh_pointer=Pointer(mesh))
        return builder

    def accessor_bytes(self, builder, name):
        attrs = builder.document['meshes'][0]['primitives'][0]['attributes']
        accessor = builder.document['accessors'][attrs[name]]
        view = builder.document['bufferViews'][accessor['bufferView']]
        raw = bytes(builder.binary[view['byteOffset']:view['byteOffset']+view['byteLength']])
        return accessor, raw

    def test_nonendpoint_source_uv0_float32_bits_survive_without_v_round_trip(self):
        values = [(float32(.371), float32(1e-9)),
                  (float32(-.217), float32(1.837)), (float32(.093), -0.0)]
        builder = self.export((0,), m_UV0=values)
        accessor, raw = self.accessor_bytes(builder, '_SOURCE_UV0')
        self.assertEqual((accessor['count'], accessor['type'], accessor['componentType']), (3,'VEC2',5126))
        self.assertEqual(raw, struct.pack('<6f', *(x for row in values for x in row)))
        texture_accessor, texture_raw = self.accessor_bytes(builder, 'TEXCOORD_0')
        self.assertEqual(texture_accessor['type'], 'VEC2')
        self.assertEqual(struct.unpack('<6f', texture_raw), tuple(float32(x) for row in values for x in (row[0],1-row[1])))
        # Tiny source V is lost if recovered from the flipped texture UV.
        self.assertNotEqual(float32(1-struct.unpack('<6f',texture_raw)[1]), values[0][1])

    def test_uv1_control_values_are_not_flipped_normalized_or_truncated(self):
        for width in (2,3,4):
            values = [tuple(float32(x) for x in (1.37,-.81,.271,-1.9)[:width]),
                      tuple(float32(x) for x in (-.49,.23,-.117,.063)[:width]),
                      tuple(float32(x) for x in (.83,1.29,-.731,.311)[:width])]
            with self.subTest(width=width):
                builder = self.export((1,), m_UV1=values)
                accessor, raw = self.accessor_bytes(builder, '_SOURCE_UV1')
                self.assertEqual(accessor['type'],f'VEC{width}')
                self.assertEqual(raw,struct.pack(f'<{width*3}f',*(x for row in values for x in row)))
                self.assertNotIn('normalized',accessor)

    def test_default_export_emits_only_existing_texture_uv_behavior(self):
        self.assertEqual(inspect.signature(nm.export_normalized_model).parameters['source_uv_channels'].default,())
        values = [(.371,.217),(.837,.163),(.219,.731)]
        builder = self.export(m_UV0=values,m_UV1=values)
        attrs = builder.document['meshes'][0]['primitives'][0]['attributes']
        self.assertIn('TEXCOORD_0',attrs)
        self.assertFalse(any(name.startswith('_SOURCE_UV') for name in attrs))

    def test_missing_source_channels_emit_no_invented_accessor(self):
        for data in ({},{'m_UV1':None},{'m_UV1':[]}):
            with self.subTest(data=data):
                builder = self.export((0,1),**data)
                attrs = builder.document['meshes'][0]['primitives'][0]['attributes']
                self.assertEqual(set(attrs),{'POSITION'})

    def test_invalid_channels_fail_before_export(self):
        for channels in ((0,0),(-1,),(8,),(True,),('1',),(.5,),None):
            with self.subTest(channels=channels),self.assertRaises((TypeError,ValueError)):
                nm.export_normalized_model(None,None,{},source_uv_channels=channels)
        self.assertEqual(nm._validated_source_uv_channels((0,7)),(0,7))

    def test_mismatched_vertex_count_and_component_width_fail(self):
        cases = [([(.2,.3)]*2,'count'),
                 ([(.2,)]*3,'components'),
                 ([(.2,.3,.4,.5,.6)]*3,'components'),
                 ([(.2,.3),(.2,.3,.4),(.2,.3)],'components')]
        for values,message in cases:
            with self.subTest(values=values),self.assertRaisesRegex(ValueError,message):
                self.export((1,),m_UV1=values)

    def test_source_channel_seven_uses_its_requested_identity(self):
        builder=self.export((7,),m_UV7=[(.17,.29),(.31,.43),(.59,.67)])
        accessor,_=self.accessor_bytes(builder,'_SOURCE_UV7')
        self.assertEqual(accessor['type'],'VEC2')


if __name__ == '__main__':
    unittest.main()
