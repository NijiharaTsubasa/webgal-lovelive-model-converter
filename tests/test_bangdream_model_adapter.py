import unittest
from types import SimpleNamespace

from converter.bangdream.model_adapter import BangDreamModelAdapter


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

        self.assertEqual(adapter.textured_materials_by_mesh, {})

    def test_adaptation_preserves_empty_material_slot_without_dereferencing_it(self):
        mesh = Pointer(object())
        textured_pointer = Pointer(material("Face_01", textured=True))
        adapter = BangDreamModelAdapter(SimpleNamespace(objects=[]))
        adapter.textured_materials_by_mesh[(id(mesh.assetsfile), mesh.m_PathID)] = [
            textured_pointer
        ]
        empty_pointer = Pointer(path_id=0)
        renderer = SimpleNamespace(
            m_Mesh=mesh,
            m_Materials=[empty_pointer, Pointer(material("Face", textured=False))],
        )

        adapted = adapter.adapt_renderer(renderer)

        self.assertIs(adapted.m_Materials[0], empty_pointer)
        self.assertIs(adapted.m_Materials[1], textured_pointer)


if __name__ == "__main__":
    unittest.main()
