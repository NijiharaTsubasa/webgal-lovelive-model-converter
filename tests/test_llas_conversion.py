from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from converter.llas import discover_models, package_motion
from converter.llas.source_inventory import SourceInventory
from converter.bake_llas import verify_body_motion
from converter.common.motion_binary import decode_motion


class LlasConversionTests(unittest.TestCase):
    def test_cli_logs_japanese_filenames_as_utf8_under_gbk_environment(self) -> None:
        filename = "ミア・テイラー_member.prefab.unity3d"
        script = (
            "import converter.convert_llas as convert_llas, sys; "
            "from pathlib import Path; "
            "from converter.llas.source_inventory import SourceInventory; "
            "source = Path('opaque-model'); "
            "convert_llas.active_sources = lambda root: SourceInventory("
            "(source,), (), {source: 'a_member'}, {}, {}, {}); "
            f"convert_llas.convert_all = lambda *args, **kwargs: print({filename!r}); "
            "sys.argv = ['converter.convert_llas']; convert_llas.main()"
        )
        result = subprocess.run(
            [sys.executable, "-c", script],
            cwd=Path(__file__).resolve().parents[1],
            env={**os.environ, "PYTHONIOENCODING": "gbk"},
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", errors="replace"))
        self.assertEqual(result.stdout.decode("utf-8").strip(), filename)

    def test_static_humanoid_motion_is_valid(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            baked = Path(directory) / "motion.baked.json"
            baked.write_text(json.dumps({"clips": [{"name": "Idle", "frames": 3, "tracks": [
                {"bone": "Hips", "rotation": [0, 0, 0, 1] * 3},
            ]}]}), encoding="utf-8")
            verify_body_motion(baked)

    def test_model_discovery_accepts_only_member_prefab_bundles(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            wanted = root / "opaque-pack"
            inventory = SourceInventory((wanted,), (), {wanted: "a_member"}, {}, {}, {})
            with patch("converter.llas.active_sources", return_value=inventory):
                self.assertEqual(discover_models(root), [wanted])

    def test_motion_package_uses_source_loop_flag_and_config_relative_src(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "idle.unity3d"
            source.touch()
            baked = root / "idle.baked.json"
            baked.write_text(json.dumps({
                "schemaVersion": 8,
                "clips": [{
                    "name": "Idle",
                    "duration": 1.0,
                    "sampleRate": 30.0,
                    "frames": 2,
                    "tracks": [{
                        "bone": "Hips",
                        "rotation": [0.0, 0.0, 0.0, 1.0] * 2,
                        "translation": [0.0, -2.0, 0.0, 0.0, -2.0, 0.0],
                    }],
                    "groupTracks": [],
                }],
                "auxiliaryClips": [],
                "leftHandPoses": [],
                "rightHandPoses": [],
            }), encoding="utf-8")
            motion_root = root / "package" / "motions"
            with patch("converter.llas._source_clip_loop_flags", return_value={"Idle": True}):
                component = package_motion(source, baked, motion_root, "idle")

            self.assertEqual(component["src"], "idle.motionbin")
            self.assertEqual(component["name"], "llas/idle")
            self.assertEqual(component["description"], "")
            payload = decode_motion((motion_root / "idle.motionbin").read_bytes())
            state = payload["program"]["layers"][0]["states"][0]
            self.assertTrue(state["loop"])
            self.assertEqual(payload["clips"][0]["tracks"][0]["translation"], [0.0, -2.0, 0.0] * 2)


if __name__ == "__main__":
    unittest.main()
