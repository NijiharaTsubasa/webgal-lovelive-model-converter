import struct
import unittest
import zlib
from types import SimpleNamespace as O

from converter.bangdream.meteor_texture import extract_raw_mip_chain
from converter.common.glb import GlbBuilder


def block(values):
    return bytes.fromhex('fcfdffffffffffff') + struct.pack('<4H', *values)


def texture(color=1, **changes):
    fields = dict(m_TextureFormat=50, m_ColorSpace=color, m_ImageCount=1,
                  m_TextureDimension=2, m_Width=6, m_Height=12, m_MipCount=2,
                  get_image_data=lambda: block((12345, 23456, 34567, 65535))
                  + block((45678, 34567, 23456, 65535))
                  + block((9876, 8765, 7654, 65535)))
    return O(**(fields | changes))


class RawMipTests(unittest.TestCase):
    def test_original_levels_and_image_row_orientation(self):
        chain = extract_raw_mip_chain(texture())
        self.assertEqual(chain['format'], 'rgba8')
        self.assertEqual([(l['width'], l['height']) for l in chain['levels']], [(6, 12), (3, 6)])
        level0, level1 = chain['levels']
        self.assertEqual(level0['data'][:4], bytes((178, 135, 91, 255)))
        self.assertEqual(level0['data'][-4:], bytes((48, 91, 135, 255)))
        # Level1 is the third source block, not a resized level0.
        self.assertEqual(level1['data'][:4], bytes((38, 34, 29, 255)))

    def test_linear_half_is_little_endian_and_not_u8_quantized(self):
        chain = extract_raw_mip_chain(texture(0))
        self.assertEqual(chain['format'], 'rgba16f')
        raw = chain['levels'][0]['data'][-8:]
        values = struct.unpack('<4e', raw)
        self.assertAlmostEqual(values[0], 12345 / 65535, delta=.0005)
        self.assertNotEqual(values[0], round(values[0] * 255) / 255)
        self.assertEqual(values[3], 1)

    def test_bad_source_and_truncation_fail(self):
        for changes in ({'m_TextureFormat': 4}, {'m_ColorSpace': 3},
                        {'m_ImageCount': 2}, {'m_TextureDimension': 3},
                        {'m_MipsStripped': 1}, {'m_MipCount': 20},
                        {'get_image_data': lambda: b'\0' * 32}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                extract_raw_mip_chain(texture(**changes))

    def test_builder_embeds_exact_levels_and_retains_metadata(self):
        b = GlbBuilder()
        b.document['textures'].append({'sampler': 0, 'extras': {'colorSpace': 'linear'}})
        chain = extract_raw_mip_chain(texture(0))
        b.add_raw_mip_chain(0, chain)
        extras = b.document['textures'][0]['extras']
        self.assertEqual(extras['colorSpace'], 'linear')
        self.assertEqual(b.document['textures'][0]['sampler'], 0)
        for original, encoded in zip(chain['levels'], extras['rawMipChain']['levels']):
            view = b.document['bufferViews'][encoded['bufferView']]
            self.assertEqual(view['byteOffset'] % 4, 0)
            self.assertEqual(b.binary[view['byteOffset']:view['byteOffset']+view['byteLength']], original['data'])
        with self.assertRaises(ValueError):
            b.add_raw_mip_chain(0, chain)

    def test_invalid_chain_does_not_partially_append_bin(self):
        for chain in ({'format': 'rgb8', 'levels': []},
                      {'format': 'rgba8', 'levels': [{'width': 1, 'height': 1, 'data': b''}]},
                      {'format': 'rgba8', 'levels': [{'width': 1, 'height': 1, 'data': b'1234'}]*2}):
            b = GlbBuilder()
            b.document['textures'].append({'extras': {'colorSpace': 'srgb'}})
            with self.assertRaises(ValueError):
                b.add_raw_mip_chain(0, chain)
            self.assertEqual(b.binary, b'')
            self.assertNotIn('rawMipChain', b.document['textures'][0]['extras'])

    def test_deflate_preserves_every_raw_byte_including_half_bit_patterns(self):
        for color in (0, 1):
            b = GlbBuilder()
            b.document['textures'].append({'extras': {'colorSpace': 'linear' if color == 0 else 'srgb'}})
            chain = extract_raw_mip_chain(texture(color))
            b.add_raw_mip_chain(0, chain, compression='deflate')
            stored = b.document['textures'][0]['extras']['rawMipChain']
            self.assertEqual(stored['compression'], 'deflate')
            for raw, encoded in zip(chain['levels'], stored['levels']):
                v = b.document['bufferViews'][encoded['bufferView']]
                compressed = bytes(b.binary[v['byteOffset']:v['byteOffset']+v['byteLength']])
                self.assertEqual(zlib.decompress(compressed), raw['data'])
        b = GlbBuilder()
        b.document['textures'].append({})
        with self.assertRaises(ValueError):
            b.add_raw_mip_chain(0, chain, compression='gzip')
        self.assertEqual(b.binary, b'')


if __name__ == '__main__':
    unittest.main()
