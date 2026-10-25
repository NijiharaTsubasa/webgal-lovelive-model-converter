"""Resolve only material uniforms actually read by observed native variants.

Original PlayerSettings.m_ActiveColorSpace=1 is recorded in the project-local
validation/source-color-space.json. Color RGB therefore requires the original
Unity gamma-to-linear conversion; alpha, Float and Vector are not transformed.
No global/per-draw value is inferred here and no half narrowing is performed.
"""
from __future__ import annotations

import copy
import math
from numbers import Real

from .meteor_passes import SOURCE_CONTRACTS, resolve_meteor_passes
from .meteor_uniform_data import UNIFORM_DATA
from .meteor_color import unity_gamma_to_linear


class UnresolvedMaterialUniform(ValueError):
    """The required original value or numeric conversion is not recovered."""


def _number(value, label):
    if isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(value):
        raise ValueError(f"{label} must be a finite numeric value")
    return value


def _entry(snapshot, name, allowed_fields):
    matches = [(field, row['value'])
               for field, entries in snapshot.get('saved_properties', {}).items()
               for row in entries if row['name'] == name]
    if len(matches) > 1:
        raise ValueError(f"Ambiguous saved property {name}")
    if matches and matches[0][0] not in allowed_fields:
        raise ValueError(f"Saved field {matches[0][0]} is incompatible with {name}")
    return (bool(matches), matches[0][1] if matches else None)


def _required(snapshot, pass_ids=None):
    shader = snapshot.get('shader', {}).get('name')
    if shader not in UNIFORM_DATA['shaders']:
        raise ValueError(f"Unrecognized original Shader: {shader}")
    keywords = snapshot.get('m_ValidKeywords')
    if not isinstance(keywords, list) or any(not isinstance(k, str) or not k for k in keywords):
        raise ValueError('Missing or invalid explicit m_ValidKeywords')
    keywords = sorted(set(keywords))
    matches = [r for r in UNIFORM_DATA['shaders'][shader] if r['keywords'] == keywords]
    if len(matches) != 1:
        raise ValueError(f"Unobserved original Material keyword combination: {shader} {keywords}")
    combination = matches[0]
    if pass_ids is None:
        pass_ids = [p['id'] for p in resolve_meteor_passes(snapshot)['passes']]
    if not isinstance(pass_ids, (list, tuple)) or not pass_ids or any(not isinstance(p, str) or not p for p in pass_ids):
        raise ValueError('pass_ids must be a nonempty sequence of original stable Pass IDs')
    if len(set(pass_ids)) != len(pass_ids):
        raise ValueError('pass_ids contains duplicate original Pass IDs')
    for pass_id in pass_ids:
        if pass_id not in combination['uniforms_by_pass']:
            raise ValueError(f'Unknown original Pass ID for {shader}: {pass_id}')
    return shader, sorted({field for p in pass_ids for field in combination['uniforms_by_pass'][p]})


def _property_value(snapshot, shader, field):
    if field.endswith('_ST'):
        texture = field[:-3]
        declaration = SOURCE_CONTRACTS[shader]['properties'].get(texture)
        if declaration is None or declaration['type'] not in ('2D', '2DArray'):
            raise UnresolvedMaterialUniform(f"Unresolved original texture property for {field}")
        found, env = _entry(snapshot, texture, ('m_TexEnvs',))
        if not found or not isinstance(env, dict) or 'scale' not in env or 'offset' not in env:
            raise UnresolvedMaterialUniform(f"Missing original saved scale/offset for {field}; no evidenced implicit ST default")
        values = []
        for name in ('scale', 'offset'):
            vector = env[name]
            if not isinstance(vector, list) or len(vector) != 2:
                raise ValueError(f"{texture}.{name} must contain two components")
            values.extend(_number(v, field) for v in vector)
        return values, 'Vector'
    declaration = SOURCE_CONTRACTS[shader]['properties'].get(field)
    if declaration is None:
        raise UnresolvedMaterialUniform(f"No original ShaderLab declaration/default for {shader} {field}")
    kind, default = declaration['type'], declaration['default']
    if kind in ('Float', 'Int') or kind.startswith('Range('):
        found, value = _entry(snapshot, field, ('m_Floats', 'm_Ints'))
        return _number(value if found else float(default), field), kind
    if kind in ('Color', 'Vector'):
        found, value = _entry(snapshot, field, ('m_Colors', 'm_Vectors'))
        if not found:
            value = [float(v.strip()) for v in default.strip('()').split(',')]
        if not isinstance(value, list) or len(value) != 4:
            raise ValueError(f"Declared {kind} {field} requires four original components")
        return [_number(v, field) for v in value], kind
    raise ValueError(f"Unsupported source property type {kind} for material uniform {field}")


def resolve_meteor_uniforms(material_snapshot, *, pass_ids=None, color_to_linear=unity_gamma_to_linear):
    """Return shaderParams and separate conversion-only uniformTypes.

    Required fields are the union of actual UnityPerMaterial read sites across
    every candidate program of every provided Pass for this observed material
    keyword set, including confirmed native fallback selections. Global keyword
    branches are all represented; no first-candidate selection is performed.
    By default provided Pass IDs come from resolve_meteor_passes(snapshot), so
    disabled LightModes do not contribute reads. pass_ids may reuse a caller's
    already-resolved nonempty provided-Pass list without resolving states twice.

    The default color provider uses the finite 191-input native CPU probe table;
    see meteor_color.py for its f2-versus-source-f1/backend evidence boundary.
    Unknown inputs fail instead of substituting an assumed sRGB/HDR formula.
    Only shaderParams belongs in published Material extras.
    """
    shader, required = _required(material_snapshot, pass_ids)
    params, types = {}, {}
    for field in required:
        signature = UNIFORM_DATA['fields'][field]
        if signature['array'] is not None:
            raise ValueError(f"Material uniform array export is not implemented: {field}")
        raw, property_type = _property_value(material_snapshot, shader, field)
        if property_type == 'Color':
            if color_to_linear is None:
                raise UnresolvedMaterialUniform(f"Original Unity Color RGB conversion required for {field}")
            raw = [_number(color_to_linear(v), field) for v in raw[:3]] + raw[3:]
        width, scalar_type = signature['width'], signature['type']
        if width == 1:
            if isinstance(raw, list):
                raise ValueError(f"Scalar uniform {field} cannot consume a vector property")
            value = raw
        else:
            if not isinstance(raw, list) or len(raw) < width:
                raise ValueError(f"Uniform {field} requires original width {width}")
            value = raw[:width]
        values = value if isinstance(value, list) else [value]
        if scalar_type == 'int':
            if any(int(v) != v or not -(2**31) <= v < 2**31 for v in values):
                raise UnresolvedMaterialUniform(f"Nonintegral/out-of-range source value for int uniform {field}")
            value = [int(v) for v in values] if isinstance(value, list) else int(value)
        elif scalar_type not in ('float', 'half'):
            raise ValueError(f"Unsupported original scalar type {scalar_type}")
        params[field] = value
        types[field] = copy.deepcopy(signature)
    return {'shaderParams': params, 'uniformTypes': types}
