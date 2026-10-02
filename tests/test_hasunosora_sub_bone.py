import unittest
from types import SimpleNamespace as NS

from converter.common.normalized_model import NormalizedNodeMapping
from converter.common.unity import object_id
from converter.hasunosora.sub_bone import build_sub_bone_parameters, extract_sub_bone_behavior


IDENTITY = [1., 0., 0., 0., 0., 1., 0., 0., 0., 0., 1., 0., 0., 0., 0., 1.]


class Pointer:
    def __init__(self, value, kind="Transform"):
        self.value = value
        self.type = NS(name=kind)

    def read(self):
        return self.value

    deref_parse_as_object = read


def fixture():
    asset = object()
    transforms = []
    gltf = []
    for i, (name, exported_name, parent) in enumerate([
        ("Root", "Root", None), ("K_Hips", "Hips", 0),
        ("K_Input", "LeftLowerArm", 1), ("K_Output", "K_Output", 2),
        ("K_Input", "DuplicateInput", 1), ("Extension_K_Hand", "Extension_K_Hand", 2),
    ]):
        go = NS(m_Name=name, m_Component=[], m_IsActive=True)
        transform = NS(object_reader=NS(assets_file=asset, path_id=i), m_GameObject=Pointer(go, "GameObject"),
                       m_Father=Pointer(transforms[parent]) if parent is not None else None, m_Children=[])
        go.m_Component.append((4, Pointer(transform)))
        transforms.append(transform)
        gltf.append({"name": exported_name, "children": []})
        if parent is not None:
            transforms[parent].m_Children.append(Pointer(transform))
            gltf[parent]["children"].append(i)
    definition = NS(inputs=["Input", "Unused"], outputs=["Output", "Extension_Hand"], category=1,
                    magnification=.37, minAngle=-30., maxAngle=20., inputAxis=1, outputAxis=3)
    metadata = NS(initialMainRotation=NS(x=.1, y=.2, z=.3, w=.9),
                  initialSubRotation=NS(x=0., y=0., z=0., w=1.),
                  initialMainRight=NS(x=1., y=0., z=0.), initialSubPosition=NS(x=.1, y=.2, z=.3),
                  inputs=["labels_are_not_keys"], outputs=[])
    controller = NS(m_Script=Pointer(NS(m_ClassName="SubBoneController"), "MonoScript"),
                    m_GameObject=transforms[0].m_GameObject, m_Enabled=True,
                    master=Pointer(NS(definitions=[definition])), data=[metadata])
    transforms[0].m_GameObject.read().m_Component.append((114, Pointer(controller, "MonoBehaviour")))
    mapping = NormalizedNodeMapping(
        {object_id(transform): i for i, transform in enumerate(transforms)},
        [list(IDENTITY) for _ in transforms], [list(IDENTITY) for _ in transforms],
        [list(IDENTITY) for _ in transforms], {},
    )
    exported = NS(node_mapping=mapping, builder=NS(document={"nodes": gltf}),
                  standard_bones={"Hips": 1, "LeftLowerArm": 2})
    return controller, exported, transforms, definition, metadata


class SubBoneExportTests(unittest.TestCase):
    def test_source_dfs_first_match_master_index_and_extension_prefix(self):
        controller, exported, _, definition, metadata = fixture()
        # Metadata labels deliberately differ; source uses the same array index.
        parameters = build_sub_bone_parameters(controller, exported)
        frames, rule = parameters["frames"], parameters["rules"][0]
        self.assertEqual(frames[rule["input"]]["node"], "LeftLowerArm")
        self.assertEqual([frames[index]["node"] for index in rule["outputs"]], ["K_Output", "Extension_K_Hand"])
        self.assertEqual(rule["magnification"], .37)
        self.assertEqual(rule["initialMainRotation"], [.1, .2, .3, .9])
        self.assertNotIn("inputAxis", rule)
        self.assertNotIn("initialSubPosition", rule)
        self.assertNotIn("DuplicateInput", [frame["node"] for frame in frames])

    def test_only_runtime_parameters_of_each_branch_are_published(self):
        controller, exported, _, definition, metadata = fixture()
        twist = NS(**{**vars(definition), "category": 2})
        move = NS(**{**vars(definition), "category": 7, "magnification": -.021})
        controller.master.read().definitions.extend([twist, move])
        controller.data.extend([metadata, metadata])
        rules = build_sub_bone_parameters(controller, exported)["rules"]
        self.assertEqual([rule["category"] for rule in rules], [1, 2, 7])
        self.assertEqual(set(rules[1]), {"category", "input", "outputs", "magnification", "initialMainRotation"})
        self.assertEqual(rules[2]["initialSubPosition"], [.1, .2, .3])
        self.assertEqual((rules[2]["minAngle"], rules[2]["maxAngle"]), (-30., 20.))

    def test_disabled_and_inactive_source_controller_do_not_run(self):
        controller, exported, transforms, _, _ = fixture()
        root = transforms[0].m_GameObject.read()
        declarations = extract_sub_bone_behavior(root, exported)
        self.assertEqual(declarations[0]["name"], "Hasunosora.SubBoneController")
        self.assertTrue(declarations[0]["required"])
        controller.m_Enabled = False
        self.assertEqual(extract_sub_bone_behavior(root, exported), [])
        controller.m_Enabled = True
        root.m_IsActive = False
        self.assertEqual(extract_sub_bone_behavior(root, exported), [])

    def test_bind_matrix_uses_source_neutral_and_canonical_frames(self):
        controller, exported, _, _, _ = fixture()
        # Both frames share the pivot; source X rotates into source Y.
        exported.node_mapping.neutral_world[2] = [0., 1., 0., 0., -1., 0., 0., 0., 0., 0., 1., 0., 0., 0., 0., 1.]
        parameters = build_sub_bone_parameters(controller, exported)
        frame = parameters["frames"][parameters["rules"][0]["input"]]
        self.assertEqual(frame["basis"], exported.node_mapping.neutral_world[2])
        self.assertEqual(parameters["frames"][frame["parent"]]["node"], "Hips")

    def test_unknown_category_missing_data_and_missing_source_transform_fail(self):
        controller, exported, _, definition, _ = fixture()
        definition.category = 9
        with self.assertRaisesRegex(ValueError, "not been recovered"):
            build_sub_bone_parameters(controller, exported)
        definition.category = 1
        definition.inputs = ["Absent"]
        with self.assertRaisesRegex(ValueError, "Transform missing"):
            build_sub_bone_parameters(controller, exported)
        controller.data = []
        with self.assertRaisesRegex(ValueError, "count mismatch"):
            build_sub_bone_parameters(controller, exported)

    def test_runtime_name_collision_gets_source_path_identity(self):
        controller, exported, _, _, _ = fixture()
        exported.builder.document["nodes"][4]["name"] = "K_Output"
        parameters = build_sub_bone_parameters(controller, exported)
        output_name = parameters["frames"][parameters["rules"][0]["outputs"][0]]["node"]
        self.assertEqual(output_name, "K_Output__SubBone_0_0_0")
        self.assertEqual(exported.builder.document["nodes"][3]["name"], output_name)
        self.assertEqual(exported.builder.document["nodes"][4]["name"], "K_Output")
        self.assertEqual(build_sub_bone_parameters(controller, exported), parameters)

    def test_renamed_source_parent_is_shared_by_input_and_output_frames(self):
        controller, exported, _, _, _ = fixture()
        del exported.standard_bones["LeftLowerArm"]
        exported.builder.document["nodes"][4]["name"] = "LeftLowerArm"
        parameters = build_sub_bone_parameters(controller, exported)
        frames, rule = parameters["frames"], parameters["rules"][0]
        self.assertEqual(frames[rule["input"]]["node"], "LeftLowerArm__SubBone_0_0")
        self.assertEqual(frames[rule["outputs"][0]]["parent"], rule["input"])

    def test_affine_output_parent_and_changed_parent_fail(self):
        controller, exported, _, _, _ = fixture()
        exported.node_mapping.neutral_world[3][12] = .01
        with self.assertRaisesRegex(ValueError, "rigid basis"):
            build_sub_bone_parameters(controller, exported)
        exported.node_mapping.neutral_world[3][12] = 0
        exported.node_mapping.neutral_world[2][0] = 2
        with self.assertRaisesRegex(ValueError, "rigid basis"):
            build_sub_bone_parameters(controller, exported)
        exported.node_mapping.neutral_world[2][0] = 1
        exported.builder.document["nodes"][2]["children"].remove(3)
        exported.builder.document["nodes"][1]["children"].append(3)
        with self.assertRaisesRegex(ValueError, "original direct parent"):
            build_sub_bone_parameters(controller, exported)

    def test_multiple_active_controllers_require_order_evidence(self):
        controller, exported, transforms, _, _ = fixture()
        root = transforms[0].m_GameObject.read()
        root.m_Component.append((114, Pointer(controller, "MonoBehaviour")))
        with self.assertRaisesRegex(ValueError, "execution-order evidence"):
            extract_sub_bone_behavior(root, exported)

    def test_self_and_later_writer_feedback_fail_but_prior_write_is_valid(self):
        controller, exported, _, definition, metadata = fixture()
        definition.inputs = ["Output"]
        with self.assertRaisesRegex(ValueError, "cross-frame feedback"):
            build_sub_bone_parameters(controller, exported)
        definition.inputs = ["Input"]
        definition.outputs = ["Output"]
        chained = NS(**{**vars(definition), "inputs": ["Output"], "outputs": ["Extension_Hand"]})
        controller.master.read().definitions.append(chained)
        controller.data.append(metadata)
        self.assertEqual(len(build_sub_bone_parameters(controller, exported)["rules"]), 2)
        controller.master.read().definitions.reverse()
        with self.assertRaisesRegex(ValueError, "cross-frame feedback"):
            build_sub_bone_parameters(controller, exported)


if __name__ == "__main__":
    unittest.main()
