import unittest

from converter.common.glb import trim_unused_trailing_renderer_bones


class RendererBoneCompatibilityTests(unittest.TestCase):
    def test_trims_an_unreferenced_trailing_bone(self):
        bones = ["hip", "spine", "unused"]

        result = trim_unused_trailing_renderer_bones(
            "body",
            bones,
            ["hip bind", "spine bind"],
            [(0, 1, 2, 0)],
            [(0.5, 0.5, 0.0, 0.0)],
        )

        self.assertEqual(result, ["hip", "spine"])
        self.assertEqual(bones, ["hip", "spine", "unused"])

    def test_rejects_a_trailing_bone_with_nonzero_weight(self):
        with self.assertRaisesRegex(
            RuntimeError,
            r"body: vertex 0 references bone 2, but mesh has 2 bind poses",
        ):
            trim_unused_trailing_renderer_bones(
                "body",
                ["hip", "spine", "used tail"],
                ["hip bind", "spine bind"],
                [(0, 2, 0, 0)],
                [(0.5, 0.5, 0.0, 0.0)],
            )

    def test_preserves_non_trailing_mismatches_for_the_caller_to_reject(self):
        bones = ["hip"]

        result = trim_unused_trailing_renderer_bones(
            "body",
            bones,
            ["hip bind", "spine bind"],
            [(0, 0, 0, 0)],
            [(1.0, 0.0, 0.0, 0.0)],
        )

        self.assertIs(result, bones)


if __name__ == "__main__":
    unittest.main()
