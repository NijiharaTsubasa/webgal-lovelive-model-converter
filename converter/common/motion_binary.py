"""Single-file binary storage for standard motion payloads."""

from __future__ import annotations

import copy
import json
import math
import struct
from typing import Any


MAGIC = b"MOTION\x00\x00"
CLIP_COLLECTIONS = ("clips", "auxiliaryClips", "leftHandPoses", "rightHandPoses")
SAMPLE_FIELDS = ("rotation", "translation", "scale", "values")
PREFIX_SIZE = 12


def _aligned(length: int, alignment: int) -> int:
    return (length + alignment - 1) // alignment * alignment


def _same_number(left: float, right: float) -> bool:
    return left == right and (left != 0 or math.copysign(1, left) == math.copysign(1, right))


def encode_motion(payload: dict[str, Any]) -> bytes:
    """Preserve the motion schema while moving sampled number arrays into binary."""
    header = copy.deepcopy(payload)
    samples = bytearray()
    for collection in CLIP_COLLECTIONS:
        for clip in header.get(collection, []):
            for track in (*clip.get("tracks", []), *clip.get("groupTracks", [])):
                for field in SAMPLE_FIELDS:
                    values = track.get(field)
                    if not values:
                        continue
                    if not isinstance(values, list) or any(
                        isinstance(value, bool) or not isinstance(value, (int, float))
                        or not math.isfinite(value) for value in values
                    ):
                        raise ValueError(f"{collection} {clip.get('id')}: invalid {field} samples")
                    try:
                        packed = struct.pack(f"<{len(values)}f", *values)
                        restored = struct.unpack(f"<{len(values)}f", packed)
                        exact = all(_same_number(value, result) for value, result in zip(values, restored))
                    except (OverflowError, struct.error):
                        exact = False
                    if exact:
                        sample_type, item_size = "f32", 4
                    else:
                        sample_type, item_size = "f64", 8
                        packed = struct.pack(f"<{len(values)}d", *values)
                    offset = _aligned(len(samples), item_size)
                    samples.extend(b"\x00" * (offset - len(samples)))
                    samples.extend(packed)
                    track[field] = {"offset": offset, "length": len(values), "type": sample_type}
    header_bytes = json.dumps(header, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")
    if len(header_bytes) > 0xFFFFFFFF:
        raise ValueError("motion header exceeds 4 GiB")
    padding = _aligned(PREFIX_SIZE + len(header_bytes), 8) - PREFIX_SIZE - len(header_bytes)
    return MAGIC + struct.pack("<I", len(header_bytes)) + header_bytes + b"\x00" * padding + samples


def decode_motion(source: bytes) -> dict[str, Any]:
    """Decode binary motion files for converter verification and migration."""
    if len(source) < PREFIX_SIZE or source[:8] != MAGIC:
        raise ValueError("not a binary motion file")
    header_length = struct.unpack_from("<I", source, 8)[0]
    header_end = PREFIX_SIZE + header_length
    data_start = _aligned(header_end, 8)
    if data_start > len(source):
        raise ValueError("truncated binary motion header")
    payload = json.loads(source[PREFIX_SIZE:header_end].decode("utf-8"))
    for collection in CLIP_COLLECTIONS:
        for clip in payload.get(collection, []):
            for track in (*clip.get("tracks", []), *clip.get("groupTracks", [])):
                for field in SAMPLE_FIELDS:
                    descriptor = track.get(field)
                    if not isinstance(descriptor, dict):
                        continue
                    sample_type = descriptor.get("type")
                    item_size = {"f32": 4, "f64": 8}.get(sample_type)
                    offset, length = descriptor.get("offset"), descriptor.get("length")
                    if (item_size is None or not isinstance(offset, int) or isinstance(offset, bool)
                        or not isinstance(length, int) or isinstance(length, bool)
                        or offset < 0 or length < 0 or offset % item_size
                        or data_start + offset + length * item_size > len(source)):
                        raise ValueError(f"invalid {field} binary range")
                    code = "f" if sample_type == "f32" else "d"
                    track[field] = list(struct.unpack_from(f"<{length}{code}", source, data_start + offset))
    return payload
