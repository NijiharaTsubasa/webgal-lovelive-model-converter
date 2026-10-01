from __future__ import annotations

from typing import Any


def shader_kind(floats: dict[str, float], colors: dict[str, Any], textures: dict[str, Any]) -> str | None:
    """Identify which reverse-engineered shader a material uses by its property
    fingerprint (the shader objects themselves do not resolve by name).

    Order matters: MELPOT/Toon always sets the shadow-ramp step, the lens uses
    _DistortionIntensity, the highlight sets the cry/noise params or
    _HighlightMainColor, and the plain eye base is left over (main tex + main
    color but no toon step). Returns one of:
    "melpot-toon", "character-eye", "character-highlight", "highlight-distortion"."""
    if "_1stShadowStep" in floats:
        return "melpot-toon"
    if "_DistortionIntensity" in floats:
        return "highlight-distortion"
    if "_Cry_TilingFrequency" in floats or "_HighlightMainColor" in colors:
        return "character-highlight"
    if "_MainTex" in textures and "_MainColor" in colors:
        return "character-eye"
    return None


def renderer_uses_eye_shader(renderer: Any) -> bool:
    for pointer in getattr(renderer, "m_Materials", []):
        if not pointer:
            continue
        try:
            material = pointer.deref_parse_as_object()
        except (FileNotFoundError, ValueError):
            continue
        colors = {str(getattr(k, "name", k)): v for k, v in material.m_SavedProperties.m_Colors}
        textures = {str(getattr(k, "name", k)): v for k, v in material.m_SavedProperties.m_TexEnvs}
        floats = {str(getattr(k, "name", k)): float(v) for k, v in material.m_SavedProperties.m_Floats}
        if shader_kind(floats, colors, textures) in {
            "character-eye", "character-highlight", "highlight-distortion",
        }:
            return True
    return False