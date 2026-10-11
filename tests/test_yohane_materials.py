import unittest

from converter.yohane.materials import auxiliary_programs, shader_programs, unity_material_vector


class YohaneMaterialTests(unittest.TestCase):
    def test_hdr_color_preserves_overbright_channels_and_alpha(self):
        source = [.5, .1, 2.996078491, .37]
        self.assertEqual(unity_material_vector(source, 0, 16), source)
        self.assertEqual(unity_material_vector(source, 1, 0), source)

    def test_color_and_gamma_vector_follow_unity_piecewise_transfer(self):
        source = [.02, .5, 2.996078491, .37]
        expected = [.02 / 12.92, ((.5 + .055) / 1.055) ** 2.4, 2.996078491 ** 2.2, .37]
        for kind, flags in [(0, 0), (0, 256), (1, 32)]:
            self.assertEqual(unity_material_vector(source, kind, flags), expected)

    def test_forward_and_normals_select_independent_keyword_variants(self):
        keywords = ['_ALPHATEST_ON', '_FLATNORMAL_ON', '_HAIRHIGHLIGHT_ON']
        shader = 'URP/BX/Toon-DoubleSide'
        color = shader_programs(shader, keywords)
        self.assertEqual(len(color), 2)
        self.assertTrue(all(entry['purpose'] == 'color' for entry in color))
        auxiliary = auxiliary_programs(shader, keywords)
        self.assertEqual(set(auxiliary['DepthNormals']['keywords']), {'_ALPHATEST_ON', '_FLATNORMAL_ON'})
        self.assertEqual(auxiliary['ShadowCaster']['keywords'], ['_ALPHATEST_ON'])

    def test_aura_has_no_unrecovered_normal_pass(self):
        self.assertEqual(auxiliary_programs('URP/BX/ef_outline_aura_generated', []), {})

    def test_unknown_forward_keyword_is_not_silently_ignored(self):
        with self.assertRaises(ValueError):
            shader_programs('URP/BX/Toon', ['_UNKNOWN_ON'])


if __name__ == '__main__':
    unittest.main()
