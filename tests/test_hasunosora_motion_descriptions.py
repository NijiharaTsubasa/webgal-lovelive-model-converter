import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from converter.hasunosora.motion import collect_baked_motions, load_motion_descriptions
from converter.common.motion_binary import decode_motion, encode_motion
from tools.refresh_hasunosora_motion_descriptions import refresh


class HasunosoraMotionDescriptionTests(unittest.TestCase):
    def test_csv_fourth_column_is_used_without_consulting_review_status(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "motion-label-candidates.csv"
            with source.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.writer(stream)
                writer.writerow(["motion", "bundle_present", "review_status", "description"])
                writer.writerow(["mot_00_00010", "yes", "needs_review", "通常立ち"])
                writer.writerow(["mot_01_00010", "yes", "confirmed", ""])
            self.assertEqual(load_motion_descriptions(source), {
                "mot_00_00010": "通常立ち", "mot_01_00010": "",
            })
            self.assertEqual(load_motion_descriptions(root / "missing.csv"), {})

            baked = root / "baked"
            inputs = root / "input"
            output = root / "output"
            baked.mkdir()
            inputs.mkdir()
            for name in ("mot_00_00010", "mot_01_00010", "mot_02_00010"):
                (inputs / f"{name}.assetbundle").touch()
                (baked / f"{name}.baked.json").write_text(json.dumps({
                    "schemaVersion": 8, "sourceBundle": name,
                    "clips": [], "auxiliaryClips": [],
                    "leftHandPoses": [], "rightHandPoses": [],
                }), encoding="utf-8")
            with patch("converter.hasunosora.motion.MOTION_DESCRIPTIONS_CSV", source), \
                 patch("converter.hasunosora.motion.controller_program", return_value={"layers": []}):
                entries = collect_baked_motions(baked, inputs, output)
            descriptions = {entry["name"]: entry["description"] for entry in entries}
            self.assertEqual(descriptions, {
                "mot_00_00010": "通常立ち", "mot_01_00010": "", "mot_02_00010": "",
            })
            payload = decode_motion((output / "mot_00_00010.motionbin").read_bytes())
            self.assertEqual(list(payload)[:3], ["type", "name", "description"])
            self.assertFalse((output / "config.json").exists())

    def test_metadata_only_refresh_uses_fourth_column_and_keeps_header_order(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "labels.csv"
            source.write_text(
                "motion,bundle_present,review_status,description\n"
                "mot_00_00010,yes,needs_review,通常立ち\n",
                encoding="utf-8",
            )
            motions = root / "motions"
            motions.mkdir()
            for name in ("mot_00_00010", "mot_01_00010"):
                (motions / f"{name}.motionbin").write_bytes(encode_motion({
                    "type": "motion", "name": name, "motionGroup": "hasunosora", "clips": [],
                }))
            self.assertEqual(refresh(motions, source), (2, 1))
            payloads = [decode_motion(path.read_bytes()) for path in sorted(motions.glob("*.motionbin"))]
            self.assertEqual([entry["description"] for entry in payloads], ["通常立ち", ""])
            self.assertEqual(list(payloads[0])[:3], ["type", "name", "description"])

    def test_packaging_strips_source_path_from_group_tracks(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            baked = root / "baked"
            inputs = root / "input"
            output = root / "output"
            baked.mkdir()
            inputs.mkdir()
            (inputs / "mot_00_00010.assetbundle").touch()
            (baked / "mot_00_00010.baked.json").write_text(json.dumps({
                "schemaVersion": 8, "sourceBundle": "mot_00_00010",
                "clips": [{"tracks": [], "groupTracks": [
                    {"kind": "visibility", "path": "source/eye", "node": "eye", "property": "visible", "values": [1, 0]},
                ]}],
            }), encoding="utf-8")
            with patch("converter.hasunosora.motion.controller_program", return_value={"layers": []}):
                collect_baked_motions(baked, inputs, output)
            packaged = decode_motion((output / "mot_00_00010.motionbin").read_bytes())
            self.assertEqual(packaged["clips"][0]["groupTracks"][0], {
                "kind": "visibility", "node": "eye", "property": "visible", "values": [1, 0],
            })

    def test_missing_description_csv_does_not_stop_conversion_or_refresh(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            missing_csv = root / "missing.csv"
            baked = root / "baked"
            inputs = root / "input"
            output = root / "output"
            baked.mkdir()
            inputs.mkdir()
            (inputs / "mot_00_00010.assetbundle").touch()
            (baked / "mot_00_00010.baked.json").write_text(json.dumps({
                "schemaVersion": 8, "sourceBundle": "mot_00_00010",
                "clips": [], "auxiliaryClips": [],
                "leftHandPoses": [], "rightHandPoses": [],
            }), encoding="utf-8")
            with patch("converter.hasunosora.motion.MOTION_DESCRIPTIONS_CSV", missing_csv), \
                 patch("converter.hasunosora.motion.controller_program", return_value={"layers": []}):
                entries = collect_baked_motions(baked, inputs, output)
            self.assertEqual(entries[0]["description"], "")
            payload = decode_motion((output / "mot_00_00010.motionbin").read_bytes())
            self.assertEqual(payload["description"], "")

if __name__ == "__main__":
    unittest.main()
