import unittest
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from converter.hasunosora import character_identity
from converter.hasunosora.identity import CHARACTER_SLUGS, load_costume_motion_groups


def pointer(value):
    return SimpleNamespace(deref_parse_as_object=lambda: value)


class HasunosoraIdentityTests(unittest.TestCase):
    def test_role_domains_follow_master_data_not_costume_number(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "CostumeModels.yaml"
            # Deliberately unrelated ids prove identity comes from CharactersId.
            source.write_text("\n".join(
                f"- Id: {700 + index}\n  CharactersId: {character}"
                for index, character in enumerate(CHARACTER_SLUGS)
            ), encoding="utf-8")
            groups = load_costume_motion_groups(Path(directory))
            self.assertEqual(groups, {
                f"3d_costume_{700 + index}": f"hasunosora.{slug}"
                for index, slug in enumerate(CHARACTER_SLUGS.values())
            })

    def test_costumes_share_character_domain_and_npc_stays_ungrouped(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "CostumeModels.yaml"
            self.assertEqual(load_costume_motion_groups(Path(directory)), {})
            source.write_text(
                "- Id: 101\n  CharactersId: 1031\n"
                "- Id: 202\n  CharactersId: 1031\n"
                "- Id: 303\n  CharactersId: 1011\n"
                "- Id: 404\n", encoding="utf-8")
            self.assertEqual(load_costume_motion_groups(Path(directory)), {
                "3d_costume_101": "hasunosora.kaho",
                "3d_costume_202": "hasunosora.kaho",
            })

    def test_conflicting_master_identity_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "CostumeModels.yaml"
            source.write_text(
                "- Id: 101\n  CharactersId: 1031\n"
                "- Id: 101\n  CharactersId: 1021\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "conflicting character identity"):
                load_costume_motion_groups(Path(directory))

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
