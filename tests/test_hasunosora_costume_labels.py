import tempfile
import unittest
from pathlib import Path

from converter.common.component_order import order_model_component
from converter.hasunosora import load_costume_labels


class HasunosoraCostumeLabelsTests(unittest.TestCase):
    def test_missing_master_data_is_optional(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(load_costume_labels(Path(directory)), {
                "3d_costume_1001901201": "制服(冬)_上靴_錦上マイカ",
                "3d_costume_1001901301": "制服(冬)_上靴_令沢葵",
            })

    def test_supplemental_labels_are_exact_and_master_label_takes_precedence(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "CostumeModels.yaml"
            source.write_text(
                "- Id: 1001901201\n  Label: マスターの衣装名\n"
                "- Id: 1001901202\n  CharactersId: 9012\n",
                encoding="utf-8",
            )
            self.assertEqual(load_costume_labels(Path(directory)), {
                "3d_costume_1001901201": "マスターの衣装名",
                "3d_costume_1001901301": "制服(冬)_上靴_令沢葵",
            })

    def test_label_matches_bundle_id_and_precedes_large_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "CostumeModels.yaml"
            source.write_text(
                "- Id: 1001102101\n"
                "  Label: 制服(冬)_上靴_乙宗梢\n"
                "- Id: 1001102201\n"
                "  Label: 制服(冬)_上靴_夕霧綴理\n",
                encoding="utf-8",
            )
            labels = load_costume_labels(Path(directory))
            self.assertEqual(labels["3d_costume_1001102101"], "制服(冬)_上靴_乙宗梢")
            self.assertEqual(labels["3d_costume_1001102201"], "制服(冬)_上靴_夕霧綴理")

            component = order_model_component({
                "type": "model", "name": "3d_costume_1001102101",
                "group": "hasunosora", "expressionGroups": [],
                "description": labels["3d_costume_1001102101"],
            })
            self.assertEqual(list(component)[:3], ["type", "name", "description"])


if __name__ == "__main__":
    unittest.main()
