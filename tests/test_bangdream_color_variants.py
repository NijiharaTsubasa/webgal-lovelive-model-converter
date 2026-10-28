import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import Mock, patch

from converter.bangdream import build_package_config
from converter.bangdream import color_variants as variants


class Pointer:
    def __init__(self, identity, asset, value, kind="Material", file_id=0):
        self.m_PathID = identity
        self.m_FileID = file_id
        self.assetsfile = asset
        self.value = value
        self.type = NS(name=kind)

    def deref_parse_as_object(self):
        return self.value


def reader(kind, value, **extra):
    return NS(type=NS(name=kind), read=lambda: value, **extra)


class ColorVariantDiscoveryTests(unittest.TestCase):
    def test_monthly_jobs_ignore_head_changes_by_canonical_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = [(root / 'renamed-head', 'head'), (root / 'renamed-body', 'body')]
            with patch.object(variants, 'discover_bundle_inputs', return_value=paths), \
                    patch.object(variants, 'load_bundle_assets', return_value=object()), \
                    patch.object(variants, '_package_name', return_value='000_cos_monthly_2023_3'), \
                    patch.object(variants, 'changed_color_types', return_value=[1, 2]) as changes:
                jobs = variants.discover_variant_jobs(root)
            self.assertEqual(len(jobs), 1)
            self.assertEqual(jobs[0]['body'], [1, 2])
            self.assertEqual(jobs[0]['head'], [])
            self.assertIsNone(jobs[0]['head_path'])
            changes.assert_called_once()

    def test_compares_semantics_and_only_active_scoped_prefab_renderers(self):
        asset = object()
        root = NS(object_reader=NS(assets_file=asset, path_id=1), m_Layer=22)
        other = NS(object_reader=NS(assets_file=asset, path_id=2))
        pointers = {}

        def material(identity, name, colour, file_id=0):
            pointer = Pointer(identity, asset, NS(m_Name=name, colour=colour), file_id=file_id)
            pointers[file_id, identity] = pointer
            return pointer

        original = material(10, "body_Base", "white")
        mapped_original = material(15, "base replacement", "green")
        same = material(11, "renamed material", "green")
        changed = material(12, "body_Base_alt", "red")
        offset_only = material(16, "body_Offset", "green")
        external_same_path = material(15, "body_Base", "purple", file_id=1)
        unused = material(13, "unused", "white")
        unused_alt = material(14, "unused_alt", "blue")
        active = NS(m_Materials=[original], active=True, root=root, scoped=True,
                    m_GameObject=Pointer(1, asset, root, "GameObject"))
        inactive = NS(m_Materials=[unused], active=False, root=root, scoped=True)
        outside = NS(m_Materials=[unused], active=True, root=other, scoped=True)
        unscoped = NS(m_Materials=[unused], active=True, root=root, scoped=False)
        objects = [reader("SkinnedMeshRenderer", r) for r in [active, inactive, outside, unscoped]]
        script = Pointer(99, asset, NS(m_ClassName="ColorVariation"))
        for index, replacement in [(0, mapped_original), (1, same), (2, changed),
                                   (3, offset_only), (4, external_same_path)]:
            tree = {"m_Name": f"Color_bundle_{index + 1:02d}", "mapping": [
                {"Name": "body_Base", "Material": {"m_FileID": replacement.m_FileID, "m_PathID": replacement.m_PathID}},
                {"Name": "unused", "Material": {"m_FileID": 0, "m_PathID": unused_alt.m_PathID if index else unused.m_PathID}},
            ]}
            objects.append(reader("MonoBehaviour", NS(m_Script=script), assets_file=asset,
                                  read_typetree=lambda tree=tree: tree))
        bundle = NS(env=NS(objects=objects, container={"prefab/test.prefab": Pointer(1, asset, root, "GameObject")}))
        mapping = NS(variation_name="Color_bundle_01", context_for_renderer=lambda r: object() if r.scoped else None)
        with patch.object(variants, "MeteorMaterialMapping", return_value=mapping), \
                patch.object(variants, "renderer_activity", side_effect=lambda r: (r.active, r.root)), \
                patch.object(variants, "PPtr", side_effect=lambda **kw: pointers[kw["m_FileID"], kw["m_PathID"]]), \
                patch.object(variants, "material_snapshot", side_effect=lambda m: {"name": m.m_Name, "colour": m.colour}):
            self.assertEqual(variants.changed_color_types(bundle), [2, 3, 4])
            # Offset changes the initialized layer only inside the source menu range.
            root.m_Layer = 25
            self.assertEqual(variants.changed_color_types(bundle), [2, 4])

    def test_absent_colour_asset_has_no_alternate_outputs(self):
        with patch.object(variants, "MeteorMaterialMapping", return_value=NS(variation_name=None)):
            self.assertEqual(variants.changed_color_types(NS(env=NS(objects=[], container={}))), [])

    def test_duplicate_source_role_is_not_silently_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sources = [(root / "body1", "body"), (root / "body2", "body")]
            with patch.object(variants, "discover_bundle_inputs", return_value=sources), \
                    patch.object(variants, "load_bundle_assets", return_value=object()), \
                    patch.object(variants, "_package_name", return_value="001_costume"), \
                    patch.object(variants, "changed_color_types", return_value=[1]):
                with self.assertRaisesRegex(ValueError, "Duplicate body source"):
                    variants.discover_variant_jobs(root)

    def test_canonical_identity_not_filename_and_unchanged_heads_not_exported(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sources = [(root / "renamed-head", "head"), (root / "renamed-body", "body")]
            bundles = {role: NS(role=role) for _, role in sources}
            with patch.object(variants, "discover_bundle_inputs", return_value=sources), \
                    patch.object(variants, "load_bundle_assets", side_effect=lambda path, expected_role: bundles[expected_role]) as load, \
                    patch.object(variants, "_package_name", return_value="037_cos_outfit"), \
                    patch.object(variants, "changed_color_types", side_effect=lambda bundle: [2] if bundle.role == "head" else [1, 2]):
                jobs = variants.discover_variant_jobs(root)
            self.assertEqual(load.call_count, 2)
            self.assertEqual(jobs, [{"name": "037_cos_outfit", "body_path": str(sources[1][0].resolve()),
                                    "head_path": str(sources[0][0].resolve()), "body": [1, 2], "head": [2],
                                    "input_root": str(root.resolve())}])
            json.dumps(jobs)


class ColorVariantConversionTests(unittest.TestCase):
    def test_overwrite_reexports_existing_variant_instead_of_reusing_old_glb(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "out"
            job = self.job(root)
            job.update(body=[1], head=[])
            name = job["name"] + "_another1"
            self.complete(output, name, ["body"])
            self.complete(output, job["name"], ["body"])
            original = (output / job["name"] / "body.glb").read_bytes()

            def convert(path, output_dir, baked_dir, **kwargs):
                (output_dir / name / "body.glb").write_bytes(b"current exported model")
                return name, {"role": "body", "model": "body.glb"}

            with patch.object(variants, "load_bundle_assets", return_value=object()), \
                    patch.object(variants, "_package_name", return_value=job["name"]), \
                    patch.object(variants, "BodyPreviews", return_value=Mock(get=lambda name: None)), \
                    patch.object(variants, "convert_one", side_effect=convert) as export:
                result = variants.convert_variant_job(job, output, None, overwrite=True)
            self.assertEqual(result["generated"], [name])
            self.assertEqual(result["skipped"], [])
            self.assertEqual(result["failures"], [])
            export.assert_called_once()
            self.assertEqual((output / name / "body.glb").read_bytes(), b"current exported model")
            self.assertEqual((output / job["name"] / "body.glb").read_bytes(), original)

    def test_complete_alternate_receives_default_metadata_without_reexport(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            job = self.job(root)
            job.update(name='037_cos_party', body=[1], head=[])
            name = job['name'] + '_another1'
            output = root / 'output'
            self.complete(output, name, ['body'])
            with patch.object(variants, 'convert_one') as export, \
                    patch.object(variants, 'load_bundle_assets') as load:
                result = variants.convert_variant_job(job, output, None)
            self.assertEqual(result['skipped'], [name])
            export.assert_not_called()
            load.assert_not_called()
            config = json.loads((output / name / 'config.json').read_text(encoding='utf-8'))
            self.assertEqual(config['components'][0]['defaultMotion'], 'garupa/characterunique/ch037/001')
            self.assertEqual((output / name / 'body.glb').read_bytes(), b'complete fixture')

    def setUp(self):
        variants._previews_by_root.clear()

    def job(self, root):
        return {"name": "001_costume", "body_path": str(root / "body"), "head_path": str(root / "head"),
                "input_root": str(root / "input"), "body": [1, 2, 3, 4], "head": [2, 4]}

    def complete(self, output, name, roles):
        directory = output / name
        directory.mkdir(parents=True)
        components = [{"role": role, "model": f"{role}.glb"} for role in roles]
        (directory / "config.json").write_text(json.dumps(build_package_config(name, components)), encoding="utf-8")
        for role in roles:
            (directory / f"{role}.glb").write_bytes(b"complete fixture")

    def test_incremental_conversion_preserves_original_and_complete_alternates(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "out"
            job = self.job(root)
            self.complete(output, job["name"], ["head", "body"])
            self.complete(output, job["name"] + "_another1", ["body"])
            existing = {path: path.read_bytes() for path in output.rglob("*") if path.is_file()}
            bundles = {role: NS(role=role) for role in ("head", "body")}
            preview = Mock(get=lambda name: "preview:" + name)

            def convert(path, output_dir, baked_dir, *, expected_role, color_type, loaded_bundle):
                self.assertIs(loaded_bundle, bundles[expected_role])
                name = job["name"] + f"_another{color_type}"
                target = output_dir / name
                target.mkdir(parents=True, exist_ok=True)
                (target / f"{expected_role}.glb").write_bytes(b"new fixture")
                return name, {"role": expected_role, "model": f"{expected_role}.glb"}

            with patch.object(variants, "load_bundle_assets", side_effect=lambda path, expected_role: bundles[expected_role]) as load, \
                    patch.object(variants, "_package_name", return_value=job["name"]), \
                    patch.object(variants, "BodyPreviews", return_value=preview) as previews, \
                    patch.object(variants, "convert_one", side_effect=convert) as convert_mock:
                result = variants.convert_variant_job(job, output, root / "baked")
                again = variants.convert_variant_job(job, output, root / "baked")
            self.assertEqual(load.call_count, 2)
            self.assertEqual(previews.call_count, 1)
            self.assertEqual(convert_mock.call_count, 5)
            self.assertEqual(result["skipped"], [job["name"] + "_another1"])
            self.assertEqual(len(result["generated"]), 3)
            self.assertEqual(len(again["skipped"]), 4)
            for path, content in existing.items():
                self.assertEqual(path.read_bytes(), content)
            for index, roles in [(2, {"head", "body"}), (3, {"body"}), (4, {"head", "body"})]:
                name = job["name"] + f"_another{index}"
                config = json.loads((output / name / "config.json").read_text(encoding="utf-8"))
                self.assertEqual({c["role"] for c in config["components"]}, roles)
                self.assertEqual(config["components"][-1]["preview"], "preview:" + name)
            self.assertFalse((output / "index.json").exists())

    def test_failure_continues_and_incomplete_package_is_retried(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            job = self.job(root)
            job.update(body=[1, 2], head=[])
            output = root / "out"
            partial = output / (job["name"] + "_another1")
            partial.mkdir(parents=True)
            (partial / "body.glb").write_bytes(b"interrupted")

            def convert(path, output_dir, baked_dir, *, expected_role, color_type, loaded_bundle):
                if color_type == 1:
                    raise ValueError("broken source")
                name = job["name"] + "_another2"
                target = output_dir / name
                target.mkdir(parents=True)
                (target / "body.glb").write_bytes(b"new")
                return name, {"role": "body", "model": "body.glb"}

            with patch.object(variants, "load_bundle_assets", return_value=object()), \
                    patch.object(variants, "_package_name", return_value=job["name"]), \
                    patch.object(variants, "BodyPreviews", return_value=Mock(get=lambda name: None)), \
                    patch.object(variants, "convert_one", side_effect=convert):
                result = variants.convert_variant_job(job, output, None)
            self.assertEqual(result["generated"], [job["name"] + "_another2"])
            self.assertEqual(result["failures"], [{"name": job["name"] + "_another1", "error": "broken source"}])
            self.assertFalse((partial / "config.json").exists())


if __name__ == "__main__":
    unittest.main()
