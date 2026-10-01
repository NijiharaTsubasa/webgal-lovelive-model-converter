import unittest
import json
import struct
from pathlib import Path
from types import SimpleNamespace

from PIL import Image
import UnityPy

from converter.common import (
    bundle_metadata, component_pointer, dependency_closure,
    game_object_transform, logical_name,
)
from converter.common.glb import GlbBuilder, unity_color_to_linear_rgba
from converter.hasunosora import HasunosoraModelAdapter, _pose_targets


class HasunosoraPackagingTests(unittest.TestCase):
    def test_shader_colors_and_vectors_do_not_lose_decimal_precision(self):
        value = SimpleNamespace(r=0.12345679104328156, g=0.5432109832763672,
                                b=0.23456789553165436, a=0.8765432238578796)
        extras = GlbBuilder()._melpot_extras(
            SimpleNamespace(m_Name='Face'),
            {'_MainColor': value, '_MainLightOffset': value, '_OutlineColor': value},
            {}, {'_1stShadowStep': 0.5},
        )
        self.assertEqual(extras['shaderParams']['MainLightOffset'], [value.r, value.g, value.b, value.a])
        self.assertEqual(extras['shaderParams']['MainColor'], unity_color_to_linear_rgba(value))
        self.assertEqual(extras['passes'][1]['shaderParams']['OutlineColor'], unity_color_to_linear_rgba(value))

    def test_hasunosora_shader_classification_uses_source_identity(self):
        for source_name, expected in HasunosoraModelAdapter.SHADERS.items():
            shader = SimpleNamespace(m_ParsedForm=SimpleNamespace(m_Name=source_name))
            material = SimpleNamespace(
                m_Name="Face",
                m_Shader=SimpleNamespace(deref_parse_as_object=lambda: shader),
            )
            self.assertEqual(HasunosoraModelAdapter.classify_shader(material), expected)

        unknown = SimpleNamespace(m_ParsedForm=SimpleNamespace(m_Name="Unknown/Shader"))
        material = SimpleNamespace(
            m_Name="Face",
            m_Shader=SimpleNamespace(deref_parse_as_object=lambda: unknown),
        )
        with self.assertRaisesRegex(ValueError, "unsupported source Shader"):
            HasunosoraModelAdapter.classify_shader(material)


    def test_texture_color_space_is_preserved_in_gltf_metadata(self):
        builder = GlbBuilder()
        srgb = SimpleNamespace(
            m_Name="shadow_color",
            m_ColorSpace=1,
            m_MipCount=1,
            m_TextureSettings=SimpleNamespace(m_FilterMode=1, m_WrapU=0, m_WrapV=0),
            image=Image.new("RGBA", (1, 1), (128, 64, 32, 255)),
            object_reader=SimpleNamespace(assets_file=object(), path_id=1),
        )
        linear = SimpleNamespace(
            m_Name="control_mask",
            m_ColorSpace=0,
            m_MipCount=1,
            m_TextureSettings=SimpleNamespace(m_FilterMode=1, m_WrapU=0, m_WrapV=0),
            image=Image.new("RGBA", (1, 1), (128, 64, 32, 255)),
            object_reader=SimpleNamespace(assets_file=object(), path_id=2),
        )

        srgb_index = builder.add_image(srgb)
        linear_index = builder.add_image(linear)

        self.assertEqual(
            builder.document["textures"][srgb_index]["extras"],
            {"colorSpace": "srgb"},
        )
        self.assertEqual(
            builder.document["textures"][linear_index]["extras"],
            {"colorSpace": "linear"},
        )

    def test_melpot_extras_do_not_synthesize_texture_presence_params(self):
        texture = SimpleNamespace()
        pointer = SimpleNamespace(deref_parse_as_object=lambda: texture)
        texture_env = SimpleNamespace(m_Texture=pointer)
        builder = GlbBuilder()
        builder.add_image = lambda value: 0

        extras = builder._melpot_extras(
            SimpleNamespace(m_Name="Body"),
            {},
            {"_ControlMap1": texture_env},
            {"_1stShadowStep": 0.5, "_AlphaClipThreshold": 0.5},
        )

        self.assertEqual(extras["textures"], {"ControlMap1": 0})
        self.assertEqual(extras["passes"], [{"id": "Forward"}])
        self.assertEqual(extras["shaderParams"]["AlphaClipThreshold"], 0.5)
        self.assertNotIn("HasDetailMask", extras["shaderParams"])
        self.assertNotIn("HasMatcapTex", extras["shaderParams"])
        self.assertNotIn("outlineParams", extras)

    def test_melpot_exports_each_compiled_uv_transform(self):
        builder = GlbBuilder()
        def env(scale_x, scale_y, offset_x, offset_y):
            return SimpleNamespace(
                m_Texture=None,
                m_Scale=SimpleNamespace(x=scale_x, y=scale_y),
                m_Offset=SimpleNamespace(x=offset_x, y=offset_y),
            )
        extras = builder._melpot_extras(
            SimpleNamespace(m_Name="Body"), {},
            {
                "_MainTex": env(1.25, 0.75, 0.1, 0.2),
                "_DetailMask": env(2, 3, 0.2, 0.3),
                "_GlossMap": env(4, 5, 0.3, 0.4),
                "_UVTexMask": env(6, 7, 0.4, 0.5),
            },
            {"_1stShadowStep": 0.5},
        )
        self.assertEqual(extras["shaderParams"]["MainTex_ST"], [1.25, 0.75, 0.1, 0.2])
        self.assertEqual(extras["shaderParams"]["DetailMask_ST"], [2, 3, 0.2, 0.3])
        self.assertEqual(extras["shaderParams"]["GlossMap_ST"], [4, 5, 0.3, 0.4])
        self.assertEqual(extras["shaderParams"]["UVTexMask_ST"], [6, 7, 0.4, 0.5])

    def test_melpot_main_texture_transform_reaches_gltf_base_color_sampler(self):
        builder = GlbBuilder()
        builder.shader_classifier = lambda material: "melpot-toon"
        builder.add_image = lambda texture: 0
        tex_pointer = SimpleNamespace(deref_parse_as_object=lambda: object())
        main_env = SimpleNamespace(
            m_Texture=tex_pointer,
            m_Scale=SimpleNamespace(x=1.25, y=0.75),
            m_Offset=SimpleNamespace(x=0.1, y=0.2),
        )
        material = SimpleNamespace(
            object_reader=SimpleNamespace(assets_file=object(), path_id=1),
            m_Name="Body",
            m_CustomRenderQueue=-1,
            m_SavedProperties=SimpleNamespace(
                m_Colors=[], m_TexEnvs=[("_MainTex", main_env)],
                m_Floats=[("_1stShadowStep", 0.5)],
            ),
        )
        index = builder.add_material(SimpleNamespace(deref_parse_as_object=lambda: material))
        info = builder.document["materials"][index]["pbrMetallicRoughness"]["baseColorTexture"]
        self.assertEqual(info["extensions"]["KHR_texture_transform"],
                         {"offset": [0.1, 0.2], "scale": [1.25, 0.75]})
        self.assertIn("KHR_texture_transform", builder.document["extensionsUsed"])

    def test_melpot_outline_is_an_ordered_material_pass(self):
        builder = GlbBuilder()
        extras = builder._melpot_extras(
            SimpleNamespace(m_Name="Body"),
            {},
            {},
            {"_1stShadowStep": 0.5, "_OutlineWidth": 0.003},
        )

        self.assertEqual([entry["id"] for entry in extras["passes"]], ["Forward", "Outline"])
        self.assertEqual(extras["passes"][1]["shaderParams"], {"OutlineWidth": 0.003})
        self.assertEqual(extras["passes"][1]["renderState"], {"cull": 1})
        self.assertNotIn("outlineParams", extras)

    def test_facial_melpot_keeps_its_own_shader_and_active_params(self):
        builder = GlbBuilder()
        builder.add_image = lambda texture: 5
        main_tex = SimpleNamespace(
            m_Texture=SimpleNamespace(deref_parse_as_object=lambda: object()),
            m_Scale=SimpleNamespace(x=1.5, y=2.0),
            m_Offset=SimpleNamespace(x=0.25, y=0.0),
        )
        extras = builder._melpot_extras(
            SimpleNamespace(m_Name="SCSch017Sac_Face_MT"),
            {}, {"_MainTex": main_tex},
            {
                "_1stShadowStep": 0.5,
                "_IsShadeEmissionLightColorContribution": 1.0,
                "_AlphaClipThreshold": 0.5,
            },
            shader_name="melpot-toon-hlslmacros",
        )

        self.assertEqual(extras["shader"], "melpot-toon-hlslmacros")
        self.assertEqual(extras["textures"], {"MainTex": 5})
        self.assertEqual(extras["shaderParams"]["MainTex_ST"], [1.5, 2.0, 0.25, 0.0])
        self.assertEqual(extras["shaderParams"]["IsShadeEmissionLightColorContribution"], 1.0)
        self.assertEqual(extras["shaderParams"]["AlphaClipThreshold"], 0.5)

    def test_melpot_eye_exports_source_uv_transform_and_sampler_slots(self):
        builder = GlbBuilder()
        builder.add_image = lambda texture: 3
        texture_env = SimpleNamespace(
            m_Texture=SimpleNamespace(deref_parse_as_object=lambda: object()),
            m_Scale=SimpleNamespace(x=2.0, y=3.0),
            m_Offset=SimpleNamespace(x=0.25, y=0.5),
        )
        extras = builder._eye_extras(
            SimpleNamespace(m_Name="Eye"),
            {"_MainColor": SimpleNamespace(r=1.0, g=0.5, b=0.0, a=1.0)},
            {"_MainTex": texture_env},
            {"_AddIntensity": 1.0, "_AlphaClipThreshold": 0.5},
            "melpot-toon-eye",
        )

        self.assertEqual(extras["shader"], "melpot-toon-eye")
        self.assertEqual(extras["textures"], {"MainTex": 3})
        self.assertEqual(extras["shaderParams"]["MainTex_ST"], [2.0, 3.0, 0.25, 0.5])
        self.assertEqual(extras["shaderParams"]["MainColor"][0], 1.0)
        self.assertLess(extras["shaderParams"]["MainColor"][1], 0.5)

    def test_character_eye_exports_source_uv_transform(self):
        builder = GlbBuilder()
        builder.add_image = lambda texture: 4
        texture_env = SimpleNamespace(
            m_Texture=SimpleNamespace(deref_parse_as_object=lambda: object()),
            m_Scale=SimpleNamespace(x=1.25, y=0.75),
            m_Offset=SimpleNamespace(x=0.125, y=-0.25),
        )
        extras = builder._eye_extras(
            SimpleNamespace(m_Name="Eye"), {}, {"_MainTex": texture_env},
            {"_AlphaClipThreshold": 0.5}, "character-eye",
        )
        self.assertEqual(extras["shader"], "character-eye")
        self.assertEqual(extras["shaderParams"]["MainTex_ST"], [1.25, 0.75, 0.125, -0.25])

    def test_urp_lit_eye_strip_keeps_material_and_fixed_state(self):
        extras = GlbBuilder._urp_lit_extras(
            SimpleNamespace(m_Name="Default_Material", m_CustomRenderQueue=-1),
            {"_Metallic": 0.0, "_Smoothness": 0.0, "_Cull": 2.0, "_ZWrite": 1.0},
        )
        self.assertEqual(extras["shader"], "urp-lit")
        self.assertEqual(extras["shaderParams"], {"Metallic": 0.0, "Smoothness": 0.0})
        self.assertEqual(extras["renderState"], {"cull": 2.0, "zWrite": 1.0, "renderQueue": 2000})
        self.assertEqual(extras["passes"], [{"id": "Forward"}])


    def test_pose_targets_have_stable_node_and_morph_order(self):
        model = SimpleNamespace(
            builder=SimpleNamespace(
                document={"nodes": [{"name": "Face"}, {"name": "Eye"}]}
            )
        )
        pose = {
            (1, 3, "blink_z"): 0.0,
            (0, 7, "mouth_z"): 1.0,
            (0, 2, "mouth_a"): 0.5,
        }

        targets = _pose_targets(model, pose)

        self.assertEqual(list(targets), ["Face", "Eye"])
        self.assertEqual(list(targets["Face"]), ["mouth_a", "mouth_z"])


if __name__ == "__main__":
    unittest.main()
