import io
import os
from pathlib import Path
import struct
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from PIL import Image

from converter.common.glb import GlbBuilder
from converter.common.uastc import encode_uastc, IDENTIFIER, texture_key, read_compressed_texture, write_compressed_texture


def texture(size=64, mips=1):
    return SimpleNamespace(m_Name="sample", m_ColorSpace=1,
        m_TextureSettings=SimpleNamespace(m_Aniso=1, m_WrapU=0, m_WrapV=1, m_FilterMode=1),
        m_MipCount=mips, image=Image.new("RGBA", (size, size), (30, 60, 90, 128)),
        object_reader=SimpleNamespace(assets_file=object(), path_id=1))


class UastcTests(unittest.TestCase):
    def test_glb_extension_preserves_sampler_and_metadata(self):
        builder = GlbBuilder(compress_textures=True)
        source = texture(mips=3)
        with patch("converter.common.uastc.read_compressed_texture", return_value=b"encoded") as encode:
            index = builder.add_image(source)
            self.assertEqual(builder.add_image(source), index)
        encode.assert_called_once()
        self.assertEqual(encode.call_args.kwargs['mip_count'], 7)
        entry = builder.document['textures'][index]
        self.assertEqual(entry['extensions'], {'KHR_texture_basisu': {'source': 0}})
        self.assertNotIn('source', entry)
        self.assertEqual(entry['extras']['colorSpace'], 'srgb')
        self.assertEqual(builder.document['samplers'][0]['wrapS'], 10497)
        self.assertEqual(builder.document['samplers'][0]['wrapT'], 33071)
        self.assertEqual(builder.document['images'][0]['mimeType'], 'image/ktx2')
        self.assertIn('KHR_texture_basisu', builder.document['extensionsRequired'])

    def test_default_and_tiny_texture_use_png(self):
        for builder, source in [(GlbBuilder(), texture()), (GlbBuilder(compress_textures=True), texture(32)), (GlbBuilder(compress_textures=True), texture(65))]:
            with patch("converter.common.uastc.read_compressed_texture") as encode:
                builder.add_image(source)
                encode.assert_not_called()
            self.assertEqual(builder.document['images'][0]['mimeType'], 'image/png')

    def test_alpha_endpoint_texture_is_preserved_before_shared_usage(self):
        from converter.hasunosora import HasunosoraModelAdapter
        source = texture()
        pointer = lambda value: SimpleNamespace(deref_parse_as_object=lambda: value)
        material = SimpleNamespace(
            m_Shader=pointer(SimpleNamespace(m_ParsedForm=SimpleNamespace(
                m_Name="Character/ToonShader_CharacterEye"))),
            m_SavedProperties=SimpleNamespace(m_Floats=[("_AlphaClipThreshold", 1.0)],
                m_TexEnvs=[("_MainTex", SimpleNamespace(m_Texture=pointer(source)))]))
        reader = SimpleNamespace(type=SimpleNamespace(name="Material"), read=lambda: material)
        adapter = SimpleNamespace(environment=SimpleNamespace(objects=[reader]))
        builder = GlbBuilder(compress_textures=True)
        HasunosoraModelAdapter.bind_builder(adapter, builder)
        with patch("converter.common.uastc.read_compressed_texture") as encode:
            # First use may belong to a different material. The shared key is
            # already protected before either material is emitted.
            first = builder.add_image(source)
            second = builder.add_image(source)
            encode.assert_not_called()
        self.assertEqual(first, second)
        self.assertEqual(len(builder.document['images']), 1)
        self.assertEqual(builder.document['images'][0]['mimeType'], 'image/png')
        material.m_SavedProperties.m_Floats = [("_AlphaClipThreshold", 0.5)]
        builder = GlbBuilder(compress_textures=True)
        HasunosoraModelAdapter.bind_builder(adapter, builder)
        self.assertEqual(builder.lossless_texture_keys, set())

    def test_missing_precompressed_texture_outputs_png_without_encoder(self):
        with tempfile.TemporaryDirectory() as temp, patch('converter.common.uastc.TEXTURE_ROOT', Path(temp)), patch('converter.common.uastc.encoder_path', side_effect=AssertionError('must not encode')):
            builder = GlbBuilder(compress_textures=True)
            builder.add_image(texture())
            self.assertEqual(builder.document['images'][0]['mimeType'], 'image/png')

    @staticmethod
    def container(width=64, height=64, mips=1):
        payload = bytearray(80 + 24 * mips + mips)
        payload[:12] = IDENTIFIER
        struct.pack_into('<II', payload, 20, width, height)
        struct.pack_into('<I', payload, 40, mips)
        for i in range(mips):
            struct.pack_into('<QQQ', payload, 80 + 24 * i, 80 + 24 * mips + i, 1, 1)
        return bytes(payload)

    def test_pipe_encoder_never_writes_input_png(self):
        data = self.container(mips=7)
        def run(command, **kwargs):
            self.assertEqual(command[-2:], ['-', '-'])
            self.assertEqual(kwargs['input'], b'png')
            self.assertNotIn('TOKTX_OPTIONS', kwargs['env'])
            self.assertIn('--genmipmap', command)
            self.assertEqual(command[command.index('--threads')+1], '2')
            return SimpleNamespace(returncode=0, stdout=data)
        with patch.dict(os.environ, {'TOKTX_OPTIONS': 'ignored'}), patch('converter.common.uastc.subprocess.run', side_effect=run):
            self.assertEqual(encode_uastc(b'png', width=64, height=64, color_space='linear', mip_count=7, threads=2, executable='toktx'), data)

    def test_content_settings_lookup_and_atomic_write(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            args = dict(width=64, height=64, color_space='linear', mip_count=1)
            key = texture_key(b'png', **args)
            target = root / (key + '.ktx2')
            self.assertIsNone(read_compressed_texture(b'png', root=root, **args))
            write_compressed_texture(target, self.container())
            self.assertEqual(read_compressed_texture(b'png', root=root, **args), self.container())
            self.assertIsNone(read_compressed_texture(b'updated', root=root, **args))
            self.assertIsNone(read_compressed_texture(b'png', root=root, **dict(args, color_space='srgb')))
            self.assertEqual(list(root.iterdir()), [target])
            target.write_bytes(self.container()[:-1])
            with self.assertRaisesRegex(RuntimeError, 'mip'):
                read_compressed_texture(b'png', root=root, **args)

    def test_missing_encoder_is_actionable(self):
        with patch.dict(os.environ, {}, clear=True), patch('converter.common.uastc.shutil.which', return_value=None):
            with self.assertRaisesRegex(RuntimeError, 'TOKTX'):
                encode_uastc(b'', width=64, height=64, color_space='linear', mip_count=1)
