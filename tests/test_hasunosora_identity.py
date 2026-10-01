import unittest
from types import SimpleNamespace
from unittest.mock import patch

from converter.hasunosora import character_identity


def pointer(value):
    return SimpleNamespace(deref_parse_as_object=lambda: value)


class HasunosoraIdentityTests(unittest.TestCase):
    def test_body_variants_resolve_to_the_unity_skeleton_name(self):
        for body_name, expected in (
            ("SCSch012KozDeB", "SCSch012KozDeB"),
            ("SCSch012KozSuA", "SCSch012KozSuA"),
            ("SCSch013TsuLfA_fb", "SCSch013TsuLfA"),
        ):
            body = SimpleNamespace(m_GameObject=pointer(SimpleNamespace(m_Name=body_name)), m_Children=[])
            face = SimpleNamespace(m_GameObject=pointer(SimpleNamespace(m_Name="SCSch012Koz_Face_normal")), m_Children=[])
            root = SimpleNamespace(m_GameObject=pointer(SimpleNamespace(m_Name="3d_costume")),
                                   m_Children=[pointer(body), pointer(face)])
            with self.subTest(body_name=body_name), patch("converter.hasunosora.game_object_transform", return_value=root):
                self.assertEqual(character_identity(object()), expected)


if __name__ == "__main__":
    unittest.main()
