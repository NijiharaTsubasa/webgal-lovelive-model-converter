"""Small source-binding fixtures for ordinary LLAS face companion export."""
import copy
from pathlib import Path
import struct
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import zlib

from converter.llas.face_companions import (
    assemble_companions, build_face_behavior, source_companions, streamed_polynomials,
)


def packed_stream(frames, curve_count=0, dense_count=0):
    raw = b"".join(struct.pack("<fi", time, len(keys)) + b"".join(
        struct.pack("<i4f", *key) for key in keys) for time, keys in frames)
    return SimpleNamespace(
        m_StreamedClip=SimpleNamespace(data=list(struct.unpack(f"<{len(raw)//4}I", raw)),
                                      curveCount=curve_count),
        m_DenseClip=SimpleNamespace(m_CurveCount=dense_count),
    )


def source_node(path="Face_Root/Eye", position=(0, 0, 0), rotation=(0, 0, 0, 1),
                scale=(1, 1, 1), enabled=False):
    return dict(path=path, position=dict(zip("xyz", position)),
                rotation=dict(zip("xyzw", rotation)), scale=dict(zip("xyz", scale)),
                active=True, enabled=enabled)


def companion_source(name="eye/Close", companions=None):
    return dict(name=name, clip_name=name.replace("/", "_"), source=Path("fixture-source.ab"),
                bundle=Path("fixture-stage.ab"), path_id=17, domain="eye", index=1,
                companions=companions or [])


class FaceCompanionSourceTests(unittest.TestCase):
    def extract(self, bindings, constants=(), curves=None, packed=None):
        packed = packed if packed is not None else packed_stream([])
        eye = SimpleNamespace(m_Children=[], m_GameObject=SimpleNamespace(
            read=lambda: SimpleNamespace(m_Name="Eye")))
        root = SimpleNamespace(m_Children=[SimpleNamespace(read=lambda: eye)])
        face = SimpleNamespace(face_root=root)
        clip = SimpleNamespace(m_MuscleClip=SimpleNamespace(
            m_Clip=SimpleNamespace(data=packed), m_StartTime=0, m_StopTime=1))
        reader = SimpleNamespace(type=SimpleNamespace(name="AnimationClip"), path_id=17,
                                 read=lambda: clip,
                                 read_typetree=lambda: {"m_ClipBindingConstant": {"genericBindings": bindings}})
        with patch("converter.llas.face_companions.UnityPy.load", return_value=SimpleNamespace(objects=[reader])), \
                patch.object(Path, "read_bytes", return_value=b"fixture"), \
                patch("converter.llas.face_companions.packed_clip_values", return_value=(list(constants), curves or {})):
            return source_companions(face, [companion_source()])[0]["companions"]

    @staticmethod
    def binding(kind=4, attribute=1):
        return dict(typeID=kind, attribute=attribute,
                    path=zlib.crc32(b"Eye") & 0xffffffff, isPPtrCurve=False)

    def test_stream_preserves_cubic_coefficients_and_ignores_infinite_sentinels(self):
        packed = packed_stream([
            (-float("inf"), [(0, 9, 9, 9, 9)]),
            (0, [(0, 2, -3, 4, 0), (1, 0, 0, 0, 1)]),
            (.5, [(0, -4, 2, .25, 1)]),
            (float("inf"), [(0, 8, 8, 8, 8)]),
        ])
        self.assertEqual(streamed_polynomials(packed), {
            0: [[0, 2, -3, 4, 0], [.5, -4, 2, .25, 1]],
            1: [[0, 0, 0, 0, 1]],
        })

    def test_constant_trs_binding_keeps_property_identity(self):
        result = self.extract([self.binding(attribute=a) for a in (1, 2, 3)],
                              constants=[0, .2, .3, 0, 0, 0, 1, 1, 1, 1])
        self.assertEqual(result, [dict(path="Eye", property="position", value=[0, .2, .3]),
                                  dict(path="Eye", property="quaternion"),
                                  dict(path="Eye", property="scale", value=[1, 1, 1])])

    def test_variable_trs_samples_are_not_silently_reduced_to_endpoint(self):
        with self.assertRaisesRegex(ValueError, "Nonconstant face TRS requires"):
            self.extract([self.binding()], curves={0: [(0, 0), (1, .5)],
                                                  1: [(0, 0)], 2: [(0, 0)]},
                         packed=packed_stream([], curve_count=3))

    def test_equal_key_values_do_not_hide_nonconstant_cubic_trs(self):
        with self.assertRaisesRegex(ValueError, "Nonconstant face TRS polynomial"):
            self.extract([self.binding()], curves={i: [(0, 0), (1, 0)] for i in range(3)},
                         packed=packed_stream([(0, [(0, 1, -1, 0, 0)])], curve_count=3))

    def test_visibility_retains_streamed_polynomial_and_duration(self):
        packed = packed_stream([(0, [(0, 2, -3, 1, 0)]),
                                (1, [(0, 0, 0, 0, 1)]),
                                (2, [(0, 0, 0, 0, 1)])], curve_count=1)
        result = self.extract([self.binding(25, 3305885265)],
                              curves={0: [(0, 0), (1, 1), (2, 1)]}, packed=packed)
        self.assertEqual(result, [dict(path="Eye", property="visible", length=1,
                                       curve=[[0, 2, -3, 1, 0], [1, 0, 0, 0, 1]])])

    def test_constant_visibility_and_morph_offsets_remain_correct(self):
        result = self.extract([self.binding(137, 12345), self.binding(137, 3305885265)],
                              constants=[100, 0])
        self.assertEqual(result, [dict(path="Eye", property="visible", length=1,
                                       curve=[[0, 0, 0, 0, 0]])])

    def test_dense_visibility_requires_recovery_instead_of_guessing(self):
        with self.assertRaisesRegex(ValueError, "Dense visibility"):
            self.extract([self.binding(25, 3305885265)], curves={0: [(0, 0), (1, 1)]},
                         packed=packed_stream([], dense_count=1))


class FaceCompanionAssemblyTests(unittest.TestCase):
    @staticmethod
    def report(source, default, sampled):
        return dict(defaults=[default], clips=[dict(name=source["clip_name"], bundle=source["bundle"],
                    poses=[dict(nodes=[node]) for node in sampled])])

    def test_default_trs_is_constant_folded_but_visibility_is_preserved(self):
        default = source_node()
        source = companion_source(companions=[
            dict(path=default["path"], property="scale", value=[1, 1, 1]),
            dict(path=default["path"], property="visible", length=1, curve=[[0, 0, 0, 0, 0]]),
        ])
        result = assemble_companions([source], self.report(source, default, [copy.deepcopy(default)]))
        self.assertEqual(result, {"bindings": [dict(path=default["path"], property="visible", default=False,
            poses=[dict(name="eye/Close", length=1, curve=[[0, 0, 0, 0, 0]])])]})

    def test_nondefault_trs_retains_all_recipes_including_default_valued_recipe(self):
        default = source_node()
        first = companion_source(companions=[dict(path=default["path"], property="scale", value=[1, 1, 1])])
        second = companion_source("eye/Closish", companions=[dict(path=default["path"], property="scale", value=[1, .9, 1])])
        report = self.report(first, default, [copy.deepcopy(default)])
        report["clips"].extend(self.report(second, default, [source_node(scale=(1, .9, 1))])["clips"])
        result = assemble_companions([first, second], report)
        self.assertEqual(result["bindings"], [dict(path=default["path"], property="scale", default=[1, 1, 1],
            poses=[dict(name="eye/Close", value=[1, 1, 1]), dict(name="eye/Closish", value=[1, .9, 1])])])

    def test_native_samples_must_confirm_constant_trs_and_existing_targets(self):
        default = source_node()
        source = companion_source(companions=[dict(path=default["path"], property="position", value=[0, 0, 0])])
        with self.assertRaisesRegex(ValueError, "Native face transform is not constant"):
            assemble_companions([source], self.report(source, default, [default, source_node(position=(.1, 0, 0))]))
        with self.assertRaisesRegex(ValueError, "Missing native companion node"):
            assemble_companions([source], self.report(source, default, [source_node(path="other")]))

    def test_source_constant_position_survives_single_clip_native_constant_fold(self):
        default = source_node()
        source = companion_source(companions=[dict(path=default["path"], property="position", value=[.000002, 0, 0])])
        result = assemble_companions([source], self.report(source, default, [copy.deepcopy(default)]))
        self.assertEqual(result["bindings"][0]["poses"], [dict(name="eye/Close", value=[.000002, 0, 0])])

    def test_quaternion_uses_native_value_instead_of_source_vector_shortcut(self):
        default = source_node()
        source = companion_source(companions=[dict(path=default["path"], property="quaternion")])
        result = assemble_companions([source], self.report(source, default, [source_node(rotation=(0, .6, 0, .8))]))
        self.assertEqual(result["bindings"][0]["poses"], [dict(name="eye/Close", value=[0, .6, 0, .8])])


class FaceCompanionBehaviorTests(unittest.TestCase):
    @staticmethod
    def sampled():
        return {"bindings": [
            dict(path="Face_Root/Eye", property="position", default=[1, 2, 3],
                 poses=[dict(name="eye/Close", value=[4, 5, 6])]),
            dict(path="Face_Root/Eye", property="quaternion", default=[0, 0, 0, 1],
                 poses=[dict(name="eye/Close", value=[0, .6, 0, .8])]),
            dict(path="Face_Root/Eye", property="scale", default=[1, 1, 1],
                 poses=[dict(name="eye/Close", value=[1, .9, 1])]),
            dict(path="display_OnOff/WhiteLine", property="visible", default=False,
                 poses=[dict(name="eye/Close", length=1, curve=[[0, 0, 0, 0, 0], [1, 0, 0, 0, 1]])]),
        ]}

    def test_behavior_reflects_trs_only_and_preserves_visibility_curve(self):
        sampled = self.sampled()
        original = copy.deepcopy(sampled)
        behavior = build_face_behavior({"nodes": [dict(name="Eye"), dict(name="WhiteLine", mesh=0)]},
                                       sampled, [dict(name="eye/Close")])
        self.assertEqual(behavior["name"], "LLAS.Face")
        self.assertIs(behavior["required"], True)
        bindings = behavior["parameters"]["bindings"]
        self.assertEqual(bindings[0]["default"], [-1, 2, 3])
        self.assertEqual(bindings[0]["poses"][0]["value"], [-4, 5, 6])
        self.assertEqual(bindings[1]["poses"][0]["value"], [0, -.6, 0, .8])
        self.assertEqual(bindings[2]["poses"][0]["value"], [1, .9, 1])
        self.assertEqual(bindings[3]["poses"], sampled["bindings"][3]["poses"])
        self.assertIs(bindings[3]["default"], False)
        self.assertEqual(sampled, original)

    def test_target_and_recipe_must_exist_and_target_name_must_be_unique(self):
        sampled = {"bindings": self.sampled()["bindings"][:1]}
        for nodes in ([], [dict(name="Eye"), dict(name="Eye")]):
            with self.subTest(nodes=nodes), self.assertRaisesRegex(ValueError, "resolve uniquely"):
                build_face_behavior({"nodes": nodes}, sampled, [dict(name="eye/Close")])
        with self.assertRaisesRegex(ValueError, "no Morph recipe"):
            build_face_behavior({"nodes": [dict(name="Eye")]}, sampled, [dict(name="eye/Open")])

    def test_visibility_requires_exported_mesh_not_just_transform(self):
        sampled = {"bindings": self.sampled()["bindings"][3:]}
        with self.assertRaisesRegex(ValueError, "renderer was not exported"):
            build_face_behavior({"nodes": [dict(name="WhiteLine")]}, sampled, [dict(name="eye/Close")])


if __name__ == "__main__":
    unittest.main()
