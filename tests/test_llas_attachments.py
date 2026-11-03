import unittest
import tempfile
import json
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch

from converter.common.unity import object_id
from converter.llas.attachments import AttachmentMaterialAdapter, MemberAttachment, member_attachments
from converter.llas.materials import MEMBER_SHADER


def identity(value):
    value.object_reader = NS(assets_file=object(), path_id=1)
    return value


class Pointer:
    def __init__(self, value, kind='Material'):
        self.value = value
        self.type = NS(name=kind)
        self.m_FileID = 0
        self.m_PathID = 1

    def read(self):
        return self.value

    def deref_parse_as_object(self):
        return self.value


def material(name, texture=None, tint=1):
    return identity(NS(m_Name=name, m_Shader=NS(m_PathID=MEMBER_SHADER),
        m_ShaderKeywords='_RIMLIGHT_ON _MATCAP_ON',
        m_SavedProperties=NS(m_Floats=[('_RIMLIGHT', 1), ('_RimglightIntensity', 1)],
            m_Colors=[('_Tint', tint)], m_TexEnvs=[('_MainTex', NS(m_Texture=texture,
                m_Scale=NS(x=2, y=3), m_Offset=NS(x=.2, y=.3)))])))


def face(renderers):
    components = [Pointer(renderer, 'SkinnedMeshRenderer') for renderer in renderers]
    go = NS(m_Name='root', m_Component=[])
    transform = identity(NS(m_GameObject=Pointer(go, 'GameObject'), m_Children=[]))
    go.m_Component = [(0, Pointer(transform, 'Transform'))] + [(0, p) for p in components]
    return NS(root=Pointer(go, 'GameObject'), head_all=transform,
              head_material=renderers[0].m_Materials[0])


class LlasAttachmentTests(unittest.TestCase):
    def test_selected_source_exports_declared_variants_and_indexes_packages(self):
        from converter.llas import convert_all
        from converter.llas.metadata import ModelDescriptions
        from converter.llas.source_inventory import SourceInventory
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / 'pack__9.unity3d'
            inventory = SourceInventory((source,), (), {source: 'member'}, {}, {}, {})
            descriptions = ModelDescriptions({('pack', 9): 'Original'}, {('pack', 9, 'blue'): 'Blue'})
            def export(source, output, baked, description, input_root, **kwargs):
                if 'discovered_attachments' in kwargs:
                    kwargs['discovered_attachments'].append(MemberAttachment('blue', 1, ()))
                name = 'member' + ('_' + kwargs['attachment'].key if 'attachment' in kwargs else '')
                directory = output / name
                directory.mkdir()
                component = {'type': 'model', 'name': name, 'description': description}
                (directory / 'config.json').write_text(json.dumps({'components': [component]}), encoding='utf8')
                return component
            with patch('converter.llas.active_sources', return_value=inventory), \
                 patch('converter.llas.inspect_model', return_value='member'), \
                 patch('converter.llas.model_descriptions', return_value=descriptions), \
                 patch('converter.llas.convert_model', side_effect=export), \
                 patch('converter.llas.package_all_motions', return_value=[]):
                models, _ = convert_all(root, root / 'output', root / 'baked', model_names=['member'])
            self.assertEqual([(row['name'], row['description']) for row in models],
                             [('member', 'Original'), ('member_blue', 'Blue')])
            self.assertEqual(json.loads((root / 'output/index.json').read_text())['configs'],
                             ['member/config.json', 'member_blue/config.json'])

    def test_texture_replacement_uses_first_slot_and_first_material_with_name(self):
        old_texture = Pointer(NS(m_Name='original'), 'Texture2D')
        replacement = Pointer(NS(m_Name='alternate'), 'Texture2D')
        first = material('costume', old_texture, 1)
        same_name = material('costume', old_texture, .5)
        untouched = material('second_slot', old_texture)
        a = identity(NS(m_Materials=[Pointer(first), Pointer(untouched)]))
        b = identity(NS(m_Materials=[Pointer(same_name)]))
        source_face = face([a, b])
        source_face.root.read().m_IsActive = False
        adapter = AttachmentMaterialAdapter(source_face, False,
            MemberAttachment('c7', 1, (('costume', replacement),)))
        adapted_a = adapter.adapt_renderer(a)
        adapted_b = adapter.adapt_renderer(b)
        clone = adapted_a.m_Materials[0].read()
        self.assertIs(adapted_a.m_Materials[0], adapted_b.m_Materials[0])
        self.assertEqual(clone.m_SavedProperties.m_Colors, [('_Tint', 1)])
        self.assertIs(adapted_a.m_Materials[1], a.m_Materials[1])
        env = dict(clone.m_SavedProperties.m_TexEnvs)['_MainTex']
        self.assertIs(env.m_Texture, replacement)
        self.assertEqual((env.m_Scale.x, env.m_Scale.y, env.m_Offset.x), (2, 3, .2))
        self.assertEqual(dict(clone.m_SavedProperties.m_Floats)['_RIMLIGHT'], 0)
        self.assertEqual(dict(clone.m_SavedProperties.m_Floats)['_RimglightIntensity'], 0)
        self.assertNotIn('_RIMLIGHT_ON', clone.m_ShaderKeywords.split())
        self.assertIn('_MATCAP_ON', clone.m_ShaderKeywords.split())
        self.assertIs(dict(first.m_SavedProperties.m_TexEnvs)['_MainTex'].m_Texture, old_texture)
        self.assertEqual(dict(first.m_SavedProperties.m_Floats)['_RIMLIGHT'], 1)
        self.assertIn(object_id(clone), adapter.material_sources)

    def test_shared_grafted_head_receives_same_replacement(self):
        source = material('head')
        renderer = identity(NS(m_Materials=[Pointer(source)]))
        replacement = Pointer(NS(), 'Texture2D')
        adapter = AttachmentMaterialAdapter(face([renderer]), True,
            MemberAttachment('blue', 1, (('head', replacement),)))
        self.assertIs(adapter.adapt_renderer(renderer).m_Materials[0], adapter.head_material)

    def test_missing_binding_and_non_material_color_type_follow_native_noop(self):
        renderer = identity(NS(m_Materials=[Pointer(material('body'))]))
        for attachment in (MemberAttachment('x', 0, ()), MemberAttachment('x', 1, (('other', Pointer(NS(), 'Texture2D')),))):
            adapter = AttachmentMaterialAdapter(face([renderer]), False, attachment)
            self.assertIs(adapter.adapt_renderer(renderer).m_Materials[0], renderer.m_Materials[0])

    def test_material_branch_reports_unrestored_runtime_state(self):
        renderer = identity(NS(m_Materials=[Pointer(material('body'))]))
        with self.assertRaisesRegex(NotImplementedError, 'runtime ambient'):
            AttachmentMaterialAdapter(face([renderer]), False,
                MemberAttachment('x', 1, (('body', Pointer(material('other'))),)))

    def test_null_and_wrong_object_types_match_native_dereference_and_cast_constraints(self):
        renderer = identity(NS(m_Materials=[Pointer(material('body'))]))
        null = Pointer(None)
        null.m_PathID = 0
        with self.assertRaisesRegex(ValueError, 'replaceObject is null'):
            AttachmentMaterialAdapter(face([renderer]), False, MemberAttachment('x', 1, (('body', null),)))
        with self.assertRaisesRegex(TypeError, 'Texture2D or Material'):
            AttachmentMaterialAdapter(face([renderer]), False,
                MemberAttachment('x', 1, (('body', Pointer(NS(), 'Mesh')),)))

    def test_table_uses_declared_external_cab_and_first_duplicate_entry(self):
        table = NS(read_typetree=lambda: {'datas': [
            {'attachName': 'c9', 'attachType': 1, 'replaceObjects': []},
            {'attachName': 'c9', 'attachType': 0, 'replaceObjects': []},
            {'attachName': 'red', 'attachType': 1, 'replaceObjects': []},
        ]})
        table_pointer = NS(m_FileID=3, deref=lambda: table)
        reader = NS(read_typetree=lambda: {'attachTable': {'m_FileID': 3, 'm_PathID': 91}})
        source = NS(manager=NS(object_reader=reader), environment=object(), cab_paths={'cab': ()})
        with patch('converter.llas.attachments._pointer', return_value=table_pointer), \
             patch('converter.llas.attachments._load_dependency') as load:
            rows = member_attachments(source, 'source')
        self.assertEqual([(row.key, row.kind) for row in rows], [('c9', 1), ('red', 1)])
        self.assertEqual(load.call_args.kwargs['resource'], 'attachment')

