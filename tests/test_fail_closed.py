import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from converter.hasunosora.motion import collect_baked_motions
from converter.common.unity import dependency_closure


class FailClosedConversionTests(unittest.TestCase):
    def test_missing_assetbundle_dependency_is_an_error(self):
        root = Path("root.assetbundle")
        with patch(
            "converter.common.unity.bundle_metadata",
            return_value=("root", ["missing.assetbundle"]),
        ):
            with self.assertRaisesRegex(FileNotFoundError, "missing.assetbundle"):
                dependency_closure(root, {"root": root})

    def test_invalid_baked_motion_is_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            baked = root / "baked"
            baked.mkdir()
            inputs = root / "input"
            inputs.mkdir()
            (inputs / "mot_broken.assetbundle").touch()
            (baked / "mot_broken.baked.json").write_text("not json", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "Invalid baked motion file"):
                collect_baked_motions(baked, inputs, root / "output")

    def test_unsupported_baked_motion_schema_is_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            baked = root / "baked"
            baked.mkdir()
            inputs = root / "input"
            inputs.mkdir()
            (inputs / "mot_old.assetbundle").touch()
            (baked / "mot_old.baked.json").write_text(
                '{"schemaVersion":7}',
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "Unsupported baked motion schema"):
                collect_baked_motions(baked, inputs, root / "output")


if __name__ == "__main__":
    unittest.main()
