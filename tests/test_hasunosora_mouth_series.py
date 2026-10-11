import unittest
from copy import deepcopy

from converter.hasunosora.mouth_series import LIPS, deduplicate_mouth_series


def package():
    result = {"morphPoses": [], "expressionGroups": [
        {"type": "eye", "states": []}, {"type": "mouth", "states": []}],
        "preview": "unchanged", "physics": {"keep": True},
        "defaultExpression": {"eye": "happy", "closed": "happy/close", "open": "happy/a"}}
    for name in ("normal", "happy", "different"):
        result["expressionGroups"][0]["states"].append({"name": name, "poses": {}})
        poses = {lip: f"mouth.{name}.{lip}" for lip in LIPS}
        for index, lip in enumerate(LIPS):
            value = index + 1 if name != "different" or lip != "o" else 20
            result["morphPoses"].append({"name": poses[lip], "targets": {
                "Face": {"mouth": value, "unused": 0}}})
            result["expressionGroups"][1]["states"].append({"name": f"{name}/{lip}",
                "poses": {poses[lip]: 1}, "controls": {
                    "visemes": {vowel: {poses[vowel]: 1} for vowel in "aiueo"}}})
    return result


class MouthSeriesTests(unittest.TestCase):
    def test_complete_series_dedup_and_pairing_not_single_endpoint(self):
        source = package()
        original = deepcopy(source)
        result = deduplicate_mouth_series(source)
        self.assertEqual(source, original)
        self.assertEqual(len(result["expressionGroups"][1]["states"]), 12)
        eyes = {state["name"]: state for state in result["expressionGroups"][0]["states"]}
        self.assertEqual(eyes["happy"]["mouth"], {"closed": "normal/close", "open": "normal/a"})
        self.assertEqual(eyes["different"]["mouth"], {"closed": "different/close", "open": "different/a"})
        self.assertEqual(result["defaultExpression"], {"eye": "happy", "closed": "normal/close", "open": "normal/a"})
        self.assertEqual(result["preview"], source["preview"])
        self.assertEqual(result["physics"], source["physics"])
        self.assertEqual(result, deduplicate_mouth_series(result))

    def test_fixed_series_ignore_names_zero_items_and_order(self):
        source = {"morphPoses": [
            {"name": "mouth.a", "targets": {"Face": {"m": 2, "unused": 0}}},
            {"name": "mouth.b", "targets": {"Face": {"m": 2}}}],
            "expressionGroups": [{"type": "eye", "states": [
                {"name": "a", "poses": {}}, {"name": "b", "poses": {}}]},
                {"type": "mouth", "states": [
                    {"name": "a", "poses": {"mouth.a": 1}},
                    {"name": "b", "poses": {"mouth.b": 1}}]}]}
        result = deduplicate_mouth_series(source)
        self.assertEqual(len(result["expressionGroups"][1]["states"]), 1)
        self.assertEqual(result["expressionGroups"][0]["states"][1]["mouth"], {"closed": "a", "open": "a"})

    def test_incomplete_vowels_are_not_silently_merged(self):
        source = package()
        source["expressionGroups"][1]["states"].pop()
        with self.assertRaisesRegex(ValueError, "Incomplete"):
            deduplicate_mouth_series(source)

    def test_control_endpoint_difference_keeps_series(self):
        source = package()
        states = source["expressionGroups"][1]["states"]
        for state in states:
            if state["name"].startswith("happy/"):
                state["controls"]["visemes"]["o"] = {"mouth.happy.o": .5}
        result = deduplicate_mouth_series(source)
        self.assertEqual(len(result["expressionGroups"][1]["states"]), 18)

    def test_visemes_are_complete_targets_independent_of_recipe_alias_overlap(self):
        source = package()
        # The same physical base and endpoint have different recipe names.
        # Reusing a base recipe inside one endpoint must not add the other
        # series' base on top of its independently named endpoint.
        for state in source["expressionGroups"][1]["states"]:
            if state["name"].startswith("happy/"):
                lip = state["name"].rsplit("/", 1)[1]
                state["poses"] = {f"mouth.normal.{lip}": 1}
        result = deduplicate_mouth_series(source)
        self.assertEqual(len(result["expressionGroups"][1]["states"]), 12)
        self.assertEqual(result["expressionGroups"][0]["states"][1]["mouth"],
                         {"closed": "normal/close", "open": "normal/a"})

    def test_viseme_empty_target_clears_base_and_deduplicates(self):
        source = package()
        for state in source["expressionGroups"][1]["states"]:
            if state["name"].startswith(("normal/", "happy/")):
                lip = state["name"].rsplit("/", 1)[1]
                state["controls"]["visemes"]["u"] = (
                    {f"mouth.normal.{lip}": 0} if state["name"].startswith("normal/") else {})
        result = deduplicate_mouth_series(source)
        self.assertEqual(len(result["expressionGroups"][1]["states"]), 12)


if __name__ == "__main__":
    unittest.main()
