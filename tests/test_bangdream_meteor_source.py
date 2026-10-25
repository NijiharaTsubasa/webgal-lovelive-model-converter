import json
import unittest
from types import SimpleNamespace as Object

from converter.bangdream.meteor_source import (
    SHADER_NAMES, material_snapshot, pointer_snapshot, renderer_snapshot, shader_snapshot,
)


class Pointer:
    def __init__(self, path_id, file_id=0, target=None):
        self.m_PathID = path_id
        self.m_FileID = file_id
        self.target = target

    def __bool__(self):
        return self.m_PathID != 0

    def deref_parse_as_object(self):
        if self.m_PathID == 0:
            raise AssertionError("null PPtr must not be dereferenced")
        if self.target is None:
            raise AssertionError("material and texture pointers must not be dereferenced")
        return self.target


class MeteorSourceTests(unittest.TestCase):
    def test_four_source_shader_ids_are_explicit_and_negative(self):
        expected = {
            -5077109074445152229: "Meteor/MeteorShader",
            -1458684833486557259: "Meteor/MeteorShaderOffset",
            -694225609340431268: "Meteor/MeteorShaderTransparent",
            -2437954453210527100: "Universal Render Pipeline/Lit",
        }
        self.assertEqual(SHADER_NAMES, expected)
        for path_id, name in expected.items():
            snapshot = shader_snapshot(Pointer(path_id, file_id=3), require_known=True)
            self.assertEqual(snapshot, {"pointer": {"path_id": path_id, "file_id": 3}, "name": name})

    def test_unknown_shader_preserves_pointer_or_explicitly_fails(self):
        material = Object(m_Name="HasEyeLikeProperties", m_Shader=Pointer(-999, 7),
                          m_SavedProperties=Object(m_Floats=[("_MainColor", .3)]))
        snapshot = material_snapshot(material)
        self.assertEqual(snapshot["shader"], {"pointer": {"path_id": -999, "file_id": 7}, "name": None})
        with self.assertRaisesRegex(ValueError, "Unrecognized"):
            material_snapshot(material, require_known_shader=True)

    def test_missing_fields_stay_missing_without_defaults(self):
        self.assertEqual(material_snapshot(Object()), {})
        self.assertEqual(material_snapshot(Object(m_SavedProperties=Object())), {"saved_properties": {}})
        self.assertEqual(renderer_snapshot(Object()), {})
        with self.assertRaisesRegex(ValueError, "no serialized Shader"):
            material_snapshot(Object(), require_known_shader=True)

    def test_saved_properties_preserve_nonendpoint_values_types_and_order(self):
        material = Object(m_Name="Face_01", m_Shader=Pointer(-5077109074445152229),
            m_CustomRenderQueue=-1, m_ValidKeywords=["_USE_SHADING", "_USE_NORMALMAP"],
            m_InvalidKeywords=["STALE", "STALE"], m_ShaderKeywords=" legacy  text ",
            m_SavedProperties=Object(
                m_Floats=[("_Opacity", .371), ("_Opacity", -.25)],
                m_Ints=[("_Enum", 7), ("_UnsignedBits", 0xffffffff)],
                m_Colors=[("_ColorOrVector", Object(r=.13, g=-.22, b=1.37, a=.43))],
                m_Vectors=[("_Vector", Object(x=.19, y=.27, z=-.41, w=1.9))],
                m_TexEnvs=[("_MainTex", Object(m_Texture=Pointer(-871, 2),
                    m_Scale=Object(x=1.37, y=.81), m_Offset=Object(x=-.23, y=.19)))]))
        snapshot = material_snapshot(material)
        self.assertEqual(snapshot["name"], "Face_01")
        self.assertEqual(snapshot["custom_render_queue"], -1)
        self.assertEqual(snapshot["m_ValidKeywords"], ["_USE_SHADING", "_USE_NORMALMAP"])
        self.assertEqual(snapshot["m_InvalidKeywords"], ["STALE", "STALE"])
        self.assertEqual(snapshot["m_ShaderKeywords"], " legacy  text ")
        saved = snapshot["saved_properties"]
        self.assertEqual(saved["m_Floats"], [{"name": "_Opacity", "value": .371}, {"name": "_Opacity", "value": -.25}])
        self.assertIs(type(saved["m_Ints"][0]["value"]), int)
        self.assertEqual(saved["m_Ints"][1]["value"], 0xffffffff)
        self.assertEqual(saved["m_Colors"][0]["value"], [.13, -.22, 1.37, .43])
        self.assertEqual(saved["m_Vectors"][0]["value"], [.19, .27, -.41, 1.9])
        self.assertEqual(saved["m_TexEnvs"][0]["value"], {
            "texture": {"path_id": -871, "file_id": 2}, "scale": [1.37,.81], "offset": [-.23,.19]})
        material.m_ValidKeywords.append("LATER")
        self.assertEqual(snapshot["m_ValidKeywords"], ["_USE_SHADING", "_USE_NORMALMAP"])
        self.assertEqual(json.loads(json.dumps(snapshot)), snapshot)

    def test_null_texture_pointer_and_missing_st_are_not_invented(self):
        source = Object(m_SavedProperties=Object(m_TexEnvs=[("_NormalMap", Object(m_Texture=Pointer(0, 2)))]))
        self.assertEqual(material_snapshot(source)["saved_properties"]["m_TexEnvs"], [
            {"name": "_NormalMap", "value": {"texture": {"path_id": 0, "file_id": 2}}}])
        self.assertEqual(pointer_snapshot(None), None)
        self.assertEqual(pointer_snapshot(Object(m_PathID=-15)), {"path_id": -15})

    def test_renderer_keeps_original_slots_and_source_layer(self):
        go = Object(m_Name="Eye", m_Layer=25, m_IsActive=False)
        renderer = Object(m_GameObject=Pointer(-10, target=go), m_Enabled=True,
                          m_Materials=[Pointer(-123), Pointer(0), None, Pointer(-123)])
        snapshot = renderer_snapshot(renderer)
        self.assertEqual(snapshot, {
            "enabled": True,
            "materials": [{"path_id": -123, "file_id": 0}, {"path_id": 0, "file_id": 0}, None,
                          {"path_id": -123, "file_id": 0}],
            "game_object": {"path_id": -10, "file_id": 0},
            "game_object_name": "Eye", "layer": 25, "active": False})

    def test_empty_game_object_does_not_dereference_or_supply_layer(self):
        self.assertEqual(renderer_snapshot(Object(m_GameObject=Pointer(0), m_Enabled=0)), {
            "enabled": False, "game_object": {"path_id": 0, "file_id": 0}})
        self.assertEqual(renderer_snapshot(Object(), game_object=Object(m_Layer=31)), {"layer": 31})

    def test_invalid_integer_bool_and_layer_fields_fail_instead_of_coercing(self):
        for value in (3.4, True, "4"):
            with self.subTest(value=value), self.assertRaises(TypeError):
                material_snapshot(Object(m_SavedProperties=Object(m_Ints=[("_Enum", value)])))
        with self.assertRaises(TypeError):
            material_snapshot(Object(m_ValidKeywords="_A _B"))
        with self.assertRaises(TypeError):
            material_snapshot(Object(m_CustomRenderQueue=2000.5))
        with self.assertRaises(ValueError):
            renderer_snapshot(Object(), game_object=Object(m_Layer=32))
        with self.assertRaises(TypeError):
            renderer_snapshot(Object(m_Enabled="false"))


if __name__ == "__main__":
    unittest.main()
