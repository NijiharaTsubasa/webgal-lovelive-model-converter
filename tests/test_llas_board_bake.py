import copy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from converter.llas.board_bake import board_pose_path, _assemble_boards, bake_board_faces, _source_bindings
from converter.llas.board_controls import append_board_controls, SIGNAL_NODE


def fixture():
    sources, report = [], dict(defaults=[], clips=[])
    for domain, name in [('eye', 'Close'), ('mouth', 'A')]:
        sources.append(dict(domain=domain, name=f'{domain}/{name}', index=1,
                            clip_name=f'{domain}_001', bundle=Path('presets'),
                            source_visibility={domain+'_neutral': False}, bindings=[]))
        report['defaults'].append(dict(domain=domain, nodes=[dict(name=domain+'_neutral', visible=True)]))
        report['clips'].append(dict(domain=domain, index=1, name=f'{domain}_001', bundle='presets',
            poses=[dict(fraction=t, nodes=[dict(name=domain+'_neutral', visible=False)])
                   for t in [0, .25, .5, .75, 1]]))
    return sources, report


class BoardBakeTests(unittest.TestCase):
    def test_board_controls_expose_raw_signals_and_default_endpoints(self):
        sampled = {'domains': [
            {'name': domain, 'defaults': {domain + '_neutral': True}, 'entries': [
                {'name': domain + '/' + label, 'visibility': {domain + '_neutral': label == 'Open'}}
                for label in labels]}
            for domain, labels in [('eye', ['Open', 'Close', 'WinkL', 'CloseSmile']),
                                   ('mouth', ['N', 'Smile', 'A', 'Sad'])]]}
        builder = SimpleNamespace(document={
            'nodes': [{'name': 'Head'}, {'name': 'eye_neutral', 'mesh': 0},
                      {'name': 'mouth_neutral', 'mesh': 0}], 'meshes': [{}]},
            add_accessor=Mock(side_effect=[0, 1]))
        result = append_board_controls(builder, sampled)
        self.assertNotIn('expressions', result)
        self.assertEqual(result['defaultExpression'], {'eye': 'Open', 'closed': 'Smile', 'open': 'A'})
        self.assertEqual([g['type'] for g in result['expressionGroups']], ['eye', 'mouth'])
        eyes, mouths = [{s['name']: s for s in g['states']} for g in result['expressionGroups']]
        self.assertEqual(mouths['Sad'], {'name': 'Sad', 'poses': {'mouth/Sad': 1}})
        self.assertEqual(eyes['WinkL']['controls']['blink'], {'eye/WinkL': 0, 'eye/CloseSmile': 1})
        self.assertNotIn('controls', eyes['Close'])
        recipes = {p['name']: p['targets'] for p in result['morphPoses']}
        self.assertEqual(recipes['mouth/Sad'], {SIGNAL_NODE: {'mouth/Sad': 1}})
        self.assertEqual(result['behaviors'][0]['parameters']['domains'][1]['entries'][3]['morph'], 'mouth/Sad')

    def test_member_not_shared_face_keys_the_board_output(self):
        for name in ['ch9999_co0002_member', 'ch9999_co0069_member']:
            self.assertEqual(board_pose_path(SimpleNamespace(name=name), 'baked'),
                             Path(f'baked/boards/{name}.json'))
        for name in ['', '.', '..', '../bad', 'bad/name', 'bad\\name']:
            with self.assertRaises(ValueError):
                board_pose_path(SimpleNamespace(name=name), 'baked')

    def test_assembly_keeps_native_defaults_and_indices(self):
        sources, report = fixture()
        result = _assemble_boards(sources, report)
        self.assertEqual(result, dict(domains=[dict(name=d, defaults={d+'_neutral': True},
            entries=[dict(index=1, name=d+'/'+n, visibility={d+'_neutral': False})])
            for d, n in [('eye', 'Close'), ('mouth', 'A')]]))

    def test_missing_ambiguous_or_nonstatic_results_are_rejected(self):
        sources, good = fixture()
        variants = []
        report = copy.deepcopy(good); report['clips'].pop(); variants.append(report)
        report = copy.deepcopy(good); report['clips'].append(report['clips'][0]); variants.append(report)
        report = copy.deepcopy(good); report['clips'][0]['poses'].pop(); variants.append(report)
        report = copy.deepcopy(good); report['clips'][0]['poses'][2]['nodes'][0]['visible'] = True; variants.append(report)
        report = copy.deepcopy(good); report['clips'][0]['poses'][0]['nodes'][0]['name'] = 'missing'; variants.append(report)
        report = copy.deepcopy(good); report['clips'][0]['poses'][0]['nodes'][0]['visible'] = 1; variants.append(report)
        report = copy.deepcopy(good); report['error'] = 'Unexpected TRS'; variants.append(report)
        report = copy.deepcopy(good)
        for clip in report['clips']:
            for pose in clip['poses']:
                pose['nodes'][0]['visible'] = True
        variants.append(report)  # A non-binding graph must not pass as all defaults.
        for report in variants:
            with self.subTest(report=report), self.assertRaises(ValueError):
                _assemble_boards(sources, report)

    def test_semantic_aliases_are_not_collapsed_in_output(self):
        sources, report = fixture()
        sources.append(dict(sources[0], name='eye/RinNyaa', index=101))
        report['clips'].append(dict(report['clips'][0], index=101))
        result = _assemble_boards(sources, report)
        self.assertEqual([row['index'] for row in result['domains'][0]['entries']], [1, 101])

    def test_runs_per_member_with_single_container_for_shared_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            faces = [SimpleNamespace(name=f'ch9999_{costume}_member', needs_merging_face=False)
                     for costume in ['co0002', 'co0069']]
            sources, sample = fixture()
            def presets(face, field, domain):
                return [dict(s, source=root/'original', path_id=10 if domain == 'eye' else 20)
                        for s in sources if s['domain'] == domain]
            def run(command, check):
                request = json.loads(Path(command[command.index('-boardRequest')+1]).read_text(encoding='utf-8'))
                self.assertEqual(len({item['bundle'] for item in request['clips']}), 1)
                native = copy.deepcopy(sample)
                for clip in native['clips']:
                    clip['bundle'] = request['clips'][0]['bundle']
                Path(command[command.index('-boardReport')+1]).write_text(json.dumps(native), encoding='utf-8')
                return SimpleNamespace(returncode=0)
            real_mkdtemp = tempfile.mkdtemp
            stages = []
            def make_stage(*, prefix, dir):
                stage = Path(real_mkdtemp(prefix=prefix, dir=dir))
                stages.append(stage)
                return str(stage)
            with patch('converter.llas.board_bake.load_member_with_face', side_effect=faces), \
                 patch('converter.llas.board_bake._head_path', return_value='Head_All'), \
                 patch('converter.llas.board_bake._board_sources', side_effect=presets), \
                 patch('converter.llas.board_bake._source_bindings'), \
                 patch('converter.llas.board_bake._expose_clips') as expose, \
                 patch('converter.llas.board_bake.tempfile.mkdtemp', side_effect=make_stage), \
                 patch('converter.llas.board_bake.subprocess.run', side_effect=run) as unity:
                bake_board_faces(['member1', 'member2'], root/'baked', 'unity', 'project')
            self.assertEqual(unity.call_count, 2)
            self.assertEqual(expose.call_count, 2)
            self.assertEqual(expose.call_args.args[1], [10, 20])
            self.assertEqual(len(list((root/'baked/boards').glob('*.json'))), 2)
            self.assertEqual(len(stages), 2)
            self.assertTrue(all(not stage.exists() for stage in stages))

    def test_ordinary_morph_face_never_launches_unity(self):
        with patch('converter.llas.board_bake.load_member_with_face', return_value=SimpleNamespace(needs_merging_face=True)), \
             patch('converter.llas.board_bake.subprocess.run') as unity:
            bake_board_faces(['ordinary'], 'baked', 'unity', 'project')
        unity.assert_not_called()

    def test_packed_source_bindings_require_static_boolean_renderer_data(self):
        import zlib
        def node(name, children):
            value = SimpleNamespace(m_GameObject=Mock(), m_Children=[Mock() for _ in children])
            value.m_GameObject.read.return_value.m_Name = name
            for pointer, child in zip(value.m_Children, children):
                pointer.read.return_value = child
            return value
        root = node('Head_All', [node('Head_Face', [node('mesh_facedots', [node('eye_closed', [])])])])
        binding = dict(path=zlib.crc32(b'Head_Face/mesh_facedots/eye_closed'), typeID=25,
                       attribute=3305885265, isPPtrCurve=0)
        packed = SimpleNamespace(m_StreamedClip=SimpleNamespace(curveCount=0),
            m_DenseClip=SimpleNamespace(m_CurveCount=0), m_ConstantClip=SimpleNamespace(data=[1]))
        reader = Mock(path_id=7)
        reader.type.name = 'AnimationClip'
        reader.read.return_value.m_MuscleClip.m_Clip.data = packed
        reader.read_typetree.return_value = dict(m_ClipBindingConstant=dict(genericBindings=[binding]))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'clip'
            path.write_bytes(b'fixture')
            source = dict(source=path, path_id=7, domain='eye', name='eye/Close')
            with patch('converter.llas.board_bake.UnityPy.load', return_value=SimpleNamespace(objects=[reader])):
                _source_bindings(SimpleNamespace(head_all=root), [source])
                self.assertEqual(source['source_visibility'], {'eye_closed': True})
                packed.m_StreamedClip.curveCount = 1
                with self.assertRaisesRegex(ValueError, 'variable'):
                    _source_bindings(SimpleNamespace(head_all=root), [source])
                packed.m_StreamedClip.curveCount = 0
                binding['typeID'] = 4
                with self.assertRaisesRegex(ValueError, 'Unsupported'):
                    _source_bindings(SimpleNamespace(head_all=root), [source])


if __name__ == '__main__':
    unittest.main()
