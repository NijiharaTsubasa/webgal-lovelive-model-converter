import json
import struct
import tempfile
import unittest
from copy import deepcopy
from contextlib import ExitStack
from collections import defaultdict
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import UnityPy

from converter.common import dependency_closure, logical_name
from converter.common.unity import crc
from converter.hasunosora import (
    ExportedExpression, _clip_pose, _expression_controller_data,
    build_expression_package, convert,
)


def evaluate(package, state, control=None, amount=0):
    poses = {pose["name"]: pose["targets"] for pose in package["morphPoses"]}
    base = state["poses"]
    endpoint = state.get("controls", {}).get(control, {})
    result = {}
    for name in base.keys() | endpoint.keys():
        coefficient = base.get(name, 0) + amount * (endpoint.get(name, base.get(name, 0)) - base.get(name, 0))
        for node, shapes in poses[name].items():
            for shape, value in shapes.items():
                result[node, shape] = result.get((node, shape), 0) + coefficient * value
    return result


class HasunosoraExpressionTests(unittest.TestCase):
    def test_static_source_mouth_is_independent_without_fabricated_speech_control(self):
        model = SimpleNamespace(builder=SimpleNamespace(document={"nodes": [{"name": "Face"}]}))
        face_key = (0, 0, "eye")
        mouth_key = (0, 1, "mouth")
        entry = ExportedExpression("shout", "face", None, ["mouth"])
        with patch("converter.hasunosora._clip_pose", side_effect=lambda clip, _: {
                "face": {face_key: 1, mouth_key: 0.5},
                "mouth": {mouth_key: 1},
        }[clip]):
            package = build_expression_package(model, [entry])
        self.assertEqual(package["morphPoses"][0]["targets"], {"Face": {"eye": 1}})
        self.assertEqual(package["morphPoses"][1]["targets"], {"Face": {"mouth": 1}})
        mouth_state = package["expressionGroups"][1]["states"][0]
        self.assertEqual(mouth_state["poses"], {"mouth.shout": 1})
        self.assertNotIn("controls", mouth_state)

    def test_selected_models_only_never_export_other_models_or_motions(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            source = directory / "input"
            source.mkdir()
            for name in ("3d_a", "3d_b"):
                (source / f"{name}.assetbundle").touch()
            output = directory / "output"
            def environment(path):
                identity = logical_name(Path(path))
                return SimpleNamespace(container={identity: SimpleNamespace(deref_parse_as_object=lambda: identity)})
            exported = SimpleNamespace(builder=SimpleNamespace(write=Mock()), human_scale=1)
            with ExitStack() as stack:
                stack.enter_context(patch("converter.hasunosora.dependency_closure", side_effect=lambda bundle, index: [bundle]))
                stack.enter_context(patch("converter.hasunosora.UnityPy.load", side_effect=environment))
                stack.enter_context(patch("converter.hasunosora.bundle_metadata", side_effect=lambda bundle: (logical_name(bundle), [])))
                stack.enter_context(patch("converter.hasunosora.character_identity", return_value="SCSch011kahDeA"))
                normalized = stack.enter_context(patch("converter.hasunosora._load_normalized",
                                                       return_value={"sourceCharacter": "SCSch011KahDeA"}))
                export = stack.enter_context(patch("converter.hasunosora.export_normalized_model", return_value=exported))
                stack.enter_context(patch("converter.hasunosora.HasunosoraModelAdapter"))
                stack.enter_context(patch("converter.hasunosora.extract_model_physics", return_value=None))
                stack.enter_context(patch("converter.hasunosora.extract_sub_bone_behavior", return_value=[]))
                stack.enter_context(patch("converter.hasunosora.shutil.copytree"))
                motions = stack.enter_context(patch("converter.hasunosora.collect_baked_motions"))                convert(source, output, None, False, model_names=["3d_b"], models_only=True)
                export.assert_called_once()
                normalized.assert_called_once_with(None, "3d_b")
                motions.assert_not_called()                self.assertFalse((output / "hasunosora/3d_a").exists())
                component = json.loads((output / "hasunosora/3d_b/config.json").read_text(encoding="utf-8"))["components"][0]
                self.assertEqual(component["name"], "3d_b")
                self.assertEqual(component["morphPoses"], [])
                self.assertEqual(component["expressionGroups"], [])
                self.assertEqual(component["expressions"], [])
                with self.assertRaisesRegex(ValueError, "requested models not found"):
                    convert(source, output, None, False, model_names=["absent"], models_only=True)

    def test_each_expression_owns_its_blink_and_mouth_without_name_heuristics(self):
        model = SimpleNamespace(builder=SimpleNamespace(document={"nodes": [{"name": "Face"}]}))
        a, b, lip0, lip1 = [(0, i, name) for i, name in enumerate(("arbitraryA", "arbitraryB", "lip0", "lip1"))]
        normal = ExportedExpression("normal", "normal", "normal-blink", [f"normal-{i}" for i in range(6)])
        happy = ExportedExpression("happy", "happy", "happy-blink", [f"happy-{i}" for i in range(6)])
        fixed = ExportedExpression("fixed", "happy", None, [])
        poses = {
            "normal": {a: 0, b: 0}, "normal-blink": {a: 1, b: 0},
            "happy": {a: 0.3, b: 0}, "happy-blink": {a: 0, b: 1},
        }
        for i in range(6):
            poses[f"normal-{i}"] = {lip0: 1 if i == 0 else 0, lip1: i / 5}
            poses[f"happy-{i}"] = {lip0: 0.8 if i == 0 else 0, lip1: i / 10}
        with patch("converter.hasunosora._clip_pose", side_effect=lambda clip, model: dict(poses[clip])):
            package = build_expression_package(model, [normal, happy, fixed])
        face, mouth = [{s["name"]: s for s in g["states"]} for g in package["expressionGroups"]]
        self.assertEqual(evaluate(package, face["normal"], "blink", 1),
                         {("Face", "arbitraryA"): 1, ("Face", "arbitraryB"): 0})
        self.assertEqual(evaluate(package, face["happy"], "blink", 1),
                         {("Face", "arbitraryA"): 0, ("Face", "arbitraryB"): 1})
        self.assertEqual(evaluate(package, mouth["happy"], "speech", 1),
                         {("Face", "lip0"): 0, ("Face", "lip1"): .1})
        self.assertEqual(evaluate(package, mouth["happy"])["Face", "lip0"], .8)
        self.assertNotIn("controls", face["fixed"])
        self.assertNotIn("controls", mouth["fixed"])
        self.assertEqual(set(mouth["happy"]["controls"]["visemes"]), set("aiueo"))
        self.assertEqual(package["defaultExpression"], "normal")
        self.assertEqual(package["expressions"][1], {"name": "happy", "selections": {"face": "happy", "mouth": "happy"}})
        self.assertFalse(evaluate(package, face["happy"]).keys() & evaluate(package, mouth["normal"]).keys())

    def test_dynamic_morph_cannot_silently_become_zero(self):
        clip = SimpleNamespace(
            m_Name="animated-face", m_ClipBindingConstant=SimpleNamespace(genericBindings=[SimpleNamespace(attribute=123)]),
            m_MuscleClip=SimpleNamespace(m_Clip=SimpleNamespace(data=SimpleNamespace(
                m_StreamedClip=SimpleNamespace(curveCount=1), m_DenseClip=SimpleNamespace(m_CurveCount=0),
            ))),
        )
        model = SimpleNamespace(morph_targets={123: [(0, 0, "shape")]})
        with patch("converter.hasunosora.packed_clip_values", return_value=([], {0: [(0, 0), (1, 100)]})):
            with self.assertRaisesRegex(ValueError, "dynamic Morph"):
                _clip_pose(clip, model)

    def test_finite_raw_recipe_coefficients_are_preserved(self):
        model = SimpleNamespace(builder=SimpleNamespace(document={"nodes": [{"name": "Face"}]}))
        entry = ExportedExpression("source", "source", None, [])
        key = (0, 0, "sourceShape")
        for value in (-.25, 1.5):
            with patch("converter.hasunosora._clip_pose", return_value={key: value}):
                package = build_expression_package(model, [entry])
            self.assertEqual(package["morphPoses"][0]["targets"]["Face"]["sourceShape"], value)
        for value in (float("nan"), float("inf")):
            with patch("converter.hasunosora._clip_pose", return_value={key: value}):
                with self.assertRaisesRegex(ValueError, "non-finite"):
                    build_expression_package(model, [entry])






if __name__ == "__main__":
    unittest.main()
