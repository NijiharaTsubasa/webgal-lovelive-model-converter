import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from converter import convert_bangdream as cli


class VariantCliTests(unittest.TestCase):
    def test_normal_conversion_includes_variants(self):
        calls = []
        with patch("sys.argv", ["convert_bangdream"]), \
                patch.object(cli, "discover_bundle_inputs", return_value=[("body", "body")]), \
                patch.object(cli, "discover_motion_bundles", return_value=[]), \
                patch.object(cli, "convert_all", side_effect=lambda *args: calls.append("original")), \
                patch.object(cli, "convert_variants", side_effect=lambda *args: calls.append("alternate")):
            cli.main()
        self.assertEqual(calls, ["original", "alternate"])

    def test_variants_only_does_not_convert_originals_or_motions(self):
        with patch("sys.argv", ["convert_bangdream", "--variants-only"]), \
                patch.object(cli, "convert_variants") as variants, \
                patch.object(cli, "convert_all") as originals, \
                patch.object(cli, "package_existing_motions") as motions:
            cli.main()
        variants.assert_called_once()
        originals.assert_not_called()
        motions.assert_not_called()

    def test_variants_only_rejects_clean_before_writing(self):
        with patch("sys.argv", ["convert_bangdream", "--variants-only", "--clean"]), \
                patch.object(cli, "clean_game_output") as clean:
            with self.assertRaises(SystemExit):
                cli.main()
        clean.assert_not_called()

    def test_index_includes_existing_and_new_packages_without_rewriting_configs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("original", "original_another1"):
                (root / name).mkdir()
                (root / name / "config.json").write_text("unchanged", encoding="utf-8")
            with patch.object(cli, "discover_variant_jobs", return_value=[{"body": [1]}]), \
                    patch.object(cli, "convert_variant_job", return_value={"failures": []}):
                cli.convert_variants(root, root, root)
            self.assertEqual(json.loads((root / "index.json").read_text(encoding="utf-8")),
                             {"configs": ["original/config.json", "original_another1/config.json"]})
            self.assertEqual((root / "original/config.json").read_text(encoding="utf-8"), "unchanged")

    def test_failed_variants_are_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(cli, "discover_variant_jobs", return_value=[{"body": [1]}]), \
                    patch.object(cli, "convert_variant_job", return_value={
                        "failures": [{"name": "costume_another1", "error": "missing skeleton"}]}):
                with self.assertRaisesRegex(RuntimeError, "costume_another1.*missing skeleton"):
                    cli.convert_variants(root, root, root)
