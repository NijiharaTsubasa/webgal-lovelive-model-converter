import copy
import unittest

from converter.bangdream.meteor_passes import (
    SOURCE_CONTRACTS, resolve_meteor_passes, resolve_pass_state, _queue,
)


def material(shader, *, floats=(), ints=(), colors=(), queue=-1):
    return {"shader": {"name": shader}, "custom_render_queue": queue,
            "saved_properties": {field: [{"name": n, "value": v} for n, v in values]
                                 for field, values in (("m_Floats", floats), ("m_Ints", ints), ("m_Colors", colors))}}


class MeteorPassTests(unittest.TestCase):
    def test_disabled_material_passes_use_case_insensitive_lightmode_not_pass_name(self):
        # Original corpus fixture: costume/000_cos_monthly_2023_10.json,
        # CH000_monthly_2023_10_body_Mask_02, path_id -3832437117249453279,
        # disabled_shader_passes=["OutlineExtension"]. The Pass Name is Outline.
        value = material("Meteor/MeteorShader")
        value["disabledShaderPasses"] = ["OutlineExtension"]
        output = resolve_meteor_passes(value)
        self.assertEqual([p["id"].split("::")[-2] for p in output["passes"]], ["ForwardLit", "DepthOnly"])
        value["disabledShaderPasses"] = ["oUtLiNeExTeNsIoN"]
        self.assertEqual(output["passes"], resolve_meteor_passes(value)["passes"])
        value["disabledShaderPasses"] = ["Outline"]
        self.assertEqual(len(resolve_meteor_passes(value)["passes"]), 3)
        self.assertEqual(sum(len(s["passes"]) for s in SOURCE_CONTRACTS.values()), 15)

    def test_absent_disabled_tag_has_no_effect_and_all_disabled_is_an_error(self):
        # The real 035 birthday Transparent material disables OutlineExtension,
        # which that original Shader does not provide: all four remain present.
        value = material("Meteor/MeteorShaderTransparent")
        value["disabledShaderPasses"] = ["OutlineExtension"]
        self.assertEqual(len(resolve_meteor_passes(value)["passes"]), 4)
        value["disabledShaderPasses"] = [p["lightMode"] for p in SOURCE_CONTRACTS["Meteor/MeteorShaderTransparent"]["passes"]]
        with self.assertRaisesRegex(ValueError, "disables all"):
            resolve_meteor_passes(value)
        for invalid in (None, "OutlineExtension", [1], [""]):
            value["disabledShaderPasses"] = invalid
            with self.assertRaisesRegex(ValueError, "disabledShaderPasses"):
                resolve_meteor_passes(value)

    def test_shaderlab_named_queue_offsets(self):
        self.assertEqual(_queue("Transparent-17"), 2983)
        self.assertEqual(_queue("Geometry+37"), 2037)
        self.assertEqual(_queue(None), 2000)
        with self.assertRaisesRegex(ValueError, "Unsupported original Queue"):
            _queue("GuessTransparent")

    def test_all_fifteen_original_pass_default_states(self):
        # Literal expected queue/cull/zWrite/mask and RGB/alpha blend factors,
        # transcribed from original serialized Shader values and Properties.
        fixtures = {
            "Meteor/MeteorShader": (2000, [
                ("ForwardLit", 0, 1, 15, [1, 0, 1, 0]),
                ("Outline", 1, 1, 15, [1, 0, 1, 0]),
                ("DepthOnly", 0, 1, 0, [1, 0, 1, 0])]),
            "Meteor/MeteorShaderOffset": (3000, [
                ("ForwardLit", 2, 1, 15, [1, 0, 1, 0]),
                ("Offset", 2, 1, 15, [5, 10, 5, 10]),
                ("AlphaWriteOffBase", 2, 1, 14, [1, 0, 1, 0]),
                ("AlphaWriteOffOffset", 2, 1, 14, [5, 10, 5, 10])]),
            "Meteor/MeteorShaderTransparent": (3000, [
                ("ForwardLit", 0, 0, 15, [5, 10, 1, 10]),
                ("Accumulate", 0, 0, 15, [1, 1, 0, 10]),
                ("DepthOnly", 0, 1, 0, [1, 0, 1, 0]),
                ("AlphaOnly", 0, 0, 15, [0, 1, 1, 1])]),
            "Universal Render Pipeline/Lit": (2000, [
                ("ForwardLit", 2, 1, 15, [1, 0, 1, 0]),
                ("DepthOnly", 2, 1, 8, [1, 0, 1, 0]),
                ("DepthNormals", 2, 1, 15, [1, 0, 1, 0]),
                ("Universal2D", 2, 1, 15, [1, 0, 1, 0])]),
        }
        count = 0
        for shader, (queue, expected) in fixtures.items():
            output = resolve_meteor_passes(material(shader))
            self.assertEqual(output["renderState"], {"renderQueue": queue})
            self.assertEqual(len(output["passes"]), len(expected))
            for p, (name, cull, zwrite, mask, factors) in zip(output["passes"], expected):
                count += 1
                self.assertEqual(p["id"].split("::")[-2], name)
                state = p["renderState"]
                self.assertEqual([state["cull"], state["zWrite"], state["colorMask"]], [cull, zwrite, mask])
                self.assertEqual([state["blend"][k] for k in ("srcRgb", "dstRgb", "srcAlpha", "dstAlpha")], factors)
                self.assertEqual([state["blend"]["opRgb"], state["blend"]["opAlpha"], state["zTest"]], [0, 0, 4])
                self.assertNotIn("renderQueue", state)
                self.assertEqual(set(p["extras"]), {"lightMode"})
        self.assertEqual(count, 15)

    def test_saved_values_override_property_defaults_not_serialized_placeholder(self):
        output = resolve_meteor_passes(material("Meteor/MeteorShader", floats=[
            ("_Cull", 2), ("_StencilRef", 173), ("_StencilComp", 6), ("_StencilPass", 2),
            ("_GlobalOpacity", .371)], colors=[("_BaseColor", [.13, -.22, 1.37, .43])], queue=2871))
        forward, outline, depth = output["passes"]
        self.assertEqual(forward["renderState"]["cull"], 2)
        self.assertEqual(outline["renderState"]["cull"], 1)
        for p in (forward, outline):
            self.assertEqual(p["renderState"]["stencil"], {"ref": 173, "readMask": 255,
                "writeMask": 255, "comp": 6, "pass": 2, "fail": 0, "zFail": 0})
        self.assertEqual(depth["renderState"]["stencil"]["comp"], 8)
        self.assertEqual(output["renderState"]["renderQueue"], 2871)
        self.assertEqual(output["properties"]["_GlobalOpacity"]["value"], .371)
        self.assertEqual(output["properties"]["_GlobalOpacity"]["type"], "Range(0, 1)")
        self.assertEqual(output["properties"]["_BaseColor"]["value"], [.13, -.22, 1.37, .43])

    def test_urp_dynamic_state_preserves_separate_alpha_and_explicit_queue(self):
        output = resolve_meteor_passes(material("Universal Render Pipeline/Lit", ints=[("_Cull", 1)],
            floats=[("_SrcBlend", 5), ("_DstBlend", 10), ("_SrcBlendAlpha", 1),
                    ("_DstBlendAlpha", 10), ("_ZWrite", 0), ("_AlphaToMask", 1)], queue=3017))
        state = output["passes"][0]["renderState"]
        self.assertEqual(state["blend"], {"srcRgb": 5, "dstRgb": 10, "srcAlpha": 1,
            "dstAlpha": 10, "opRgb": 0, "opAlpha": 0})
        self.assertEqual([state["zWrite"], state["alphaToMask"], state["cull"]], [0, 1, 1])
        self.assertEqual(output["passes"][1]["renderState"]["zWrite"], 1)
        self.assertEqual(output["renderState"]["renderQueue"], 3017)

    def test_common_attachment_state_never_uses_rtBlend1(self):
        shader = "Meteor/MeteorShaderTransparent"
        props = resolve_meteor_passes(material(shader))["properties"]
        state = copy.deepcopy(SOURCE_CONTRACTS[shader]["passes"][1]["state"])
        state["rtBlend1"] = {"srcBlend": "MISSING", "destBlend": 999}
        output = resolve_pass_state(state, props)
        self.assertEqual(output["blend"]["dstRgb"], 1)
        self.assertEqual(output["blend"]["dstAlpha"], 10)
        state["rtSeparateBlend"] = True
        with self.assertRaisesRegex(ValueError, "Independent attachment"):
            resolve_pass_state(state, props)

    def test_offset_fractional_values_and_unsupported_capabilities_fail_closed(self):
        shader = "Meteor/MeteorShaderOffset"
        props = resolve_meteor_passes(material(shader))["properties"]
        state = copy.deepcopy(SOURCE_CONTRACTS[shader]["passes"][0]["state"])
        state.update(offsetFactor=-.375, offsetUnits=1.125)
        self.assertEqual(resolve_pass_state(state, props)["offset"], {"factor": -.375, "units": 1.125})
        for key, value in (("zClip", 0), ("conservative", 1)):
            changed = copy.deepcopy(state)
            changed[key] = value
            with self.assertRaisesRegex(ValueError, "unsupported standard capability"):
                resolve_pass_state(changed, props)
        state["stencilOpFront"]["pass_"] = 2
        with self.assertRaisesRegex(ValueError, "Face-specific"):
            resolve_pass_state(state, props)

    def test_missing_ambiguous_and_invalid_values_are_not_invented(self):
        shader = "Meteor/MeteorShader"
        for snapshot in [material("unknown"), {"shader": {"name": shader}},
                         material(shader, floats=[("_Cull", .5)]),
                         material(shader, floats=[("_Cull", 0)], ints=[("_Cull", 2)]),
                         material(shader, floats=[("_Cull", 0), ("_Cull", 0)])]:
            with self.assertRaises(ValueError):
                resolve_meteor_passes(snapshot)
        output = resolve_meteor_passes(material(shader))
        props = output["properties"]
        state = copy.deepcopy(SOURCE_CONTRACTS[shader]["passes"][0]["state"])
        state["culling"] = "_NOT_DECLARED"
        with self.assertRaisesRegex(ValueError, "Unresolved render-state"):
            resolve_pass_state(state, props)
        self.assertEqual(props["_MainTex"]["value"], {"shaderlab_default": '"white" { }'})


if __name__ == "__main__":
    unittest.main()
