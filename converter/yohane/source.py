"""Discover decrypted Yohane bundles through their original asset references."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import stat

import UnityPy


@dataclass(frozen=True)
class BundleInfo:
    path: Path
    files: tuple[str, ...]
    externals: tuple[str, ...]
    assets: tuple[tuple[str, str, str, int], ...]
    human_avatar: bool = False


@dataclass(frozen=True)
class YohaneModelSource:
    name: str
    prefab_name: str
    bundle_path: Path
    asset_path: str
    prefab_path_id: int
    controller_name: str
    controller_bundle: Path
    controller_asset_path: str
    bundle_paths: tuple[Path, ...]
    idle_clip_names: tuple[str, ...] = ()


def read_bundle(path: Path) -> BundleInfo:
    with path.open('rb') as stream:
        signature = stream.read(8)
    if not signature.startswith((b'UnityFS', b'UnityRaw', b'UnityWeb')):
        raise ValueError(f'{path}: expected a decrypted Unity AssetBundle')
    environment = UnityPy.load(str(path))
    files = {obj.assets_file.name: obj.assets_file for obj in environment.objects}
    assets = {}
    human_avatar = False
    for obj in environment.objects:
        if obj.type.name == 'Avatar':
            avatar = obj.read_typetree().get('m_Avatar', {})
            human_avatar |= bool(avatar.get('m_HumanSkeletonIndexArray'))
        if obj.type.name != 'AssetBundle':
            continue
        for asset_path, asset in obj.read().m_Container:
            pointer = asset.asset
            # Containers can include dependency assets; only record assets owned
            # by this bundle so an incomplete input cannot appear self-contained.
            if pointer.m_FileID != 0 or not pointer.m_PathID:
                continue
            reader = pointer.deref()
            assets[(asset_path, reader.path_id)] = (
                asset_path, reader.type.name, reader.peek_name(), reader.path_id)
    external = {Path(value.path.replace('\\', '/')).name.lower()
                for file in files.values() for value in file.externals}
    return BundleInfo(path, tuple(name.lower() for name in files),
                      tuple(sorted(external)), tuple(assets.values()), human_avatar)


def dependency_closure(roots: tuple[Path, ...], bundles: list[BundleInfo]) -> tuple[Path, ...]:
    by_path = {item.path: item for item in bundles}
    owners = {}
    for item in bundles:
        for file in item.files:
            previous = owners.get(file)
            if previous is not None and previous.path != item.path:
                # Identical copied bundles are safe; different CAB owners are not.
                if previous.path.read_bytes() != item.path.read_bytes():
                    raise ValueError(f'Duplicate serialized file {file}: {previous.path}, {item.path}')
            owners[file] = item
    pending = list(roots)
    selected = set()
    while pending:
        path = pending.pop()
        if path in selected:
            continue
        selected.add(path)
        for name in by_path[path].externals:
            if name in ('unity default resources', 'unity_builtin_extra'):
                continue
            owner = owners.get(name)
            if owner is None:
                raise FileNotFoundError(f'{path.name}: missing AssetBundle dependency {name}')
            pending.append(owner.path)
    return tuple(sorted(selected))


def discover_models(input_dir: Path) -> list[YohaneModelSource]:
    try:
        input_stat = input_dir.stat()
    except FileNotFoundError:
        return []
    if not stat.S_ISDIR(input_stat.st_mode):
        raise NotADirectoryError(input_dir)
    paths = sorted(path for path in input_dir.rglob('*')
                   if path.is_file() and path.suffix.lower() == '.bundle')
    bundles = []
    for number, path in enumerate(paths, 1):
        bundles.append(read_bundle(path))
        if number % 25 == 0 or number == len(paths):
            print(f'[yohane:discover] bundles {number}/{len(paths)}', flush=True)
    controllers = {}
    models = {}
    for bundle in bundles:
        for asset_path, kind, name, path_id in bundle.assets:
            if kind == 'AnimatorController' and name.startswith(('CH_', 'EN_')) and name.endswith('_story'):
                controllers[name.lower()] = (name, bundle.path, asset_path)
            if kind != 'GameObject' or not asset_path.lower().endswith('.prefab') or not name.startswith(('CH_', 'EN_')) or name.endswith('_story'):
                continue
            if Path(asset_path).stem.lower() != name.lower():
                continue
            # Full body prefabs live in their own character directory. Cut-ins
            # and scene prefabs reference these assets but are not model roots.
            if Path(asset_path).parent.name.lower() != name.lower():
                continue
            if name in models and models[name][0] != bundle.path:
                raise ValueError(f'Ambiguous model prefab {name}')
            models[name] = (bundle.path, asset_path, path_id)
    result = []
    # Resolve shared Avatars/controllers once for the discovery pass. Individual
    # model conversion and Unity batches still use their bounded CAB closures.
    environment = UnityPy.load(*map(str, paths)) if models else None
    for number, (name, (bundle_path, asset_path, path_id)) in enumerate(sorted(models.items()), 1):
        print(f'[yohane:discover] models {number}/{len(models)} {name}', flush=True)
        model_closure = dependency_closure((bundle_path,), bundles)
        if not any(item.human_avatar for item in bundles if item.path in model_closure):
            continue
        character = name.split('_')[1].lower()
        exact = controllers.get((name + '_story').lower())
        candidates = [exact] if exact else [item for key, item in sorted(controllers.items())
                                           if key.split('_')[1] == character]
        if not candidates:
            # Enemy assets also contain creatures without a story character
            # controller. Only story-capable humanoids are conversion inputs.
            if name.startswith('EN_'):
                continue
            raise FileNotFoundError(f'{name}: missing character story AnimatorController')
        # Other costumes reuse a character's story graph. Unity ignores facial
        # bindings absent from a costume, including fully masked/armored faces.
        exact = min(candidates, key=lambda item: ('_normal01_story' not in item[0].lower(), item[2]))
        controller_name, controller_bundle, controller_asset_path = exact
        closure = dependency_closure((bundle_path, controller_bundle), bundles)
        provisional = YohaneModelSource(name, name, bundle_path, asset_path, path_id,
                                        controller_name, controller_bundle, controller_asset_path, closure)
        prefab = source_prefab(environment, provisional).deref_parse_as_object()
        if not has_human_avatar(prefab):
            continue
        idle_names = controller_idle_clips(environment, controller_name)
        result.append(YohaneModelSource(name, name, bundle_path, asset_path, path_id,
                                       controller_name, controller_bundle, controller_asset_path, closure, idle_names))
    return result


def load_environment(source: YohaneModelSource) -> Any:
    return UnityPy.load(*map(str, source.bundle_paths))


def source_prefab(environment: Any, source: YohaneModelSource) -> Any:
    candidates = { (value.asset.deref().assets_file.name, value.asset.m_PathID): value.asset
                  for obj in environment.objects if obj.type.name == 'AssetBundle'
                  for key, value in obj.read().m_Container
                  if key == source.asset_path and value.asset.m_FileID == 0
                  and value.asset.m_PathID == source.prefab_path_id}
    if len(candidates) != 1:
        raise ValueError(f'{source.name}: ambiguous original prefab')
    return next(iter(candidates.values()))


def has_human_avatar(prefab: Any) -> bool:
    for pair in prefab.m_Component:
        reader = pair.component.deref()
        if reader.type.name == 'Animator':
            animator = reader.read()
            if animator.m_Avatar.m_PathID:
                avatar = animator.m_Avatar.deref().read_typetree()
                if avatar['m_Avatar']['m_HumanSkeletonIndexArray']:
                    return True
        elif reader.type.name == 'Transform':
            for child in reader.read().m_Children:
                if has_human_avatar(child.deref_parse_as_object().m_GameObject.deref_parse_as_object()):
                    return True
    return False


def controller_idle_clips(environment: Any, name: str) -> tuple[str, ...]:
    reader = next(obj for obj in environment.objects
                  if obj.type.name == 'AnimatorController' and obj.peek_name() == name)
    tree = reader.read_typetree()
    controller = tree['m_Controller']
    layer = controller['m_LayerArray'][0]['data']
    machine = controller['m_StateMachineArray'][layer['m_StateMachineIndex']]['data']
    states = machine['m_StateConstantArray']
    clips = reader.read().m_AnimationClips
    strings = dict(tree['m_TOS'])
    order = [machine['m_DefaultState']] + [index for index, wrapped in enumerate(states)
             if index != machine['m_DefaultState'] and 'idle' in strings[wrapped['data']['m_NameID']].lower()]
    for index in order:
        ids = {node['data']['m_ClipID'] for blend in states[index]['data']['m_BlendTreeConstantArray']
               for node in blend['data']['m_NodeArray'] if not node['data']['m_ChildIndices']
               and 0 <= node['data']['m_ClipID'] < len(clips)}
        names = tuple(sorted({clips[clip].deref().peek_name() for clip in ids}))
        if names:
            return names
    raise ValueError(f'{name}: no idle clip in the original body state machine')


