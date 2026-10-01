"""Map Unity-sampled LLAS facial poses to independent standard Morph groups.

These endpoints use the standard linear controls. They do not reproduce the
original game's intermediate facial-playable progress or Renderer visibility.
"""
from collections import Counter, defaultdict
import math


_EYE_PARTS = ("Eye_Around", "LeftEyeWhiteLine", "RightEyeWhiteLine")
_MOUTH_PARTS = ("Mouth",)
_COMBINED_PARTS = {"Eye_Around", "Mouth"}


def _targets(document):
    nodes = document.get("nodes", [])
    meshes = document.get("meshes", [])
    counts = Counter(node.get("name") for node in nodes)
    parts = defaultdict(list)
    by_shape = defaultdict(list)
    for node in nodes:
        if "mesh" not in node:
            continue
        index = node["mesh"]
        if isinstance(index, bool) or not isinstance(index, int) or not 0 <= index < len(meshes):
            raise ValueError("LLAS facial target has an invalid mesh index")
        mesh = meshes[index]
        part = mesh.get("name")
        if part not in (*_EYE_PARTS, *_MOUTH_PARTS):
            continue
        name = node.get("name")
        if not name or counts[name] != 1:
            raise ValueError(f"LLAS facial node name must resolve uniquely: {name!r}")
        shapes = mesh.get("extras", {}).get("targetNames", [])
        if not shapes:
            raise ValueError(f"LLAS facial Morph controls unsupported: {part} has no Morph targets")
        if any(not isinstance(shape, str) or not shape for shape in shapes) or len(set(shapes)) != len(shapes):
            raise ValueError(f"LLAS facial Morph names must be nonempty and unique: {name}")
        primitives = mesh.get("primitives", [])
        if not primitives or any(len(p.get("targets", [])) != len(shapes) for p in primitives):
            raise ValueError(f"LLAS facial Morph target count differs from primitive targets: {name}")
        parts[part].append((name, tuple(shapes)))
        for shape in shapes:
            by_shape[shape].append((part, name))
    if not parts:
        raise ValueError("LLAS facial Morph controls unsupported: model has no supported Morph targets")
    for part in (*_EYE_PARTS, *_MOUTH_PARTS):
        if len(parts[part]) != 1:
            raise ValueError(f"LLAS facial target {part} must resolve uniquely; got {len(parts[part])}")
    return parts, by_shape


def _endpoint(pose, domain, parts, by_shape):
    samples = {}
    has_combined = False
    for morph in pose.get("morphs", []):
        source_path = morph.get("node")
        shape = morph.get("name")
        if not isinstance(source_path, str) or not source_path or not isinstance(shape, str) or not shape:
            raise ValueError("LLAS sampled Morph requires source node and shape names")
        part = source_path.replace("\\", "/").rsplit("/", 1)[-1]
        if part not in (*_EYE_PARTS, *_MOUTH_PARTS, "CombineFace"):
            continue
        key = (part, shape)
        if key in samples:
            raise ValueError(f"Duplicate LLAS sampled Morph reference: {source_path}/{shape}")
        value = morph.get("value")
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 100:
            raise ValueError(f"Invalid LLAS sampled Morph weight: {source_path}/{shape}: {value!r}")
        if part == "CombineFace":
            has_combined = True
            matches = [target for target in by_shape.get(shape, []) if target[0] in _COMBINED_PARTS]
            if len(matches) != 1:
                raise ValueError(f"Combined LLAS Morph must resolve uniquely: {shape!r}; got {len(matches)}")
        else:
            _, names = parts[part][0]
            if shape not in names:
                raise ValueError(f"Missing LLAS Morph target: {part}/{shape}")
        samples[key] = float(value) / 100.0
    endpoint = {}
    for part in domain:
        node_name, shapes = parts[part][0]
        source_part = "CombineFace" if has_combined and part in _COMBINED_PARTS else part
        weights = {}
        for shape in shapes:
            key = (source_part, shape)
            if key not in samples:
                raise ValueError(f"Missing Unity endpoint sample: {source_part}/{shape}")
            weights[shape] = samples[key]
        endpoint[node_name] = weights
    return endpoint


def build_facial_endpoints(gltf_document: dict, closed_pose: dict, open_pose: dict) -> dict:
    """Build eye-close and mouth-open endpoints solely from supplied Unity poses.

    CombineFace values override the original Eye_Around/Mouth renderers left in
    the sampling rig. The complete endpoint domains include explicit zeros.
    Ordinary Renderer-only Rina faces are intentionally unsupported here.
    """
    parts, by_shape = _targets(gltf_document)
    return {
        "blink": _endpoint(closed_pose, _EYE_PARTS, parts, by_shape),
        "speech": _endpoint(open_pose, _MOUTH_PARTS, parts, by_shape),
    }


def build_facial_expressions(gltf_document: dict, expressions: list,
                             closed_pose: dict, open_pose: dict) -> dict:
    """Export all sampled poses, independent eye/mouth states and presets.

    Matching source eye/mouth labels are paired as a consumer adaptation, not as
    an assertion that the game fixes those pairs. Eye-only presets use the
    sampled A mouth; mouth-only states remain available through the mouth group.
    Every mouth state transitions from sampled Smile to its own sampled pose,
    except Smile itself, which transitions to A. Complete poses are
    replaced, not added: additive poses visibly overdeform Rin's source mouth.
    Already closed eye states stay fixed; Wink closes the other eye towards
    sampled CloseSmile. These are consumer controls, not source-game scheduling.
    Renderer visibility and auxiliary transforms remain outside this subset.
    """
    if not isinstance(expressions, list):
        raise ValueError('LLAS sampled expressions must be a list')
    parts, by_shape = _targets(gltf_document)
    domains, seen = {'eye': {}, 'mouth': {}}, set()
    for entry in expressions:
        if not isinstance(entry, dict):
            raise ValueError('Invalid LLAS sampled expression')
        name, domain, pose = entry.get('name'), entry.get('domain'), entry.get('pose')
        if not isinstance(name, str) or not name.strip() or domain not in ('eye', 'mouth') or not isinstance(pose, dict):
            raise ValueError('LLAS sampled expression requires name, eye/mouth domain and pose')
        if name in seen:
            raise ValueError(f'Duplicate LLAS expression name: {name}')
        seen.add(name)
        if not name.startswith(domain + '/') or not name[len(domain) + 1:]:
            raise ValueError(f'LLAS sampled expression name must identify its domain: {name}')
        targets = _endpoint(pose, _EYE_PARTS if domain == 'eye' else _MOUTH_PARTS, parts, by_shape)
        domains[domain][name.split('/', 1)[1]] = targets
    if 'Open' not in domains['eye'] or not {'N', 'A', 'Smile'} <= domains['mouth'].keys():
        raise ValueError('LLAS full-face presets require sampled eye/Open and mouth/N, mouth/A, mouth/Smile')
    endpoints = build_facial_endpoints(gltf_document, closed_pose, open_pose)
    morph_poses = [{'name': f'{domain}/{label}', 'targets': targets}
                   for domain, presets in domains.items() for label, targets in presets.items()]

    def endpoint_pose(domain, key, targets):
        for label, sampled in domains[domain].items():
            if sampled == targets:
                return f'{domain}/{label}'
        name = f'control/{key}'
        morph_poses.append({'name': name, 'targets': targets})
        return name

    blink_pose = endpoint_pose('eye', 'blink', endpoints['blink'])
    pose_targets = {entry['name']: entry['targets'] for entry in morph_poses}

    def replacement(base, target):
        # Endpoints inherit omitted coefficients, so a full sampled-pose
        # replacement must explicitly remove the current baseline recipe.
        return {target: 1} if base == target else {base: 0, target: 1}

    groups = []
    for domain, presets in domains.items():
        states = []
        # Match the documented defaults even when source sampling order differs.
        neutral = 'Open' if domain == 'eye' else 'N'
        for label in [neutral, *(label for label in presets if label != neutral)]:
            base = f'{domain}/{label}'
            controls = {}
            if domain == 'eye':
                if label not in {'Close', 'CloseSmile', 'Missing', 'Tightly'}:
                    target = 'eye/CloseSmile' if label in {'WinkL', 'WinkR'} else blink_pose
                    if target not in pose_targets:
                        raise ValueError(f'LLAS {label} blink requires sampled {target}')
                    if pose_targets[base] != pose_targets[target]:
                        controls['blink'] = replacement(base, target)
            else:
                target = 'mouth/A' if label == 'Smile' else base
                base = 'mouth/Smile'
                if pose_targets[base] != pose_targets[target]:
                    controls['speech'] = replacement(base, target)
            state = {'name': label, 'poses': {base: 1}}
            if controls:
                state['controls'] = controls
            states.append(state)
        groups.append({'name': domain, 'states': states})
    result = []

    def append(name, eye, mouth):
        if any(entry['name'] == name for entry in result):
            raise ValueError(f'Duplicate LLAS composed expression name: {name}')
        result.append({'name': name, 'selections': {'eye': eye, 'mouth': mouth}})

    append('Neutral', 'Open', 'A')
    paired = set(domains['eye']).intersection(domains['mouth']) - {'Open', 'N'}
    for label, targets in domains['eye'].items():
        if label == 'Open':
            continue
        if label in paired:
            append(label, label, label)
            continue
        # A source preset with no Morph effect must not acquire an invented
        # effect from its label (e.g. a visibility-only special face).
        if any(value != 0 for weights in targets.values() for value in weights.values()):
            append(label, label, 'A')
    return {'morphPoses': morph_poses, 'expressionGroups': groups,
            'expressions': result, 'defaultExpression': 'Neutral'}
