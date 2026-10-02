from __future__ import annotations

import json
import struct
from io import BytesIO
from pathlib import Path
from typing import Any, Callable, Iterable

from .shader import shader_kind
from .unity import (
    COMPONENT_FLOAT,
    COMPONENT_UNSIGNED_BYTE,
    COMPONENT_UNSIGNED_SHORT,
    COMPONENT_UNSIGNED_INT,
    object_id,
)


def mat4_transform_dir(m: list[float], v: list[float]) -> list[float]:
    """Transform a 3D direction vector by the 3x3 rotation part of a 4x4 matrix."""
    x, y, z = v
    return [
        m[0] * x + m[4] * y + m[8] * z,
        m[1] * x + m[5] * y + m[9] * z,
        m[2] * x + m[6] * y + m[10] * z,
    ]


def srgb_channel_to_linear(value: float) -> float:
    """Match the sRGB-to-linear conversion Unity applies to Color properties."""
    if value <= 0.04045:
        return value / 12.92
    return ((value + 0.055) / 1.055) ** 2.4


def unity_color_to_linear_rgba(color: Any) -> list[float]:
    """Convert Unity material Color RGB to linear while preserving alpha."""
    return [
        srgb_channel_to_linear(float(color.r)),
        srgb_channel_to_linear(float(color.g)),
        srgb_channel_to_linear(float(color.b)),
        float(color.a),
    ]


class GlbBuilder:
    def __init__(self) -> None:
        self.document: dict[str, Any] = {
            "asset": {"version": "2.0", "generator": "assetbundle-standalone-packager"},
            "scene": 0,
            "scenes": [{"nodes": []}],
            "nodes": [],
            "meshes": [],
            "skins": [],
            "materials": [],
            "textures": [],
            "images": [],
            "samplers": [],
            "animations": [],
            "bufferViews": [],
            "accessors": [],
            "buffers": [{"byteLength": 0}],
        }
        self.binary = bytearray()
        self.materials: dict[tuple[int, int], int] = {}
        self.textures: dict[tuple[int, int], int] = {}
        self.shader_classifier: Callable[[Any], str | None] | None = None
        self.material_adapter: Callable[[Any, dict], None] | None = None

    def add_view(self, data: bytes, target: int | None = None) -> int:
        while len(self.binary) % 4:
            self.binary.append(0)
        offset = len(self.binary)
        self.binary.extend(data)
        view: dict[str, Any] = {"buffer": 0, "byteOffset": offset, "byteLength": len(data)}
        if target is not None:
            view["target"] = target
        self.document["bufferViews"].append(view)
        return len(self.document["bufferViews"]) - 1

    def add_accessor(
        self,
        values: Iterable[Any],
        accessor_type: str,
        component_type: int,
        *,
        target: int | None = None,
        minimum: list[float] | None = None,
        maximum: list[float] | None = None,
    ) -> int:
        values = list(values)
        component_count = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}[accessor_type]
        fmt = {
            COMPONENT_FLOAT: "f",
            COMPONENT_UNSIGNED_BYTE: "B",
            COMPONENT_UNSIGNED_SHORT: "H",
            COMPONENT_UNSIGNED_INT: "I",
        }[component_type]
        flat: list[Any] = []
        for value in values:
            if component_count == 1:
                flat.append(value)
            else:
                flat.extend(value)
        data = struct.pack(f"<{len(flat)}{fmt}", *flat) if flat else b""
        view = self.add_view(data, target)
        accessor: dict[str, Any] = {
            "bufferView": view,
            "componentType": component_type,
            "count": len(values),
            "type": accessor_type,
        }
        if minimum is not None:
            accessor["min"] = minimum
        if maximum is not None:
            accessor["max"] = maximum
        self.document["accessors"].append(accessor)
        return len(self.document["accessors"]) - 1

    def add_image(self, texture: Any) -> int:
        key = object_id(texture)
        if key in self.textures:
            return self.textures[key]
        color_space = getattr(texture, "m_ColorSpace", None)
        if color_space not in {0, 1}:
            raise RuntimeError(
                f"Texture {texture.m_Name!r} has unsupported m_ColorSpace {color_space!r}"
            )
        settings = texture.m_TextureSettings
        wrap_modes = {0: 10497, 1: 33071, 2: 33648}
        wrap_u, wrap_v = int(settings.m_WrapU), int(settings.m_WrapV)
        if wrap_u not in wrap_modes or wrap_v not in wrap_modes:
            raise ValueError(
                f"Texture {texture.m_Name!r} has unsupported wrap mode {wrap_u}/{wrap_v}"
            )
        filter_mode, mip_count = int(settings.m_FilterMode), int(texture.m_MipCount)
        if filter_mode not in {0, 1, 2} or mip_count < 1:
            raise ValueError(
                f"Texture {texture.m_Name!r} has unsupported filtering {filter_mode}, mips {mip_count}"
            )
        # Unity Bilinear selects a mip level without interpolating between
        # levels. Only Trilinear uses LINEAR_MIPMAP_LINEAR; no-mip textures
        # must retain a non-mip minification filter.
        sampler = {
            "magFilter": 9728 if filter_mode == 0 else 9729,
            "minFilter": ((9728 if filter_mode == 0 else 9729) if mip_count == 1
                          else {0: 9984, 1: 9985, 2: 9987}[filter_mode]),
            "wrapS": wrap_modes[wrap_u],
            "wrapT": wrap_modes[wrap_v],
        }
        image = texture.image
        if image.mode not in {"RGB", "RGBA"}:
            image = image.convert("RGBA")
        output = BytesIO()
        image.save(output, format="PNG")
        view = self.add_view(output.getvalue())
        self.document["images"].append({"name": texture.m_Name, "bufferView": view, "mimeType": "image/png"})
        samplers = self.document["samplers"]
        try:
            sampler_index = samplers.index(sampler)
        except ValueError:
            sampler_index = len(samplers)
            samplers.append(sampler)
        self.document["textures"].append({
            "source": len(self.document["images"]) - 1,
            "sampler": sampler_index,
            "extras": {"colorSpace": "srgb" if color_space == 1 else "linear"},
        })
        index = len(self.document["textures"]) - 1
        self.textures[key] = index
        return index

    def add_material(self, pointer: Any) -> int:
        if not pointer:
            raise RuntimeError("Renderer submesh has no material")
        material = pointer.deref_parse_as_object()
        key = object_id(material)
        if key in self.materials:
            return self.materials[key]
        colors = {str(getattr(k, "name", k)): v for k, v in material.m_SavedProperties.m_Colors}
        textures = {str(getattr(k, "name", k)): v for k, v in material.m_SavedProperties.m_TexEnvs}
        floats = {str(getattr(k, "name", k)): float(v) for k, v in material.m_SavedProperties.m_Floats}
        color = colors.get("_BaseColor") or colors.get("_Color") or colors.get("_MainColor")
        # Custom toon shaders commonly repurpose color alpha. Preserve the alpha
        # channel only when the material declares itself transparent
        # (_SurfaceMode > 0), so opaque toon materials stay fully opaque but
        # transparent ones (e.g. EyeShadow with alpha=0) keep their transparency.
        surface_mode_raw = floats.get("_SurfaceMode", floats.get("_Surface", 0.0))
        base = [float(color.r), float(color.g), float(color.b), float(color.a) if surface_mode_raw > 0.5 else 1.0] if color else [1.0, 1.0, 1.0, 1.0]
        result: dict[str, Any] = {
            "name": material.m_Name,
            "pbrMetallicRoughness": {"baseColorFactor": base, "metallicFactor": 0.0, "roughnessFactor": 0.9},
            "doubleSided": True,
        }
        texture_env = textures.get("_MainTex") or textures.get("_MainTexture")
        if texture_env and texture_env.m_Texture:
            texture = texture_env.m_Texture.deref_parse_as_object()
            result["pbrMetallicRoughness"]["baseColorTexture"] = {"index": self.add_image(texture)}
        surface_mode = floats.get("_SurfaceMode", floats.get("_Surface", 0.0))
        alpha_clip = floats.get("_AlphaClip", floats.get("_AlphaTest", 0.0))
        render_queue = int(getattr(material, "m_CustomRenderQueue", -1))
        if surface_mode > 0.5 or render_queue >= 3000:
            result["alphaMode"] = "BLEND"
        elif alpha_clip > 0.5 or 2450 <= render_queue < 3000:
            result["alphaMode"] = "MASK"
            result["alphaCutoff"] = floats.get("_AlphaClipThreshold", floats.get("_Cutoff", 0.5))
        self.document["materials"].append(result)
        index = len(self.document["materials"]) - 1
        self.materials[key] = index
        kind = (
            self.shader_classifier(material)
            if self.shader_classifier is not None
            else shader_kind(floats, colors, textures)
        )
        if kind in {"melpot-toon", "melpot-toon-hlslmacros", "melpot-toon-eye", "urp-lit"}:
            # glTF and Three.js expect base-color factors in linear space. Unity
            # stores Color properties as sRGB values and converts them before
            # passing them to a shader, so preserve that behavior on export.
            result["pbrMetallicRoughness"]["baseColorFactor"][:3] = [
                srgb_channel_to_linear(channel) for channel in base[:3]
            ]
        if kind == "urp-lit":
            result["pbrMetallicRoughness"]["metallicFactor"] = floats.get("_Metallic", 0.0)
            result["pbrMetallicRoughness"]["roughnessFactor"] = 1.0 - floats.get("_Smoothness", 0.5)
            result["doubleSided"] = floats.get("_Cull", 2.0) == 0.0
            result["extras"] = self._urp_lit_extras(material, floats)
        elif kind in {"melpot-toon", "melpot-toon-hlslmacros"}:
            melpot_extras = self._melpot_extras(material, colors, textures, floats, shader_name=kind)
            if melpot_extras:
                result["extras"] = melpot_extras
            if kind == "melpot-toon":
                # The source Forward program samples _MainTex through
                # _MainTex_ST. Three owns the glTF base-color sampler, so use
                # glTF's texture-transform extension for that one sampler;
                # the other source samplers use shaderParams ST uniforms.
                main_env = textures.get("_MainTex")
                base_info = result["pbrMetallicRoughness"].get("baseColorTexture")
                if main_env and main_env.m_Texture and base_info:
                    st = self._unity_texture_st(main_env)
                    if st != [1.0, 1.0, 0.0, 0.0]:
                        base_info["extensions"] = {"KHR_texture_transform": {
                            "offset": st[2:], "scale": st[:2],
                        }}
                        used = self.document.setdefault("extensionsUsed", [])
                        if "KHR_texture_transform" not in used:
                            used.append("KHR_texture_transform")
        elif kind:
            extras = self._eye_extras(material, colors, textures, floats, kind)
            if extras:
                result["extras"] = extras
        if self.material_adapter is not None:
            self.material_adapter(material, result)
        return index

    @staticmethod
    def _urp_lit_extras(material: Any, floats: dict[str, float]) -> dict[str, Any]:
        extras: dict[str, Any] = {
            "shader": "urp-lit",
            "programCacheKey": f"urp-lit:{material.m_Name}",
            "shaderParams": {
                "Metallic": floats["_Metallic"],
                "Smoothness": floats["_Smoothness"],
            },
            "renderState": {
                "cull": floats["_Cull"],
                "zWrite": floats["_ZWrite"],
                "renderQueue": 2000 if material.m_CustomRenderQueue == -1 else int(material.m_CustomRenderQueue),
            },
            "passes": [{"id": "Forward"}],
        }
        return extras

    @staticmethod
    def _unity_texture_st(texture_env: Any) -> list[float]:
        scale = texture_env.m_Scale
        offset = texture_env.m_Offset
        return [float(scale.x), float(scale.y), float(offset.x), float(offset.y)]

    def _melpot_extras(
        self, material: Any, colors: dict[str, Any], textures: dict[str, Any],
        floats: dict[str, float], *, shader_name: str = "melpot-toon",
    ) -> dict[str, Any]:
        """Carry the reverse-engineered MELPOT/Toon material data into the GLB so the
        web preview can reproduce the original toon shading.

        Structure (same shape as _eye_extras — both feed the generic binder):
            extras.shader         = "melpot-toon"         (dispatch id)
            extras.programCacheKey = "<shader>:<mat_name>"  (three.js cache key)
            extras.shaderParams   = { ... }               (shared uniform params)
            extras.textures       = { slot: texIndex }    (texture slot → glTF index;
                                                           texture.extras.colorSpace required)
            extras.renderState    = { ... }               (generic render state)
            extras.passes         = [{ id, ...overrides }] (ordered pass plan)

        Keys drop the leading '_'. Only present when the material actually
        assigns them. The MELPOT UberToon shader is identified by its
        shadow-ramp step property; materials from OTHER shaders (e.g. the
        CharacterEye/Highlight eye shaders) share a few outline props but
        are NOT UberToon and must not be tagged."""
        if "_1stShadowStep" not in floats:
            return {}
        extras: dict[str, Any] = {"shader": shader_name}
        mat_name = str(getattr(material, "m_Name", ""))
        extras["programCacheKey"] = f"{shader_name}:{mat_name}"
        tex_slots: list[str] = [
            "_1stShadowTex", "_2ndShadowTex", "_ControlMap1", "_ControlMap2",
            "_NormalTex", "_MatcapTex", "_GlossMap", "_DetailMask", "_UVTexMask",
        ]
        if shader_name == "melpot-toon-hlslmacros":
            tex_slots.insert(0, "_MainTex")
        texture_indices: dict[str, int] = {}
        for slot in tex_slots:
            texture_env = textures.get(slot)
            if not (texture_env and texture_env.m_Texture):
                continue
            texture = texture_env.m_Texture.deref_parse_as_object()
            texture_indices[slot.lstrip("_")] = self.add_image(texture)
        if texture_indices:
            extras["textures"] = texture_indices
        # Shader params (uniforms — NOT render state)
        float_params: list[str] = [
            "_1stShadowStep", "_1stShadowFather", "_2ndShadowStep", "_2ndShadowFather",
            "_ReceiveShadowMappingAmount", "_ShadowBorderRange", "_RimPower", "_RimSmoothness",
            "_SpecularPower", "_SpecularSmoothness", "_MatcapBlendLevel", "_AddIntensity",
            "_MainLightIntensity", "_OverrideMainLightColor", "_NormalScale", "_AmbientMode",
            "_Transparency", "_AlphaClipThreshold", "_UVintensity",
            "_SphericalNormalCorrect", "_AffectedRimByShadowStep", "_AffectedMatcapByShadowStep",
            "_AffectedSpecularByShadowStep", "_AffectedAnisotropicByShadowStep",
            "_AnisotropicSmoothness", "_JitterIntensity",
        ]
        if shader_name == "melpot-toon-hlslmacros":
            float_params.extend(["_IsShadeEmissionLightColorContribution", "_AlphaClipThreshold"])
        outline_float_params: list[str] = [
            "_OutlineWidth", "_OutlineDistance",
            "_OutlineClipThreshold", "_OutlineMaskScale", "_OutlineBlendFinalColor",
            "_ReceiveShadowMappingAmount",
        ]
        shader_params: dict[str, Any] = {}
        outline_params: dict[str, Any] = {}

        # Main-pass floats
        for prop in float_params:
            if prop in floats:
                shader_params[prop.lstrip("_")] = floats[prop]
        # Outline-pass floats
        for prop in outline_float_params:
            if prop in floats:
                outline_params[prop.lstrip("_")] = floats[prop]

        # Main-pass colors (OutlineColor is split out below)
        color_params: list[str] = [
            "_MainColor", "_1stShadowColor", "_2ndShadowColor", "_ShadowBorderColor",
            "_RimColor", "_SpecularColor", "_MatcapColor", "_UVColor", "_AnisotropicColor",
            "_KeyLightColor", "_AmbientColor",
        ]
        vector_params: list[str] = [
            "_MainLightOffset", "_AnisotropicIntensity",
            "_SpecularXScaleYOffset", "_InverseNormal",
            "_SphericalNormalCorrectOrigin",
        ]
        for prop in color_params:
            if prop not in colors:
                continue
            c = colors[prop]
            shader_params[prop.lstrip("_")] = unity_color_to_linear_rgba(c)
        for prop in vector_params:
            if prop not in colors:
                continue
            value = colors[prop]
            shader_params[prop.lstrip("_")] = [
                float(value.r), float(value.g), float(value.b), float(value.a),
            ]
        if shader_name == "melpot-toon":
            for slot in ("_MainTex", "_DetailMask", "_GlossMap", "_UVTexMask"):
                texture_env = textures.get(slot)
                shader_params[f"{slot.lstrip('_')}_ST"] = (
                    self._unity_texture_st(texture_env) if texture_env is not None
                    else [1.0, 1.0, 0.0, 0.0]
                )
        if shader_name == "melpot-toon-hlslmacros":
            for slot in ("_MainTex", "_DetailMask", "_GlossMap"):
                texture_env = textures.get(slot)
                if texture_env is None:
                    continue
                shader_params[f"{slot.lstrip('_')}_ST"] = self._unity_texture_st(texture_env)

        # Outline color (separate from main-pass colors)
        if "_OutlineColor" in colors:
            c = colors["_OutlineColor"]
            outline_params["OutlineColor"] = unity_color_to_linear_rgba(c)

        if shader_params:
            extras["shaderParams"] = shader_params
        passes: list[dict[str, Any]] = [{"id": "Forward"}]
        if outline_params:
            passes.append({
                "id": "Outline",
                "shaderParams": outline_params,
                "renderState": {"cull": 1},
            })
        extras["passes"] = passes
        # Generic render state — same schema as _eye_extras, consumed by the
        # generic applyRenderState() in the renderer.
        render_state: dict[str, Any] = {}
        # Top-level state
        for src, dst in [
            ("_SurfaceMode", "surfaceType"),
            ("_CullMode", "cull"),
            ("_ZWriteMode", "zWrite"),
            ("_ZTestMode", "zTest"),
        ]:
            if src in floats:
                render_state[dst] = floats[src]
        # Blend state
        blend: dict[str, Any] = {}
        for src, dst in [
            ("_BlendRGBSrc", "srcRgb"),
            ("_BlendRGBDst", "dstRgb"),
            ("_BlendAlphaSrc", "srcAlpha"),
            ("_BlendAlphaDst", "dstAlpha"),
            ("_BlendOpRGB", "opRgb"),
            ("_BlendOpAlpha", "opAlpha"),
        ]:
            if src in floats:
                blend[dst] = floats[src]
        if blend:
            render_state["blend"] = blend
        # Stencil state
        stencil: dict[str, Any] = {}
        for src, dst in [
            ("_StencilReference", "ref"),
            ("_StencilReadMask", "readMask"),
            ("_StencilWriteMask", "writeMask"),
            ("_StencilComparison", "comp"),
            ("_StencilPassFront", "pass"),
            ("_StencilFailFront", "fail"),
            ("_StencilZFailFront", "zFail"),
        ]:
            if src in floats:
                stencil[dst] = floats[src]
        if stencil:
            render_state["stencil"] = stencil
        # Polygon offset
        offset: dict[str, Any] = {}
        if "_OffsetFactor" in floats:
            offset["factor"] = floats["_OffsetFactor"]
        if "_OffsetUnits" in floats:
            offset["units"] = floats["_OffsetUnits"]
        if offset:
            render_state["offset"] = offset
        # Color mask (Unity ColorMask enum value)
        if "_ColorMask" in floats:
            render_state["colorMask"] = floats["_ColorMask"]
        # Try to read RenderType / RenderQueue from the shader's tag list.
        # UnityPy exposes material shader details via m_Shader; tags live on
        # the shader, not the material, so we skip them for now. RenderQueue
        # can be overridden per-material via CustomRenderQueue.
        if hasattr(material, "m_CustomRenderQueue"):
            crq = int(material.m_CustomRenderQueue)
            if crq != -1:  # -1 means "use shader default"
                render_state["renderQueue"] = crq
        if render_state:
            extras["renderState"] = render_state
        return extras

    def _eye_extras(self, material: Any, colors: dict[str, Any], textures: dict[str, Any], floats: dict[str, float], kind: str) -> dict[str, Any]:
        """Carry the eye-area shaders (CharacterEye base, CharacterHighlight
        sparkle, Highlight_Distortion lens) into the GLB.

        Same structure as _melpot_extras — both feed the generic binder:
            extras.shader         = dispatch id
            extras.programCacheKey = cache key
            extras.shaderParams   = shared uniform params
            extras.textures       = texture slot → index
            extras.renderState    = generic render state
            extras.passes         = ordered pass plan"""
        extras: dict[str, Any] = {"shader": kind}
        mat_name = str(getattr(material, "m_Name", ""))
        extras["programCacheKey"] = f"{kind}:{mat_name}"
        extras["passes"] = [{"id": "Forward"}]

        shader_params: dict[str, Any] = {}

        def cprop(src: str, dst: str) -> None:
            if src in colors:
                c = colors[src]
                values = unity_color_to_linear_rgba(c) if kind == "melpot-toon-eye" else [
                    float(c.r), float(c.g), float(c.b), float(c.a),
                ]
                shader_params[dst] = values

        def fprop(src: str, dst: str) -> None:
            if src in floats:
                shader_params[dst] = floats[src]

        def vprop(src: str, dst: str) -> None:
            if src in colors:
                value = colors[src]
                shader_params[dst] = [
                    float(value.r), float(value.g), float(value.b), float(value.a),
                ]

        # Lighting / environment params (shader uniforms, not render state)
        cprop("_KeyLightColor", "KeyLightColor")
        cprop("_AmbientColor", "AmbientColor")
        for src, dst in [
            ("_OverrideMainLightColor", "OverrideMainLightColor"),
            ("_MainLightIntensity", "MainLightIntensity"),
            ("_AmbientMode", "AmbientMode"),
        ]:
            fprop(src, dst)

        # --- Shader-specific params ---
        tex_slots: dict[str, str] = {}
        if kind == "character-eye":
            cprop("_MainColor", "MainColor")
            fprop("_AlphaClipThreshold", "AlphaClipThreshold")
            main_tex = textures.get("_MainTex")
            if main_tex:
                scale = main_tex.m_Scale
                offset = main_tex.m_Offset
                shader_params["MainTex_ST"] = [
                    float(scale.x), float(scale.y), float(offset.x), float(offset.y),
                ]
            tex_slots = {"_MainTex": "MainTex"}
        elif kind == "melpot-toon-eye":
            for source in (
                "_MainColor", "_HighlightMainColor", "_HighlightSubColor",
            ):
                cprop(source, source.lstrip("_"))
            for source in (
                "_UVOffsetNoiseRange", "_UVScaleNoiseRange",
                "_UVRotationNoiseRange", "_ExpNoiseRange",
            ):
                vprop(source, source.lstrip("_"))
            for source in (
                "_SeparateHighlightRandom", "_AddIntensity", "_AlphaClipThreshold",
            ):
                fprop(source, source.lstrip("_"))
            main_tex = textures.get("_MainTex")
            if main_tex:
                scale = main_tex.m_Scale
                offset = main_tex.m_Offset
                shader_params["MainTex_ST"] = [
                    float(scale.x), float(scale.y), float(offset.x), float(offset.y),
                ]
            tex_slots = {
                "_MainTex": "MainTex",
                "_HighlightMainTex": "HighlightMainTex",
                "_HighlightSubTex": "HighlightSubTex",
            }
        elif kind == "character-highlight":
            cprop("_HighlightMainColor", "HighlightMainColor")
            cprop("_UVOffsetNoiseRange", "HighlightUVOffset")
            for src, dst in [
                ("_UseCryParameters", "UseCryParameters"),
                ("_Normal_TilingNoiseWidth", "Normal_TilingNoiseWidth"),
                ("_Normal_RotateNoiseWidth", "Normal_RotateNoiseWidth"),
                ("_Normal_TilingFrequency", "Normal_TilingFrequency"),
                ("_Normal_RotateFrequency", "Normal_RotateFrequency"),
                ("_Cry_TilingNoiseWidth", "Cry_TilingNoiseWidth"),
                ("_Cry_RotateNoiseWidth", "Cry_RotateNoiseWidth"),
                ("_Cry_TilingFrequency", "Cry_TilingFrequency"),
                ("_Cry_RotateFrequency", "Cry_RotateFrequency"),
                ("_TimeScale", "TimeScale"),
                ("_FrequencyValue", "FrequencyValue"),
                ("_DivideValue", "DivideValue"),
                ("_AlphaClipThreshold", "AlphaClipThreshold"),
            ]:
                fprop(src, dst)
            tex_slots = {"_MainTexture": "MainTexture", "_CryTexture": "CryTexture"}
        elif kind == "highlight-distortion":
            cprop("_HighlightMainColor", "HighlightMainColor")
            cprop("_HighlightSubColor", "HighlightSubColor")
            cprop("_MainLightOffset", "MainLightOffset")
            cprop("_MatcapColor", "MatcapColor")
            for src, dst in [
                ("_DistortionIntensity", "DistortionIntensity"),
                ("_TilinegValue", "TilinegValue"),
                ("_HighlightBlendMode", "HighlightBlendMode"),
                ("_MatcapBlendLevel", "MatcapBlendLevel"),
            ]:
                fprop(src, dst)

        texture_indices: dict[str, int] = {}
        for slot, dst in tex_slots.items():
            texture_env = textures.get(slot)
            if not (texture_env and texture_env.m_Texture):
                continue
            texture = texture_env.m_Texture.deref_parse_as_object()
            texture_indices[dst] = self.add_image(texture)
        if texture_indices:
            extras["textures"] = texture_indices

        if shader_params:
            extras["shaderParams"] = shader_params

        # --- Generic render state (same schema as _melpot_extras) ---
        render_state: dict[str, Any] = {}
        for src, dst in [
            ("_SurfaceMode", "surfaceType"),
            ("_CullMode", "cull"),
            ("_ZWriteMode", "zWrite"),
            ("_ZTestMode", "zTest"),
        ]:
            if src in floats:
                render_state[dst] = floats[src]
        # Blend
        blend: dict[str, Any] = {}
        for src, dst in [
            ("_BlendRGBSrc", "srcRgb"),
            ("_BlendRGBDst", "dstRgb"),
            ("_BlendAlphaSrc", "srcAlpha"),
            ("_BlendAlphaDst", "dstAlpha"),
            ("_BlendOpRGB", "opRgb"),
            ("_BlendOpAlpha", "opAlpha"),
        ]:
            if src in floats:
                blend[dst] = floats[src]
        if blend:
            render_state["blend"] = blend
        # Stencil
        stencil: dict[str, Any] = {}
        for src, dst in [
            ("_StencilReference", "ref"),
            ("_StencilReadMask", "readMask"),
            ("_StencilWriteMask", "writeMask"),
            ("_StencilComparison", "comp"),
            ("_StencilPassFront", "pass"),
            ("_StencilFailFront", "fail"),
            ("_StencilZFailFront", "zFail"),
        ]:
            if src in floats:
                stencil[dst] = floats[src]
        if stencil:
            render_state["stencil"] = stencil
        # Polygon offset
        offset: dict[str, Any] = {}
        if "_OffsetFactor" in floats:
            offset["factor"] = floats["_OffsetFactor"]
        if "_OffsetUnits" in floats:
            offset["units"] = floats["_OffsetUnits"]
        if offset:
            render_state["offset"] = offset
        # Color mask
        if "_ColorMask" in floats:
            render_state["colorMask"] = floats["_ColorMask"]
        # Custom render queue
        if hasattr(material, "m_CustomRenderQueue"):
            crq = int(material.m_CustomRenderQueue)
            if crq != -1:
                render_state["renderQueue"] = crq
        if render_state:
            extras["renderState"] = render_state

        if shader_params:
            extras["shaderParams"] = shader_params
        return extras

    def write(self, path: Path) -> None:
        for key in ["skins", "materials", "textures", "images", "samplers", "animations"]:
            if not self.document[key]:
                del self.document[key]
        self.document["buffers"][0]["byteLength"] = len(self.binary)
        json_data = json.dumps(self.document, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        json_data += b" " * ((-len(json_data)) & 3)
        binary = bytes(self.binary) + b"\0" * ((-len(self.binary)) & 3)
        total = 12 + 8 + len(json_data) + 8 + len(binary)
        path.write_bytes(b"".join([
            struct.pack("<4sII", b"glTF", 2, total),
            struct.pack("<I4s", len(json_data), b"JSON"), json_data,
            struct.pack("<I4s", len(binary), b"BIN\0"), binary,
        ]))


def _strip_blendshape_asset_prefix(name: str) -> str:
    """Strip Unity's BlendShape asset prefix when present.

    Unity names BlendShape channels `<asset>.<morph>`. For assets produced
    from a separate BlendShape mesh the asset is named `<mesh>_blendShape`,
    e.g. `face_main_blendShape.face_main_eye_joy_L`. The morph portion is the
    renderer-facing identifier; we drop the asset prefix so the channel name
    matches the standardized config (which never carries the asset half).
    Names without the `_blendShape` suffix are left untouched."""
    if "." in name:
        prefix, rest = name.split(".", 1)
        if prefix.endswith("_blendShape"):
            return rest
    return name


def mesh_morphs(mesh: Any, vertex_count: int, builder: GlbBuilder) -> tuple[list[dict[str, int]], list[str]]:
    shapes = getattr(mesh, "m_Shapes", None)
    if not shapes or not getattr(shapes, "channels", None):
        return [], []
    targets: list[dict[str, int]] = []
    names: list[str] = []
    for channel in shapes.channels:
        frame = shapes.shapes[channel.frameIndex + channel.frameCount - 1]
        deltas = [[0.0, 0.0, 0.0] for _ in range(vertex_count)]
        for delta in shapes.vertices[frame.firstVertex:frame.firstVertex + frame.vertexCount]:
            deltas[delta.index] = [-float(delta.vertex.x), float(delta.vertex.y), float(delta.vertex.z)]
        minimum = [min(value[i] for value in deltas) for i in range(3)]
        maximum = [max(value[i] for value in deltas) for i in range(3)]
        targets.append({"POSITION": builder.add_accessor(
            deltas, "VEC3", COMPONENT_FLOAT, target=34962, minimum=minimum, maximum=maximum
        )})
        names.append(_strip_blendshape_asset_prefix(channel.name))
    return targets, names


def trim_unused_trailing_renderer_bones(
    mesh_name: str,
    bones: list[Any],
    bind_poses: list[Any],
    bone_indices: list[Any],
    bone_weights: list[Any],
) -> list[Any]:
    """Match a renderer's bones to its mesh when only an unused tail differs.

    Unity assets can retain extra bones at the end of a renderer's bone array
    even though the shared mesh has fewer bind poses.  The prefix still maps
    one-to-one to the bind poses, so dropping the tail is safe only when no
    non-zero vertex weight refers to it.
    """
    if len(bones) <= len(bind_poses):
        return bones

    bind_pose_count = len(bind_poses)
    for vertex_index, raw_indices in enumerate(bone_indices):
        values = list(raw_indices if isinstance(raw_indices, (tuple, list)) else [raw_indices])
        weights = list(bone_weights[vertex_index]) if bone_weights else [1.0]
        for bone_index, weight in zip(values, weights):
            if weight and not 0 <= bone_index < bind_pose_count:
                raise RuntimeError(
                    f"{mesh_name}: vertex {vertex_index} references bone {bone_index}, "
                    f"but mesh has {bind_pose_count} bind poses"
                )
    return bones[:bind_pose_count]


__all__ = [
    "GlbBuilder",
    "mat4_transform_dir",
    "mesh_morphs",
    "trim_unused_trailing_renderer_bones",
]
