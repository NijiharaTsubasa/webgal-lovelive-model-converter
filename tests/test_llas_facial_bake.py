import unittest
import json
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from converter.llas.facial_bake import face_pose_path, _static_entries, _assemble_poses, bake_model_faces, _expose_clips


class FacialBakeTests(unittest.TestCase):
    def test_static_selection_uses_real_entries_filters_motion_and_aliases(self):
        def entry(index, clip):
            return dict(index=index, summary=index, clip=dict(m_FileID=0, m_PathID=clip))
        rows = [entry(1, 10), entry(3, 30), entry(6, 60), entry(900, 9000),
                entry(16, 160), entry(101, 10), entry(20, 0)]
        selected = _static_entries(rows, 'eye')
        self.assertEqual([(e['index'], name) for e, name in selected],
                         [(1, 'eye/Close'), (3, 'eye/Open'), (16, 'eye/Angry')])
        with self.assertRaisesRegex(ValueError, 'index 1'):
            _static_entries(rows[1:], 'eye')
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            _static_entries(rows + [rows[0]], 'eye')

    def test_report_assembly_requires_exact_bundle_and_clip_and_uses_last_pose(self):
        sources = [dict(domain=d, name=n, index=1, clip_name='same', bundle=Path(b))
                   for d, n, b in [('eye', 'eye/Close', 'a'), ('mouth', 'mouth/A', 'b')]]
        clips = [dict(bundle=b, name='same', poses=[{'morphs': [{'value': 0}]},
                 {'morphs': [{'value': value}]}]) for b, value in [('a', 25), ('b', 70)]]
        result = _assemble_poses(sources, clips)
        self.assertEqual(result['closed']['morphs'][0]['value'], 25)
        self.assertEqual(result['open']['morphs'][0]['value'], 70)
        self.assertEqual(result['expressions'][0],
                         dict(name='eye/Close', domain='eye', pose=result['closed']))
        for bad in (clips[:1], clips + [clips[0]],
                    [dict(clips[0], poses=[]), clips[1]]):
            with self.assertRaises(ValueError):
                _assemble_poses(sources, bad)

    def test_one_unity_run_per_face_and_one_copy_per_original_bundle(self):
        with tempfile.TemporaryDirectory() as folder:
            stage = Path(folder)
            face = SimpleNamespace(needs_merging_face=True, face_source_path=stage/'face.unity3d')
            source = stage/'both-tables.unity3d'
            def presets(face, field, domain):
                return [dict(domain=domain, name=domain+'/sample', index=1,
                             source=source, path_id=10 if domain == 'eye' else 20,
                             clip_name=domain+' clip')]
            def run(command, check):
                bundles = command[command.index('-faceBundles')+1].split('|')
                self.assertEqual(len(bundles), 1)
                report = Path(command[command.index('-faceReport')+1])
                report.write_text(json.dumps({'clips': [dict(bundle=bundles[0], name=d+' clip',
                    poses=[dict(morphs=[dict(node='mesh_face/CombineFace', name='test', value=100)])])
                    for d in ('eye', 'mouth')]}), encoding='utf-8')
                return SimpleNamespace(returncode=0)
            destination = stage/'baked/faces/same-face.json'
            with patch('converter.llas.facial_bake.load_member_with_face', return_value=face), \
                 patch('converter.llas.facial_bake.source_companions', side_effect=lambda face, sources: sources), \
                 patch('converter.llas.facial_bake.assemble_companions', return_value={'bindings': []}), \
                 patch('converter.llas.facial_bake.face_pose_path', return_value=destination), \
                 patch('converter.llas.facial_bake._preset_sources', side_effect=presets), \
                 patch('converter.llas.facial_bake._expose_clips') as expose, \
                 patch('converter.llas.facial_bake.subprocess.run', side_effect=run) as unity:
                bake_model_faces(['costume1', 'costume2'], stage/'baked', 'unity', 'project')
            self.assertEqual(unity.call_count, 1)
            self.assertEqual(expose.call_count, 1)
            self.assertEqual(expose.call_args.args[1], [10, 20])
            self.assertEqual(len(json.loads(destination.read_text(encoding='utf-8'))['expressions']), 2)

    def test_exposes_all_selected_clips_in_single_container(self):
        bundle = Mock()
        bundle.type.name = 'AssetBundle'
        tree = {'m_PreloadTable': [], 'm_Container': []}
        bundle.read_typetree.return_value = tree
        clips = []
        for path_id in (10, 20):
            clip = Mock(path_id=path_id)
            clip.type.name = 'AnimationClip'
            clip.read.return_value.m_Name = f'clip-{path_id}'
            clips.append(clip)
        file = Mock()
        file.save.return_value = b'disposable bundle'
        environment = SimpleNamespace(objects=[bundle, *clips], files={'test': file})
        with tempfile.TemporaryDirectory() as folder, patch('converter.llas.facial_bake.UnityPy.load', return_value=environment):
            source = Path(folder)/'source'
            source.write_bytes(b'source')
            _expose_clips(source, [10, 20, 10], Path(folder)/'copy')
        self.assertEqual([item[1]['asset']['m_PathID'] for item in tree['m_Container']], [10, 20])
        self.assertEqual([item[1]['preloadIndex'] for item in tree['m_Container']], [0, 1])
        bundle.save_typetree.assert_called_once_with(tree)

    def test_shared_face_identity_not_costume_is_cache_key(self):
        face = SimpleNamespace(face_root=SimpleNamespace(m_GameObject=Mock()))
        face.face_root.m_GameObject.read.return_value.m_Name = 'ch0001_co0000_facedynamic'
        self.assertEqual(face_pose_path(face, Path('baked')), Path('baked/faces/ch0001_co0000_facedynamic.json'))
        for unsafe in ('../bad', 'a/b', 'a\\b'):
            face.face_root.m_GameObject.read.return_value.m_Name = unsafe
            with self.assertRaises(ValueError):
                face_pose_path(face, Path('baked'))


if __name__ == '__main__':
    unittest.main()
