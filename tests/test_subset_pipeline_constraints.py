import json
import math
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from converter.bake_bangdream_motion import _verify_export, package_existing_motions
from converter.bake_hasunosora import main as bake_hasunosora
from converter.bake_llas import verify_body_motion
from converter.bangdream import discover_bundle_inputs
from converter.convert_bangdream import main as convert_bangdream
from converter.hasunosora.motion import collect_baked_motions, write_motion_index


class HasunosoraSubsetTests(unittest.TestCase):
    def test_motion_bake_uses_requested_reference_model(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            inputs = root / "input"
            outputs = root / "baked"
            inputs.mkdir()
            unity = root / "Unity.exe"
            unity.touch()
            for name in ("3d_costume_001", "3d_costume_002", "mot_current"):
                (inputs / f"{name}.assetbundle").touch()

            def record_bake(*args, **kwargs):
                self.assertEqual(args[7], {"3d_costume_002", "mot_current"})
                self.assertFalse(kwargs["models_only"])
                (outputs / "mot_current.baked.json").write_text("{}", encoding="utf-8")

            argv = ["bake", "--unity", str(unity), "--input", str(inputs),
                    "--output", str(outputs), "--motions-only", "--model", "3d_costume_002"]
            with patch.object(sys, "argv", argv), \
                 patch("converter.bake_hasunosora.bundle_metadata", side_effect=lambda path: (path.stem, [])), \
                 patch("converter.bake_hasunosora.run_batch", side_effect=record_bake) as run:
                bake_hasunosora()
            run.assert_called_once()

    def test_current_motion_subset_ignores_stale_cache_and_preserves_manifest(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            inputs, baked, output = (root / name for name in ("input", "baked", "output"))
            inputs.mkdir()
            baked.mkdir()
            output.mkdir()
            (inputs / "mot_current.assetbundle").touch()
            (baked / "mot_current.baked.json").write_text(json.dumps({
                "schemaVersion": 8, "sourceBundle": "mot_current", "clips": [],
            }), encoding="utf-8")
            (baked / "mot_stale.baked.json").write_text("invalid stale cache", encoding="utf-8")
            old = {"type": "motion", "name": "hasunosora/mot_stale", "description": "",
                   "motionGroup": "hasunosora", "src": "mot_stale.motionbin"}
            (output / "config.json").write_text(json.dumps({"components": [old]}), encoding="utf-8")
            with patch("converter.hasunosora.motion.controller_program", return_value={"layers": []}) as compile:
                entries = collect_baked_motions(baked, inputs, output)
            compile.assert_called_once()
            self.assertEqual(compile.call_args.args[0], inputs / "mot_current.assetbundle")
            self.assertEqual([entry["name"] for entry in entries], ["hasunosora/mot_current"])
            write_motion_index(output, entries)
            result = json.loads((output / "config.json").read_text(encoding="utf-8"))["components"]
            self.assertIn(old, result)

    def test_current_motion_without_bake_fails_including_missing_cache_directory(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            inputs = root / "input"
            inputs.mkdir()
            (inputs / "motion_current.assetbundle").touch()
            for baked in (None, root / "missing", root / "baked"):
                with self.subTest(baked=baked):
                    with self.assertRaisesRegex(FileNotFoundError, "[Mm]issing baked motion"):
                        collect_baked_motions(baked, inputs, root / "output")

    def test_no_current_motions_ignores_all_cached_motions(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "mot_stale.baked.json").write_text("invalid stale cache", encoding="utf-8")
            self.assertEqual(collect_baked_motions(root, root / "input", root / "output"), [])

    def test_native_clip_bundle_name_resolves_current_controller(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            inputs, baked = root / "input", root / "baked"
            inputs.mkdir()
            baked.mkdir()
            (inputs / "mot_00_001.assetbundle").touch()
            (baked / "m_00_001.baked.json").write_text(json.dumps({
                "schemaVersion": 8, "sourceBundle": "m_00_001", "clips": [],
            }), encoding="utf-8")
            with patch("converter.hasunosora.motion.controller_program", return_value={"layers": []}) as compile:
                entries = collect_baked_motions(baked, inputs, root / "output")
            self.assertEqual(compile.call_args.args[0], inputs / "mot_00_001.assetbundle")
            self.assertEqual(entries[0]["name"], "hasunosora/m_00_001")


class LlasMotionSampleTests(unittest.TestCase):
    def verify(self, **track_updates):
        with tempfile.TemporaryDirectory() as folder:
            baked = Path(folder) / "motion.baked.json"
            track = {"bone": "Hips", "rotation": [0, 0, 0, 1] * 3, **track_updates}
            baked.write_text(json.dumps({"clips": [{"name": "Idle", "frames": 3,
                                                     "tracks": [track]}]}), encoding="utf-8")
            verify_body_motion(baked)

    def test_sub_degree_rotation_and_hips_only_translation_are_valid(self):
        angle = math.radians(0.25) / 2
        self.verify(rotation=[0, 0, 0, 1, 0, math.sin(angle), 0, math.cos(angle), 0, 0, 0, 1])
        self.verify(translation=[0, 0, 0, 0.25, 0, 0, 0.5, 0, 0])

    def test_bone_without_translation_accepts_unity_empty_array(self):
        self.verify(bone="Spine", translation=[])
        self.verify(bone="Spine", translation=None)

    def test_broken_samples_remain_errors(self):
        for update, message in (
            ({"rotation": [0, 0, 0, 1] * 2}, "invalid rotation samples"),
            ({"rotation": [0, 0, 0, float("nan")] * 3}, "invalid rotation samples"),
            ({"rotation": [0, 0, 0, float("inf")] * 3}, "invalid rotation samples"),
            ({"rotation": [0, 0, 0, 0] * 3}, "zero rotation quaternion"),
            ({"translation": [0, 0, 0] * 2}, "invalid Hips translation samples"),
            ({"translation": [0, 0, float("inf")] * 3}, "invalid Hips translation samples"),
            ({"bone": "Spine", "translation": [0, 0, 0] * 3}, "invalid Hips translation samples"),
        ):
            with self.subTest(update=update):
                with self.assertRaisesRegex(RuntimeError, message):
                    self.verify(**update)


class BangDreamSubsetTests(unittest.TestCase):
    def test_head_only_and_body_only_inputs_are_valid(self):
        for directory, role in (("head", "head"), ("costume", "body")):
            with self.subTest(role=role), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                source = root / directory / "model"
                source.parent.mkdir()
                source.touch()
                self.assertEqual(discover_bundle_inputs(root), [(source, role)])

    def test_missing_or_empty_model_inputs_return_empty_inventory(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.assertEqual(discover_bundle_inputs(root), [])
            (root / "head").mkdir()
            (root / "costume").mkdir()
            self.assertEqual(discover_bundle_inputs(root), [])

    def test_models_without_motion_sources_keep_existing_motion_index(self):
        for preserve in (False, True):
            with self.subTest(preserve=preserve), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                output = root / "output"
                output.mkdir()
                old_config = '{"components":[]}\n'
                if preserve:
                    (output / "motions").mkdir()
                    (output / "motions" / "config.json").write_text(old_config, encoding="utf-8")

                def convert_models(*args):
                    (output / "index.json").write_text(json.dumps({"configs": ["model/config.json"]}), encoding="utf-8")

                argv = ["convert", "--input", str(root / "input"), "--output", str(output),
                        "--baked", str(root / "baked")]
                source = root / "input" / "head" / "model"
                source.parent.mkdir(parents=True)
                source.touch()
                with patch.object(sys, "argv", argv), \
                     patch("converter.convert_bangdream.convert_all", side_effect=convert_models), \
                     patch("converter.convert_bangdream.package_existing_motions") as package:
                    convert_bangdream()
                package.assert_not_called()
                configs = json.loads((output / "index.json").read_text(encoding="utf-8"))["configs"]
                self.assertEqual(configs, ["model/config.json", "motions/config.json"] if preserve else ["model/config.json"])
                if preserve:
                    self.assertEqual((output / "motions" / "config.json").read_text(encoding="utf-8"), old_config)

    def test_placeholder_only_source_needs_no_motion_package(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            output = root / "output"
            output.mkdir()
            (output / "config.json").write_text('{"components": []}', encoding="utf-8")
            selected = [("characterunique/ch001/001", root / "source")]
            names = {selected[0][0]: ["CalibrationPose", "TPose"]}
            self.assertEqual(_verify_export(selected, names, output), (0, 0))
            with patch("converter.bake_bangdream_motion._select_bundles", return_value=selected), \
                 patch("converter.bake_bangdream_motion._source_clip_names", return_value=names[selected[0][0]]):
                self.assertEqual(package_existing_motions(root, root / "no-baked-files", output), (0, 0))

    def test_playable_source_without_package_still_fails(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "config.json").write_text('{"components": []}', encoding="utf-8")
            selected = [("characterunique/ch001/001", root / "source")]
            with self.assertRaisesRegex(ValueError, "No package for source"):
                _verify_export(selected, {selected[0][0]: ["CalibrationPose", "mot_playable"]}, root)


if __name__ == "__main__":
    unittest.main()
