import tempfile
import unittest
from pathlib import Path

from converter.common.component_order import order_model_component
from converter.hasunosora import load_costume_labels


class HasunosoraCostumeLabelsTests(unittest.TestCase):
    def test_missing_master_data_is_optional(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(load_costume_labels(Path(directory)), {})

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
                "group": "hasunosora", "expressions": [],
                "description": labels["3d_costume_1001102101"],
            })
            self.assertEqual(list(component)[:3], ["type", "name", "description"])


if __name__ == "__main__":
    unittest.main()
