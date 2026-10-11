"""Convert decrypted Yohane character bundles and Unity-baked story resources."""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from ..common.cli import configure_output
from ..common.component_order import order_model_component
from ..common.idle_pose import sample_baked_pose
from ..common.motion_binary import encode_motion
from ..common.normalized_model import export_normalized_model
from ..common.unity import game_object_transform, safe_name
from .face import export_face
from .model_adapter import YohaneModelAdapter
from .motion import default_action, export_motions
from .physics import extract_physics
from .source import discover_models, load_environment


CHARACTERS = {'yohane': '夜羽', 'ruby': '露比', 'chika': '千歌', 'you': '曜',
              'riko': '梨子', 'hanamaru': '花丸', 'dia': '黛雅', 'kanan': '果南', 'mari': '鞠莉'}
COSTUMES = {'normal01': '默认服装', 'fairy01': '妖精服'}


def model_description(name: str) -> str:
    parts = name.split('_')
    if len(parts) < 3 or parts[1] not in CHARACTERS:
        return ''
    return ' '.join(part for part in (CHARACTERS[parts[1]], COSTUMES.get(parts[2], '')) if part)


def find_prefab(environment, source):
    pointers = []
    for obj in environment.objects:
        if obj.type.name != 'AssetBundle':
            continue
        for path, asset in obj.read().m_Container:
            if path == source.asset_path and asset.asset.m_FileID == 0:
                pointer = asset.asset
                if pointer.read().m_Name == source.prefab_name:
                    pointers.append(pointer)
    if len(pointers) != 1:
        raise ValueError(f'{source.name}: expected one original prefab at {source.asset_path}')
    return pointers[0]


def prepare_prefab(pointer, name: str) -> None:
    # Fairy Ruby's source root shrinks the entire character to 40%; restore it
    # before normalization, matching the Unity baker's preprocessing.
    if name.split('_')[1:2] != ['ruby']:
        return
    transform = game_object_transform(pointer.read())
    tree = transform.object_reader.read_typetree()
    if not all(abs(float(tree['m_LocalScale'][axis]) - .4) < 1e-6 for axis in 'xyz'):
        return
    tree['m_LocalScale'] = {'x': 1., 'y': 1., 'z': 1.}
    transform.object_reader.save_typetree(tree)


def find_controller(environment, source):
    candidates = [obj for obj in environment.objects if obj.type.name == 'AnimatorController'
                  and obj.peek_name() == source.controller_name]
    if len(candidates) != 1:
        raise ValueError(f'{source.name}: expected one story controller {source.controller_name}')
    return candidates[0]


def _read_baked(directory: Path, filename: str, model: str) -> dict:
    path = directory / filename
    if not path.is_file():
        raise FileNotFoundError(f'{model}: missing Unity bake {path}; run bake:yohane first')
    return json.loads(path.read_text(encoding='utf-8'))


def convert(input_dir: Path, output_dir: Path, baked_dir: Path, clean: bool = False,
            *, model_names=None, models_only: bool = False, motions_only: bool = False) -> None:
    if models_only and motions_only:
        raise ValueError('--models-only and --motions-only are mutually exclusive')
    sources = discover_models(input_dir)
    if not sources:
        print('[yohane] 输入为空，跳过转换', flush=True)
        return
    requested = set(model_names or ())
    if requested:
        missing = requested - {source.name for source in sources}
        if missing:
            raise ValueError(f'Yohane requested models not found: {sorted(missing)}')
        sources = [source for source in sources if source.name in requested]
    game_dir, motion_dir = output_dir / 'yohane', output_dir / 'motion' / 'yohane'
    if clean:
        for directory in ([game_dir] if models_only else [motion_dir] if motions_only else [game_dir, motion_dir]):
            if directory.exists():
                shutil.rmtree(directory)
    completed_controllers = set()
    body_files = {}
    for source in sources:
        candidate = baked_dir / 'yohane' / source.name / 'body_baked.json'
        if candidate.is_file():
            body_files.setdefault(source.controller_name, candidate)
    for number, source in enumerate(sources, 1):
        if motions_only and source.controller_name in completed_controllers:
            continue
        print(f'[yohane] {number}/{len(sources)} {source.name}', flush=True)
        environment = load_environment(source)
        controller = find_controller(environment, source)
        baked = baked_dir / 'yohane' / source.name
        body_file = body_files.get(source.controller_name)
        if models_only and body_file is None:
            candidate = baked / 'idle_baked.json'
            body_file = candidate if candidate.is_file() else None
        body = json.loads(body_file.read_text(encoding='utf-8')) if body_file else None
        character = CHARACTERS.get(source.name.split('_')[1], '')
        if not models_only and body is None:
            raise FileNotFoundError(f'{source.name}: missing Unity body bake; run bake:yohane:motions first')
        if not models_only and source.controller_name not in completed_controllers:
            motions = export_motions(controller, body, character)
            destination = motion_dir / source.controller_name
            destination.mkdir(parents=True, exist_ok=True)
            filenames = set()
            for name, payload in motions.items():
                filename = safe_name(name)
                if filename in filenames:
                    raise ValueError(f'{source.controller_name}: colliding motion filenames after sanitization: {name}')
                filenames.add(filename)
                (destination / f'{filename}.motionbin').write_bytes(encode_motion(payload))
            completed_controllers.add(source.controller_name)
            print(f'[yohane:motion] {source.controller_name}: {len(motions)} complete actions', flush=True)
        if motions_only:
            continue
        skeleton = _read_baked(baked, 'skeleton.json', source.name)
        face_file = baked / 'face_samples.json'
        if not face_file.is_file():
            raise FileNotFoundError(f'{source.name}: missing Unity face bake {face_file}')
        pointer = find_prefab(environment, source)
        prepare_prefab(pointer, source.name)
        exported = export_normalized_model(environment, pointer, skeleton, YohaneModelAdapter())
        component = {'type': 'model', 'name': source.name, 'description': model_description(source.name),
                     'group': 'yohane', 'role': 'integrated', 'model': 'model.glb',
                     'humanoidScale': exported.human_scale}
        idle_motion, idle_clip = default_action(controller)
        idle = [clip['name'] for clip in body.get('clips', [])
                if clip['name'] == idle_clip] if body else []
        if len(idle) == 1:
            component['defaultMotion'] = f'yohane/{source.controller_name}/{safe_name(idle_motion)}'
            component['idlePose'] = sample_baked_pose(body_file, idle_clip, 0)
        component.update(export_face(face_file, controller, exported.builder.document))
        physics = extract_physics(environment, exported)
        if physics:
            component['physics'] = physics
        destination = game_dir / source.name
        destination.mkdir(parents=True, exist_ok=True)
        exported.builder.write(destination / 'model.glb')
        (destination / 'config.json').write_text(json.dumps(
            {'components': [order_model_component(component)]}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    if not motions_only:
        configs = sorted(f'{directory.name}/config.json' for directory in game_dir.iterdir()
                         if directory.is_dir() and (directory / 'config.json').is_file())
        (game_dir / 'index.json').write_text(json.dumps({'configs': configs}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main() -> None:
    configure_output()
    parser = argparse.ArgumentParser(description='Convert decrypted Yohane character AssetBundles.')
    parser.add_argument('--input', type=Path, default=Path('input_yohane'))
    parser.add_argument('--output', type=Path, default=Path('output_packages'))
    parser.add_argument('--baked', type=Path, default=Path('baked_motions'))
    parser.add_argument('--clean', action='store_true', help='Rebuild Yohane outputs.')
    parser.add_argument('--model', action='append', help='Exact original prefab name; repeat for multiple models.')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--models-only', action='store_true')
    mode.add_argument('--motions-only', action='store_true')
    args = parser.parse_args()
    convert(args.input.resolve(), args.output.resolve(), args.baked.resolve(), args.clean,
            model_names=args.model, models_only=args.models_only, motions_only=args.motions_only)
