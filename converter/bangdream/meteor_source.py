"""Read raw Meteor material and renderer inputs for the character converter.

The snapshots retain Unity's saved fields and pointer identities. Color/vector
meaning, Shader defaults and GPU bindings are resolved by the material exporter.
"""
from __future__ import annotations

from numbers import Integral, Real
from typing import Any


# Source corpus: collection Shader objects and embedded URP/Lit, indexed by
# shader-source.md and the retained shader-core material matrix.
SHADER_NAMES = {
    -5077109074445152229: "Meteor/MeteorShader",
    -1458684833486557259: "Meteor/MeteorShaderOffset",
    -694225609340431268: "Meteor/MeteorShaderTransparent",
    -2437954453210527100: "Universal Render Pipeline/Lit",
}


def _integer(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral):
        raise TypeError(f"{label} must be an integer")
    return int(value)


def _number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{label} must be numeric")
    return float(value)


def pointer_snapshot(pointer: Any) -> dict[str, int] | None:
    """Copy a PPtr without dereferencing it, including an explicit PathID zero."""
    if pointer is None:
        return None
    result = {"path_id": _integer(pointer.m_PathID, "PPtr PathID")}
    if hasattr(pointer, "m_FileID"):
        result["file_id"] = _integer(pointer.m_FileID, "PPtr FileID")
    return result


def shader_snapshot(pointer: Any, *, require_known: bool = False) -> dict[str, Any]:
    """Identify only the four Shader identities proven for this source corpus."""
    identity = pointer_snapshot(pointer)
    name = SHADER_NAMES.get(identity["path_id"]) if identity is not None else None
    if name is None and require_known:
        raise ValueError(f"Unrecognized BanG Dream Shader pointer: {identity}")
    return {"pointer": identity, "name": name}


def _components(value: Any, names: str, label: str) -> list[float]:
    return [_number(getattr(value, name), f"{label}.{name}") for name in names]


def _named_values(entries: Any, convert, label: str) -> list[dict[str, Any]]:
    # Lists preserve source order and even duplicate property names. A dict
    # would silently replace an earlier serialized value.
    return [{"name": str(getattr(name, "name", name)), "value": convert(value, label)}
            for name, value in entries]


def _texture_env(value: Any, label: str) -> dict[str, Any]:
    result = {}
    if hasattr(value, "m_Texture"):
        result["texture"] = pointer_snapshot(value.m_Texture)
    if hasattr(value, "m_Scale"):
        result["scale"] = _components(value.m_Scale, "xy", f"{label}.scale")
    if hasattr(value, "m_Offset"):
        result["offset"] = _components(value.m_Offset, "xy", f"{label}.offset")
    return result


def material_snapshot(material: Any, *, require_known_shader: bool = False) -> dict[str, Any]:
    """Copy saved Material inputs; absent serialized fields remain absent.

    Unity stores Color and Vector properties together in ``m_Colors``. Their
    original RGBA slots stay in that source field until Shader property types
    determine their interpretation. No linearization or half narrowing occurs.
    """
    result: dict[str, Any] = {}
    if hasattr(material, "m_Name"):
        result["name"] = str(material.m_Name)
    if hasattr(material, "m_Shader"):
        result["shader"] = shader_snapshot(material.m_Shader, require_known=require_known_shader)
    elif require_known_shader:
        raise ValueError("Material has no serialized Shader pointer")
    if hasattr(material, "m_CustomRenderQueue"):
        result["custom_render_queue"] = _integer(material.m_CustomRenderQueue, "custom render queue")
    for field in ("m_ValidKeywords", "m_InvalidKeywords"):
        if hasattr(material, field):
            values = getattr(material, field)
            if isinstance(values, str):
                raise TypeError(f"{field} must be a sequence of keyword strings")
            if any(not isinstance(value, str) for value in values):
                raise TypeError(f"{field} must contain keyword strings")
            result[field] = list(values)
    if hasattr(material, "disabledShaderPasses"):
        disabled = material.disabledShaderPasses
        if not isinstance(disabled, (list, tuple)) or any(not isinstance(value, str) for value in disabled):
            raise TypeError("disabledShaderPasses must contain LightMode tag strings")
        result["disabledShaderPasses"] = list(disabled)
    if hasattr(material, "m_ShaderKeywords"):
        # The raw field can exist alongside the valid/invalid arrays in source
        # serialization. Keep its spelling and whitespace without interpreting it.
        result["m_ShaderKeywords"] = material.m_ShaderKeywords
    if hasattr(material, "m_SavedProperties"):
        properties = material.m_SavedProperties
        saved = {}
        converters = {
            "m_Floats": _number,
            "m_Ints": _integer,
            "m_Colors": lambda value, label: _components(value, "rgba", label),
            "m_Vectors": lambda value, label: _components(value, "xyzw", label),
            "m_TexEnvs": _texture_env,
        }
        for field, convert in converters.items():
            if hasattr(properties, field):
                saved[field] = _named_values(getattr(properties, field), convert, field)
        result["saved_properties"] = saved
    return result


def renderer_snapshot(renderer: Any, *, game_object: Any = None) -> dict[str, Any]:
    """Copy renderer membership and original material slots, without adaptation."""
    result: dict[str, Any] = {}
    if hasattr(renderer, "m_Enabled"):
        value = renderer.m_Enabled
        if not isinstance(value, (bool, Integral)) or value not in (0, 1):
            raise TypeError("Renderer enabled must be a boolean or serialized 0/1")
        result["enabled"] = bool(value)
    if hasattr(renderer, "m_Materials"):
        result["materials"] = [pointer_snapshot(pointer) for pointer in renderer.m_Materials]
    if hasattr(renderer, "m_GameObject"):
        pointer = renderer.m_GameObject
        identity = pointer_snapshot(pointer)
        result["game_object"] = identity
        if game_object is None and identity is not None and identity["path_id"] != 0:
            game_object = pointer.deref_parse_as_object()
    if game_object is not None:
        if hasattr(game_object, "m_Name"):
            result["game_object_name"] = str(game_object.m_Name)
        if hasattr(game_object, "m_Layer"):
            layer = _integer(game_object.m_Layer, "GameObject layer")
            if not 0 <= layer <= 31:
                raise ValueError("GameObject layer must be in 0..31")
            result["layer"] = layer
        if hasattr(game_object, "m_IsActive"):
            result["active"] = bool(game_object.m_IsActive)
    return result
