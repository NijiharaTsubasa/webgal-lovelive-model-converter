from pathlib import Path
import tempfile
from threading import Event
from types import SimpleNamespace
from unittest.mock import Mock
import unittest
from unittest.mock import patch

from converter.compress_textures import CompressionQueue, TextureCollector, concurrency, collect_materials
from converter.common.uastc import texture_key
import test_uastc as fixtures


class CompressionPipelineTests(unittest.TestCase):
    def test_cpu_budget_and_single_override(self):
        self.assertEqual(concurrency(cpu_count=16), (4,4))
        self.assertEqual(concurrency(cpu_count=1), (1,1))
        self.assertEqual(concurrency(workers=8,cpu_count=16), (8,2))
        self.assertEqual(concurrency(threads=2,cpu_count=16), (8,2))
        self.assertEqual(concurrency(workers=8,threads=4,cpu_count=16), (8,4))

    def test_empty_scan_needs_no_encoder(self):
        with tempfile.TemporaryDirectory() as temp, patch('converter.compress_textures.encoder_path', side_effect=AssertionError('must be lazy')):
            queue = CompressionQueue(Path(temp), 1, 1)
            queue.close()
            self.assertEqual(queue.completed, 0)

    def test_content_dedup_resume_and_corrupt_product_repair(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            args=dict(width=64,height=64,color_space='linear',mip_count=1)
            data=fixtures.UastcTests.container()
            with patch('converter.compress_textures.encoder_path', return_value='toktx'), patch('converter.compress_textures.encode_uastc', return_value=data) as encode:
                queue=CompressionQueue(root,2,1)
                queue.submit(b'png',**args);queue.submit(b'png',**args);queue.close()
                self.assertEqual(encode.call_count,1)
                self.assertEqual(queue.completed,1)
                queue=CompressionQueue(root,2,1)
                queue.submit(b'png',**args);queue.close()
                self.assertEqual(encode.call_count,1)
                self.assertEqual(queue.skipped,1)
                (root/(texture_key(b'png',**args)+'.ktx2')).write_bytes(b'broken')
                queue=CompressionQueue(root,2,1)
                queue.submit(b'png',**args);queue.close()
                self.assertEqual(encode.call_count,2)

    def test_failed_texture_is_reported_and_other_texture_survives(self):
        with tempfile.TemporaryDirectory() as temp:
            def encode(png,**kwargs):
                if png==b'bad':raise RuntimeError('encoder error')
                return fixtures.UastcTests.container()
            with patch('converter.compress_textures.encoder_path',return_value='toktx'),patch('converter.compress_textures.encode_uastc',side_effect=encode):
                queue=CompressionQueue(Path(temp),1,1)
                for png in [b'bad',b'good']:queue.submit(png,width=64,height=64,color_space='linear',mip_count=1)
                queue.close()
                self.assertEqual(queue.completed,1)
                self.assertEqual(len(queue.failures),1)
                self.assertEqual(len(list(Path(temp).glob('*.ktx2'))),1)

    def test_collector_never_decodes_protected_image(self):
        class Queue:
            def submit(self,*args,**kwargs):raise AssertionError('protected texture must not be encoded')
        from converter.common.unity import object_id
        source=fixtures.texture()
        collector=TextureCollector(Queue())
        collector.lossless_texture_keys.add(object_id(source))
        self.assertEqual(collector.add_image(source),collector.add_image(source))
        self.assertFalse(collector.binary)

    def test_material_scan_uses_actual_submesh_slots_without_decoding_geometry(self):
        mesh = SimpleNamespace(m_SubMeshes=[object()])
        mesh_pointer = SimpleNamespace(assetsfile=object(), m_PathID=1, deref_parse_as_object=lambda:mesh)
        renderer = SimpleNamespace(m_Mesh=mesh_pointer, m_Materials=['used','unused'])
        pointer = SimpleNamespace(type=SimpleNamespace(name='SkinnedMeshRenderer'),deref_parse_as_object=lambda:renderer)
        go = SimpleNamespace(m_IsActive=True,m_Component=[(0,pointer)])
        transform = SimpleNamespace(m_GameObject=SimpleNamespace(deref_parse_as_object=lambda:go),m_Children=[])
        adapter = Mock()
        adapter.should_export_renderer.return_value=True
        adapter.adapt_renderer.side_effect=lambda value:value
        builder = Mock()
        with patch('converter.compress_textures.TextureCollector',return_value=builder),patch('converter.compress_textures.game_object_transform',return_value=transform):
            collect_materials(go,adapter,object())
        builder.add_material.assert_called_once_with('used')
        adapter.bind_builder.assert_called_once_with(builder)

    def test_queue_is_bounded_and_cancel_stops_workers(self):
        with tempfile.TemporaryDirectory() as temp:
            started=Event()
            def encode(*args,cancel_event,**kwargs):
                started.set();cancel_event.wait(2);raise RuntimeError('cancelled')
            with patch('converter.compress_textures.encoder_path',return_value='toktx'),patch('converter.compress_textures.encode_uastc',side_effect=encode):
                queue=CompressionQueue(Path(temp),1,1)
                queue.submit(b'one',width=64,height=64,color_space='linear',mip_count=1)
                self.assertTrue(started.wait(1))
                self.assertLessEqual(len(queue.pending),queue.limit)
                queue.close(cancel=True)
                self.assertTrue(queue.cancel_event.is_set())
                self.assertEqual(list(Path(temp).glob('*.ktx2')),[])
