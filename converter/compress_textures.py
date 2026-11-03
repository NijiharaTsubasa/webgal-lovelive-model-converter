"""Discover material textures and preprocess them with bounded parallel encoders."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from io import BytesIO
import os
from pathlib import Path
import time
from threading import Event

from converter.common.glb import GlbBuilder
from converter.common.unity import component_pointer, game_object_transform, object_id, pointer_id
from converter.common.shader import renderer_uses_eye_shader
from converter.common.uastc import (TEXTURE_ROOT, texture_key, read_compressed_texture,
    encode_uastc, write_compressed_texture, encoder_path, EncoderUnavailableError)


class CompressionQueue:
    def __init__(self, root: Path, workers: int, threads: int):
        self.root, self.threads = root, threads
        self.started = time.monotonic()
        self.executable = None
        self.pool = ThreadPoolExecutor(max_workers=workers)
        self.limit = workers * 2
        self.pending = {}
        self.cancel_event = Event()
        self.seen = set()
        self.completed = self.skipped = 0
        self.failures = []

    def submit(self, png, **settings):
        key = texture_key(png, **settings)
        if key in self.seen:
            return
        self.seen.add(key)
        try:
            if read_compressed_texture(png, root=self.root, **settings) is not None:
                self.skipped += 1
                return
        except RuntimeError:
            # A broken preprocessing product is repaired on the next compress run.
            pass
        if self.executable is None:
            self.executable = encoder_path()
        while len(self.pending) >= self.limit:
            self.drain()
        def encode():
            data = encode_uastc(png, threads=self.threads, executable=self.executable, cancel_event=self.cancel_event, **settings)
            write_compressed_texture(self.root / (key + '.ktx2'), data)
        self.pending[self.pool.submit(encode)] = key

    def drain(self):
        if not self.pending:
            return
        done, _ = wait(self.pending, return_when=FIRST_COMPLETED)
        for future in done:
            key = self.pending.pop(future)
            try:
                future.result()
                self.completed += 1
                elapsed = time.monotonic() - self.started
                print(f"[compress] 已发现 {len(self.seen)} 张唯一纹理，完成 {self.completed}，复用 {self.skipped}，失败 {len(self.failures)}，待处理 {len(self.pending)}，耗时 {elapsed:.1f}s，{self.completed * 60 / max(elapsed, .001):.2f} 张/分钟", flush=True)
            except Exception as exc:
                self.failures.append(f"{key}: {exc}")

    def close(self, *, cancel=False):
        if cancel:
            self.cancel_event.set()
            for future in self.pending:
                future.cancel()
            self.pool.shutdown(wait=True, cancel_futures=True)
            return
        try:
            while self.pending:
                self.drain()
        finally:
            self.pool.shutdown(wait=True, cancel_futures=True)


class TextureCollector(GlbBuilder):
    def __init__(self, queue):
        super().__init__(compress_textures=True)
        self.queue = queue

    def add_image(self, texture):
        key = object_id(texture)
        if key in self.textures:
            return self.textures[key]
        index = len(self.textures)
        self.textures[key] = index
        if key in self.lossless_texture_keys:
            return index
        image = texture.image
        if max(image.size) <= 32 or image.width % 4 or image.height % 4:
            return index
        if image.mode not in {'RGB', 'RGBA'}:
            image = image.convert('RGBA')
        output = BytesIO()
        image.save(output, format='PNG')
        color_space = texture.m_ColorSpace
        if color_space not in {0, 1}:
            raise ValueError(f"{texture.m_Name}: unsupported m_ColorSpace {color_space}")
        self.queue.submit(output.getvalue(), width=image.width, height=image.height,
            color_space='srgb' if color_space == 1 else 'linear',
            mip_count=max(image.size).bit_length() if texture.m_MipCount > 1 else 1)
        return index


def collect_materials(root, adapter, queue):
    """Use the exporter material seam without decoding meshes or normalizing skins."""
    builder = TextureCollector(queue)
    adapter.bind_builder(builder)
    builder.shader_classifier = adapter.classify_shader
    builder.material_adapter = adapter.adapt_material
    emitted = set()
    stack = [game_object_transform(root)]
    while stack:
        transform = stack.pop()
        go = transform.m_GameObject.deref_parse_as_object()
        for entry in go.m_Component:
            pointer = component_pointer(entry)
            if not pointer or pointer.type.name not in {'SkinnedMeshRenderer', 'MeshRenderer'}:
                continue
            renderer = pointer.deref_parse_as_object()
            mesh = getattr(renderer, 'm_Mesh', None)
            if pointer.type.name == 'MeshRenderer':
                if not adapter.should_export_static_renderer(renderer):
                    continue
                filters = [component_pointer(item) for item in go.m_Component
                    if component_pointer(item) and component_pointer(item).type.name == 'MeshFilter']
                if len(filters) != 1:
                    raise ValueError(f"{go.m_Name}: expected one MeshFilter for MeshRenderer")
                mesh = filters[0].deref_parse_as_object().m_Mesh
            if not mesh or not adapter.should_export_renderer(renderer):
                continue
            renderer = adapter.adapt_renderer(renderer)
            mesh_key = pointer_id(mesh)
            if not getattr(go, 'm_IsActive', True) and (mesh_key in emitted or not renderer_uses_eye_shader(renderer)):
                continue
            materials = list(renderer.m_Materials)
            # Submesh metadata is enough; do not decode vertex/index buffers.
            for index in range(len(mesh.deref_parse_as_object().m_SubMeshes)):
                builder.add_material(materials[index] if index < len(materials) else None)
            emitted.add(mesh_key)
        stack.extend(child.deref_parse_as_object() for child in reversed(transform.m_Children) if child)


def compress_bangdream(root, queue, failures):
    from converter.bangdream import load_bundle_assets, discover_bundle_inputs, _package_name, should_export_component
    from converter.bangdream.color_variants import changed_color_types
    from converter.bangdream.model_adapter import BangDreamModelAdapter
    paths = discover_bundle_inputs(root)
    if not paths:
        print(f"[compress:bangdream] 输入为空: {root}", flush=True)
    for number, (path, role) in enumerate(paths, 1):
        try:
            bundle = load_bundle_assets(path, expected_role=role)
            if not should_export_component(_package_name(bundle), role):
                continue
            print(f"[compress:bangdream] {number}/{len(paths)} {path.name}", flush=True)
            root_pointer = next((pointer for name, pointer in bundle.env.container.items()
                if name.endswith('.prefab') and pointer.type.name == 'GameObject'), None)
            for color_type in [0, *changed_color_types(bundle)]:
                adapter = BangDreamModelAdapter(bundle.env, color_type=color_type, role=role, prefab_pointer=root_pointer)
                collect_materials(bundle.prefab, adapter, queue)
        except EncoderUnavailableError:
            raise
        except Exception as exc:
            failures.append(f"{path}: {exc}")


def compress_hasunosora(root, queue, failures):
    import UnityPy
    from converter.hasunosora import HasunosoraModelAdapter
    from converter.hasunosora.source import discover_inputs
    from converter.common import dependency_closure, bundle_metadata
    index, _, _ = discover_inputs(root)
    paths = sorted((p for name, p in index.items() if name.startswith('3d')), key=lambda p: p.name)
    if not paths:
        print(f"[compress:hasunosora] 输入为空: {root}", flush=True)
    for number, path in enumerate(paths, 1):
        try:
            print(f"[compress:hasunosora] {number}/{len(paths)} {path.name}", flush=True)
            environment = UnityPy.load(*map(str, dependency_closure(path, index)))
            name, _ = bundle_metadata(path)
            containers = dict(environment.container.items())
            pointer = containers.get(name) or containers.get(path.stem)
            if not pointer:
                raise RuntimeError(f"Could not find root container for {path.name}")
            source = pointer.deref_parse_as_object()
            collect_materials(source, HasunosoraModelAdapter(environment, source), queue)
        except EncoderUnavailableError:
            raise
        except Exception as exc:
            failures.append(f"{path}: {exc}")


def concurrency(workers=None, threads=None, *, cpu_count=None):
    cpu = max(1, cpu_count if cpu_count is not None else (os.cpu_count() or 1))
    if threads is None:
        threads = min(4, max(1, cpu // workers)) if workers is not None else min(4, cpu)
    if workers is None:
        workers = max(1, cpu // threads)
    return workers, threads


def main():
    from converter.common.cli import configure_output
    configure_output()
    parser = argparse.ArgumentParser(description='Precompress model textures for conversion.')
    parser.add_argument('--game', choices=['hasunosora', 'bangdream'])
    parser.add_argument('--input', type=Path, help='Input directory for the selected game.')
    parser.add_argument('--output', type=Path, default=TEXTURE_ROOT)
    parser.add_argument('--workers', type=int, help='Concurrent encoder processes; inferred from CPU count by default.')
    parser.add_argument('--threads', type=int, help='Threads per encoder; up to four by default.')
    args = parser.parse_args()
    if (args.workers is not None and args.workers < 1) or (args.threads is not None and args.threads < 1):
        parser.error('--workers and --threads must be positive')
    if args.input and not args.game:
        parser.error('--input requires --game')
    args.workers, args.threads = concurrency(args.workers, args.threads)
    started = time.monotonic()
    failures = []
    queue = CompressionQueue(args.output.resolve(), args.workers, args.threads)
    print(f"[compress] 并发 {args.workers}，每进程 {args.threads} 线程", flush=True)
    interrupted = False
    try:
        for game in ([args.game] if args.game else ['hasunosora', 'bangdream']):
            source = args.input or Path('input_' + game)
            globals()['compress_' + game](source.resolve(), queue, failures)
    except BaseException:
        interrupted = True
        raise
    finally:
        queue.close(cancel=interrupted)
    failures.extend(queue.failures)
    print(f"[compress] 完成 {queue.completed}，复用 {queue.skipped}，失败 {len(failures)}，耗时 {time.monotonic()-started:.1f}s", flush=True)
    if failures:
        raise SystemExit('\n'.join(failures))


if __name__ == '__main__':
    main()
