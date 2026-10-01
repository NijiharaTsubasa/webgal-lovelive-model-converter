import unittest
from types import SimpleNamespace

from converter.common.glb import srgb_channel_to_linear, unity_color_to_linear_rgba


class GlbColorSpaceTests(unittest.TestCase):
    def test_unity_color_rgb_becomes_linear_but_alpha_is_unchanged(self):
        color = SimpleNamespace(r=0.19607843, g=0.5, b=1.0, a=0.25)

        converted = unity_color_to_linear_rgba(color)

        self.assertAlmostEqual(converted[0], 0.03189603, places=7)
        self.assertAlmostEqual(converted[1], 0.21404114, places=7)
        self.assertEqual(converted[2], 1.0)
        self.assertEqual(converted[3], 0.25)

    def test_srgb_linear_segment_is_preserved(self):
        self.assertAlmostEqual(srgb_channel_to_linear(0.02), 0.02 / 12.92)


if __name__ == "__main__":
    unittest.main()
