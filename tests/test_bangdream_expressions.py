import math
import unittest
from pathlib import Path
from unittest.mock import patch

from converter.bangdream import BundleAssets, extract_head_expression, load_bundle_assets


def groups(package):
    return {group["name"]: {state["name"]: state for state in group["states"]}
            for group in package["expressionGroups"]}


def evaluate(package, state, control=None, amount=0):
    poses = {entry["name"]: entry["targets"] for entry in package["morphPoses"]}
    base = state["poses"]
    endpoint = state.get("controls", {}).get(control, {})
    coefficients = {key: base.get(key, 0) + amount * (endpoint.get(key, base.get(key, 0)) - base.get(key, 0))
                    for key in base.keys() | endpoint.keys()}
    result = {}
    for key, coefficient in coefficients.items():
        for node, targets in poses[key].items():
            for morph, value in targets.items():
                result[node, morph] = result.get((node, morph), 0) + coefficient * value
    return result


class BangDreamExpressionTests(unittest.TestCase):
    def setUp(self):
        self.face = {
            "BlendShapes": [
                {"Type": 0, "Name": "joy_l", "RangeMax": 80},
                {"Type": 1, "Name": "joy", "RangeMax": 100},
                {"Type": 2, "Name": "close_l", "RangeMax": 100},
                {"Type": 3, "Name": "open_a", "RangeMax": 100},
                {"Type": 4, "Name": "open_i", "RangeMax": 100},
                {"Type": 5, "Name": "wink_l", "RangeMax": 100},
                {"Type": 6, "Name": "wink_r", "RangeMax": 100},
            ],
            "Layers": [
                {"Name": "Expressions", "Mixers": [
                    {"Name": "Neutral", "Shapes": []}, {"Name": "Joy", "Shapes": [0]},
                ]},
                {"Name": "Eyes", "Mixers": [
                    {"Name": "Open", "Shapes": []}, {"Name": "Close", "Shapes": [2]},
                    {"Name": "WinkL", "Shapes": [5], "OverrideBlink": True},
                    {"Name": "WinkR", "Shapes": [6], "OverrideBlink": True},
                ]},
                {"Name": "Lipsync", "Mixers": [
                    {"Name": "Joy", "Shapes": [1]}, {"Name": "A", "Shapes": [3]},
                    {"Name": "I", "Shapes": [4]},
                ]},
            ],
        }
        self.mesh_morphs = {
            "face_Base_obj": ["face_main_eye_joy_L", "face_main_eye_close_L",
                              "face_main_eye_wink_L", "face_main_eye_wink_R",
                              "face_main_mouth_joy", "face_main_mouth_open_a", "face_main_mouth_open_i"],
            "face_NoOutline_obj": ["eyelash_joy_L", "eyelash_eye_close_L",
                                   "eyelash_eye_wink_L", "eyelash_eye_wink_R"],
        }
        # Explicit controller Targets need not follow a morph-name convention.
        targets = [
            [('face_Base_obj', 0), ('face_NoOutline_obj', 0)],
            [('face_Base_obj', 4)],
            [('face_Base_obj', 1), ('face_NoOutline_obj', 1)],
            [('face_Base_obj', 5)], [('face_Base_obj', 6)],
            [('face_Base_obj', 2), ('face_NoOutline_obj', 2)],
            [('face_Base_obj', 3), ('face_NoOutline_obj', 3)],
        ]
        for shape, slots in zip(self.face['BlendShapes'], targets):
            shape['RangeMin'] = 0
            shape['Targets'] = [{'mesh': mesh, 'morph': self.mesh_morphs[mesh][slot]}
                                for mesh, slot in slots]
        self.bundle = BundleAssets(path=Path("head"), env=object(), prefab=None,
                                   face_controller=self.face, kind="head")

    def extract(self):
        return extract_head_expression(self.bundle, exported_mesh_morphs=self.mesh_morphs)

    def test_preserves_source_recipes_and_independent_groups(self):
        package = self.extract()
        recipes = {p["name"]: p["targets"] for p in package["morphPoses"]}
        self.assertEqual(recipes["face.Joy"]["face_Base_obj"]["face_main_eye_joy_L"], 0.8)
        self.assertEqual(recipes["mouth.Joy"]["face_Base_obj"], {"face_main_mouth_joy": 1})
        self.assertEqual(recipes["face.Neutral"], {})
        states = groups(package)
        self.assertEqual(list(states), ["face", "mouth"])
        self.assertEqual(len(states["face"]), 8)
        self.assertEqual(set(states["mouth"]), {"Neutral", "Joy", "A", "I"})
        self.assertEqual(package["defaultExpression"], {"eye": "Neutral", "closed": "Neutral", "open": "A"})
        self.assertNotIn("expressions", package)
        face = evaluate(package, states["face"]["Joy-WinkL"], "blink", 1)
        self.assertEqual(face["face_Base_obj", "face_main_eye_wink_L"], 1)
        self.assertNotIn("blink", states["face"]["Joy-WinkL"].get("controls", {}))
        self.assertTrue(all("mouth" not in morph for _, morph in face))
        mouth = evaluate(package, states["mouth"]["Joy"])
        self.assertEqual(mouth["face_Base_obj", "face_main_mouth_joy"], 1)
        self.assertTrue(all("eye" not in morph for _, morph in mouth))
        self.assertEqual(states["mouth"]["Neutral"]["poses"], {})
        self.assertEqual(states["mouth"]["Joy"]["controls"]["visemes"]["a"], {"mouth.A": 1})
        self.assertTrue(all("speech" not in state.get("controls", {}) for state in states["mouth"].values()))

    def test_uses_exported_inventory_without_reenumeration(self):
        with patch("converter.bangdream.mesh_morph_names", side_effect=AssertionError("must use exported inventory")):
            package = self.extract()
        self.assertEqual(len(groups(package)["face"]), 8)

    def test_static_head_has_no_expression_controls(self):
        self.mesh_morphs = {}
        self.face['Layers'][0]['Mixers'].append({'Name': 'Sad', 'Shapes': []})
        with patch('converter.bangdream.mesh_morph_names', return_value={}):
            self.assertEqual(self.extract(),
                             {'morphPoses': [], 'expressionGroups': []})

    def test_empty_source_mouth_and_missing_a_are_valid(self):
        self.face['Layers'][2]['Mixers'] = [{'Name': 'Rest', 'Shapes': []}, {'Name': 'I', 'Shapes': [4]}]
        package = self.extract()
        self.assertEqual(package['defaultExpression'], {'eye': 'Neutral', 'closed': 'Rest', 'open': 'Rest'})
        self.assertEqual(groups(package)['mouth']['Rest']['poses'], {'mouth.Rest': 1})
        self.assertEqual(groups(package)['mouth']['I']['controls']['visemes'], {'i': {'mouth.I': 1}})

    def test_zero_input_name_cannot_collide_with_source_lipsync(self):
        self.face['Layers'][2]['Mixers'].append({'Name': 'Neutral', 'Shapes': [4]})
        package = self.extract()
        self.assertEqual(package['defaultExpression']['closed'], 'Neutral_')
        self.assertEqual(groups(package)['mouth']['Neutral_']['poses'], {})
        self.assertEqual(groups(package)['mouth']['Neutral']['poses'], {'mouth.Neutral': 1})

    def test_empty_export_does_not_hide_source_morph_loss(self):
        with patch('converter.bangdream.mesh_morph_names', return_value=self.mesh_morphs):
            with self.assertRaisesRegex(ValueError, 'source Morph.*export'):
                extract_head_expression(self.bundle, exported_mesh_morphs={})




    def test_shapes_are_array_indices_not_type_or_name(self):
        for shape in self.face['BlendShapes']:
            shape['Type'] = 99
            shape['Name'] = 'not_a_morph_name'
        package = self.extract()
        recipes = {p["name"]: p["targets"] for p in package["morphPoses"]}
        self.assertEqual(recipes["face.Joy"]["face_Base_obj"]["face_main_eye_joy_L"], .8)
        self.assertEqual(recipes["mouth.A"]["face_Base_obj"]["face_main_mouth_open_a"], 1)

    def test_rejects_missing_controller_shape(self):
        self.face["Layers"][0]["Mixers"][1]["Shapes"] = [31]
        with self.assertRaisesRegex(ValueError, "missing BlendShapes index 31"):
            self.extract()

    def test_rejects_missing_controller_and_export_target(self):
        self.bundle.face_controller = None
        with self.assertRaisesRegex(ValueError, 'no FaceController'):
            self.extract()
        self.bundle.face_controller = self.face
        self.face['BlendShapes'][0]['Targets'][0]['morph'] = 'missing'
        with self.assertRaisesRegex(ValueError, 'missing from exported Morph inventory'):
            self.extract()

    def test_preserves_finite_non_unit_source_weights_and_rejects_nonfinite(self):
        for value in (-25, 150):
            self.face["BlendShapes"][0]["RangeMax"] = value
            pose = next(p for p in self.extract()["morphPoses"] if p["name"] == "face.Joy")
            self.assertEqual(pose["targets"]["face_Base_obj"]["face_main_eye_joy_L"], value / 100)
        for value in (float("nan"), float("inf")):
            self.face["BlendShapes"][0]["RangeMax"] = value
            with self.assertRaisesRegex(ValueError, "Non-finite"):
                self.extract()

    def test_override_blink_is_source_data_not_name(self):
        self.face["Layers"][0]["Mixers"][1]["OverrideBlink"] = True
        states = groups(self.extract())["face"]
        for name in ("Joy", "Joy-Close", "Joy-WinkL", "Joy-WinkR"):
            self.assertEqual(states[name]["poses"], {"face.Joy": 1})
            self.assertNotIn("blink", states[name].get("controls", {}))
        self.assertIn("blink", states["Neutral"]["controls"])






if __name__ == "__main__":
    unittest.main()
