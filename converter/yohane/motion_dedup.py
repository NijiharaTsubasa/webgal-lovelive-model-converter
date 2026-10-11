"""Keep one copy of equivalent Yohane actions, preferring normal costumes."""
from __future__ import annotations

import copy
import json
import math
from pathlib import Path

from ..common.motion_binary import decode_motion


def motion_content(payload: dict) -> dict:
    """Compare playback data with clip/state identifiers renamed consistently."""
    result = copy.deepcopy(payload)
    result.pop('name', None)
    result.pop('description', None)
    clips = result.get('clips', [])
    clip_ids = {clip['id']: f'clip-{index}' for index, clip in enumerate(clips)}
    for clip in clips:
        clip.pop('name', None)
        clip.pop('description', None)
        clip['id'] = clip_ids[clip['id']]
    for layer in result.get('program', {}).get('layers', []):
        states = layer.get('states', [])
        state_ids = {state['id']: f'state-{index}' for index, state in enumerate(states)}
        layer['initialState'] = state_ids[layer['initialState']]
        for state in states:
            state['id'] = state_ids[state['id']]
            state['clip'] = clip_ids[state['clip']]
            for transition in state.get('transitions', []):
                transition['to'] = state_ids[transition['to']]
    return result


def equivalent(left, right) -> bool:
    if isinstance(left, (int, float)) and not isinstance(left, bool):
        return (isinstance(right, (int, float)) and not isinstance(right, bool)
                and math.isclose(left, right, rel_tol=0, abs_tol=1e-5))
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(equivalent(left[key], right[key]) for key in left)
    if isinstance(left, list):
        return len(left) == len(right) and all(equivalent(a, b) for a, b in zip(left, right))
    return left == right


def motion_order(path: Path):
    controller = path.parent.name
    return ('_normal01_story' not in controller, controller, path.name)


def character_motions(output_dir: Path, character: str) -> list[Path]:
    return sorted((path for path in (output_dir / 'motion' / 'yohane').glob('*/*.motionbin')
                   if path.parent.name.split('_')[1:2] == [character]), key=motion_order)


def resolve_default_motion(output_dir: Path, controller: str, name: str, payload: dict) -> str:
    relative = f'yohane/{controller}/{name}'
    if (output_dir / 'motion' / f'{relative}.motionbin').is_file():
        return relative
    content = motion_content(payload)
    for path in character_motions(output_dir, controller.split('_')[1]):
        if equivalent(content, motion_content(decode_motion(path.read_bytes()))):
            return path.relative_to(output_dir / 'motion').with_suffix('').as_posix()
    return relative


def deduplicate_motions(output_dir: Path) -> dict[str, str]:
    retained = {}
    replacements = {}
    paths = sorted((output_dir / 'motion' / 'yohane').glob('*/*.motionbin'), key=motion_order)
    for path in paths:
        character = path.parent.name.split('_')[1]
        content = motion_content(decode_motion(path.read_bytes()))
        candidates = retained.setdefault(character, [])
        previous = next((prior for prior, data in candidates if equivalent(content, data)), None)
        if previous is None:
            candidates.append((path, content))
            continue
        old = path.relative_to(output_dir / 'motion').with_suffix('').as_posix()
        new = previous.relative_to(output_dir / 'motion').with_suffix('').as_posix()
        replacements[old] = new
    # Update model references before removing their former motion files.
    for path in (output_dir / 'yohane').glob('*/config.json'):
        manifest = json.loads(path.read_text(encoding='utf-8'))
        changed = False
        for component in manifest.get('components', []):
            old = component.get('defaultMotion')
            if old in replacements:
                component['defaultMotion'] = replacements[old]
                changed = True
        if changed:
            path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    for old in replacements:
        (output_dir / 'motion' / f'{old}.motionbin').unlink()
    for directory in (output_dir / 'motion' / 'yohane').glob('*'):
        if directory.is_dir() and not any(directory.iterdir()):
            directory.rmdir()
    return replacements
