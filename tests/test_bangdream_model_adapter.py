import unittest
from types import SimpleNamespace
from unittest.mock import patch

from converter.bangdream.model_adapter import BangDreamModelAdapter
from converter.bangdream.meteor_material_mapping import MaterialControllerContext


class Pointer:
    def __init__(self, target=None, *, path_id=1):
        self.target = target
        self.m_PathID = path_id
        self.assetsfile = object()

    def __bool__(self):
        return self.m_PathID != 0

    def deref_parse_as_object(self):
        if not self:
            raise AssertionError("empty Unity pointer must not be dereferenced")
        return self.target


def material(name, *, textured):
    texture = Pointer(object(), path_id=1 if textured else 0)
    return SimpleNamespace(
        m_Name=name,
        m_SavedProperties=SimpleNamespace(
            m_TexEnvs=[("_MainTex", SimpleNamespace(m_Texture=texture))]
        ),
    )


class BangDreamModelAdapterTests(unittest.TestCase):
    def test_constructor_ignores_empty_unity_material_pointer(self):
        renderer = SimpleNamespace(
            m_Mesh=Pointer(object()),
            m_Materials=[Pointer(path_id=0)],
        )
        reader = SimpleNamespace(
            type=SimpleNamespace(name="SkinnedMeshRenderer"),
            read=lambda: renderer,
        )

        adapter = BangDreamModelAdapter(SimpleNamespace(objects=[reader]))

        self.assertEqual(adapter.material_mapping.mapping, {})
        self.assertEqual(adapter.material_mapping.selection_status, "absent")

    def test_adaptation_preserves_empty_material_slot_without_dereferencing_it(self):
        mesh = Pointer(object())
        textured_pointer = Pointer(material("Face_01", textured=True))
        adapter = BangDreamModelAdapter(SimpleNamespace(objects=[]))
        # SetupColor supplies the exact source Material name as its key. Mesh
        # identity and the target material's suffix do not participate.
        adapter.material_mapping.mapping["Face"] = textured_pointer
        empty_pointer = Pointer(path_id=0)
        renderer = SimpleNamespace(
            m_Mesh=mesh,
            m_Materials=[empty_pointer, Pointer(material("Face", textured=False))],
        )

        with patch.object(adapter.material_mapping, "context_for_renderer", return_value=MaterialControllerContext((1, 1), False)):
            adapted = adapter.adapt_renderer(renderer)

        self.assertIs(adapted.m_Materials[0], empty_pointer)
        self.assertIs(adapted.m_Materials[1].source_pointer, textured_pointer)
        self.assertEqual(renderer.m_Materials[1].deref_parse_as_object().m_Name, "Face")
        self.assertIs(adapted.source_renderer, renderer)

    def test_menu_layer_uses_first_selected_material_without_mutating_game_object(self):
        game_object = SimpleNamespace(m_Layer=24)
        renderer = SimpleNamespace(
            m_Materials=[Pointer(material("HairOffset", textured=True))],
            m_GameObject=Pointer(game_object),
        )
        adapted = BangDreamModelAdapter(SimpleNamespace(objects=[])).adapt_renderer(renderer)
        self.assertEqual(adapted.original_layer, 24)
        self.assertEqual(adapted.initialized_layer, 29)
        self.assertEqual(game_object.m_Layer, 24)


if __name__ == "__main__":
    unittest.main()
