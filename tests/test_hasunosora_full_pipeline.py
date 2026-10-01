import json
import tempfile
import unittest
from pathlib import Path

from converter.hasunosora.motion import write_motion_index


class HasunosoraFullPipelineTests(unittest.TestCase):
    def test_hasunosora_motion_manifest_contains_only_hasunosora(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            (output / "config.json").write_text(
                json.dumps({
                    "components": [{
                        "type": "motion",
                        "name": "garupa-motion",
                        "src": "garupa/motion.json",
                        "motionGroup": "garupa",
                    }],
                }),
                encoding="utf-8",
            )

            write_motion_index(output, [{
                "type": "motion",
                "name": "mot_00_41021",
                "src": "mot_00_41021.motionbin",
            }])

            motions = json.loads((output / "config.json").read_text(encoding="utf-8"))["components"]
            self.assertEqual(
                [(entry["name"], entry["motionGroup"]) for entry in motions],
                [("mot_00_41021", "hasunosora")],
            )


if __name__ == "__main__":
    unittest.main()
