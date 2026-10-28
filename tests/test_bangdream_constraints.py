import unittest
import tempfile
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch

import converter.bangdream as bangdream
from converter.bangdream.constraints import extract_transform_constraint_behavior
from converter.common.normalized_model import NormalizedNodeMapping
from converter.common.unity import object_id


IDENTITY = [1., 0., 0., 0., 0., 1., 0., 0., 0., 0., 1., 0., 0., 0., 0., 1.]


class Pointer:
    def __init__(self, value, kind="Transform"):
        self.value = value
        self.type = NS(name=kind)

    def __bool__(self):
        return self.value is not None

    def deref_parse_as_object(self):
        return self.value


def fixture():
    asset = object()
    transforms, nodes = [], []
    for i, (name, parent) in enumerate([
        ("Root", None), ("Shoulder", 0), ("Arm", 1),
        ("Twist", 2), ("OtherTwist", 2),
    ]):
        go = NS(m_Name=name, m_Component=[], m_IsActive=True)
        transform = NS(object_reader=NS(assets_file=asset, path_id=i),
                       m_GameObject=Pointer(go, "GameObject"), m_Children=[],
                       m_Father=Pointer(transforms[parent]) if parent is not None else None)
        go.m_Component.append((4, Pointer(transform)))
        transforms.append(transform)
        nodes.append({"name": name, "children": []})
        if parent is not None:
            transforms[parent].m_Children.append(Pointer(transform))
            nodes[parent]["children"].append(i)
    constraint = NS(
        m_Enabled=1, m_Active=True, m_Weight=.7,
        m_RotationAtRest=NS(x=2., y=-3., z=8.),
        m_RotationOffset=NS(x=-.4, y=12., z=.3),
        m_AffectRotationX=True, m_AffectRotationY=False, m_AffectRotationZ=True,
        m_Sources=[NS(sourceTransform=Pointer(transforms[1]), weight=.2),
                   NS(sourceTransform=Pointer(None), weight=.6),
                   NS(sourceTransform=Pointer(transforms[2]), weight=.8)],
    )
    transforms[3].m_GameObject.value.m_Component.append((181, Pointer(constraint, "RotationConstraint")))
    mapping = NormalizedNodeMapping(
        {object_id(transform): i for i, transform in enumerate(transforms)},
        [list(IDENTITY) for _ in transforms], [list(IDENTITY) for _ in transforms],
        [list(IDENTITY) for _ in transforms], {},
    )
    exported = NS(node_mapping=mapping, builder=NS(document={"nodes": nodes}),
                  standard_bones={"LeftShoulder": 1})
    return transforms, constraint, exported


class TransformConstraintExportTests(unittest.TestCase):
    def test_exports_actual_source_order_weights_axes_and_source_euler_values(self):
        transforms, constraint, exported = fixture()
        behavior, = extract_transform_constraint_behavior(transforms[0].m_GameObject.value, exported)
        self.assertEqual((behavior["name"], behavior["required"]), ("Garupa.TransformConstraint", True))
        parameters = behavior["parameters"]
        frames = parameters["frames"]
        rule, = parameters["constraints"]
        self.assertEqual(frames[rule["target"]]["node"], "Twist")
        self.assertEqual([frames[source["frame"]]["node"] if source["frame"] is not None else None
                          for source in rule["sources"]], ["Shoulder", None, "Arm"])
        self.assertEqual([source["weight"] for source in rule["sources"]], [.2, .6, .8])
        self.assertEqual(rule["rotationAtRest"], [2., -3., 8.])
        self.assertEqual(rule["rotationOffset"], [-.4, 12., .3])
        self.assertEqual(rule["type"], "rotation")
        self.assertEqual(rule["axes"], [True, False, True])
        self.assertEqual(rule["weight"], .7)
        self.assertTrue(rule["enabled"])
        self.assertTrue(rule["active"])

    def test_frame_seam_uses_normalized_neutral_mapping_and_original_parents(self):
        transforms, _, exported = fixture()
        # A source neutral frame differing from the canonical frame must be
        # restored before evaluating a world-space RotationConstraint.
        exported.node_mapping.neutral_world[3] = [
            0., 1., 0., 0., -1., 0., 0., 0., 0., 0., 1., 0., .2, .3, .4, 1.,
        ]
        parameters = extract_transform_constraint_behavior(transforms[0].m_GameObject.value, exported)[0]["parameters"]
        frame = parameters["frames"][parameters["constraints"][0]["target"]]
        self.assertEqual(frame["basis"], exported.node_mapping.neutral_world[3])
        self.assertEqual(parameters["frames"][frame["parent"]]["node"], "Arm")
        parents = {item["node"]: None if item["parent"] is None
                   else parameters["frames"][item["parent"]]["node"]
                   for item in parameters["frames"]}
        self.assertEqual(parents, {"Twist": "Arm", "Arm": "Shoulder", "Shoulder": "Root", "Root": None})

    def test_frame_preserves_source_euler_hint_and_native_stripped_default(self):
        transforms, _, exported = fixture()
        transforms[3].m_LocalEulerAnglesHint = NS(x=23., y=-41., z=197.)
        parameters = extract_transform_constraint_behavior(transforms[0].m_GameObject.value, exported)[0]["parameters"]
        frames = {item["node"]: item for item in parameters["frames"]}
        self.assertEqual(frames["Twist"]["eulerHint"], [23., -41., 197.])
        self.assertEqual(frames["Shoulder"].get("eulerHint", [0., 0., 0.]), [0., 0., 0.])

    def test_constraint_count_and_target_names_come_from_components(self):
        transforms, constraint, exported = fixture()
        second = NS(**vars(constraint))
        second.m_Sources = []
        transforms[3].m_GameObject.value.m_Component.append((181, Pointer(second, "RotationConstraint")))
        transforms[4].m_GameObject.value.m_Component.append((181, Pointer(second, "RotationConstraint")))
        parameters = extract_transform_constraint_behavior(transforms[0].m_GameObject.value, exported)[0]["parameters"]
        self.assertEqual([parameters["frames"][rule["target"]]["node"]
                          for rule in parameters["constraints"]], ["Twist", "Twist", "OtherTwist"])
        self.assertEqual(parameters["constraints"][1]["sources"], [])

    def test_disabled_and_inactive_controls_are_retained(self):
        transforms, constraint, exported = fixture()
        root = transforms[0].m_GameObject.value
        constraint.m_Enabled = 0
        constraint.m_Active = False
        rule = extract_transform_constraint_behavior(root, exported)[0]["parameters"]["constraints"][0]
        self.assertFalse(rule["enabled"])
        self.assertFalse(rule["active"])
        constraint.m_Enabled = 1
        transforms[1].m_GameObject.value.m_IsActive = False
        rule = extract_transform_constraint_behavior(root, exported)[0]["parameters"]["constraints"][0]
        self.assertFalse(rule["enabled"])

    def test_duplicate_auxiliary_names_are_resolved_without_changing_core_name(self):
        transforms, _, exported = fixture()
        exported.builder.document["nodes"][4]["name"] = "Twist"
        root = transforms[0].m_GameObject.value
        parameters = extract_transform_constraint_behavior(root, exported)[0]["parameters"]
        name = parameters["frames"][parameters["constraints"][0]["target"]]["node"]
        self.assertEqual(name, "Twist__TransformConstraint_3")
        self.assertEqual(exported.builder.document["nodes"][4]["name"], "Twist")
        self.assertEqual(extract_transform_constraint_behavior(root, exported)[0]["parameters"], parameters)

    def test_no_constraints_does_not_require_mapping(self):
        transforms, _, _ = fixture()
        transforms[3].m_GameObject.value.m_Component.pop()
        self.assertEqual(extract_transform_constraint_behavior(transforms[0].m_GameObject.value, object()), [])

    def test_model_conversion_includes_constraints_in_the_body_component(self):
        transforms, _, exported = fixture()
        exported.human_scale = 1.
        exported.builder.write = lambda path: Path(path).write_bytes(b"glb")
        bundle = bangdream.BundleAssets(Path("costume/package"), NS(),
                                        transforms[0].m_GameObject.value, kind="body")
        with tempfile.TemporaryDirectory() as temporary, \
                patch.object(bangdream, "_package_name", return_value="package"), \
                patch.object(bangdream, "_load_normalized", return_value={}), \
                patch.object(bangdream, "export_glb", return_value=exported), \
                patch.object(bangdream, "extract_model_physics", return_value=None):
            name, component = bangdream.convert_one(
                bundle.path, Path(temporary), loaded_bundle=bundle, expected_role="body")
        self.assertEqual(name, "package")
        self.assertEqual(component["behaviors"][0]["name"], "Garupa.TransformConstraint")
        self.assertEqual(component["behaviors"][0]["parameters"]["constraints"][0]["weight"], .7)

    def test_nonfinite_values_fail_the_current_numeric_contract(self):
        transforms, constraint, exported = fixture()
        constraint.m_RotationOffset.x = float("nan")
        with self.assertRaisesRegex(ValueError, "finite numeric"):
            extract_transform_constraint_behavior(transforms[0].m_GameObject.value, exported)

    def test_exports_position_rest_offset_axes_and_inactive_state(self):
        transforms, rotation, exported = fixture()
        position = NS(
            m_Enabled=1, m_Active=False, m_Weight=.25, m_Sources=rotation.m_Sources,
            m_TranslationAtRest=NS(x=.01, y=.02, z=-.03),
            m_TranslationOffset=NS(x=.04, y=-.05, z=.06),
            m_AffectTranslationX=False, m_AffectTranslationY=True, m_AffectTranslationZ=False,
        )
        transforms[4].m_GameObject.value.m_Component.append((181, Pointer(position, "PositionConstraint")))
        behavior, = extract_transform_constraint_behavior(transforms[0].m_GameObject.value, exported)
        result = behavior["parameters"]["constraints"][1]
        self.assertEqual(result["type"], "position")
        self.assertEqual(result["translationAtRest"], [.01, .02, -.03])
        self.assertEqual(result["translationOffset"], [.04, -.05, .06])
        self.assertEqual(result["axes"], [False, True, False])
        self.assertFalse(result["active"])
        self.assertEqual(result["weight"], .25)
        self.assertEqual([s["weight"] for s in result["sources"]], [.2, .6, .8])

    def test_parent_preserves_each_indexed_offset_and_both_axis_masks(self):
        transforms, rotation, exported = fixture()
        parent = NS(
            m_Enabled=1, m_Active=True, m_Weight=.6, m_Sources=rotation.m_Sources,
            m_TranslationAtRest=NS(x=.1, y=.2, z=.3),
            m_RotationAtRest=NS(x=11., y=-29., z=53.),
            m_TranslationOffsets=[NS(x=.01+i, y=-.02-i, z=.03+i) for i in range(3)],
            m_RotationOffsets=[NS(x=10.+i, y=-20.-i, z=30.+i) for i in range(3)],
            m_AffectTranslationX=True, m_AffectTranslationY=False, m_AffectTranslationZ=True,
            m_AffectRotationX=False, m_AffectRotationY=True, m_AffectRotationZ=True,
        )
        transforms[3].m_GameObject.value.m_Component.append((181, Pointer(parent, "ParentConstraint")))
        parameters = extract_transform_constraint_behavior(transforms[0].m_GameObject.value, exported)[0]["parameters"]
        result = parameters["constraints"][1]
        self.assertEqual(result["type"], "parent")
        self.assertEqual(result["translationAtRest"], [.1, .2, .3])
        self.assertEqual(result["rotationAtRest"], [11., -29., 53.])
        self.assertEqual(result["translationOffsets"], [[.01+i, -.02-i, .03+i] for i in range(3)])
        self.assertEqual(result["rotationOffsets"], [[10.+i, -20.-i, 30.+i] for i in range(3)])
        self.assertEqual(result["translationAxes"], [True, False, True])
        self.assertEqual(result["rotationAxes"], [False, True, True])
        self.assertIsNone(result["sources"][1]["frame"])

    def test_mixed_native_components_retain_game_object_component_order(self):
        transforms, rotation, exported = fixture()
        go = transforms[3].m_GameObject.value
        parent = NS(**vars(rotation),
                    m_TranslationAtRest=NS(x=0.,y=0.,z=0.),
                    m_TranslationOffsets=[],m_RotationOffsets=[],
                    m_AffectTranslationX=True,m_AffectTranslationY=True,m_AffectTranslationZ=True)
        parent.m_Sources = []
        go.m_Component.insert(1, (181, Pointer(parent, "ParentConstraint")))
        result = extract_transform_constraint_behavior(transforms[0].m_GameObject.value, exported)[0]["parameters"]
        self.assertEqual([rule["type"] for rule in result["constraints"]], ["parent", "rotation"])


if __name__ == "__main__":
    unittest.main()
