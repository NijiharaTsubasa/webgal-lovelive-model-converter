import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import converter.bangdream as bangdream
from converter.bangdream import (
    BundleAssets,
    _avatar_binding_parameters,
    _avatar_profile_parameters,
    _breast_behavior_binding,
    _secondary_offsets,
    _source_direction_frame,
    _source_scale_frame,
    breast_morph_endpoint,
    breast_size_value,
    build_component_config,
    build_package_config,
    discover_bundle_inputs,
)
from converter.common.glb import GlbBuilder
from converter.convert_bangdream import clean_game_output


class BangDreamManifestTests(unittest.TestCase):
    def test_clean_rebuilds_entire_game_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            model = output / "model"
            motions = output / "motions"
            model.mkdir()
            motions.mkdir()
            (model / "config.json").write_text("{}", encoding="utf-8")
            (motions / "config.json").write_text("{}", encoding="utf-8")
            (output / "index.json").write_text("{}", encoding="utf-8")
            clean_game_output(output)
            self.assertFalse(model.exists())
            self.assertFalse((output / "index.json").exists())
            self.assertFalse(motions.exists())

    def test_secondary_offsets_skip_null_targets_like_original_runtime(self):
        scaler = {
            "_secondaryOffsets": [{
                "Target": {"m_FileID": 0, "m_PathID": 0},
                "UseRotation": 0,
                "Default": {"x": 1.0, "y": 2.0, "z": 3.0},
                "OffsetAxis": {"x": 4.0, "y": 5.0, "z": 6.0},
                "OffsetRange": {"x": 7.0, "y": 8.0},
            }],
        }

        self.assertEqual(
            _secondary_offsets(scaler, {"bones": []}, {}, {}, [], []),
            [],
        )

    def test_load_bundle_selects_avatar_description_attached_to_exported_prefab(self):
        selected = {
            "m_GameObject": {"m_FileID": 0, "m_PathID": 101},
            "BreastSize": 50.0,
            "BoneSettings": [],
        }
        unrelated = {
            "m_GameObject": {"m_FileID": 0, "m_PathID": 202},
            "BreastSize": 75.0,
            "BoneSettings": [],
        }
        prefab = SimpleNamespace(object_reader=SimpleNamespace(path_id=101), m_Component=[])
        pointer = SimpleNamespace(deref_parse_as_object=lambda: prefab, type=SimpleNamespace(name="GameObject"))

        def mono(tree):
            return SimpleNamespace(
                type=SimpleNamespace(name="MonoBehaviour"),
                read_typetree=lambda: tree,
            )

        environment = SimpleNamespace(
            container={
                "metadata.prefab": SimpleNamespace(type=SimpleNamespace(name="MonoBehaviour")),
                "assets/character/character.prefab": pointer,
            },
            objects=[mono(selected), mono(unrelated)],
        )
        with patch.object(bangdream.UnityPy, "load", return_value=environment):
            bundle = bangdream.load_bundle_assets(Path("character"))

        self.assertIs(bundle.avatar_description, selected)
        self.assertEqual(bangdream._package_name(bundle), 'character')
        with patch.object(bangdream, 'export_normalized_model') as export:
            bangdream.export_glb(bundle, {'humanScale': 1})
            self.assertIs(export.call_args.args[1], pointer)

    def test_source_direction_frame_uses_zero_muscle_parent_axes(self):
        transform = SimpleNamespace(
            m_LocalPosition=SimpleNamespace(x=-0.3, y=0.1, z=0.2),
        )
        parent_neutral = bangdream._trs_to_mat(
            [0.0, 0.0, 0.0],
            [0.0, 0.0, 2 ** -0.5, 2 ** -0.5],
            [1.0, 1.0, 1.0],
        )
        identity = bangdream._trs_to_mat(
            [0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 1.0], [1.0, 1.0, 1.0]
        )

        frame = _source_direction_frame(
            transform,
            1,
            [
                {"parentIndex": -1, "neutralWorldMatrix": parent_neutral},
                {"parentIndex": 0, "neutralWorldMatrix": identity},
            ],
            [identity, identity],
        )

        self.assertEqual(frame["sourcePosition"], [-0.3, 0.1, 0.2])
        self.assertTrue(all(
            abs(a - b) < 1e-9
            for a, b in zip(frame["projection"], parent_neutral)
        ))

    def test_source_scale_frame_uses_zero_muscle_axes(self):
        transform = SimpleNamespace(
            m_LocalPosition=SimpleNamespace(x=1.0, y=2.0, z=3.0),
            m_LocalRotation=SimpleNamespace(x=0.0, y=0.0, z=0.0, w=1.0),
            m_LocalScale=SimpleNamespace(x=1.0, y=1.0, z=1.0),
        )
        neutral = bangdream._trs_to_mat(
            [0.0, 0.0, 0.0],
            [0.0, 0.0, 2 ** -0.5, 2 ** -0.5],
            [1.0, 1.0, 1.0],
        )
        identity = bangdream._trs_to_mat(
            [0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 1.0], [1.0, 1.0, 1.0]
        )

        frame = _source_scale_frame(
            transform,
            0,
            [{"neutralWorldMatrix": neutral}],
            [identity],
        )

        recovered = bangdream._mat4_mul(neutral, frame["projection"]["right"])
        self.assertTrue(all(abs(a - b) < 1e-9 for a, b in zip(recovered, identity)))
        self.assertEqual(frame["source"]["position"], [1.0, 2.0, 3.0])

    def test_source_frames_preserve_nonidentity_canonical_joint_axes(self):
        transform = SimpleNamespace(
            m_LocalPosition=SimpleNamespace(x=-0.3, y=0.1, z=0.2),
            m_LocalRotation=SimpleNamespace(x=0.0, y=0.0, z=0.0, w=1.0),
            m_LocalScale=SimpleNamespace(x=1.0, y=1.0, z=1.0),
        )
        neutral = bangdream._trs_to_mat(
            [0.0, 1.0, 0.0], [0.0, 0.0, 2 ** -0.5, 2 ** -0.5], [1.0, 1.0, 1.0]
        )
        canonical = bangdream._trs_to_mat(
            [0.0, 1.0, 0.0], [0.5, 0.5, 0.5, 0.5], [1.0, 1.0, 1.0]
        )
        bones = [
            {"parentIndex": -1, "neutralWorldMatrix": neutral},
            {"parentIndex": 0, "neutralWorldMatrix": neutral},
        ]
        direction = _source_direction_frame(transform, 1, bones, [canonical, canonical])
        recovered_parent = bangdream._mat4_mul(canonical, direction["projection"])
        self.assertTrue(all(abs(a - b) < 1e-9 for a, b in zip(recovered_parent, neutral)))
        frame = _source_scale_frame(transform, 1, bones, [canonical, canonical])
        recovered_joint = bangdream._mat4_mul(neutral, frame["projection"]["right"])
        self.assertTrue(all(abs(a - b) < 1e-9 for a, b in zip(recovered_joint, canonical)))
        self.assertNotEqual(frame["projection"]["right"], canonical)

    def test_serializes_avatar_scaler_profile_and_resolved_body_binding(self):
        profile = _avatar_profile_parameters({
            "Height": 1.52,
            "BreastSize": 50.0,
            "LegSpacing": 1.1,
            "HeadScaling": 0.9,
            "HipScaling": 1.2,
            "ShoulderSpacing": 0.8,
            "BoneSettings": [{
                "Name": "Upper Legs",
                "HeightInfluence": 0.28,
                "Length": 1.01,
                "Thickness": -1.02,
            }],
        })
        self.assertEqual(profile, {
            "height": 1.52,
            "breastSize": 50.0,
            "legSpacing": 1.1,
            "headScaling": 0.9,
            "hipScaling": 1.2,
            "shoulderSpacing": 0.8,
            "boneSettings": [{
                "name": "Upper Legs",
                "heightInfluence": 0.28,
                "length": 1.01,
                "thickness": -1.02,
            }],
        })

        scaler = {
            "Height": 1.55,
            "UseScaling": 1,
            "LegSpacing": 1.0,
            "HeadScaling": 1.0,
            "HipScaling": 1.0,
            "ShoulderSpacing": 1.0,
            "BreastSize": 50.0,
            "_positionOffset": {"x": 0.0, "y": 0.0, "z": 0.0},
            "_propPositionOffset": 0.0,
            "_adjustOffsetRatio": {"x": 0.0, "y": 0.0, "z": 0.0},
            "_boneParts": [{
                "Name": "Upper Legs",
                "HeightInfluence": 0.3,
                "Length": 1.0,
                "Thickness": 1.0,
                "Bones": [{"m_FileID": 0, "m_PathID": 11}],
                "Targets": [{"m_FileID": 0, "m_PathID": 12}],
            }, {
                "Name": "Hands",
                "HeightInfluence": 0.0,
                "Length": 1.0,
                "Thickness": 1.0,
                "Bones": [{"m_FileID": 0, "m_PathID": 13}],
                "Targets": [{"m_FileID": 0, "m_PathID": 0}],
            }],
            "_accessories": [{"m_FileID": 0, "m_PathID": 14}],
            "_hip": {"m_FileID": 0, "m_PathID": 15},
        }
        binding = _avatar_binding_parameters(
            scaler,
            {11: "LeftUpperLeg", 12: "LeftLowerLeg", 14: "Skirt", 15: "Hips"},
        )
        self.assertTrue(binding["useScaling"])
        self.assertEqual(binding["upperLegs"], ["LeftUpperLeg", "RightUpperLeg"])
        self.assertEqual(binding["shoulders"], ["LeftShoulder", "RightShoulder"])
        self.assertEqual(binding["head"], "Head")
        self.assertEqual(binding["hip"], "Hips")
        self.assertEqual(binding["leftLeg"], ["LeftUpperLeg", "LeftLowerLeg", "LeftFoot"])
        self.assertEqual(binding["accessories"], ["Skirt"])
        self.assertEqual(binding["boneParts"][0]["bones"], ["LeftUpperLeg"])
        self.assertEqual(binding["boneParts"][0]["targets"], ["LeftLowerLeg"])
        self.assertEqual(binding["boneParts"][1]["bones"], [])
        self.assertEqual(binding["boneParts"][1]["targets"], [])
        self.assertEqual(binding["profile"]["height"], 1.55)

    def test_avatar_binding_rejects_unresolved_non_null_transform(self):
        scaler = {
            "Height": 1.55, "UseScaling": 1, "LegSpacing": 1,
            "HeadScaling": 1, "HipScaling": 1, "ShoulderSpacing": 1,
            "BreastSize": 50,
            "_positionOffset": {"x": 0, "y": 0, "z": 0},
            "_propPositionOffset": 0,
            "_adjustOffsetRatio": {"x": 0, "y": 0, "z": 0},
            "_boneParts": [], "_accessories": [],
            "_hip": {"m_FileID": 0, "m_PathID": 99},
        }
        with self.assertRaisesRegex(RuntimeError, "unresolved Transform.*99"):
            _avatar_binding_parameters(scaler, {})

    def test_preserves_numeric_breast_sizes_and_maps_known_source_aliases(self):
        self.assertEqual(
            [breast_size_value(value) for value in (0, 50, 75, 100)],
            [0.0, 50.0, 75.0, 100.0],
        )
        with self.assertRaisesRegex(ValueError, "finite BreastSize"):
            breast_size_value(float("nan"))

        self.assertEqual(breast_morph_endpoint("body_Base_breastS"), 0.0)
        self.assertEqual(breast_morph_endpoint("body_Base_breastMShape"), 50.0)
        self.assertEqual(breast_morph_endpoint("body_Base_reastM"), 50.0)
        self.assertEqual(breast_morph_endpoint("body_Base_breast_L1"), 100.0)
        self.assertIsNone(breast_morph_endpoint("body_Base_other"))

    def test_builds_self_contained_breast_behavior_binding_without_animation(self):
        class LocalPointer:
            def __init__(self, target):
                self.target = target

            def __bool__(self):
                return True

            def deref_parse_as_object(self):
                return self.target

        mesh = SimpleNamespace(m_Name="body_Mask_obj")
        renderer = SimpleNamespace(m_Mesh=LocalPointer(mesh))
        source = SimpleNamespace(
            path_id=11,
            type=SimpleNamespace(name="SkinnedMeshRenderer"),
            read=lambda: renderer,
        )
        bundle = BundleAssets(
            path=Path("costume/body"),
            env=SimpleNamespace(objects=[source]),
            prefab=None,
            avatar_scaler={
                "BreastSize": 75.0,
                "DefaultBreastSize": 1,
                "_blendShapeMax": {"x": 100.0, "y": 100.0},
                "_bodyRenderers": [{"m_FileID": 0, "m_PathID": 11}],
            },
            kind="body",
        )
        builder = GlbBuilder()
        builder.document["meshes"].append({
            "name": "body_Mask_obj",
            "weights": [0.0, 0.0, 0.0],
            "extras": {"targetNames": [
                "body_Mask_objS",
                "body_Mask_objL",
                "unrelated_after_runtime_slots",
            ]},
            "primitives": [],
        })
        builder.document["nodes"].append({
            "name": "body_Mask_obj Renderer",
            "mesh": 0,
        })
        exported = SimpleNamespace(builder=builder)

        binding = _breast_behavior_binding(bundle, exported)

        self.assertEqual(binding, {
            "defaultValue": 50.0,
            "blendShapeMax": [100.0, 100.0],
            "renderers": [{
                "target": "body_Mask_obj Renderer",
                "morphs": [
                    {"value": 0.0, "index": 0},
                    {"value": 100.0, "index": 1},
                ],
            }],
        })
        self.assertEqual(builder.document["animations"], [])

    def test_breast_binding_omits_source_renderers_with_no_blendshape_state(self):
        class LocalPointer:
            def __init__(self, target):
                self.target = target

            def __bool__(self):
                return True

            def deref_parse_as_object(self):
                return self.target

        mesh = SimpleNamespace(
            m_Name="body_Base_obj",
            m_Shapes=SimpleNamespace(channels=[]),
        )
        renderer = SimpleNamespace(m_Mesh=LocalPointer(mesh))
        source = SimpleNamespace(
            path_id=11,
            type=SimpleNamespace(name="SkinnedMeshRenderer"),
            read=lambda: renderer,
        )
        bundle = BundleAssets(
            path=Path("costume/no_morph_body"),
            env=SimpleNamespace(objects=[source]),
            prefab=None,
            avatar_scaler={
                "BreastSize": 0.0,
                "DefaultBreastSize": 0,
                "_blendShapeMax": {"x": 100.0, "y": 100.0},
                "_bodyRenderers": [{"m_FileID": 0, "m_PathID": 11}],
            },
            kind="body",
        )
        exported = SimpleNamespace(builder=SimpleNamespace(document={
            "meshes": [{"name": "body_Base_obj", "primitives": []}],
            "nodes": [{"name": "body_Base_obj Renderer", "mesh": 0}],
        }))

        self.assertEqual(
            _breast_behavior_binding(bundle, exported)["renderers"],
            [],
        )

    def test_remaps_expression_mesh_names_to_exported_gltf_nodes(self):
        exported = SimpleNamespace(builder=SimpleNamespace(document={
            "meshes": [{
                "name": "face_Base_obj",
                "extras": {"targetNames": [
                    "face_main_eye_close_L",
                    "face_main_mouth_open_a",
                ]},
            }],
            "nodes": [
                {"name": "face_Base_obj", "children": []},
                {"name": "face_Base_obj Renderer", "mesh": 0},
            ],
        }))
        expressions = {
            "morphPoses": [
                {"name": "eyes.Close", "targets": {"face_Base_obj": {"face_main_eye_close_L": 1.0}}},
                {"name": "mouth.A", "targets": {"face_Base_obj": {"face_main_mouth_open_a": 1.0}}},
            ],
            "expressionGroups": [{"name": "face", "type": "eye", "states": [{"name": "Neutral", "poses": {},
                                   "controls": {"blink": {"eyes.Close": 1}}}]}],
            "defaultExpression": {"eye": "Neutral"},
        }

        actual_expressions = bangdream.bind_expression_nodes(
            expressions,
            exported,
        )
        self.assertEqual(
            actual_expressions["morphPoses"][0]["targets"],
            {"face_Base_obj Renderer": {"face_main_eye_close_L": 1.0}},
        )
        self.assertEqual(
            actual_expressions["morphPoses"][1]["targets"],
            {"face_Base_obj Renderer": {"face_main_mouth_open_a": 1.0}},
        )
        self.assertEqual(actual_expressions["expressionGroups"], expressions["expressionGroups"])
        self.assertEqual(actual_expressions["defaultExpression"], expressions["defaultExpression"])
        self.assertIn("face_Base_obj", expressions["morphPoses"][0]["targets"])

    def test_rejects_ambiguous_exported_expression_targets(self):
        def exported(target_names, node_names):
            return SimpleNamespace(builder=SimpleNamespace(document={
                "meshes": [{
                    "name": "face_Base_obj",
                    "extras": {"targetNames": target_names},
                }],
                "nodes": [{"name": name, "mesh": 0} for name in node_names],
            }))

        targets = {"morphPoses": [{
            "name": "Neutral",
            "targets": {"face_Base_obj": {"mouth_a": 0.0}},
        }], "expressionGroups": []}
        with self.assertRaisesRegex(RuntimeError, "repeats morph node name"):
            bangdream.bind_expression_nodes(
                targets, exported(["mouth_a"], ["face Renderer", "face Renderer"])
            )
        with self.assertRaisesRegex(RuntimeError, "repeats a morph target name"):
            bangdream.bind_expression_nodes(
                targets, exported(["mouth_a", "mouth_a"], ["face Renderer"])
            )

    def test_discovers_head_and_costume_directories_with_expected_roles(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "head").mkdir()
            (root / "costume").mkdir()
            (root / "head" / "same_name").write_bytes(b"head")
            (root / "costume" / "same_name").write_bytes(b"body")
            (root / "costume" / "body_only").write_bytes(b"body")

            discovered = discover_bundle_inputs(root)

        self.assertEqual(
            [(path.parent.name, path.name, role) for path, role in discovered],
            [
                ("head", "same_name", "head"),
                ("costume", "body_only", "body"),
                ("costume", "same_name", "body"),
            ],
        )

    def test_empty_role_directory_has_no_model_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "head").mkdir()
            self.assertEqual(discover_bundle_inputs(root), [])

    def test_builds_self_contained_manifest_and_omits_body_face_fields(self):
        head = BundleAssets(
            path=Path("head/same_name"),
            env=object(),
            prefab=None,
            kind="head",
        )
        body = BundleAssets(
            path=Path("costume/same_name"),
            env=object(),
            prefab=None,
            avatar_json={"Height": 1.48},
            kind="body",
        )
        head_component = build_component_config(
            head,
            {"morphPoses": [], "expressionGroups": [{"name": "eye", "type": "eye",
             "states": [{"name": "Neutral", "poses": {}}]}], "defaultExpression": {"eye": "Neutral"}},
            "head.glb",
            human_scale=0.901234,
        )
        body_component = build_component_config(
            body,
            [],
            "body.glb",
            human_scale=0.923456,
        )
        manifest = build_package_config("same_name", [head_component, body_component])

        self.assertEqual(set(manifest), {"components"})
        self.assertNotIn("schemaVersion", manifest)
        self.assertEqual([item["role"] for item in manifest["components"]], ["head", "body"])
        self.assertTrue(all(item["type"] == "model" for item in manifest["components"]))
        self.assertTrue(all(item["name"] == "same_name" for item in manifest["components"]))
        self.assertTrue(all(item["group"] == "garupa" for item in manifest["components"]))
        self.assertTrue(all(item["motionGroup"] == "garupa" for item in manifest["components"]))
        self.assertEqual(head_component["humanoidScale"], 0.901234)
        self.assertEqual(body_component["humanoidScale"], 0.923456)
        self.assertEqual(head_component["defaultExpression"], {"eye": "Neutral"})
        self.assertEqual(head_component["morphPoses"], [])
        for field in ("morphPoses", "expressionGroups", "expressions", "defaultExpression"):
            self.assertNotIn(field, body_component)

    def test_component_config_emits_behavior_declarations(self):
        head = BundleAssets(
            path=Path("head/model"), env=object(), prefab=None, kind="head"
        )
        behaviors = [{
            "name": "Garupa.AvatarScaler",
            "required": True,
            "parameters": {"profile": {"height": 1.55}},
        }]
        component = build_component_config(
            head, {"morphPoses": [], "expressionGroups": []},
            "head.glb", human_scale=1.0, behaviors=behaviors
        )
        self.assertEqual(component["behaviors"], behaviors)

    def test_rejects_invalid_unity_human_scale(self):
        body = BundleAssets(
            path=Path("costume/body"),
            env=object(),
            prefab=None,
            avatar_json={"Height": 1.55},
            kind="body",
        )

        for invalid in (0.0, -1.0, float("nan"), float("inf")):
            with self.subTest(human_scale=invalid), self.assertRaisesRegex(
                ValueError,
                "humanScale",
            ):
                build_component_config(
                    body,
                    [],
                    "body.glb",
                    human_scale=invalid,
                )

    def test_rejects_raw_export_without_unity_human_scale(self):
        body = BundleAssets(
            path=Path("costume/body"),
            env=SimpleNamespace(container={}),
            prefab=None,
            kind="body",
        )

        with self.assertRaisesRegex(ValueError, "normalized skeleton.*humanScale"):
            bangdream.export_glb(body)

    def test_uses_authoritative_directory_role(self):
        bundle = BundleAssets(
            path=Path("costume/same_name"),
            env=SimpleNamespace(container={}),
            prefab=None,
            kind="unknown",
        )

        class FakeBuilder:
            def write(self, path):
                Path(path).write_bytes(b"glb")

        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(bangdream, "load_bundle_assets", return_value=bundle), \
                 patch.object(bangdream, "extract_model_physics", return_value=None), \
                 patch.object(bangdream, "_package_name", return_value="same_name"), \
                 patch.object(
                     bangdream,
                     "_load_normalized",
                     return_value={"humanScale": 0.912345},
                 ), \
                 patch.object(
                     bangdream,
                     "export_glb",
                     return_value=SimpleNamespace(
                         builder=FakeBuilder(),
                         human_scale=0.912345,
                     ),
                 ), patch.object(
                     bangdream,
                     "extract_head_expression",
                     return_value=[],
                 ):
                package_name, component = bangdream.convert_one(
                    Path("costume/same_name"),
                    Path(tmp),
                    expected_role="body",
                )

        self.assertEqual(package_name, "same_name")
        self.assertEqual(component["role"], "body")
        self.assertEqual(component["model"], "body.glb")
        self.assertEqual(component["humanoidScale"], 0.912345)
        self.assertNotIn("expressions", component)

    def test_incremental_conversion_preserves_absent_packages_and_roles(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_dir = root / "input"
            output_dir = root / "output"
            (input_dir / "head").mkdir(parents=True)
            (input_dir / "costume").mkdir()
            current_input = input_dir / "head" / "current"
            current_input.write_bytes(b"head")

            old_dir = output_dir / "old"
            old_dir.mkdir(parents=True)
            (old_dir / "body.glb").write_bytes(b"old body")
            (old_dir / "config.json").write_text(
                '{"components":[{"type":"model","name":"old",'
                '"group":"garupa","motionGroup":"garupa",'
                '"role":"body","model":"body.glb","humanoidScale":1.0}]}',
                encoding="utf-8",
            )

            current_dir = output_dir / "current"
            current_dir.mkdir()
            (current_dir / "body.glb").write_bytes(b"current body")
            (current_dir / "config.json").write_text(
                '{"components":[{"type":"model","name":"current",'
                '"group":"garupa","motionGroup":"garupa",'
                '"role":"body","model":"body.glb","humanoidScale":1.0}]}',
                encoding="utf-8",
            )

            head_component = {
                "role": "head",
                "model": "head.glb",
                "humanoidScale": 1.0,
                "morphPoses": [],
                "expressionGroups": [],
            }

            def fake_convert_one(entry, destination, baked, occupied, expected_role):
                package_dir = destination / "current"
                (package_dir / "head.glb").write_bytes(b"current head")
                return "current", head_component

            with patch.object(bangdream, "convert_one", side_effect=fake_convert_one):
                configs = bangdream.convert_all(input_dir, output_dir)

            self.assertEqual(
                [config["components"][0]["name"] for config in configs],
                ["current", "old"],
            )
            current_config = json.loads(
                (current_dir / "config.json").read_text(encoding="utf-8")
            )
            self.assertEqual(
                [component["role"] for component in current_config["components"]],
                ["head", "body"],
            )
            old_config = json.loads((old_dir / "config.json").read_text(encoding="utf-8"))
            self.assertEqual([component["role"] for component in old_config["components"]], ["body"])
            index = json.loads((output_dir / "index.json").read_text(encoding="utf-8"))
            self.assertEqual(index["configs"], ["current/config.json", "old/config.json"])

    def test_rejects_component_without_directory_role(self):
        with self.assertRaisesRegex(ValueError, "role must come from"):
            bangdream.convert_one(Path("unknown"), Path("output"))

    def test_batch_conversion_fails_on_component_error(self):
        with tempfile.TemporaryDirectory() as tmp, \
             patch.object(
                 bangdream,
                 "discover_bundle_inputs",
                 return_value=[(Path("head/broken"), "head")],
             ), patch.object(
                 bangdream,
                 "convert_one",
                 side_effect=RuntimeError("broken component"),
             ):
            with self.assertRaisesRegex(RuntimeError, "broken component"):
                bangdream.convert_all(Path("input"), Path(tmp))


if __name__ == "__main__":
    unittest.main()
