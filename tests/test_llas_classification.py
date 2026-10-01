"""Classified LLAS inputs remain self-contained and control source selection."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from converter.classify_llas import _closure, classify
from converter.llas import convert_all
from converter.llas.source_inventory import BundleIndex, SourceInventory, active_sources


def inventory(models=(), motions=(), *, names=None):
    names = names or {}
    return SourceInventory(tuple(models), tuple(motions),
                           {path: names.get(path, "model") for path in models},
                           {path: names.get(path, "motion") for path in motions},
                           {path: path.name for path in (*models, *motions)}, {})


class LlasClassificationTests(unittest.TestCase):
    def test_unity_builtin_external_is_not_a_game_bundle_dependency(self):
        source = Path("model.ab")
        index = BundleIndex({source: "model.unity3d"}, {source: ()},
                            {source: ("unity_builtin_extra",)}, {})
        self.assertEqual(_closure([source], index), {source})

    def test_curated_motion_only_takes_precedence_and_conversion_rejects_without_writing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "raw").mkdir()
            (root / "motion").mkdir()
            raw_model = root / "raw/model"
            motion = root / "motion/clip"
            raw_model.touch()
            motion.touch()
            raw = inventory((raw_model,))
            curated = inventory(motions=(motion,))
            with patch("converter.llas.source_inventory.scan_sources",
                       side_effect=lambda path, *args: curated if path == root / "motion" else raw):
                active_sources.cache_clear()
                self.assertEqual(active_sources(root).models, ())
                self.assertEqual(active_sources(root).motions, (motion,))
                with patch("converter.llas.active_sources", return_value=curated):
                    with self.assertRaisesRegex(RuntimeError, "reference rig"):
                        convert_all(root, root / "output", root / "baked")
                self.assertFalse((root / "output").exists())
                active_sources.cache_clear()

    def test_classify_only_motion_copies_its_dependency_and_never_requires_model(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_root = root / "raw"
            source_root.mkdir()
            motion = source_root / "clip.ab"
            dependency = source_root / "face.ab"
            motion.write_bytes(b"clip")
            dependency.write_bytes(b"face")
            found = SourceInventory((), (motion,), {}, {motion: "clip"},
                                    {motion: "clip.fbx.unity3d"}, {})
            indexed = BundleIndex(
                {motion: "clip.fbx.unity3d", dependency: "face.unity3d"},
                {motion: ("face.unity3d",), dependency: ()},
                {motion: (), dependency: ()}, {},
            )
            with patch("converter.classify_llas.scan_sources", return_value=found), \
                 patch("converter.classify_llas.scan_bundle_index", return_value=indexed):
                result = classify(source_root, root, {"live"})
            self.assertEqual(result["models"], 0)
            self.assertEqual(result["motions"], 1)
            self.assertEqual((root / "motion/clip.ab").read_bytes(), b"clip")
            self.assertEqual((root / "motion/face.ab").read_bytes(), b"face")
            self.assertFalse((root / "character").exists())

    def test_character_only_conversion_has_no_motion_requirement(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            model = root / "character" / "body.ab"
            model.parent.mkdir()
            model.touch()
            selected = inventory(models=(model,), names={model: "ch0001_member"})
            with patch("converter.llas.active_sources", return_value=selected), \
                 patch("converter.llas.inspect_model", return_value="ch0001_member"), \
                 patch("converter.llas.convert_model", return_value={"type": "model", "name": "ch0001_member"}):
                models, motions = convert_all(root, root / "output", root / "baked")
            self.assertEqual(len(models), 1)
            self.assertEqual(motions, [])
            self.assertTrue((root / "output/index.json").is_file())
            self.assertFalse((root / "output/motions").exists())

    def test_curated_character_only_does_not_rescan_raw_motions(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "character").mkdir()
            (root / "raw").mkdir()
            model = root / "character/body.ab"
            motion = root / "raw/clip.ab"
            model.touch()
            motion.touch()
            curated = inventory(models=(model,))
            raw = inventory(motions=(motion,))
            with patch("converter.llas.source_inventory.scan_sources",
                       side_effect=lambda path, *args: curated if path == root / "character" else raw):
                active_sources.cache_clear()
                self.assertEqual(active_sources(root).models, (model,))
                self.assertEqual(active_sources(root).motions, ())
                active_sources.cache_clear()


if __name__ == "__main__":
    unittest.main()
