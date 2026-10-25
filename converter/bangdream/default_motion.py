"""Default character motion and its Unity-baked first-frame Humanoid pose."""
from __future__ import annotations

import json
import re
from pathlib import Path
import UnityPy

from converter.common.idle_pose import sample_baked_pose
from converter.common.motion import controller_program
from .motion import discover_motion_bundles, _filter_placeholders, _simple_program
from . import UNITY_VERSION


class DefaultMotions:
    def __init__(self, input_dir: Path, baked_dir: Path | None):
        self.baked_dir = baked_dir
        self.sources = {name: (index, source) for index, (name, source) in
                        enumerate(discover_motion_bundles(input_dir), 1)} if baked_dir else {}
        self.cache = {}

    def get(self, package_name: str) -> dict:
        match = re.match(r'(\d{3})_cos_', package_name)
        if not match:
            return {}
        character = '001' if match[1] == '000' else match[1]
        if character in self.cache:
            return self.cache[character]
        name = f'characterunique/ch{character}/001'
        result = {'defaultMotion': f'garupa/{name}'}
        source = self.sources.get(name)
        if source is None:
            self.cache[character] = result
            return result
        index, bundle = source
        baked = self.baked_dir / 'bangdream' / f'motion_{index:06d}.baked.json'
        if not baked.is_file():
            print(f'[bangdream] Missing default pose bake: {baked} ({name})', flush=True)
            self.cache[character] = result
            return result
        data = json.loads(baked.read_text(encoding='utf-8'))
        _filter_placeholders(data)
        UnityPy.config.FALLBACK_UNITY_VERSION = UNITY_VERSION
        program = controller_program(bundle, data) or _simple_program(data)
        layer = next(layer for layer in program['layers'] if layer['id'] == program['baseLayer'])
        state = next(state for state in layer['states'] if state['id'] == layer['initialState'])
        clip = next(clip for field in ('clips', 'auxiliaryClips') for clip in data.get(field, [])
                    if clip.get('id') == state['clip'])
        result['idlePose'] = sample_baked_pose(baked, clip['name'], 0)
        self.cache[character] = result
        return result
