import unittest
from types import SimpleNamespace as NS
from unittest.mock import patch

from converter.bangdream.model_adapter import BangDreamModelAdapter
from converter.bangdream.meteor_material_mapping import initialized_menu_layer, classify_setup_material, MaterialControllerContext
from converter.common.unity import object_id


class Pointer:
    def __init__(self, *, m_FileID=0, m_PathID=0, assetsfile=None):
        self.m_FileID, self.m_PathID, self.assetsfile = m_FileID, m_PathID, assetsfile

    def __bool__(self):
        return self.m_PathID != 0

    def deref_parse_as_object(self):
        if not self:
            raise AssertionError("Null pointer dereferenced")
        return self.assetsfile[self.m_PathID]


def fixture(mapping=None, *, variation_name="Color_test_01", with_controller=True):
    objects = {1: NS(m_Name="Face", object_reader=NS(assets_file=None, path_id=1)),
               2: NS(m_Name="Face_01", keyword="selected", object_reader=NS(assets_file=None, path_id=2)),
               3: NS(m_Name="OtherOffset", object_reader=NS(assets_file=None, path_id=3)),
               4: NS(m_ClassName="ColorVariation"), 5: NS(m_Layer=22),
               7: NS(m_ClassName="MaterialController")}
    ptr = lambda i: Pointer(m_PathID=i, assetsfile=objects)
    readers = [NS(type=NS(name="AssetBundle"), read=lambda: NS(m_Name="star3d/character/head/test"))]
    if with_controller:
        readers.append(NS(type=NS(name="MonoBehaviour"), path_id=8, assets_file=objects,
                          read=lambda: NS(m_Script=ptr(7), m_GameObject=ptr(5))))
    if mapping is not None:
        tree = {"m_Name": variation_name, "mapping": [
            {"Name": name, "Material": {"m_FileID": 0, "m_PathID": target}} for name, target in mapping]}
        readers.append(NS(type=NS(name="MonoBehaviour"), path_id=6, assets_file=objects,
                          read=lambda: NS(m_Script=ptr(4)), read_typetree=lambda: tree))
    return NS(objects=readers), ptr


def renderer_view(ptr, **kwargs):
    kwargs.setdefault("m_GameObject", ptr(5))
    return NS(**kwargs)


class MaterialMappingTests(unittest.TestCase):
    def setUp(self):
        self.patch = patch("converter.bangdream.meteor_material_mapping.PPtr", Pointer)
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def test_exact_source_name_selects_entire_material_and_reuses_instance(self):
        env, ptr = fixture([("Face", 2)])
        adapter = BangDreamModelAdapter(env)
        source = renderer_view(ptr, m_Materials=[ptr(1), ptr(1)])
        result = adapter.adapt_renderer(source)
        self.assertEqual(result.m_Materials[0].deref_parse_as_object().keyword, "selected")
        self.assertIs(result.m_Materials[0], result.m_Materials[1])
        self.assertEqual(result.m_Materials[0].source_pointer.m_PathID, 2)
        self.assertEqual(source.m_Materials[0].m_PathID, 1)
        self.assertEqual(result.original_materials[0].m_PathID, 1)

    def test_different_source_names_do_not_share_clone_even_same_target(self):
        env, ptr = fixture([("Face", 2), ("OtherOffset", 2)])
        adapter = BangDreamModelAdapter(env)
        result = adapter.adapt_renderer(renderer_view(ptr, m_Materials=[ptr(1), ptr(3)]))
        self.assertNotEqual(object_id(result.m_Materials[0].deref_parse_as_object()),
                            object_id(result.m_Materials[1].deref_parse_as_object()))

    def test_absent_variation_and_unmapped_names_clone_original_without_false_mapping(self):
        for env, ptr in [fixture(), fixture([("Face_01", 2)])]:
            original = ptr(1)
            result = BangDreamModelAdapter(env).adapt_renderer(renderer_view(ptr, m_Materials=[original, ptr(0)]))
            self.assertIs(result.m_Materials[0].source_pointer, original)
            self.assertFalse(result.m_Materials[1])

    def test_color_type_selects_original_resource_name(self):
        env, ptr = fixture([("Face", 2)], variation_name="Color_test_02")
        self.assertEqual(BangDreamModelAdapter(env).material_mapping.selection_status, "absent")
        self.assertEqual(BangDreamModelAdapter(env, color_type=1).material_mapping.selection_status, "selected")

    def test_duplicate_mapping_and_null_target_are_rejected(self):
        env, ptr = fixture([("Face", 2), ("Face", 3)])
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            BangDreamModelAdapter(env)
        env, ptr = fixture([("Face", 0)])
        with self.assertRaisesRegex(ValueError, "null Material"):
            BangDreamModelAdapter(env).adapt_renderer(renderer_view(ptr, m_Materials=[ptr(1)]))

    def test_missing_controller_does_not_run_setup_even_with_color_variation(self):
        env, ptr = fixture([("Face", 2)], with_controller=False)
        source = ptr(1)
        result = BangDreamModelAdapter(env).adapt_renderer(renderer_view(ptr, m_Materials=[source]))
        self.assertIs(result.m_Materials[0], source)

    def test_classification_order_and_forced_specular_blend(self):
        for name, category, force in [
            ("CH_FACE_BASE", "face", True), ("eye_face_Base", "eyes", False),
            ("body_Base_NoOutline", "body", True), ("acce_Base", "body", True),
            ("hair_Base", "hair", False), ("body_Mask", "body", False),
            ("face_Transparent", None, False), ("face_Offset", "faceNoOutline", False),
            ("face_NoOutline", "faceNoOutline", False), ("other_Base_face", "face", True),
            ("other_Base_Offset", None, False),
        ]:
            state = classify_setup_material(name, controller_has_prop=False)
            self.assertEqual((state.category, state.force_specular_blend_7), (category, force))
            self.assertEqual(classify_setup_material(name, controller_has_prop=True).category, "prop")

    def test_private_clone_state_uses_original_name_and_first_classification(self):
        env, ptr = fixture([("Face", 2)])
        mapper = BangDreamModelAdapter(env).material_mapping
        ptr(1).deref_parse_as_object().m_Name = "face_Base"
        mapper.mapping["face_Base"] = ptr(3)  # selected target's name is OtherOffset
        context = MaterialControllerContext((1, 1), False)
        first = mapper.bind(ptr(1), category_context=context)
        again = mapper.bind(ptr(1), category_context=MaterialControllerContext((1, 1), True))
        self.assertIs(first, again)
        self.assertEqual(first.deref_parse_as_object()._meteor_setup.category, "face")
        self.assertTrue(first.deref_parse_as_object()._meteor_setup.force_specular_blend_7)

    def test_prop_context_is_controller_game_object_not_another_object(self):
        env, ptr = fixture([("Face", 2)])
        objects = ptr(5).assetsfile
        objects[9] = NS(m_Name="renderer_or_other_object")
        objects[10] = NS(m_ClassName="PropController")
        prop = NS(m_Script=ptr(10), m_GameObject=ptr(9))
        env.objects.append(NS(type=NS(name="MonoBehaviour"), read=lambda: prop))
        renderer = renderer_view(ptr, m_Materials=[ptr(1)])
        mapper = BangDreamModelAdapter(env).material_mapping
        self.assertFalse(mapper.context_for_renderer(renderer).controller_has_prop)
        prop.m_GameObject = ptr(5)
        mapper = BangDreamModelAdapter(env).material_mapping
        context = mapper.context_for_renderer(renderer)
        self.assertTrue(context.controller_has_prop)
        self.assertEqual(mapper.bind(ptr(1), category_context=context)._meteor_setup.category, "prop")

    def test_duplicate_controller_on_same_game_object_is_not_guessed(self):
        env, ptr = fixture()
        env.objects.append(NS(type=NS(name="MonoBehaviour"), path_id=9, assets_file=ptr(5).assetsfile,
                              read=lambda: NS(m_Script=ptr(7), m_GameObject=ptr(5))))
        with self.assertRaisesRegex(ValueError, "Multiple MaterialControllers"):
            BangDreamModelAdapter(env)

    def test_equivalent_duplicate_controllers_merge_without_native_order_assumption(self):
        env, ptr = fixture()
        tree = {"m_GameObject": {"m_FileID": 0, "m_PathID": 5}, "m_Enabled": 1,
                "_faceMaterials": [], "_bodyMaterials": []}
        env.objects[1].read_typetree = lambda: dict(tree)
        env.objects.append(NS(type=NS(name="MonoBehaviour"), path_id=9, assets_file=ptr(5).assetsfile,
                              read=lambda: NS(m_Script=ptr(7), m_GameObject=ptr(5)),
                              read_typetree=lambda: dict(tree)))
        mapper = BangDreamModelAdapter(env).material_mapping
        self.assertEqual(list(mapper._controller_equivalences.values()), [[8, 9]])
        self.assertIsNotNone(mapper.context_for_renderer(renderer_view(ptr, m_Materials=[])))

    def test_menu_layer_uses_only_first_actual_material_and_keeps_source(self):
        env, ptr = fixture([("Face", 3)])
        adapter = BangDreamModelAdapter(env)
        result = adapter.adapt_renderer(NS(m_Materials=[ptr(1)], m_GameObject=ptr(5)))
        self.assertEqual((result.original_layer, result.initialized_layer), (22, 27))
        self.assertEqual(ptr(5).deref_parse_as_object().m_Layer, 22)
        result = adapter.adapt_renderer(NS(m_Materials=[ptr(2), ptr(3)], m_GameObject=ptr(5)))
        self.assertEqual(result.initialized_layer, 22)
        for layer in [0, 19, 20, 24, 25, 31]:
            self.assertEqual(initialized_menu_layer(layer, "Offset"), layer + 5 if 20 <= layer <= 24 else layer)
            self.assertEqual(initialized_menu_layer(layer, "offset"), layer)

    def test_export_hook_emits_only_effective_layer_and_preserves_other_extras(self):
        env, ptr = fixture([("Face", 3)])
        adapter = BangDreamModelAdapter(env)
        renderer = adapter.adapt_renderer(NS(m_Materials=[ptr(1)], m_GameObject=ptr(5)))
        builder = NS(document={"nodes": [{"extras": {"existing": True}}]})
        adapter.adapt_exported_renderer(renderer, 0, builder)
        self.assertEqual(builder.document["nodes"][0]["extras"], {"existing": True, "meteorLayer": 27})

    def test_export_filter_respects_disabled_renderer_and_inactive_ancestor(self):
        env, ptr = fixture()
        adapter = BangDreamModelAdapter(env)
        self.assertFalse(adapter.should_export_renderer(NS(m_Enabled=False)))
        parent = NS(m_IsActive=False, m_Component=[])
        parent_pointer = NS(deref_parse_as_object=lambda: parent)
        parent_transform = NS(m_GameObject=parent_pointer)
        father = NS(deref_parse_as_object=lambda: parent_transform)
        transform = NS(m_Father=father)
        transform_pointer = NS(type=NS(name="Transform"), deref_parse_as_object=lambda: transform)
        child = NS(m_IsActive=True, m_Component=[NS(component=transform_pointer)])
        renderer = NS(m_Enabled=True, m_GameObject=NS(deref_parse_as_object=lambda: child))
        self.assertFalse(adapter.should_export_renderer(renderer))
        parent.m_IsActive = True
        self.assertTrue(adapter.should_export_renderer(renderer))


if __name__ == "__main__":
    unittest.main()
