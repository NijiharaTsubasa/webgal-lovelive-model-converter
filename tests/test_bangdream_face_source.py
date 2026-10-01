import unittest
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import UnityPy
from UnityPy.classes.PPtr import PPtr

from converter.bangdream.face_source import load_face_controller
from converter.bangdream import load_bundle_assets


def source_map(name, *, targets=None, maximum=100, minimum=0, shape_type=90):
    return {"Name": name, "RangeMin": minimum, "RangeMax": maximum,
            "Type": shape_type, "Targets": [] if targets is None else targets}


class FaceControllerSourceTests(unittest.TestCase):
    def setUp(self):
        self.file = SimpleNamespace(objects={}, externals=[], name="head")
        self.other = SimpleNamespace(objects={}, externals=[], name="mesh")
        parent = SimpleNamespace(files={"head": self.file, "mesh": self.other})
        self.file.parent = self.other.parent = parent
        self.file.externals = [SimpleNamespace(path="archive:/mesh")]
        self.tree = {
            "m_Script": {"m_FileID": 0, "m_PathID": 2},
            "Layers": [{"Name": "Lipsync", "Mixers": [{"Name": "A", "Shapes": [1]}]}],
            "BlendShapes": [source_map("disabled", maximum=0), source_map("open_a", targets=[
                {"Renderer": {"m_FileID": 1, "m_PathID": 3}, "Index": 1},
            ])],
        }
        self.add(self.file, 1, "MonoBehaviour", self.tree)
        self.add(self.file, 2, "MonoScript", {"m_ClassName": "FaceController"})
        # Colliding IDs across files ensure both renderer and mesh use their
        # actual PPtr owner, never an environment-wide path-ID lookup.
        self.add(self.file, 3, "SkinnedMeshRenderer", {"m_Mesh": {"m_FileID": 0, "m_PathID": 4}})
        self.add(self.file, 4, "Mesh", {"m_Name": "wrong", "m_Shapes": {"channels": [{"name": "wrong"}]}})
        self.add(self.other, 3, "SkinnedMeshRenderer", {"m_Mesh": {"m_FileID": 0, "m_PathID": 4}})
        self.add(self.other, 4, "Mesh", {"m_Name": "correct_mesh", "m_Shapes": {"channels": [
            {"name": "not_this"}, {"name": "prefix.no_naming_convention"},
        ]}})
        self.root = SimpleNamespace(m_Name="root", m_Component=[
            (114, PPtr(m_FileID=0, m_PathID=1, assetsfile=self.file)),
        ])

    @staticmethod
    def add(file, path_id, kind, tree):
        reader = SimpleNamespace(assets_file=file, path_id=path_id,
                                 type=SimpleNamespace(name=kind), read_typetree=lambda: deepcopy(tree))
        file.objects[path_id] = reader
        return reader

    def test_serialized_order_zero_ranges_and_explicit_external_targets(self):
        result = load_face_controller(self.root)
        self.assertEqual([m["Type"] for m in result["BlendShapes"]], [90, 90])
        self.assertEqual(result["Layers"], self.tree["Layers"])
        self.assertEqual(result["BlendShapes"][0]["RangeMax"], 0)
        self.assertEqual(result["BlendShapes"][0]["Targets"], [])
        self.assertEqual(result["BlendShapes"][1]["Targets"], [
            {"mesh": "correct_mesh", "morph": "no_naming_convention"},
        ])

    def test_only_attached_controller_selected(self):
        other = deepcopy(self.tree)
        other["BlendShapes"][1]["RangeMax"] = 13
        self.add(self.file, 10, "MonoBehaviour", other)
        self.assertEqual(load_face_controller(self.root)["BlendShapes"][1]["RangeMax"], 100)
        self.root.m_Component = [(114, PPtr(m_FileID=0, m_PathID=10, assetsfile=self.file))]
        self.assertEqual(load_face_controller(self.root)["BlendShapes"][1]["RangeMax"], 13)
        self.root.m_Component = []
        self.assertIsNone(load_face_controller(self.root))

    def test_multiple_controllers_on_root_are_ambiguous(self):
        self.add(self.file, 10, "MonoBehaviour", self.tree)
        self.root.m_Component.append(SimpleNamespace(component=PPtr(m_FileID=0, m_PathID=10, assetsfile=self.file)))
        with self.assertRaisesRegex(ValueError, "multiple FaceControllers"):
            load_face_controller(self.root)

    def test_non_controller_component_is_not_selected_by_field_names(self):
        self.file.objects[2].read_typetree = lambda: {"m_ClassName": "OtherController"}
        self.assertIsNone(load_face_controller(self.root))

    def test_nonfinite_or_nonzero_minimum_is_not_silently_approximated(self):
        for field, value, message in [("RangeMax", float("nan"), "non-finite"),
                                      ("RangeMin", float("inf"), "non-finite"),
                                      ("RangeMin", 1, "nonzero RangeMin")]:
            with self.subTest(field=field, value=value):
                self.setUp()
                self.tree["BlendShapes"][0][field] = value
                with self.assertRaisesRegex(ValueError, message):
                    load_face_controller(self.root)

    def test_invalid_channel_or_layer_index_is_reported(self):
        self.tree["BlendShapes"][1]["Targets"][0]["Index"] = 2
        with self.assertRaisesRegex(ValueError, "invalid target channel index"):
            load_face_controller(self.root)
        self.tree["BlendShapes"][1]["Targets"][0]["Index"] = 1
        self.tree["Layers"][0]["Mixers"][0]["Shapes"] = [90]
        with self.assertRaisesRegex(ValueError, "invalid BlendShapes list offset"):
            load_face_controller(self.root)

    def test_null_or_missing_renderer_is_reported(self):
        for path_id in (0, 999):
            self.tree["BlendShapes"][1]["Targets"][0]["Renderer"]["m_PathID"] = path_id
            with self.assertRaisesRegex(ValueError, "unresolved source reference"):
                load_face_controller(self.root)




if __name__ == "__main__":
    unittest.main()
