"""Synthetic Yohane export fixtures; no game input or research files required."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch

from converter.yohane import convert, model_description, prepare_prefab
from converter.yohane.face import export_face
from converter.yohane.model_adapter import YohaneModelAdapter, renderer_is_active
from converter.yohane.motion import default_action, export_motions
from converter.yohane.physics import decode_child_weights, extract_physics, saved_render_pairs
from converter.common.normalized_model import NormalizedNodeMapping, renderer_node_name


def body_fixture():
    transition = {'data': {'m_ConditionConstantArray': [], 'm_HasExitTime': True,
        'm_HasFixedDuration': True, 'm_DestinationState': 1, 'm_ExitTime': 1,
        'm_TransitionDuration': .1, 'm_TransitionOffset': 0}}
    states = []
    for index in range(2):
        states.append({'data': {'m_NameID': index + 2, 'm_Mirror': False,
            'm_CycleOffset': 0, 'm_Speed': 1, 'm_Loop': bool(index),
            'm_BlendTreeConstantArray': [{'data': {'m_NodeArray': [
                {'data': {'m_ChildIndices': [], 'm_ClipID': index}}]}}],
            'm_TransitionConstantArray': [transition] if index == 0 else []}})
    tree = {'m_TOS': [(1, 'Base Layer'), (2, 'entry'), (3, 'loop')], 'm_Controller': {
        'm_LayerArray': [{'data': {'m_Binding': 1, 'm_StateMachineIndex': 0}}],
        'm_StateMachineArray': [{'data': {'m_DefaultState': 0, 'm_StateConstantArray': states}}]}}
    clips = ['ch_angry_enter', 'ch_angry_01']
    controller = NS(read_typetree=lambda: tree, peek_name=lambda: 'CH_test_story',
                    read=lambda: NS(m_AnimationClips=[NS(read=lambda name=name: NS(m_Name=name)) for name in clips]))
    baked = {'schemaVersion': 8, 'sourceBundle': 'internal.bundle', 'clips': [
        {'name': name, 'duration': 1, 'sampleRate': 1, 'frames': 2,
         'tracks': [{'bone': 'Hips', 'rotation': [0, 0, 0, 1] * 2, 'translation': []}],
         'groupTracks': []} for name in clips]}
    return controller, baked, tree


class YohaneExportTests(unittest.TestCase):
    def test_story_entry_and_loop_remain_one_action(self):
        controller, baked, _ = body_fixture()
        original = copy.deepcopy(baked)
        actions = export_motions(controller, baked, '夜羽')
        self.assertEqual(list(actions), ['ch_angry_01'])
        action = actions['ch_angry_01']
        self.assertEqual(action['description'], '夜羽 生气')
        self.assertEqual([clip['id'] for clip in action['clips']], ['ch_angry_enter', 'ch_angry_01'])
        layer = action['program']['layers'][0]
        self.assertEqual(layer['initialState'], 'entry')
        self.assertEqual(layer['states'][0]['transitions'][0]['to'], 'loop')
        self.assertTrue(layer['states'][1]['loop'])
        self.assertNotIn('sourceBundle', action)
        self.assertNotIn('translation', action['clips'][0]['tracks'][0])
        self.assertEqual(baked, original)

    def test_missing_bake_and_unsupported_source_are_explicit(self):
        controller, baked, tree = body_fixture()
        baked['clips'].pop()
        with self.assertRaisesRegex(ValueError, 'missing baked body clip'):
            export_motions(controller, baked)
        controller, baked, tree = body_fixture()
        tree['m_Controller']['m_StateMachineArray'][0]['data']['m_StateConstantArray'][0]['data']['m_Mirror'] = True
        with self.assertRaisesRegex(ValueError, 'unsupported Base Layer'):
            export_motions(controller, baked)

    def test_empty_input_preserves_previous_outputs(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            output = root / 'output' / 'yohane'
            output.mkdir(parents=True)
            marker = output / 'keep.txt'
            marker.write_text('keep', encoding='utf-8')
            convert(root / 'input', root / 'output', root / 'baked', clean=True)
            self.assertTrue(marker.is_file())

    def test_models_only_does_not_require_complete_body_bake(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = NS(name='CH_yohane_normal01', controller_name='CH_yohane_normal01_story')
            baked = root / 'baked' / 'yohane' / source.name
            baked.mkdir(parents=True)
            (baked / 'skeleton.json').write_text('{}', encoding='utf-8')
            (baked / 'face_samples.json').write_text('{}', encoding='utf-8')
            exported = NS(builder=NS(document={}, write=lambda destination: destination.write_bytes(b'glb')),
                          human_scale=1)
            with patch('converter.yohane.discover_models', return_value=[source]), \
                    patch('converter.yohane.load_environment'), patch('converter.yohane.find_controller'), \
                    patch('converter.yohane.find_prefab'), patch('converter.yohane.prepare_prefab'), \
                    patch('converter.yohane.export_normalized_model', return_value=exported), \
                    patch('converter.yohane.export_face', return_value={}), \
                    patch('converter.yohane.default_action', return_value=('ch_idle_01', 'ch_idle_01')), \
                    patch('converter.yohane.extract_physics', return_value=None), \
                    patch('converter.yohane.export_motions') as motions:
                convert(root / 'input', root / 'output', root / 'baked', models_only=True)
            motions.assert_not_called()
            self.assertTrue((root / 'output' / 'yohane' / source.name / 'config.json').is_file())

    def test_motions_only_uses_one_bake_for_shared_controller(self):
        controller, body, _ = body_fixture()
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            sources = [NS(name=f'CH_yohane_variant{index}', controller_name='CH_test_story') for index in range(2)]
            baked = root / 'baked' / 'yohane' / sources[0].name
            baked.mkdir(parents=True)
            (baked / 'body_baked.json').write_text(json.dumps(body), encoding='utf-8')
            with patch('converter.yohane.discover_models', return_value=sources), \
                    patch('converter.yohane.load_environment') as load, \
                    patch('converter.yohane.find_controller', return_value=controller):
                convert(root / 'input', root / 'output', root / 'baked', motions_only=True)
            self.assertEqual(load.call_count, 1)
            self.assertTrue((root / 'output' / 'motion' / 'yohane' / 'CH_test_story' / 'ch_angry_01.motionbin').is_file())

    def test_face_special_mouth_is_a_closed_base_and_speech_withdrawal(self):
        targets = ['normal', 'happy', 'eye_close', 'mouth_open', 'happy_mouth_open']
        def sample(face, weights):
            return {'face': face, 'eye': 'f_normal', 'mouth': 'f_normal', 'time': 0,
                    'meshes': [{'node': 'Face', 'targets': targets, 'weights': weights}]}
        data = {'controller': 'CH_test_story', 'poses': [sample('f_normal', [100, 0, 0, 0, 0]),
            sample('f_happy', [0, 100, 0, 0, 0])], 'isolatedClips': [
                sample('f_eye_close', [0, 0, 100, 0, 0]),
                sample('f_mouth_open', [0, 0, 0, 100, 0]),
                sample('f_happy_mouth_open', [0, 0, 0, 0, 100])]}
        controls = {'f_normal': {'blink': 'f_eye_close', 'speech': 'f_mouth_open'},
                    'f_happy': {'blink': 'f_normal', 'speech': 'f_happy_mouth_open'}}
        with tempfile.TemporaryDirectory() as folder:
            file = Path(folder) / 'face_samples.json'
            file.write_text(json.dumps(data), encoding='utf-8')
            with patch('converter.yohane.face.controller_controls', return_value=controls):
                result = export_face(file, object())
        normal, happy = result['expressionGroups'][0]['states']
        self.assertEqual(normal['controls'], {'blink': {'eye.close': 1}, 'speech': {'mouth.mouth_open': 1}})
        self.assertEqual(happy['poses'], {'face.happy': 1, 'mouth.happy_mouth_open': 1})
        self.assertEqual(happy['controls'], {'speech': {'mouth.happy_mouth_open': 0}})

    def test_original_child_weight_mapping_is_preserved(self):
        weight = {'parentIndex': 1, 'weight': .75, 'localPos': [1, 2, 3]}
        self.assertEqual(decode_child_weights({'vertexInfoList': [1 << 28],
            'vertexWeightList': [weight]}, 2), [[weight]])
        with self.assertRaisesRegex(ValueError, 'missing proxy vertex'):
            decode_child_weights({'vertexInfoList': [1 << 28], 'vertexWeightList': [weight]}, 1)

    def test_saved_render_child_pairing_uses_original_array_order_not_hashes(self):
        children = [{'childDataHash': 2073616629}, {'childDataHash': -1885373735}]
        renderers = [NS(dataHash=-602236661), NS(dataHash=-266259729)]
        pairs = saved_render_pairs({'childDataList': children}, renderers)
        self.assertEqual(pairs, [(renderers[0], children[0]), (renderers[1], children[1])])
        with self.assertRaisesRegex(ValueError, 'same index'):
            saved_render_pairs({'childDataList': children}, renderers[:1])

    def test_material_adapter_has_explicit_builder_binding(self):
        adapter = YohaneModelAdapter()
        builder = NS(document={}, add_image=lambda texture: 3)
        adapter.bind_builder(builder)
        texture = NS(m_Texture=NS(read=lambda: object()))
        material = NS(m_SavedProperties=NS(m_TexEnvs=[('_BaseMap', texture)]))
        result = {'pbrMetallicRoughness': {}}
        adapter.adapt_material(material, result)
        self.assertEqual(result['pbrMetallicRoughness']['baseColorTexture'], {'index': 3})
        self.assertEqual(builder.document['extensionsUsed'], ['KHR_materials_unlit'])

    def test_inactive_static_accessories_are_omitted(self):
        self.assertFalse(renderer_is_active(NS(m_Enabled=False)))

    def test_description_only_uses_known_source_names(self):
        self.assertEqual(model_description('CH_ruby_fairy01'), '露比 妖精服')
        self.assertEqual(model_description('CH_ruby_fairy01_inv'), '露比 妖精服')
        self.assertEqual(model_description('CH_unknown_normal01'), '')

    def test_default_action_is_controller_default_not_a_clip_name_guess(self):
        controller, _, _ = body_fixture()
        self.assertEqual(default_action(controller), ('ch_angry_01', 'ch_angry_enter'))

    def test_empty_editor_state_preserves_source_transition_indices(self):
        controller, baked, tree = body_fixture()
        machine = tree['m_Controller']['m_StateMachineArray'][0]['data']
        machine['m_StateConstantArray'].insert(1, {'data': {
            'm_BlendTreeConstantArray': [], 'm_TransitionConstantArray': []}})
        machine['m_StateConstantArray'][0]['data']['m_TransitionConstantArray'][0]['data']['m_DestinationState'] = 2
        actions = export_motions(controller, baked)
        states = actions['ch_angry_01']['program']['layers'][0]['states']
        self.assertEqual([state['id'] for state in states], ['entry', 'loop'])
        self.assertEqual(states[0]['transitions'][0]['to'], 'loop')

    def test_model_without_morphs_has_no_expression_requirement(self):
        data = {'poses': [{'meshes': [{'node': 'body', 'targets': [], 'weights': []}]}]}
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'samples.json'
            path.write_text(json.dumps(data), encoding='utf-8')
            result = export_face(path, object())
        self.assertEqual(result, {'morphPoses': [], 'expressionGroups': [], 'defaultExpression': {}})

    def test_partial_morph_model_ignores_missing_eye_and_mouth_bindings(self):
        sample = {'face': 'f_normal', 'eye': 'f_normal', 'mouth': 'f_normal', 'time': 0,
                  'meshes': [{'node': 'Face', 'targets': ['normal'], 'weights': [100]}]}
        data = {'poses': [sample], 'isolatedClips': [], 'controller': 'unused'}
        controls = {'f_normal': {'blink': 'f_eye_close', 'speech': 'f_mouth_open'}}
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'samples.json'
            path.write_text(json.dumps(data), encoding='utf-8')
            with patch('converter.yohane.face.controller_controls', return_value=controls):
                result = export_face(path, object())
        self.assertEqual(result['expressionGroups'][0]['states'], [{'name': 'normal', 'poses': {'face.normal': 1}}])

    def test_mesh_cloth_submeshes_and_unsupported_regions_do_not_reject_model(self):
        identity = [1., 0., 0., 0., 0., 1., 0., 0., 0., 0., 1., 0., 0., 0., 0., 1.]
        mapping = NormalizedNodeMapping({}, [identity], [identity], [identity], {})
        document = {'nodes': [{'name': renderer_node_name('skirt'), 'mesh': 0}],
                    'meshes': [{'name': 'skirt', 'primitives': [{'attributes': {'POSITION': 0}},
                                                              {'attributes': {'POSITION': 0}}]}],
                    'accessors': [{'count': 3}]}
        region = {'mesh': NS(m_Name='skirt'), 'fixed': [0], 'influences': [[], [], []],
                  'component': NS(clothParams=NS(useCollision=False)),
                  'renderComponent': NS(m_GameObject=NS(read=lambda: object()))}
        exported = NS(builder=NS(document=document), node_mapping=mapping)
        with patch('converter.yohane.physics.extract_model_physics', side_effect=lambda *args: {'springs': [{'keep': True}], 'colliders': []}), \
                patch('converter.yohane.physics.mesh_cloth_regions', return_value=[region]), \
                patch('converter.yohane.physics.object_id', side_effect=id), \
                patch.object(NormalizedNodeMapping, 'radius', return_value=.003), \
                patch('converter.yohane.physics.game_object_transform', return_value=object()):
            result = extract_physics(object(), exported)
            self.assertNotIn('cloths', result)
            document['meshes'][0]['primitives'].pop()
            result = extract_physics(object(), exported)
            self.assertEqual([cloth['primitive'] for cloth in result['cloths']], [0])
            region['fixed'] = []
            with patch('converter.yohane.physics.unsupported_cloth') as warning:
                result = extract_physics(object(), exported)
            warning.assert_called_once()
            self.assertEqual(result['springs'], [{'keep': True}])
            self.assertNotIn('cloths', result)


if __name__ == '__main__':
    unittest.main()
