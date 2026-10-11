"""BX material inputs and fixed states for the retained compiled programs."""
from __future__ import annotations

import json
from pathlib import Path

PROGRAMS = json.loads(Path(__file__).with_name('shader-programs.json').read_text(encoding='utf-8'))
SHADERS = {
    'URP/BX/Toon': 'yohane-toon',
    'URP/BX/Toon-DoubleSide': 'yohane-toon-double-side',
    'URP/BX/ef_outline_aura_generated': 'yohane-aura',
}


def shader_programs(source_name, keywords):
    if source_name not in SHADERS:
        raise ValueError(f'Unsupported active Yohane Shader: {source_name}')
    keywords = set(keywords)
    # Forward has no compiled FLATNORMAL branch. It affects DepthNormals only.
    ignored = {'_FLATNORMAL_ON'} if source_name != 'URP/BX/ef_outline_aura_generated' else set()
    features = keywords - ignored
    candidates = [entry for entry in PROGRAMS if entry['source'] == source_name and entry['purpose'] == 'color'
                  and set(entry['keywords']) == features]
    expected = 2 if source_name.endswith('Toon-DoubleSide') else 1
    if len(candidates) != expected:
        raise ValueError(f'{source_name}: unrecovered material keywords {sorted(keywords)}')
    return sorted(candidates, key=lambda entry: entry['passIndex'])


def auxiliary_programs(source_name, keywords):
    features = set(keywords) & {'_ALPHATEST_ON', '_FLATNORMAL_ON'}
    result = {}
    for purpose in ('DepthNormals', 'ShadowCaster'):
        selected = features if purpose == 'DepthNormals' else features - {'_FLATNORMAL_ON'}
        candidates = [entry for entry in PROGRAMS if entry['source'] == source_name
                      and entry['purpose'] == purpose and set(entry['keywords']) == selected]
        if len(candidates) > 1:
            raise ValueError(f'{source_name}: ambiguous {purpose} variant')
        if candidates:
            result[purpose] = candidates[0]
    return result


def unity_material_vector(channels, property_type, flags):
    # Unity Material uploads HDR Color and ordinary Vector unchanged. Ordinary
    # Color / Gamma Vector apply GammaToLinearSpace to RGB, preserving alpha.
    linearize = (property_type == 0 and not flags & 16) or (property_type == 1 and flags & 32)
    if not linearize:
        return channels
    def linear(value):
        if value <= 0.04045:
            return value / 12.92
        if value < 1.0:
            return ((value + 0.055) / 1.055) ** 2.4
        return value ** 2.2
    return [*(linear(value) for value in channels[:3]), channels[3]]


def material_extras(material, builder):
    shader = material.m_Shader.deref_parse_as_object()
    parsed = shader.object_reader.read_typetree()['m_ParsedForm']
    source_name = parsed['m_Name']
    programs = shader_programs(source_name, material.m_ValidKeywords)
    auxiliary = auxiliary_programs(source_name, material.m_ValidKeywords)
    properties = {p['m_Name']: p for p in parsed['m_PropInfo']['m_Props']}
    saved = material.m_SavedProperties
    floats = {str(key): float(value) for key, value in saved.m_Floats}
    colors = {str(key): value for key, value in saved.m_Colors}
    textures = {str(key): value for key, value in saved.m_TexEnvs}

    def scalar(name):
        if name in floats:
            return floats[name]
        if name in properties:
            return properties[name]['m_DefValue[0]']
        raise ValueError(f'{material.m_Name}: missing source parameter {name}')

    uniforms = {u['original']: u for program in [*programs, *auxiliary.values()] for u in program['uniforms']}
    params, tex = {}, {}
    for source, uniform in uniforms.items():
        slot = uniform['name'][1:]
        if uniform['type'] == 'sampler2D':
            environment = textures.get(source)
            if environment and environment.m_Texture:
                tex[slot] = builder.add_image(environment.m_Texture.deref_parse_as_object())
        elif source.endswith('_ST'):
            environment = textures.get(source[:-3])
            params[slot] = ([float(environment.m_Scale.x), float(environment.m_Scale.y),
                             float(environment.m_Offset.x), float(environment.m_Offset.y)]
                            if environment else [1.0, 1.0, 0.0, 0.0])
        elif uniform['type'] == 'float':
            params[slot] = scalar(source)
        elif uniform['type'] == 'vec4':
            value = colors.get(source)
            definition = properties.get(source)
            if not definition:
                raise ValueError(f'{material.m_Name}: unknown vector property {source}')
            if value is None:
                channels = [definition[f'm_DefValue[{i}]'] for i in range(4)]
            else:
                channels = [float(value.r), float(value.g), float(value.b), float(value.a)]
            params[slot] = unity_material_vector(channels, definition['m_Type'], definition['m_Flags'])
        else:
            raise ValueError(f'{material.m_Name}: unsupported material uniform {uniform}')

    def state_value(field):
        name = field['name']
        return scalar(name) if name.startswith('_') else field['val']

    passes = []
    for program in programs:
        state = program['state']
        blend = state['rtBlend0']
        passes.append({'id': program['id'], 'extras': {
            **({'depthNormalsPass': auxiliary['DepthNormals']['id']} if 'DepthNormals' in auxiliary else {}),
            **({'shadowCasterPass': auxiliary['ShadowCaster']['id']} if 'ShadowCaster' in auxiliary else {}),
        }, 'renderState': {
            'cull': state_value(state['culling']),
            'zWrite': state_value(state['zWrite']),
            'zTest': state_value(state['zTest']),
            'colorMask': state_value(blend['colMask']),
            'alphaToMask': state_value(state['alphaToMask']),
            'offset': {'factor': state_value(state['offsetFactor']), 'units': state_value(state['offsetUnits'])},
            'blend': {key: state_value(blend[source]) for key, source in (
                ('srcRgb', 'srcBlend'), ('dstRgb', 'destBlend'), ('srcAlpha', 'srcBlendAlpha'),
                ('dstAlpha', 'destBlendAlpha'), ('opRgb', 'blendOp'), ('opAlpha', 'blendOpAlpha'))},
        }})
    tags = dict(parsed['m_SubShaders'][0]['m_Tags']['tags'])
    queues = {'Geometry': 2000, 'AlphaTest': 2450, 'Transparent': 3000}
    queue = material.m_CustomRenderQueue
    if queue == -1:
        tag = tags.get('Queue', 'Geometry')
        if tag not in queues:
            raise ValueError(f'{material.m_Name}: unsupported source queue {tag}')
        queue = queues[tag]
    return {'shader': SHADERS[source_name], 'programCacheKey': SHADERS[source_name],
            'shaderParams': params, 'textures': tex,
            'renderState': {'renderQueue': int(queue), 'surfaceType': scalar('_Surface')},
            'passes': passes}
