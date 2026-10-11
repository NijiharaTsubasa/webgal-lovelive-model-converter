import unittest
from types import SimpleNamespace as NS
from unittest.mock import patch

from converter.yohane.aura import export_aura_arc


class Pointer:
    def __init__(self, value, kind='GameObject'):
        self.value = value
        self.type = NS(name=kind)

    def read(self):
        return self.value


def fixture():
    transform = NS(m_LocalPosition=NS(x=0., y=1., z=0.),
                   m_LocalRotation=NS(x=0., y=0., z=0., w=1.),
                   m_LocalScale=NS(x=1., y=1., z=1.), m_Children=[])
    mesh = NS(m_VertexData=NS(m_VertexCount=3,
                             m_Channels=[NS(stream=0, offset=0, format=0, dimension=3)]))
    renderer = NS(m_Mesh=Pointer(mesh), m_GameObject=Pointer(NS(transform=transform)), m_RootBone=Pointer(transform))
    sheet = NS(**{'m_' + kind: NS(m_Array=[]) for kind in
                  ('Float', 'Vector2f', 'Vector3f', 'Vector4f', 'Uint', 'Int', 'Matrix4x4f', 'Bool', 'NamedObject')})
    sheet.m_Float.m_Array = [NS(m_Name='Amount', m_Overridden=True, m_Value=.3)]
    sheet.m_NamedObject.m_Array = [NS(m_Name='SkinnedMeshRenderer', m_Overridden=True, m_Value=Pointer(renderer))]
    effect = NS(m_Enabled=True, m_Asset=Pointer(NS(m_Name='AuraArc')), m_PropertySheet=sheet,
                m_InitialEventName='OnPlay', m_ResetSeedOnPlay=True, m_StartSeed=0)
    go = NS(m_IsActive=True, transform=transform,
            m_Component=[NS(component=Pointer(effect, 'VisualEffect'))])
    identity = [1., 0., 0., 0., 0., 1., 0., 0., 0., 0., 1., 0., 0., 0., 0., 1.]
    mapping = NS(node_index=lambda source: 0, _local_matrix=lambda source, node: identity)
    document = {'nodes': [{}, {'mesh': 0}], 'meshes': [{'primitives': [{'attributes': {'POSITION': 0}}]}],
                'accessors': [{'count': 3}], 'scenes': [{}]}
    exported = NS(node_mapping=mapping, builder=NS(document=document))
    return Pointer(go), exported, renderer, effect


class YohaneAuraTests(unittest.TestCase):
    def export(self, prefab, exported, renderer):
        with patch('converter.yohane.aura.object_id', side_effect=id), \
                patch('converter.yohane.aura.game_object_transform', side_effect=lambda go: go.transform):
            return export_aura_arc(prefab, exported, {id(renderer): 0})

    def test_retains_native_overrides_vertex_order_and_runtime_node_markers(self):
        prefab, exported, renderer, _ = fixture()
        rows = self.export(prefab, exported, renderer)
        self.assertEqual(rows[0]['overrides']['Amount'], {'type': 'Float', 'value': .3})
        self.assertEqual(rows[0]['source']['vertexCount'], 3)
        self.assertEqual(rows[0]['source']['skinRoot']['node'], 0)
        self.assertEqual(exported.builder.document['nodes'][0]['extras']['yohaneAuraSkinRootNode'], 0)
        self.assertEqual(exported.builder.document['nodes'][1]['extras']['yohaneAuraSourceNode'], 1)
        self.assertEqual(exported.builder.document['nodes'][0]['extras']['yohaneAuraArcNode'], 0)
        self.assertEqual(exported.builder.document['scenes'][0]['extras']['yohaneAuraArc'], rows)

    def test_inactive_or_disabled_effect_is_not_created(self):
        prefab, exported, renderer, effect = fixture()
        effect.m_Enabled = False
        self.assertEqual(self.export(prefab, exported, renderer), [])
        effect.m_Enabled = True
        prefab.value.m_IsActive = False
        self.assertEqual(self.export(prefab, exported, renderer), [])
        self.assertNotIn('extras', exported.builder.document['scenes'][0])

    def test_vertex_count_mismatch_fails_instead_of_silently_reindexing(self):
        prefab, exported, renderer, _ = fixture()
        exported.builder.document['accessors'][0]['count'] = 4
        with self.assertRaisesRegex(ValueError, 'vertex counts differ'):
            self.export(prefab, exported, renderer)

    def test_sampling_frame_uses_root_bone_instead_of_renderer_transform(self):
        prefab, exported, renderer, _ = fixture()
        root_bone = NS()
        renderer.m_RootBone = Pointer(root_bone)
        exported.builder.document['nodes'].append({})
        exported.node_mapping.node_index = lambda source: 2 if source is root_bone else 0
        source_frame = [0., 1., 0., 0., -1., 0., 0., 0., 0., 0., 1., 0., 0., 0., 0., 1.]
        calls = []
        def local_matrix(source, node):
            calls.append((source, node))
            return source_frame
        exported.node_mapping._local_matrix = local_matrix
        row = self.export(prefab, exported, renderer)[0]
        self.assertEqual(calls, [(root_bone, 2)])
        self.assertEqual(row['source']['skinRoot'], {'node': 2, 'toSourceFrame': source_frame})
        self.assertEqual(exported.builder.document['nodes'][2]['extras']['yohaneAuraSkinRootNode'], 2)


if __name__ == '__main__':
    unittest.main()
