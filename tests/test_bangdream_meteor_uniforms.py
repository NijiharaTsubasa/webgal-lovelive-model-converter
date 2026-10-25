import copy
import struct
import unittest
from unittest.mock import patch

from converter.bangdream.meteor_uniforms import (
    UnresolvedMaterialUniform, resolve_meteor_uniforms,
)
from converter.bangdream.meteor_uniform_data import UNIFORM_DATA
from converter.bangdream.meteor_passes import SOURCE_CONTRACTS, resolve_meteor_passes
from converter.bangdream.meteor_color import UnresolvedMaterialColor, unity_gamma_to_linear


def snapshot(shader, keywords, **saved):
    textures = [("_MainTex", {"scale": [1.37, .81], "offset": [-.23, .19]}),
                ("_BaseMap", {"scale": [.79, 1.21], "offset": [.13, -.27]})]
    values = {"m_TexEnvs": textures, **saved}
    return {"shader": {"name": shader}, "m_ValidKeywords": keywords, "custom_render_queue": -1,
            "saved_properties": {f: [{"name": n, "value": v} for n, v in entries]
                                 for f, entries in values.items()}}


class MeteorUniformTests(unittest.TestCase):
    def test_real_disabled_outline_material_omits_only_outline_reads(self):
        # Final corpus costume/000_cos_monthly_2023_10.json,
        # CH000_monthly_2023_10_body_Mask_02, path_id -3832437117249453279.
        shader = 'Meteor/MeteorShader'
        keywords = ['_USE_ALPHACLIP', '_USE_MAIN_LIGHT_COLOR', '_USE_MATCAP',
                    '_USE_NORMALMAP', '_USE_RIMLIGHT', '_USE_SHADING',
                    '_USE_SHADING_CONTROL', '_USE_SPECULAR']
        value = snapshot(shader, keywords)
        value['disabledShaderPasses'] = ['OutlineExtension']
        value['custom_render_queue'] = 2450
        output = resolve_meteor_uniforms(value)
        self.assertIn('_MainTex_ST', output['shaderParams'])
        self.assertIn('_BaseColor', output['shaderParams'])
        # DepthOnly retains the same original outline-expanding vertex program
        # (slot106, b3a95655...484f1), so width/ZOffset remain actual reads.
        self.assertIn('_OutlineWidth', output['shaderParams'])
        self.assertIn('_OutlineZOffset', output['shaderParams'])
        for field in ('_OutlineColor', '_OutlineColorMode', '_OutlineColorBlendMethod', '_OutlineColorRatio'):
            self.assertNotIn(field, output['shaderParams'])
        provided = [p['id'] for p in resolve_meteor_passes(value)['passes']]
        self.assertEqual(output, resolve_meteor_uniforms(value, pass_ids=provided))
        combination = next(c for c in UNIFORM_DATA['shaders'][shader]
                           if c['keywords'] == sorted(keywords))
        textures = {t['texture'] for p in provided for t in combination['textures_by_pass'][p]}
        self.assertIn('_MainTex', textures)
        self.assertNotIn('_OutlineZOffsetMask', textures)
        outline_id = next(p for p in combination['uniforms_by_pass'] if '::Outline::' in p)
        self.assertIn('_OutlineWidth', combination['uniforms_by_pass'][outline_id])

    def test_explicit_provided_pass_selection_validates_ids_and_unions_stage_reads(self):
        shader = 'Meteor/MeteorShader'
        combo = UNIFORM_DATA['shaders'][shader][0]
        value = snapshot(shader, combo['keywords'])
        depth = next(p for p in combo['uniforms_by_pass'] if '::DepthOnly::' in p)
        result = resolve_meteor_uniforms(value, pass_ids=[depth])
        self.assertEqual(set(result['shaderParams']), set(combo['uniforms_by_pass'][depth]))
        self.assertIn('_OutlineWidth', result['shaderParams'])
        forward = next(p for p in combo['uniforms_by_pass'] if '::ForwardLit::' in p)
        self.assertNotIn('_OutlineWidth', resolve_meteor_uniforms(value, pass_ids=[forward])['shaderParams'])
        for invalid in ([], ['unknown'], depth, [depth, depth]):
            with self.assertRaises(ValueError):
                resolve_meteor_uniforms(value, pass_ids=invalid)

    def test_all_75_observed_combinations_resolve_exact_required_fields(self):
        count = 0
        for shader, combinations in UNIFORM_DATA['shaders'].items():
            for combo in combinations:
                output = resolve_meteor_uniforms(snapshot(shader, combo['keywords']))
                self.assertEqual(set(output['shaderParams']), set(combo['uniforms']))
                self.assertEqual(set(output['uniformTypes']), set(combo['uniforms']))
                self.assertTrue(all(k.startswith('_') for k in output['shaderParams']))
                self.assertNotIn('_FaceFrontY', output['shaderParams'])
                self.assertNotIn('_FaceRightY', output['shaderParams'])
                self.assertNotIn('unity_ObjectToWorld', output['shaderParams'])
                self.assertNotIn('_WorldSpaceCameraPos', output['shaderParams'])
                self.assertEqual(set(combo['uniforms']),
                                 {f for fields in combo['uniforms_by_pass'].values() for f in fields})
                self.assertEqual({t['uniform'] for t in combo['textures']},
                                 {t['uniform'] for textures in combo['textures_by_pass'].values() for t in textures})
                count += 1
        self.assertEqual(count, 75)
        self.assertEqual(len(UNIFORM_DATA['fields']), 46)

    def test_offset_minimal_combo_has_only_three_real_reads(self):
        output = resolve_meteor_uniforms(snapshot('Meteor/MeteorShaderOffset', []),
            color_to_linear=lambda value: value * 2)
        self.assertEqual(output['shaderParams'], {'_BaseColor': [2, 2, 2, 1],
            '_GlobalOpacity': 1.0, '_MainTex_ST': [1.37, .81, -.23, .19]})
        self.assertEqual(output['uniformTypes']['_BaseColor'], {'type': 'half', 'width': 4, 'array': None})

    def test_actual_read_width_preserved_color_rgb_only_and_no_half_narrowing(self):
        shader = 'Meteor/MeteorShader'
        kw = UNIFORM_DATA['shaders'][shader][0]['keywords']
        calls = []

        def provider(value):
            calls.append(value)
            return value + .123456789

        output = resolve_meteor_uniforms(snapshot(shader, kw,
            m_Colors=[('_OutlineColor', [.17, .29, .43, .731]),
                      ('_BaseColor', [.19, .37, .61, .413])],
            m_Floats=[('_OutlineColorRatio', .37123456789)]), color_to_linear=provider)
        params = output['shaderParams']
        self.assertEqual(params['_OutlineColor'], [.17 + .123456789, .29 + .123456789, .43 + .123456789])
        self.assertEqual(output['uniformTypes']['_OutlineColor'], {'type': 'half', 'width': 3, 'array': None})
        self.assertEqual(params['_BaseColor'][-1], .413)
        self.assertNotIn(.731, calls)
        self.assertNotIn(.413, calls)
        self.assertEqual(params['_OutlineColorRatio'], .37123456789)
        self.assertIs(type(params['_OutlineColorMode']), int)

    def test_float_and_vector_properties_do_not_receive_color_transform(self):
        shader = 'Meteor/MeteorShaderOffset'
        contracts = copy.deepcopy(SOURCE_CONTRACTS)
        contracts[shader]['properties']['_BaseColor']['type'] = 'Vector'
        with patch('converter.bangdream.meteor_uniforms.SOURCE_CONTRACTS', contracts):
            output = resolve_meteor_uniforms(snapshot(shader, [],
                m_Colors=[('_BaseColor', [.13, -.22, 1.37, .43])],
                m_Floats=[('_GlobalOpacity', .371)]),
                color_to_linear=lambda value: self.fail('Vector/Float must not be transformed'))
        self.assertEqual(output['shaderParams']['_BaseColor'], [.13, -.22, 1.37, .43])
        self.assertEqual(output['shaderParams']['_GlobalOpacity'], .371)

    def test_urp_uses_its_only_observed_combo_and_no_unread_material_properties(self):
        shader = 'Universal Render Pipeline/Lit'
        output = resolve_meteor_uniforms(snapshot(shader,
            ['_SURFACE_TYPE_TRANSPARENT', '_ALPHAPREMULTIPLY_ON'],
            m_Floats=[('_Smoothness', .371), ('_Metallic', .219), ('_Surface', 1),
                      ('_Cutoff', .123), ('_BumpScale', .875)]), color_to_linear=lambda v: v)
        self.assertEqual(output['shaderParams'], {'_BaseColor': [1, 1, 1, 1],
            '_BaseMap_ST': [.79, 1.21, .13, -.27], '_Smoothness': .371,
            '_Metallic': .219, '_Surface': 1})

    def test_unknown_keyword_states_missing_st_and_ambiguous_fields_fail(self):
        shader = 'Meteor/MeteorShaderOffset'
        for changes in ({'shader': {'name': 'unknown'}}, {'m_ValidKeywords': ['_UNKNOWN']},
                        {'m_ValidKeywords': None}):
            value = snapshot(shader, [])
            value.update(changes)
            with self.assertRaises(ValueError):
                resolve_meteor_uniforms(value, color_to_linear=lambda v: v)
        with self.assertRaisesRegex(UnresolvedMaterialUniform, 'scale/offset'):
            resolve_meteor_uniforms(snapshot(shader, [], m_TexEnvs=[]), color_to_linear=lambda v: v)
        with self.assertRaisesRegex(ValueError, 'Ambiguous'):
            resolve_meteor_uniforms(snapshot(shader, [], m_Floats=[('_GlobalOpacity', .3)],
                m_Ints=[('_GlobalOpacity', 1)]), color_to_linear=lambda v: v)

    def test_default_native_color_lookup_preserves_real_nonendpoint_and_hdr_bits(self):
        def from_bits(bits):
            return struct.unpack('<f', struct.pack('<I', bits))[0]

        def bits(value):
            return struct.unpack('<I', struct.pack('<f', value))[0]

        # Literal CPU probe fixtures include the observed slightly-HDR value
        # and a clearly HDR source color; no sRGB extrapolation is used.
        for source, expected in [(0x3f000000, 0x3e5b2d9a),
                                 (0x3f8000ca, 0x3f8001bc),
                                 (0x3f92d603, 0x3fad2204),
                                 (0x3f999a8c, 0x3fbf2cdf)]:
            self.assertEqual(bits(unity_gamma_to_linear(from_bits(source))), expected)
        value = snapshot('Meteor/MeteorShaderOffset', [],
            m_Colors=[('_BaseColor', [.5, from_bits(0x3f8000ca), from_bits(0x3f999a8c), .413])])
        output = resolve_meteor_uniforms(value)['shaderParams']['_BaseColor']
        self.assertEqual([bits(v) for v in output[:3]], [0x3e5b2d9a, 0x3f8001bc, 0x3fbf2cdf])
        self.assertEqual(output[3], .413)

    def test_unknown_native_color_input_never_uses_formula_fallback(self):
        with self.assertRaisesRegex(UnresolvedMaterialColor, 'no formula fallback'):
            unity_gamma_to_linear(-.1)
        value = snapshot('Meteor/MeteorShaderOffset', [],
                         m_Colors=[('_BaseColor', [-.1, .5, 1, .413])])
        with self.assertRaisesRegex(UnresolvedMaterialColor, 'Unresolved original-native'):
            resolve_meteor_uniforms(value)


if __name__ == '__main__':
    unittest.main()
