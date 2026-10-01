from __future__ import annotations

import math
import struct
from collections import defaultdict
from typing import Any


def packed_clip_values(clip: Any) -> tuple[list[float], dict[int, list[tuple[float, float]]]]:
    """Decode a Unity AnimationClip's muscle-clip packed keyframes.

    Returns:
        constant: per-curve constant (non-animated) values, indexed by curve
        curves: per-curve (time, value) samples, indexed by curve

    Unity packs muscle clips into three segments — a streamed variable-rate
    block, a dense fixed-rate block, and a constant block. The two variable
    blocks share a single dense sample array on disk; curve indices above the
    streamed count are dense-relative. Constant curves are returned separately
    because the caller must consult them when a binding has no keyframes."""
    muscle = clip.m_MuscleClip
    packed = muscle.m_Clip.data
    streamed_count = packed.m_StreamedClip.curveCount
    dense = packed.m_DenseClip
    curves: dict[int, list[tuple[float, float]]] = defaultdict(list)
    raw = struct.pack(f"<{len(packed.m_StreamedClip.data)}I", *packed.m_StreamedClip.data)
    offset = 0
    while offset + 8 <= len(raw):
        time, count = struct.unpack_from("<fi", raw, offset)
        offset += 8
        if count < 0 or offset + count * 20 > len(raw):
            break
        for _ in range(count):
            index, _a, _b, _c, value = struct.unpack_from("<i4f", raw, offset)
            offset += 20
            if math.isfinite(time):
                curves[index].append((max(0.0, float(time)), float(value)))
    for frame in range(dense.m_FrameCount):
        time = float(dense.m_BeginTime + frame / dense.m_SampleRate)
        for local in range(dense.m_CurveCount):
            curves[streamed_count + local].append((time, float(dense.m_SampleArray[frame * dense.m_CurveCount + local])))
    constant = list(packed.m_ConstantClip.data) if packed.m_ConstantClip else []
    return constant, curves