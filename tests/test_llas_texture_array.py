"""Check Unity Texture2DArray layer order and row orientation in glTF export."""

from io import BytesIO
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from PIL import Image

from converter.common.glb import GlbBuilder
from converter.llas.materials import _array_layers, _member


class LlasTextureArrayTests(unittest.TestCase):
    def member(self, keywords="", cheek=True, cheek_params=True):
        color = SimpleNamespace(r=1, g=1, b=1, a=1)
        colors = {"_" + name: color for name in ("TintColor", "AmbientColor", "RimlightColor", "RimlightDirection")}
        floats = {"_" + name: 0 for name in ("RimglightPower", "MainTexMipmapBias", "CullMode", "ZWrite", "OutlineStencilComp")}
        if cheek_params:
            floats.update(_CheekIntensity=0.35, _CheekTexArrayIndex=1)
        textures = {"_CheekTex": SimpleNamespace(m_Texture=object())} if cheek else {}
        material = SimpleNamespace(m_Name="head", m_ShaderKeywords=keywords, m_CustomRenderQueue=-1)
        with patch("converter.llas.materials._texture_slots", return_value={"CheekTex": [4, 5]} if cheek else {}) as slots:
            result = _member(GlbBuilder(), material, floats, colors, textures, {})
        return result, slots.call_args.args[2]

    def test_disabled_cheek_retains_source_resource_without_enabling_keyword(self):
        result, slots = self.member()
        self.assertIn("CheekTex", slots)
        self.assertEqual(result["textures"]["CheekTex"], [4, 5])
        self.assertEqual(result["shaderParams"]["CheekIntensity"], 0.35)
        self.assertEqual(result["shaderParams"]["CheekTexArrayIndex"], 1)
        self.assertEqual(result["passes"][0]["extras"]["keywords"], [])

    def test_disabled_cheek_does_not_require_unused_source_parameters(self):
        result, slots = self.member(cheek_params=False)
        self.assertIn("CheekTex", slots)
        self.assertNotIn("CheekIntensity", result["shaderParams"])

    def test_absent_cheek_still_uses_shader_missing_sampler_contract(self):
        for keywords in ("", "_CHEEK_ON"):
            result, _ = self.member(keywords=keywords, cheek=False)
            self.assertNotIn("CheekTex", result["textures"])
            self.assertEqual(result["passes"][0]["extras"]["keywords"], keywords.split())

    def test_layers_keep_index_and_unity_bottom_row_orientation(self):
        # Unity raw RGBA rows start at the bottom. Both layers have different
        # top and bottom colors so a layer swap or missing flip is observable.
        red = bytes((255, 0, 0, 255))
        blue = bytes((0, 0, 255, 255))
        green = bytes((0, 255, 0, 255))
        yellow = bytes((255, 255, 0, 255))
        texture = SimpleNamespace(
            object_reader=SimpleNamespace(assets_file=object(), path_id=1),
            m_Name="cheek-test",
            m_Width=1, m_Height=2, m_Depth=2,
            m_Format=4, m_MipCount=1, m_ColorSpace=1,
            m_TextureSettings=SimpleNamespace(m_WrapU=1, m_WrapV=1, m_FilterMode=1),
            image_data=red + blue + green + yellow,
        )
        builder = GlbBuilder()

        indices = _array_layers(builder, texture, {})

        self.assertEqual(indices, [0, 1])
        self.assertEqual(len(builder.document["images"]), 2)
        self.assertEqual([entry["extras"]["colorSpace"] for entry in builder.document["textures"]],
                         ["srgb", "srgb"])
        for index, expected in enumerate(((blue, red), (yellow, green))):
            image_def = builder.document["images"][index]
            view = builder.document["bufferViews"][image_def["bufferView"]]
            start = view["byteOffset"]
            encoded = builder.binary[start:start + view["byteLength"]]
            with Image.open(BytesIO(encoded)) as image:
                self.assertEqual(image.size, (1, 2))
                self.assertEqual(image.getpixel((0, 0)), tuple(expected[0]))
                self.assertEqual(image.getpixel((0, 1)), tuple(expected[1]))


if __name__ == "__main__":
    unittest.main()
