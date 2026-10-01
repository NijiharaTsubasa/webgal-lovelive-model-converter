import unittest

from converter.llas import _strip_bake_metadata


class LlasMotionMetadataTests(unittest.TestCase):
    def test_package_strips_source_path_from_group_tracks(self):
        motion = {"clips": [{"tracks": [], "groupTracks": [
            {"kind": "transform", "path": "source/eye", "node": "eye", "property": "localTRS", "rotation": [0, 0, 0, 1]},
        ]}]}

        _strip_bake_metadata(motion)

        self.assertEqual(motion["clips"][0]["groupTracks"][0], {
            "kind": "transform", "node": "eye", "property": "localTRS", "rotation": [0, 0, 0, 1],
        })


if __name__ == "__main__":
    unittest.main()
