import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from converter.hasunosora.motion import collect_baked_motions
from converter.common.motion_binary import decode_motion


class HasunosoraFullPipelineTests(unittest.TestCase):
    def test_incremental_self_contained_motion_preserves_other_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            inputs, baked, output = (root / name for name in ("input", "baked", "motion/hasunosora"))
            for directory in (inputs, baked, output):
                directory.mkdir(parents=True)
            retained = output / "other.motionbin"
            retained.write_bytes(b"unrelated existing motion")
            (inputs / "mot_00_41021.assetbundle").touch()
            (baked / "mot_00_41021.baked.json").write_text(json.dumps({
                "schemaVersion": 8, "sourceBundle": "mot_00_41021", "clips": [],
            }), encoding="utf-8")
            with patch("converter.hasunosora.motion.controller_program", return_value={"layers": []}):
                collect_baked_motions(baked, inputs, output)
            data = decode_motion((output / "mot_00_41021.motionbin").read_bytes())
            self.assertEqual(data["name"], "mot_00_41021")
            self.assertEqual(data["motionGroup"], "hasunosora")
            self.assertEqual(retained.read_bytes(), b"unrelated existing motion")
            self.assertFalse((output / "config.json").exists())
            self.assertFalse((output / "index.json").exists())


if __name__ == "__main__":
    unittest.main()
