"""Extract the original mip explicitly selected by a menu MatCap material."""
from __future__ import annotations

from numbers import Integral
from typing import Any
import sys

from PIL import Image
from UnityPy.enums import TextureFormat


def extract_raw_mip_chain(texture: Any) -> dict:
    """Decode every original ASTC6x6 level, never synthesize or recompress one.

    Bytes use the existing exported image row orientation. Half components are
    little-endian binary16, not quantized PNG fallback components.
    """
    import astc_encoder as astc
    if int(texture.m_TextureFormat) != int(TextureFormat.ASTC_RGB_6x6):
        raise ValueError('Original mip extraction requires ASTC_RGB_6x6')
    color = int(texture.m_ColorSpace)
    if color not in (0, 1):
        raise ValueError('Original mip extraction requires explicit color space 0/1')
    if int(texture.m_ImageCount) != 1 or int(texture.m_TextureDimension) != 2:
        raise ValueError('Original mip extraction requires one Texture2D')
    if int(getattr(texture, 'm_MipsStripped', 0)) != 0:
        raise ValueError('Stripped original mips require an explicit source-level mapping')
    width, height, count = int(texture.m_Width), int(texture.m_Height), int(texture.m_MipCount)
    if min(width, height, count) <= 0 or count > max(width, height).bit_length():
        raise ValueError('Invalid original mip dimensions/count')
    payload = texture.get_image_data()
    config = astc.ASTCConfig(astc.ASTCProfile.LDR_SRGB if color else astc.ASTCProfile.LDR,
                            6, 6, flags=astc.ASTCConfigFlags.DECOMPRESS_ONLY)
    context = astc.ASTCContext(config)
    levels, offset = [], 0
    for level in range(count):
        w, h = max(1, width >> level), max(1, height >> level)
        size = ((w + 5) // 6) * ((h + 5) // 6) * 16
        if offset + size > len(payload):
            raise ValueError(f'Original mip {level} is truncated')
        decoded = astc.ASTCImage(astc.ASTCType.U8 if color else astc.ASTCType.F16, w, h, 1)
        context.decompress(bytes(payload[offset:offset + size]), decoded,
                           astc.ASTCSwizzle.from_str('RGBA'))
        raw = bytes(decoded.data)
        stride = w * (4 if color else 8)
        if len(raw) != stride * h:
            raise ValueError(f'Decoder returned an invalid mip {level} byte count')
        if not color and sys.byteorder != 'little':
            from array import array
            halves = array('H')
            halves.frombytes(raw)
            halves.byteswap()
            raw = halves.tobytes()
        raw = b''.join(raw[row * stride:(row + 1) * stride] for row in reversed(range(h)))
        levels.append({'width': w, 'height': h, 'data': raw})
        offset += size
    return {'format': 'rgba8' if color else 'rgba16f', 'levels': levels}


def extract_matcap_image(texture: Any, level: int) -> Image.Image:
    """Return one original sRGB ASTC mip in the existing GLB image orientation.

    The material's source LOD must be offset by ``level`` when this extracted
    image becomes texture level zero. No intermediate mip is synthesized.
    """
    if isinstance(level, bool) or not isinstance(level, Integral) or level < 0:
        raise ValueError("MatCap source level must be a nonnegative integer")
    if int(texture.m_TextureFormat) != int(TextureFormat.ASTC_RGB_6x6):
        raise ValueError("MatCap source must use the verified ASTC_RGB_6x6 format")
    if int(texture.m_ColorSpace) != 1:
        raise ValueError("MatCap sRGB extraction requires source m_ColorSpace=1")
    if int(texture.m_ImageCount) != 1 or int(texture.m_TextureDimension) != 2:
        raise ValueError("MatCap source must be one Texture2D")
    if int(getattr(texture, "m_MipsStripped", 0)) != 0:
        raise ValueError("Stripped MatCap source requires an explicit source-level mapping")
    if level >= int(texture.m_MipCount):
        raise ValueError("MatCap source does not contain the selected level")
    width, height = int(texture.m_Width), int(texture.m_Height)
    if width <= 0 or height <= 0:
        raise ValueError("MatCap source dimensions must be positive")
    offset = 0
    for previous in range(level):
        w, h = max(1, width >> previous), max(1, height >> previous)
        offset += ((w + 5) // 6) * ((h + 5) // 6) * 16
    w, h = max(1, width >> level), max(1, height >> level)
    size = ((w + 5) // 6) * ((h + 5) // 6) * 16
    data = texture.get_image_data()
    if offset + size > len(data):
        raise ValueError("MatCap selected mip is truncated")
    import astc_encoder as astc
    config = astc.ASTCConfig(astc.ASTCProfile.LDR_SRGB, 6, 6,
                            flags=astc.ASTCConfigFlags.DECOMPRESS_ONLY)
    context = astc.ASTCContext(config)
    decoded = astc.ASTCImage(astc.ASTCType.U8, w, h, 1)
    context.decompress(bytes(data[offset:offset + size]), decoded,
                       astc.ASTCSwizzle.from_str("RGBA"))
    # UnityPy's existing texture.image exporter also flips to this orientation.
    return Image.frombytes("RGBA", (w, h), bytes(decoded.data)).transpose(Image.Transpose.FLIP_TOP_BOTTOM)
