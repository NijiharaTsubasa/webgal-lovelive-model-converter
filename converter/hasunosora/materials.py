"""Read effective Pass states, not similarly named stale material properties."""
from __future__ import annotations

import re
from typing import Any


FORWARD_PASSES = {
    'melpot-toon': 'ForwardLit', 'melpot-toon-hlslmacros': 'ForwardLit',
    'melpot-toon-eye': 'Forward', 'character-eye': 'Forward',
    'character-highlight': 'Forward', 'highlight-distortion': 'Universal Forward',
    'urp-lit': 'ForwardLit',
}


def source_render_states(material: Any, kind: str) -> tuple[int, dict[str, dict]]:
    shader = material.m_Shader.deref_parse_as_object().m_ParsedForm
    subshader = shader.m_SubShaders[0]
    values = {p.m_Name: p.m_DefValue_0_ for p in shader.m_PropInfo.m_Props}
    values.update({str(getattr(k, 'name', k)): v for k, v in material.m_SavedProperties.m_Floats})
    values.update({str(getattr(k, 'name', k)): v for k, v in (getattr(material.m_SavedProperties, 'm_Ints', None) or [])})

    def resolve(binding):
        if binding.name and binding.name != '<noninit>':
            return float(values[binding.name])
        return float(binding.val)

    queue = int(material.m_CustomRenderQueue)
    if queue == -1:
        tag = dict(subshader.m_Tags.tags).get('QUEUE', 'Geometry')
        match = re.fullmatch(r'(Background|Geometry|AlphaTest|Transparent|Overlay)\s*([+-]\s*\d+)?', tag)
        if match:
            queue = {'Background': 1000, 'Geometry': 2000, 'AlphaTest': 2450,
                     'Transparent': 3000, 'Overlay': 4000}[match[1]]
            queue += int((match[2] or '0').replace(' ', ''))
        else:
            queue = int(tag)

    states = {}
    for shader_pass in subshader.m_Passes:
        state = shader_pass.m_State
        if state.m_Name == FORWARD_PASSES[kind]:
            pass_id = 'Forward'
        elif state.m_Name == 'Outline':
            pass_id = 'Outline'
        else:
            continue
        blend = state.rtBlend0
        # Shipped Hasunosora passes use one Stencil block. The serialized
        # front/back blocks are default placeholders; bindings are in stencilOp.
        stencil = state.stencilOp
        states[pass_id] = {
            'cull': resolve(state.culling), 'zWrite': resolve(state.zWrite),
            'zTest': resolve(state.zTest), 'alphaToMask': resolve(state.alphaToMask),
            'colorMask': int(resolve(blend.colMask)),
            'offset': {'factor': resolve(state.offsetFactor), 'units': resolve(state.offsetUnits)},
            'blend': {key: resolve(getattr(blend, attr)) for key, attr in (
                ('srcRgb', 'srcBlend'), ('dstRgb', 'destBlend'),
                ('srcAlpha', 'srcBlendAlpha'), ('dstAlpha', 'destBlendAlpha'),
                ('opRgb', 'blendOp'), ('opAlpha', 'blendOpAlpha'))},
            'stencil': {
                'ref': resolve(state.stencilRef), 'readMask': resolve(state.stencilReadMask),
                'writeMask': resolve(state.stencilWriteMask),
                **{key: resolve(getattr(stencil, attr)) for key, attr in (
                    ('comp', 'comp'), ('pass', 'pass_'), ('fail', 'fail'), ('zFail', 'zFail'))},
            },
        }
    return queue, states


def adapt_material(material: Any, result: dict) -> None:
    extras = result['extras']
    queue, states = source_render_states(material, extras['shader'])
    forward = states['Forward']
    extras['renderState'] = {'renderQueue': queue, **forward}
    for entry in extras['passes']:
        overrides = {key: value for key, value in states[entry['id']].items() if value != forward[key]}
        entry.pop('renderState', None)
        if overrides:
            entry['renderState'] = overrides
