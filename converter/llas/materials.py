"""Translate LLAS source Material data into the current generic shader contract.

This runs after the shared face has been grafted, so only materials actually
referenced by exported renderers are written. Shader identity comes from the
original Material.m_Shader PathID, never a property-name fingerprint.
"""

from __future__ import annotations

from collections.abc import Iterable
from io import BytesIO
from typing import Any

from PIL import Image

from converter.common.glb import GlbBuilder, unity_color_to_linear_rgba
from converter.common.unity import object_id


MEMBER_SHADER = 8291131735116688333
TRANSPARENT_SHADER = 7151384334892346267
MEMBER_KEYWORDS = {"_CHEEK_ON", "_EMISSIVE_ON", "_MATCAP_ON"}


def _properties(material: Any) -> tuple[dict, dict, dict]:
    saved = material.m_SavedProperties
    key = lambda item: str(getattr(item, "name", item))
    return (
        {key(name): float(value) for name, value in saved.m_Floats},
        {key(name): value for name, value in saved.m_Colors},
        {key(name): value for name, value in saved.m_TexEnvs},
    )


def _required(values: dict, key: str, material: Any) -> Any:
    if key not in values:
        raise ValueError(f"LLAS material {material.m_Name}: missing source property {key}")
    return values[key]


def _vector(value: Any) -> list[float]:
    if hasattr(value, "x"):
        return [float(value.x), float(value.y), float(value.z), float(value.w)]
    return [float(value.r), float(value.g), float(value.b), float(value.a)]


def _sampler(builder: GlbBuilder, texture_index: int, texture: Any) -> None:
    settings = texture.m_TextureSettings
    wrap = {0: 10497, 1: 33071, 2: 33648}
    u, v = int(settings.m_WrapU), int(settings.m_WrapV)
    if u not in wrap or v not in wrap:
        raise ValueError(f"LLAS texture {texture.m_Name}: unsupported wrap mode {u}/{v}")
    mode = int(settings.m_FilterMode)
    mips = int(texture.m_MipCount)
    if mips < 1 or mode not in {0, 1, 2}:
        raise ValueError(f"LLAS texture {texture.m_Name}: unsupported filtering {mode}, mips {mips}")
    sampler = {
        "magFilter": 9728 if mode == 0 else 9729,
        "minFilter": (9728 if mode == 0 else 9729) if mips == 1 else {0: 9984, 1: 9985, 2: 9987}[mode],
        "wrapS": wrap[u], "wrapT": wrap[v],
    }
    samplers = builder.document["samplers"]
    try:
        index = samplers.index(sampler)
    except ValueError:
        index = len(samplers)
        samplers.append(sampler)
    builder.document["textures"][texture_index]["sampler"] = index


def _array_layers(builder: GlbBuilder, texture: Any, cache: dict) -> list[int]:
    key = object_id(texture)
    if key in cache:
        return cache[key]
    width, height, depth = int(texture.m_Width), int(texture.m_Height), int(texture.m_Depth)
    data = bytes(texture.image_data)
    layer_size = width * height * 4
    if (int(texture.m_Format), int(texture.m_MipCount), int(texture.m_ColorSpace)) != (4, 1, 1) \
            or len(data) != layer_size * depth or depth < 1:
        raise ValueError(f"LLAS Texture2DArray {texture.m_Name}: unsupported source layout")
    result = []
    for layer in range(depth):
        image = Image.frombytes("RGBA", (width, height), data[layer * layer_size:(layer + 1) * layer_size])
        image = image.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        output = BytesIO()
        image.save(output, format="PNG")
        view = builder.add_view(output.getvalue())
        builder.document["images"].append({
            "name": f"{texture.m_Name}[{layer}]", "bufferView": view, "mimeType": "image/png",
        })
        index = len(builder.document["textures"])
        builder.document["textures"].append({
            "source": len(builder.document["images"]) - 1,
            "extras": {"colorSpace": "srgb"},
        })
        _sampler(builder, index, texture)
        result.append(index)
    cache[key] = result
    return result


def _texture(builder: GlbBuilder, textures: dict, slot: str, array_cache: dict, *, required: bool) -> int | list[int] | None:
    entry = textures.get("_" + slot)
    if entry is None or not entry.m_Texture:
        if required:
            raise ValueError(f"LLAS source material is missing required {slot} texture")
        return None
    source = entry.m_Texture.deref_parse_as_object()
    if source.object_reader.type.name == "Texture2DArray":
        if slot != "CheekTex":
            raise ValueError(f"LLAS {slot}: unexpected Texture2DArray")
        return _array_layers(builder, source, array_cache)
    if source.object_reader.type.name != "Texture2D":
        raise ValueError(f"LLAS {slot}: unsupported texture type {source.object_reader.type.name}")
    index = builder.add_image(source)
    _sampler(builder, index, source)
    return index


def _texture_slots(builder: GlbBuilder, textures: dict, slots: Iterable[str], array_cache: dict,
                   *, required: set[str] | None = None) -> dict:
    required = required or set()
    result = {}
    for slot in slots:
        index = _texture(builder, textures, slot, array_cache, required=slot in required)
        if index is not None:
            result[slot] = index
    return result


def _member(builder: GlbBuilder, material: Any, floats: dict, colors: dict,
            textures: dict, array_cache: dict) -> dict:
    keywords = set(str(getattr(material, "m_ShaderKeywords", "")).split())
    if "PROCEDURAL_INSTANCING_ON" in keywords:
        raise ValueError(f"LLAS material {material.m_Name}: procedural instancing variant is not restored")
    active = sorted(keywords & MEMBER_KEYWORDS)
    color_names = ("TintColor", "AmbientColor", "RimlightColor")
    float_names = ("RimglightPower", "MainTexMipmapBias")
    params = {
        **{name: unity_color_to_linear_rgba(_required(colors, "_" + name, material)) for name in color_names},
        **{name: _required(floats, "_" + name, material) for name in float_names},
        # CommonCoreMember.Initialize calls Rimlight.ApplyIntensity(0) on both
        # Navi materials. Its base intensity is 0, overriding serialized values.
        "RimglightIntensity": 0.0,
        "RimlightDirection": _vector(_required(colors, "_RimlightDirection", material)),
    }
    slots = ["MainTex", "RimlightTex"]
    cheek = textures.get("_CheekTex")
    if "_CHEEK_ON" in active or (cheek is not None and cheek.m_Texture):
        # MemberCheekBase can enable this serialized resource at runtime.
        # Keep it even when the material starts with the keyword disabled;
        # resource availability must not change that original initial state.
        for name in ("CheekIntensity", "CheekTexArrayIndex"):
            if "_CHEEK_ON" in active or "_" + name in floats:
                params[name] = _required(floats, "_" + name, material)
        slots.append("CheekTex")
    if "_EMISSIVE_ON" in active:
        params["EmissiveIntensity"] = unity_color_to_linear_rgba(_required(colors, "_EmissiveIntensity", material))
        params["EmissiveFlicker"] = _vector(_required(colors, "_EmissiveFlicker", material))
        slots.extend(("EmissiveTex", "EmissiveScrollTex"))
    if "_MATCAP_ON" in active:
        params.update({name: _required(floats, "_" + name, material) for name in (
            "MatcapTexDarkenR", "MatcapTexAdd", "MatcapBrightR", "MatcapBrightG", "MatcapSpanColTexAdd",
        )})
        for name in ("MatcapIntensity", "MatcapSpanCol"):
            params[name] = unity_color_to_linear_rgba(_required(colors, "_" + name, material))
        slots.extend(("MatcapTex", "MatcapMaskTex"))
    tex = _texture_slots(builder, textures, slots, array_cache)
    queue = int(material.m_CustomRenderQueue)
    main_state = {
        "cull": _required(floats, "_CullMode", material), "zWrite": _required(floats, "_ZWrite", material),
        "zTest": 4, "colorMask": 15,
        "stencil": {"ref": 1, "comp": 8, "pass": 2, "fail": 0, "zFail": 0},
    }
    outline_state = {
        "cull": 1, "zWrite": 1, "zTest": 4, "colorMask": 15,
        "stencil": {"ref": 1, "comp": _required(floats, "_OutlineStencilComp", material),
                    "pass": 0, "fail": 0, "zFail": 0},
    }
    main_pass = {"id": "Main", "renderState": main_state, "extras": {"keywords": active}}
    return {
        "shader": "llas-member", "programCacheKey": f"llas-member:{material.m_Name}",
        "shaderParams": params, "textures": tex,
        "renderState": {"surfaceType": 0, "renderQueue": queue if queue >= 0 else 1900},
        "passes": [main_pass, {"id": "Outline", "renderState": outline_state}],
    }


def _transparent(builder: GlbBuilder, material: Any, floats: dict, colors: dict,
                 textures: dict, array_cache: dict) -> dict:
    keywords = set(str(getattr(material, "m_ShaderKeywords", "")).split())
    if "PROCEDURAL_INSTANCING_ON" in keywords:
        raise ValueError(f"LLAS material {material.m_Name}: procedural instancing variant is not restored")
    tex = _texture_slots(builder, textures, ("MainTex",), array_cache)
    env = textures.get("_MainTex")
    if env is None:
        raise ValueError(f"LLAS material {material.m_Name}: missing MainTex TexEnv")
    st = [float(env.m_Scale.x), float(env.m_Scale.y), float(env.m_Offset.x), float(env.m_Offset.y)]
    state = {
        "surfaceType": 1,
        "renderQueue": int(material.m_CustomRenderQueue) if int(material.m_CustomRenderQueue) >= 0 else 3000,
        "cull": _required(floats, "_CullMode", material),
        "zTest": _required(floats, "_ZTestMode", material),
        "zWrite": _required(floats, "_ZWriteParam", material),
        "colorMask": 15,
        "blend": {"srcRgb": _required(floats, "_BlendSrc", material),
                  "dstRgb": _required(floats, "_BlendDst", material),
                  "srcAlpha": _required(floats, "_BlendSrc", material),
                  "dstAlpha": _required(floats, "_BlendDst", material),
                  "opRgb": 0, "opAlpha": 0},
        "stencil": {"ref": _required(floats, "_StencilRef", material),
                    "comp": _required(floats, "_StencilComp", material),
                    "pass": _required(floats, "_StencilPassOp", material),
                    "zFail": _required(floats, "_StencilZFailOp", material),
                    "fail": 0, "readMask": 255, "writeMask": 255},
    }
    return {
        "shader": "llas-general-transparent",
        "programCacheKey": f"llas-general-transparent:{material.m_Name}",
        "textures": tex,
        "shaderParams": {
            "TintColor": unity_color_to_linear_rgba(_required(colors, "_TintColor", material)),
            "MainTexST": st,
            "VertexColor": 1 if "_VERTEX_COLOR_ON" in keywords else 0,
            "Saturate": 1 if "_SATURATE_ON" in keywords else 0,
        },
        "renderState": state,
        "passes": [{"id": "Forward"}],
    }


def attach_llas_materials(builder: GlbBuilder, environment: Any) -> None:
    """Apply material metadata only to Material objects used by the final GLB."""
    readers = {
        (id(reader.assets_file), reader.path_id): reader
        for reader in environment.objects if reader.type.name == "Material"
    }
    array_cache: dict = {}
    for source_id, index in builder.materials.items():
        reader = readers.get(source_id)
        if reader is None:
            raise ValueError(f"Exported LLAS material {source_id} is absent from loaded source assets")
        material = reader.read()
        floats, colors, textures = _properties(material)
        shader_path_id = int(material.m_Shader.m_PathID)
        if shader_path_id == MEMBER_SHADER:
            extras = _member(builder, material, floats, colors, textures, array_cache)
        elif shader_path_id == TRANSPARENT_SHADER:
            extras = _transparent(builder, material, floats, colors, textures, array_cache)
        else:
            raise ValueError(f"LLAS material {material.m_Name}: unknown source Shader PathID {shader_path_id}")
        builder.document["materials"][index]["extras"] = extras
