import unittest

from converter.common.component_order import order_model_component


class ComponentOrderTests(unittest.TestCase):
    def test_short_metadata_precedes_facial_tables(self):
        component = {
            "type": "model", "name": "example", "morphPoses": [],
            "expressionGroups": [], "defaultExpression": {},
            "humanoidScale": 1, "motionGroup": "game",
            "description": "角色 / 服装",
        }
        result = order_model_component(component)
        self.assertEqual(list(result), [
            "type", "name", "description", "motionGroup", "humanoidScale",
            "defaultExpression", "morphPoses", "expressionGroups",
        ])
        self.assertEqual(result, component)


if __name__ == "__main__":
    unittest.main()
