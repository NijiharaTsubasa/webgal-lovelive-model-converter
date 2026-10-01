import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch

from converter.bake_hasunosora import BundleClosures, batches, run_batch


class HasunosoraBatchingTests(unittest.TestCase):
    def test_dependency_batches_keep_shared_assets_and_bound_bundle_count(self):
        paths = {name: Path(f"{name}.assetbundle") for name in (
            "model_a", "model_b", "model_c", "reference", "motion_a", "motion_b",
            "shared", "face_a", "face_b", "face_c", "ref_face",
        )}
        dependencies = {
            "model_a": ["shared", "face_a"],
            "model_b": ["shared", "face_b"],
            "model_c": ["shared", "face_c"],
            "reference": ["shared", "ref_face"],
            "motion_a": [],
            "motion_b": [],
        }

        def metadata(path):
            return path.stem, dependencies.get(path.stem, [])

        with patch("converter.bake_hasunosora.bundle_metadata", side_effect=metadata) as load:
            closures = BundleClosures(paths)
            model_batches = batches(
                [paths[name] for name in ("model_a", "model_b", "model_c")],
                closures, max_roots=3, max_bundles=5,
            )
            self.assertEqual(
                [[root.stem for root in roots] for roots, _ in model_batches],
                [["model_a", "model_b"], ["model_c"]],
            )
            self.assertEqual(model_batches[0][1], {
                "model_a", "model_b", "shared", "face_a", "face_b",
            })
            shared = closures.for_root(paths["reference"])
            motion_batches = batches(
                [paths["motion_a"], paths["motion_b"]], closures,
                max_roots=1, max_bundles=5, shared=shared,
            )
            self.assertEqual(len(motion_batches), 2)
            for roots, staged in motion_batches:
                self.assertEqual(staged, shared | {roots[0].stem})
            self.assertEqual(load.call_count, len(paths))

    def test_missing_dependency_fails_before_unity(self):
        model = Path("model_a.assetbundle")
        with patch("converter.bake_hasunosora.bundle_metadata",
                   return_value=("model_a", ["missing_asset"])):
            with self.assertRaisesRegex(FileNotFoundError, "missing_asset"):
                batches([model], BundleClosures({"model_a": model}),
                        max_roots=1, max_bundles=8)

    def test_unity_reads_original_input_paths_without_staging_bundles(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            input_dir = root / "input"
            output = root / "output"
            input_dir.mkdir()
            output.mkdir()
            model = input_dir / "model_a.assetbundle"
            dependency = input_dir / "shared.assetbundle"
            model.write_bytes(b"model")
            dependency.write_bytes(b"dependency")
            index = {"model_a": model, "shared": dependency}

            class FinishedProcess:
                returncode = 0

                def __enter__(self):
                    return self

                def __exit__(self, *args):
                    return False

                def poll(self):
                    return 0

            def inspect_command(command):
                self.assertEqual(command[command.index("-input") + 1], str(input_dir))
                bundle_list = Path(command[command.index("-bundleList") + 1])
                self.assertEqual(bundle_list.read_text(encoding="utf-8").splitlines(),
                                 [str(model), str(dependency)])
                self.assertEqual(list(output.glob("*.assetbundle")), [])
                return FinishedProcess()

            with patch("converter.bake_hasunosora.subprocess.Popen",
                       side_effect=inspect_command):
                run_batch(Path("Unity.exe"), root / "unity_project", input_dir, index,
                          output, "models-0001-of-0001", [model], set(index), 30,
                          models_only=True)
            self.assertEqual(list(output.iterdir()), [])
            self.assertEqual(model.read_bytes(), b"model")
            self.assertEqual(dependency.read_bytes(), b"dependency")


if __name__ == "__main__":
    unittest.main()
