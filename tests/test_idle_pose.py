import json
import tempfile
import unittest
from pathlib import Path

from converter.common.component_order import order_model_component
from converter.common.idle_pose import sample_baked_pose
from converter.hasunosora import hasunosora_idle_defaults
from converter.llas import _idle_defaults_for_character


ROOT = Path(__file__).resolve().parents[1]


class IdlePoseTests(unittest.TestCase):
    def test_samples_unity_baked_frame_without_changing_motion_coordinates(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "motion.baked.json"
            source.write_text(json.dumps({
                "schemaVersion": 8,
                "clips": [{"name": "idle", "frames": 2, "tracks": [
                    {"bone": "Hips", "rotation": [0, 0, 0, 1, 0.2, 0.3, 0.4, 0.5],
                     "translation": [1, 2, 3, 4, 5, 6]},
                    {"bone": "Head", "rotation": [0, 0, 0, 1, 0.1, 0.2, 0.3, 0.9],
                     "translation": []},
                ]}],
            }), encoding="utf-8")
            self.assertEqual(sample_baked_pose(source, "idle", 0), {"tracks": [
                {"bone": "Hips", "rotation": [0, 0, 0, 1], "translation": [1, 2, 3]},
                {"bone": "Head", "rotation": [0, 0, 0, 1]},
            ]})
            self.assertEqual(sample_baked_pose(source, "idle", -1)["tracks"][0], {
                "bone": "Hips", "rotation": [0.2, 0.3, 0.4, 0.5], "translation": [4, 5, 6],
            })

    def test_missing_source_omits_both_defaults(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertEqual(hasunosora_idle_defaults(root, root), {})
            self.assertEqual(_idle_defaults_for_character("ch9999", root, root), {})




    def test_defaults_precede_expression_tables(self):
        component = order_model_component({
            "type": "model", "name": "example", "expressions": [],
            "idlePose": {"tracks": []}, "defaultMotion": "idle",
        })
        self.assertEqual(list(component), [
            "type", "name", "defaultMotion", "idlePose", "expressions",
        ])


if __name__ == "__main__":
    unittest.main()
