"""Export observed Meteor Material draws through the standard GLB contract."""
from __future__ import annotations

import math
from numbers import Real
from types import SimpleNamespace

from converter.common.unity import object_id
from .meteor_material_mapping import MaterialCategory
from .meteor_passes import SOURCE_CONTRACTS, resolve_meteor_passes
from .meteor_source import material_snapshot
from .meteor_texture import extract_matcap_image, extract_raw_mip_chain
from .meteor_uniform_data import UNIFORM_DATA
from .meteor_uniforms import resolve_meteor_uniforms


_SHADER_NAMES = {
    'Meteor/MeteorShader': 'garupa-meteor',
    'Meteor/MeteorShaderOffset': 'garupa-meteor-offset',
    'Meteor/MeteorShaderTransparent': 'garupa-meteor-transparent',
    'Universal Render Pipeline/Lit': 'garupa-urp-lit',
}


class _MatCapTexture:
    """Private selected-mip image with a distinct builder-cache identity."""

    def __init__(self, source, image):
        self._source = source
        self.image = image
        self.m_MipCount = 1
        self.m_Width, self.m_Height = image.size
        self.object_reader = SimpleNamespace(assets_file=object(), path_id=source.object_reader.path_id)

    def __getattr__(self, name):
        return getattr(self._source, name)


def _texture_environments(source):
    result = {}
    for raw_name, environment in source.m_SavedProperties.m_TexEnvs:
        name = str(getattr(raw_name, 'name', raw_name))
        if name in result:
            raise ValueError(f'Ambiguous original texture property {name}')
        result[name] = environment
    return result


def _repeat(texture):
    settings = texture.m_TextureSettings
    if settings.m_WrapU != 0 or settings.m_WrapV != 0:
        raise ValueError(f'Meteor texture {texture.m_Name!r} requires original Repeat wrap U/V; '
                         f'found {settings.m_WrapU}/{settings.m_WrapV}')


class MeteorMaterialExporter:
    def __init__(self, builder):
        self.builder = builder
        self._matcaps = {}
        self._raw_mips = set()
        # Conversion-time association for auditing/patching an existing GLB.
        self.texture_sources = {}
        self.diagnostics = []

    def adapt_material(self, source_material, gltf_material):
        snapshot = material_snapshot(source_material, require_known_shader=True)
        resolved_passes = resolve_meteor_passes(snapshot)
        pass_ids = [p['id'] for p in resolved_passes['passes']]
        resolved_uniforms = resolve_meteor_uniforms(snapshot, pass_ids=pass_ids)
        params = resolved_uniforms['shaderParams']
        shader = snapshot['shader']['name']
        keywords = sorted(set(snapshot['m_ValidKeywords']))
        combination = next(c for c in UNIFORM_DATA['shaders'][shader] if c['keywords'] == keywords)
        setup = getattr(source_material, '_meteor_setup', None)
        if setup is not None and not isinstance(setup, MaterialCategory):
            raise TypeError('_meteor_setup must be the evidenced MaterialCategory')
        if setup is not None and setup.force_specular_blend_7 and '_SpecularColorBlendMethod' in params:
            params['_SpecularColorBlendMethod'] = 7

        passes = resolved_passes['passes']
        for entry in passes:
            entry['extras']['materialKeywords'] = keywords.copy()
            if (setup is not None and setup.category == 'face'
                    and '_FaceFrontX' in combination['uniforms_by_pass'][entry['id']]):
                entry['extras']['faceLighting'] = True

        textures = {}
        for pass_id in pass_ids:
            for binding in combination['textures_by_pass'][pass_id]:
                previous = textures.get(binding['uniform'])
                if previous is not None and previous != binding:
                    raise ValueError(f'Conflicting actual texture sampler binding {binding["uniform"]}')
                textures[binding['uniform']] = binding
        environments = _texture_environments(source_material)
        exported = {}
        for uniform, binding in sorted(textures.items()):
            if not uniform.startswith('u') or len(uniform) == 1:
                raise ValueError(f'Invalid transcribed sampler uniform {uniform}')
            name = binding['texture']
            environment = environments.get(name)
            pointer = getattr(environment, 'm_Texture', None) if environment is not None else None
            if pointer is None or pointer.m_PathID == 0:
                # The actual shaders' required material samplers all declare
                # white. The Shader resource keeps that default; no fake PPtr,
                # white PNG or material-level default marker is emitted here.
                if SOURCE_CONTRACTS[shader]['properties'][name]['default'] != '"white" { }':
                    raise ValueError(f'Unbound required texture {name} has an unsupported original default')
                if name == '_MatCapMap':
                    params['_MatCapSourceMip'] = 0
                continue
            texture = pointer.deref_parse_as_object()
            _repeat(texture)
            if name == '_MatCapMap':
                level = params.get('_MatCapBlurLevel')
                if (isinstance(level, bool) or not isinstance(level, Real) or not math.isfinite(level)
                        or level < 0 or int(level) != level):
                    raise ValueError('Bound MatCap requires an actually read nonnegative integral _MatCapBlurLevel')
                level = int(level)
                cache_key = (*object_id(texture), level)
                if cache_key not in self._matcaps:
                    self._matcaps[cache_key] = _MatCapTexture(texture, extract_matcap_image(texture, level))
                texture = self._matcaps[cache_key]
                params['_MatCapSourceMip'] = level
            if binding['type'] != 'sampler2D':
                raise ValueError(f'Unsupported actual material sampler type {binding["type"]}')
            texture_index = self.builder.add_image(texture)
            self.texture_sources[texture_index] = texture
            if name != '_MatCapMap' and texture_index not in self._raw_mips:
                self.builder.add_raw_mip_chain(texture_index, extract_raw_mip_chain(texture), compression='deflate')
                self._raw_mips.add(texture_index)
            exported[uniform[1:]] = texture_index

        # Only runtime data is published. Property/default/type evidence and raw
        # Unity pointers stay in the conversion process.
        gltf_material['extras'] = {'shader': _SHADER_NAMES[shader], 'shaderParams': params,
            'renderState': resolved_passes['renderState'], 'passes': passes, 'textures': exported}
        self.diagnostics.append({'material': snapshot.get('name'),
            'pass_states': resolved_passes['diagnostics'], 'uniform_types': resolved_uniforms['uniformTypes']})
