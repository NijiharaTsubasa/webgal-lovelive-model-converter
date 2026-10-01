import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from converter.hasunosora.motion import collect_baked_motions, load_motion_descriptions, write_motion_index
from converter.common.motion_binary import decode_motion
from tools.refresh_hasunosora_motion_descriptions import refresh


class HasunosoraMotionDescriptionTests(unittest.TestCase):
    def test_incremental_motion_manifest_preserves_unrelated_entries(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            old = {"type": "motion", "name": "old", "description": "old", "motionGroup": "hasunosora", "src": "old.motionbin"}
            current = {"type": "motion", "name": "current", "description": "old", "motionGroup": "hasunosora", "src": "current.motionbin"}
            (output / "config.json").write_text(json.dumps({"components": [old, current]}), encoding="utf-8")
            updated = {**current, "description": "updated"}
            write_motion_index(output, [updated])
            components = json.loads((output / "config.json").read_text(encoding="utf-8"))["components"]
            self.assertEqual(components, [updated, old])

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
                "hasunosora/mot_00_00010": "通常立ち", "hasunosora/mot_01_00010": "", "hasunosora/mot_02_00010": "",
            })
            write_motion_index(output, entries)
            config = json.loads((output / "config.json").read_text(encoding="utf-8"))
            self.assertEqual(list(config["components"][0])[:3], ["type", "name", "description"])

    def test_metadata_only_refresh_uses_fourth_column_and_keeps_header_order(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "labels.csv"
            source.write_text(
                "motion,bundle_present,review_status,description\n"
                "mot_00_00010,yes,needs_review,通常立ち\n",
                encoding="utf-8",
            )
            config_path = root / "config.json"
            config_path.write_text(json.dumps({"components": [
                {"type": "motion", "name": "hasunosora/mot_00_00010", "motionGroup": "hasunosora", "src": "one.json"},
                {"type": "motion", "name": "hasunosora/mot_01_00010", "motionGroup": "hasunosora", "src": "two.json"},
            ]}), encoding="utf-8")
            self.assertEqual(refresh(config_path, source), (2, 1))
            components = json.loads(config_path.read_text(encoding="utf-8"))["components"]
            self.assertEqual([entry["description"] for entry in components], ["通常立ち", ""])
            self.assertEqual(list(components[0])[:3], ["type", "name", "description"])

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
            write_motion_index(output, entries)
            self.assertEqual(refresh(output / "config.json", missing_csv), (1, 0))
            config = json.loads((output / "config.json").read_text(encoding="utf-8"))
            self.assertEqual(config["components"][0]["description"], "")


if __name__ == "__main__":
    unittest.main()
