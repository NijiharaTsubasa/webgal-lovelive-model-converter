import unittest
from io import BytesIO
from types import SimpleNamespace as Object
from unittest.mock import patch

from PIL import Image

from converter.common.glb import GlbBuilder
from converter.bangdream.meteor_material import MeteorMaterialExporter
from converter.bangdream.meteor_material_mapping import MaterialCategory
from converter.bangdream.meteor_source import SHADER_NAMES
from converter.bangdream.meteor_uniform_data import UNIFORM_DATA


class Pointer:
    def __init__(self, target=None, path_id=0):
        self.target, self.m_PathID, self.m_FileID = target, path_id, 0

    def __bool__(self):
        return self.m_PathID != 0

    def deref_parse_as_object(self):
        if self.m_PathID == 0:
            raise AssertionError('null source PPtr must not be dereferenced')
        return self.target


class Texture:
    def __init__(self, *, name='sourceTexture', path_id=17, image=None, mips=1, wrap_u=0, wrap_v=0):
        self.m_Name = name
        self.object_reader = Object(assets_file=object(), path_id=path_id)
        self.m_ColorSpace, self.m_MipCount = 1, mips
        self.m_TextureFormat, self.m_ImageCount, self.m_TextureDimension = 50, 1, 2
        self.m_Width, self.m_Height = (64, 32) if mips > 1 else (2, 2)
        self.m_TextureSettings = Object(m_WrapU=wrap_u, m_WrapV=wrap_v, m_FilterMode=1, m_Aniso=0)
        self._image = image or Image.new('RGBA', (2, 2), (17, 43, 91, 255))

    @property
    def image(self):
        if self.m_MipCount > 1:
            raise AssertionError('MatCap full-resolution image must never be decoded/exported')
        return self._image


def material(shader, *, keywords=None, floats=(), textures=None, setup=None, disabled=()):
    if keywords is None:
        keywords = UNIFORM_DATA['shaders'][shader][0]['keywords']
    envs = {'_MainTex': None, '_BaseMap': None, **(textures or {})}
    result = Object(m_Name='misleading_face_Base',
        m_Shader=Pointer(path_id=next(i for i, n in SHADER_NAMES.items() if n == shader)),
        m_CustomRenderQueue=-1, m_ValidKeywords=list(keywords), m_InvalidKeywords=[],
        disabledShaderPasses=list(disabled),
        m_SavedProperties=Object(m_Floats=list(floats), m_Ints=[], m_Colors=[],
            m_TexEnvs=[(name, Object(m_Texture=Pointer(texture, 0 if texture is None else texture.object_reader.path_id),
                       m_Scale=Object(x=1, y=1), m_Offset=Object(x=0, y=0))) for name, texture in envs.items()]))
    if setup is not None:
        result._meteor_setup = setup
    return result


class MeteorMaterialTests(unittest.TestCase):
    def test_four_source_shader_names_emit_only_standard_runtime_data(self):
        expected = ['garupa-meteor', 'garupa-meteor-offset', 'garupa-meteor-transparent', 'garupa-urp-lit']
        for shader, name in zip(SHADER_NAMES.values(), expected):
            builder = GlbBuilder()
            exporter = MeteorMaterialExporter(builder)
            result = {'name': 'preserved'}
            exporter.adapt_material(material(shader), result)
            self.assertEqual(result['name'], 'preserved')
            extras = result['extras']
            self.assertEqual(set(extras), {'shader', 'shaderParams', 'renderState', 'passes', 'textures'})
            self.assertEqual(extras['shader'], name)
            self.assertEqual(extras['textures'], {})
            self.assertEqual(builder.document['images'], [])
            self.assertTrue(exporter.diagnostics)
            for entry in extras['passes']:
                self.assertEqual(set(entry['extras']), {'lightMode', 'materialKeywords'})

    def test_real_builder_embeds_only_nonzero_required_source_textures(self):
        builder = GlbBuilder()
        source = Texture()
        result = {}
        MeteorMaterialExporter(builder).adapt_material(material('Meteor/MeteorShaderOffset',
            keywords=[], textures={'_MainTex': source, '_ShadowMap': Texture(name='unused')}), result)
        self.assertEqual(result['extras']['textures'], {'_MainTex_with_sampler_MainTex': 0})
        self.assertEqual(len(builder.document['images']), 1)
        extras = builder.document['textures'][0]['extras']
        self.assertEqual(extras, {'colorSpace': 'srgb'})
        image = builder.document['images'][0]
        view = builder.document['bufferViews'][image['bufferView']]
        png = bytes(builder.binary[view['byteOffset']:view['byteOffset'] + view['byteLength']])
        self.assertEqual(Image.open(BytesIO(png)).getpixel((0, 0)), (17, 43, 91, 255))

    def test_shared_source_image_is_embedded_once(self):
        builder = GlbBuilder()
        exporter = MeteorMaterialExporter(builder)
        source = Texture()
        for _ in range(2):
            exporter.adapt_material(material('Meteor/MeteorShaderOffset', keywords=[],
                textures={'_MainTex': source}), {})
        self.assertEqual(len(builder.document['textures']), 1)
        self.assertEqual(len(builder.document['bufferViews']), 1)

    def test_regular_multilevel_texture_exports_png_without_decoding_source_levels(self):
        class OrdinaryTexture(Texture):
            @property
            def image(self):
                return self._image

            def get_image_data(self):
                raise AssertionError('Ordinary texture export must use its PNG image')

        source = OrdinaryTexture(mips=6)
        source.m_ColorSpace = 0
        source.m_TextureSettings.m_Aniso = 2
        builder = GlbBuilder()
        MeteorMaterialExporter(builder).adapt_material(material('Meteor/MeteorShaderOffset',
            keywords=[], textures={'_MainTex': source}), {})
        self.assertEqual(len(builder.document['bufferViews']), 1)
        self.assertEqual(builder.document['textures'][0]['extras'],
                         {'colorSpace': 'linear', 'anisotropy': 2})
        self.assertEqual(builder.document['samplers'][0]['minFilter'], 9985)
        self.assertEqual(builder.document['images'][0]['mimeType'], 'image/png')

    def test_disabled_outline_keeps_depth_reads_and_only_forward_can_remove_width(self):
        result = {}
        source = material('Meteor/MeteorShader', disabled=['OutlineExtension'])
        MeteorMaterialExporter(GlbBuilder()).adapt_material(source, result)
        self.assertEqual(len(result['extras']['passes']), 2)
        self.assertNotIn('_OutlineColor', result['extras']['shaderParams'])
        self.assertIn('_OutlineWidth', result['extras']['shaderParams'])
        source.disabledShaderPasses = ['OutlineExtension', 'DepthOnly']
        MeteorMaterialExporter(GlbBuilder()).adapt_material(source, result)
        self.assertNotIn('_OutlineWidth', result['extras']['shaderParams'])

    def test_bound_texture_not_sampled_by_provided_pass_is_not_embedded(self):
        shader = 'Meteor/MeteorShader'
        combo = next(c for c in UNIFORM_DATA['shaders'][shader]
                     if any('::DepthOnly::' in p and not t for p, t in c['textures_by_pass'].items()))
        builder = GlbBuilder()
        result = {}
        MeteorMaterialExporter(builder).adapt_material(material(shader, keywords=combo['keywords'],
            disabled=['UniversalForward', 'OutlineExtension'], textures={'_MainTex': Texture()}), result)
        self.assertEqual(len(result['extras']['passes']), 1)
        self.assertEqual(result['extras']['passes'][0]['extras']['lightMode'], 'DepthOnly')
        self.assertEqual(result['extras']['textures'], {})
        self.assertEqual(builder.document['images'], [])

    def test_category_override_only_changes_actually_read_specular_field(self):
        shader = 'Meteor/MeteorShader'
        keywords = next(c['keywords'] for c in UNIFORM_DATA['shaders'][shader]
                        if '_SpecularColorBlendMethod' in c['uniforms'])
        result = {}
        MeteorMaterialExporter(GlbBuilder()).adapt_material(material(shader, keywords=keywords,
            setup=MaterialCategory('body', True)), result)
        self.assertEqual(result['extras']['shaderParams']['_SpecularColorBlendMethod'], 7)
        MeteorMaterialExporter(GlbBuilder()).adapt_material(material('Meteor/MeteorShaderOffset',
            keywords=[], setup=MaterialCategory('face', True)), result)
        self.assertNotIn('_SpecularColorBlendMethod', result['extras']['shaderParams'])
        self.assertFalse(any('faceLighting' in p['extras'] for p in result['extras']['passes']))

    def test_face_lighting_is_per_pass_and_requires_evidenced_category_and_read(self):
        shader = 'Meteor/MeteorShader'
        combo = next(c for c in UNIFORM_DATA['shaders'][shader] if '_FaceFrontX' in c['uniforms'])
        result = {}
        exporter = MeteorMaterialExporter(GlbBuilder())
        exporter.adapt_material(material(shader, keywords=combo['keywords'], setup=MaterialCategory('face')), result)
        self.assertNotIn('faceLighting', result['extras'])
        for p in result['extras']['passes']:
            self.assertEqual(p['extras'].get('faceLighting', False), '_FaceFrontX' in combo['uniforms_by_pass'][p['id']])
        exporter.adapt_material(material(shader, keywords=combo['keywords']), result)
        self.assertFalse(any('faceLighting' in p['extras'] for p in result['extras']['passes']))

    def test_matcap_exports_one_selected_level_with_separate_cache_identity(self):
        shader = 'Meteor/MeteorShaderTransparent'
        combo = next(c for c in UNIFORM_DATA['shaders'][shader]
                     if any(t['texture'] == '_MatCapMap' for t in c['textures']))
        source = Texture(name='matcap', mips=6)
        source.m_TextureSettings.m_Aniso = 2
        original_reader = source.object_reader
        builder = GlbBuilder()
        exporter = MeteorMaterialExporter(builder)
        results = []
        with patch('converter.bangdream.meteor_material.extract_matcap_image',
                   side_effect=lambda texture, level: Image.new('RGBA', (64 >> level, 32 >> level), (37, 71, 97, 255))) as extract:
            for level in (2, 2, 3):
                result = {}
                exporter.adapt_material(material(shader, keywords=combo['keywords'],
                    floats=[('_MatCapBlurLevel', level)], textures={'_MatCapMap': source}), result)
                self.assertEqual(result['extras']['shaderParams']['_MatCapBlurLevel'], level)
                self.assertEqual(result['extras']['shaderParams']['_MatCapSourceMip'], level)
                results.append(result)
            self.assertEqual(extract.call_count, 2)
            self.assertEqual([c.args[1] for c in extract.call_args_list], [2, 3])
        slot = '_MatCapMap_with_sampler_MatCapMap'
        self.assertEqual(results[0]['extras']['textures'][slot], results[1]['extras']['textures'][slot])
        self.assertNotEqual(results[0]['extras']['textures'][slot], results[2]['extras']['textures'][slot])
        self.assertEqual(len(builder.document['images']), 2)
        self.assertEqual(source.m_MipCount, 6)
        self.assertEqual((source.m_Width, source.m_Height), (64, 32))
        self.assertIs(source.object_reader, original_reader)
        self.assertEqual(builder.document['samplers'][0]['minFilter'], 9729)
        self.assertTrue(all(t['extras']['anisotropy'] == 2 for t in builder.document['textures']))
        self.assertTrue(all(t['extras'] == {'colorSpace': 'srgb', 'anisotropy': 2}
                            for t in builder.document['textures']))
        for proxy in exporter._matcaps.values():
            self.assertEqual(proxy.m_MipCount, 1)
            self.assertIsNot(proxy.object_reader.assets_file, source.object_reader.assets_file)

    def test_unbound_matcap_uses_white_default_and_source_mip_zero(self):
        shader = 'Meteor/MeteorShaderTransparent'
        combo = next(c for c in UNIFORM_DATA['shaders'][shader]
                     if any(t['texture'] == '_MatCapMap' for t in c['textures']))
        builder = GlbBuilder()
        result = {}
        with patch('converter.bangdream.meteor_material.extract_matcap_image') as extract:
            MeteorMaterialExporter(builder).adapt_material(material(shader, keywords=combo['keywords'],
                floats=[('_MatCapBlurLevel', 2.5)], textures={'_MatCapMap': None}), result)
            extract.assert_not_called()
        self.assertEqual(result['extras']['shaderParams']['_MatCapSourceMip'], 0)
        self.assertEqual(builder.document['images'], [])

    def test_fractional_bound_matcap_and_nonrepeat_regular_texture_fail(self):
        shader = 'Meteor/MeteorShaderTransparent'
        combo = next(c for c in UNIFORM_DATA['shaders'][shader]
                     if any(t['texture'] == '_MatCapMap' for t in c['textures']))
        for level in (-1, 1.5):
            with self.assertRaisesRegex(ValueError, 'integral _MatCapBlurLevel'):
                MeteorMaterialExporter(GlbBuilder()).adapt_material(material(shader, keywords=combo['keywords'],
                    floats=[('_MatCapBlurLevel', level)], textures={'_MatCapMap': Texture(mips=6)}), {})
        for u, v in ((1, 0), (0, 2)):
            with self.assertRaisesRegex(ValueError, 'Repeat wrap'):
                MeteorMaterialExporter(GlbBuilder()).adapt_material(material('Meteor/MeteorShaderOffset', keywords=[],
                    textures={'_MainTex': Texture(wrap_u=u, wrap_v=v)}), {})


if __name__ == '__main__':
    unittest.main()
