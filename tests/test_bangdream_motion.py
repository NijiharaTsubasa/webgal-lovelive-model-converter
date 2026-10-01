import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from converter.bake_bangdream_motion import select_reference_pair

from converter.bangdream.motion import (
    _bind_group_track_nodes,
    _filter_placeholders,
    _simple_program,
    _strip_bake_metadata,
    actor_slot,
    discover_motion_bundles,
    is_placeholder_clip_name,
    split_actor_motions,
)


def clip(name: str) -> dict:
    return {
        "name": name,
        "duration": 1.0,
        "sampleRate": 1.0,
        "frames": 2,
        "tracks": [],
        "groupTracks": [],
    }


def baked(*clips: dict) -> dict:
    return {
        "clips": list(clips),
        "auxiliaryClips": [],
        "leftHandPoses": [],
        "rightHandPoses": [],
    }


class BangDreamMotionTests(unittest.TestCase):
    def test_reference_is_a_matching_pair_with_an_avatar(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "head").mkdir()
            (root / "costume").mkdir()
            for role, name in (
                ("head", "001_cos_live_default"),
                ("costume", "001_cos_live_default"),
                ("head", "002_cos_live_default"),
                ("costume", "002_cos_live_default"),
                ("costume", "003_cos_live_default"),
            ):
                (root / role / name).touch()
            with patch("converter.bake_bangdream_motion._has_avatar_asset",
                       side_effect=lambda path: path.name == "002_cos_live_default"):
                head, body = select_reference_pair(root)
                self.assertEqual(head.name, "002_cos_live_default")
                self.assertEqual(body.name, head.name)
                with self.assertRaisesRegex(ValueError, "No matched"):
                    select_reference_pair(root, "003_cos_live_default")

    def test_package_strips_source_path_from_group_tracks(self):
        motion = baked(clip("mot_demo"))
        motion["clips"][0]["groupTracks"] = [
            {"kind": "morph", "path": "source/face", "node": "face", "property": "smile", "values": [0, 1]},
        ]

        _strip_bake_metadata(motion)

        self.assertEqual(motion["clips"][0]["groupTracks"][0], {
            "kind": "morph", "node": "face", "property": "smile", "values": [0, 1],
        })

    def test_binds_morph_group_tracks_to_exported_renderer_nodes(self):
        motion = baked(clip("mot_demo"))
        motion["clips"][0]["groupTracks"] = [
            {"kind": "morph", "node": "face_Base_obj", "property": "mouth_a", "values": [0, 1]},
            {"kind": "transform", "node": "prop_root", "property": "localTRS", "rotation": [0, 0, 0, 1] * 2},
        ]

        _bind_group_track_nodes(motion)
        _bind_group_track_nodes(motion)

        self.assertEqual(motion["clips"][0]["groupTracks"][0]["node"], "face_Base_obj Renderer")
        self.assertEqual(motion["clips"][0]["groupTracks"][1]["node"], "prop_root")

    def test_discovers_only_requested_motion_families_by_relative_path(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            expected = [
                "charactertype/cool/003",
                "characterunique/ch018/003",
                "cutin3d/centersolo/ch018/001",
            ]
            for relative in expected + ["band/band001/003", "lipsync/cool"]:
                path = root / "motions" / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"fixture")

            discovered = discover_motion_bundles(root)

        self.assertEqual([name for name, _ in discovered], expected)

    def test_filters_only_explicit_placeholder_and_calibration_names(self):
        for name in ("TPose", "T-Pose", "bind_pose", "CalibrationPose", "reference-pose"):
            with self.subTest(name=name):
                self.assertTrue(is_placeholder_clip_name(name))
        self.assertFalse(is_placeholder_clip_name("mot_all_chr_018_pose_in"))

        data = baked(clip("TPose"), clip("mot_all_cmn_cool_003-01_in"))
        self.assertEqual(_filter_placeholders(data), ["TPose"])
        self.assertEqual([item["name"] for item in data["clips"]], ["mot_all_cmn_cool_003-01_in"])

    def test_detects_actor_slots_from_explicit_suffix_not_enumeration_order(self):
        self.assertEqual(actor_slot("mot_x-01-a_in"), "A")
        self.assertEqual(actor_slot("mot_x-01-b_lp"), "B")
        self.assertIsNone(actor_slot("mot_x_ambient_in"))

    def test_splits_dual_cutin_with_semantic_names_when_tokens_differ(self):
        data = baked(
            clip("mot_cutin_center-coupling_cmn_cool_cute_001-01-b_in"),
            clip("mot_cutin_center-coupling_cmn_cool_cute_001-01-a_in"),
        )

        result = split_actor_motions(data, "cutin3d/centercoupling/cool/cute/001")

        self.assertEqual([name for name, _ in result], [
            "cutin3d/centercoupling/cool/cute/001-cool",
            "cutin3d/centercoupling/cool/cute/001-cute",
        ])
        self.assertEqual([item[1]["clips"][0]["name"] for item in result], [
            "mot_cutin_center-coupling_cmn_cool_cute_001-01-a_in",
            "mot_cutin_center-coupling_cmn_cool_cute_001-01-b_in",
        ])

    def test_split_falls_back_to_a_b_for_equal_or_missing_semantic_tokens(self):
        data = baked(clip("mot_x-a_in"), clip("mot_x-b_in"))
        equal = split_actor_motions(data, "cutin3d/centercoupling/pure/pure/001")
        other = split_actor_motions(data, "cutin3d/centercoupling/other/001")
        self.assertEqual([name for name, _ in equal], [
            "cutin3d/centercoupling/pure/pure/001-A",
            "cutin3d/centercoupling/pure/pure/001-B",
        ])
        self.assertEqual([name for name, _ in other], [
            "cutin3d/centercoupling/other/001-A",
            "cutin3d/centercoupling/other/001-B",
        ])

    def test_simple_program_plays_in_then_loops_lp(self):
        data = baked(clip("mot_demo_lp"), clip("mot_demo_in"))

        program = _simple_program(data)

        states = program["layers"][0]["states"]
        self.assertEqual([item["id"] for item in states], ["mot_demo_in", "mot_demo_lp"])
        self.assertEqual(program["layers"][0]["initialState"], "mot_demo_in")
        self.assertEqual(states[0]["transitions"][0]["to"], "mot_demo_lp")
        self.assertFalse(states[0]["loop"])
        self.assertTrue(states[1]["loop"])
        self.assertEqual(program["commands"]["stop"], [])


if __name__ == "__main__":
    unittest.main()
