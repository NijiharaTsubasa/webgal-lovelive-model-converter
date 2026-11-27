"""Shared pieces of the verbatim source-physics exports (physics.source.*): the Unity transform table.

Transform ids are path ids as decimal strings (64-bit values do not survive JSON numbers in JavaScript).  The
exported local transforms describe the pose the GLB rest pose was exported in: nodes present in the GLB take
their Unity-baked neutral pose (mapping.neutral_world, reflected back to Unity's left-handed frame), nodes absent
from the GLB keep their serialized local transform under that parent.  "node" is the GLB node index or null.

Runtime builds (MagicaCloth2 without PreBuild) read the hierarchy as the game sees it when the prefab wakes up:
"siblingIndex" is the transform's index in its parent's children (null for the root), and where the exported
local transform differs from the serialized one, "prefabLocalPosition" / "prefabLocalRotation" / "prefabLocalScale"
carry the serialized (prefab) values.
"""

from __future__ import annotations

import math
from typing import Any

from .unity import object_id

_FLIP = (-1., 1., 1., 1.)


def unity_from_gltf(matrix: list[float]) -> list[float]:
    """Column-major glTF (X-reflected) matrix -> column-major Unity matrix: F M F (its own inverse)."""
    return [matrix[c * 4 + r] * _FLIP[r] * _FLIP[c] for c in range(4) for r in range(4)]


def mat_mul(a: list[float], b: list[float]) -> list[float]:
    return [sum(a[k * 4 + r] * b[c * 4 + k] for k in range(4)) for c in range(4) for r in range(4)]


def inverse_affine(m: list[float]) -> list[float]:
    a, b, c = m[0], m[4], m[8]
    d, e, f = m[1], m[5], m[9]
    g, h, i = m[2], m[6], m[10]
    det = a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g)
    if abs(det) < 1e-20:
        raise ValueError("singular transform in source physics hierarchy")
    k = 1. / det
    r = [(e * i - f * h) * k, -(b * i - c * h) * k, (b * f - c * e) * k,
         -(d * i - f * g) * k, (a * i - c * g) * k, -(a * f - c * d) * k,
         (d * h - e * g) * k, -(a * h - b * g) * k, (a * e - b * d) * k]
    tx, ty, tz = m[12], m[13], m[14]
    t = [-(r[0] * tx + r[1] * ty + r[2] * tz), -(r[3] * tx + r[4] * ty + r[5] * tz), -(r[6] * tx + r[7] * ty + r[8] * tz)]
    return [r[0], r[3], r[6], 0., r[1], r[4], r[7], 0., r[2], r[5], r[8], 0., t[0], t[1], t[2], 1.]


def decompose(m: list[float]) -> tuple[list[float], list[float], list[float]]:
    """Column-major affine matrix (no shear) -> Unity localPosition, localRotation (x, y, z, w), localScale."""
    cols = [[m[c * 4 + r] for r in range(3)] for c in range(3)]
    scale = [math.sqrt(sum(v * v for v in col)) for col in cols]
    if min(scale) < 1e-12:
        raise ValueError("degenerate scale in source physics hierarchy")
    rot = [[cols[c][r] / scale[c] for c in range(3)] for r in range(3)]   # rot[row][col]
    trace = rot[0][0] + rot[1][1] + rot[2][2]
    if trace > 0:
        s = math.sqrt(trace + 1.) * 2
        q = [(rot[2][1] - rot[1][2]) / s, (rot[0][2] - rot[2][0]) / s, (rot[1][0] - rot[0][1]) / s, .25 * s]
    elif rot[0][0] > rot[1][1] and rot[0][0] > rot[2][2]:
        s = math.sqrt(1. + rot[0][0] - rot[1][1] - rot[2][2]) * 2
        q = [.25 * s, (rot[0][1] + rot[1][0]) / s, (rot[0][2] + rot[2][0]) / s, (rot[2][1] - rot[1][2]) / s]
    elif rot[1][1] > rot[2][2]:
        s = math.sqrt(1. + rot[1][1] - rot[0][0] - rot[2][2]) * 2
        q = [(rot[0][1] + rot[1][0]) / s, .25 * s, (rot[1][2] + rot[2][1]) / s, (rot[0][2] - rot[2][0]) / s]
    else:
        s = math.sqrt(1. + rot[2][2] - rot[0][0] - rot[1][1]) * 2
        q = [(rot[0][2] + rot[2][0]) / s, (rot[1][2] + rot[2][1]) / s, .25 * s, (rot[1][0] - rot[0][1]) / s]
    n = math.sqrt(sum(v * v for v in q))
    return [m[12], m[13], m[14]], [v / n for v in q], scale


def father(transform: Any) -> Any | None:
    return transform.m_Father.read() if transform.m_Father else None


def in_model(transform: Any, mapping: Any) -> bool:
    """The transform belongs to the exported prefab (an AssetBundle can hold several prefabs)."""
    node = transform
    while node is not None:
        if object_id(node) in mapping.source_nodes:
            return True
        node = father(node)
    return False


class TransformTable:
    """Unity transforms referenced by a source-physics export, always with all their ancestors."""

    def __init__(self) -> None:
        self.transforms: dict[str, Any] = {}

    def add(self, transform: Any) -> str:
        key = str(object_id(transform)[1])
        known = self.transforms.get(key)
        if known is not None and object_id(known) != object_id(transform):
            raise ValueError(f"source physics transform path id {key} is not unique")
        node = transform
        while node is not None:
            k = str(object_id(node)[1])
            if k in self.transforms:
                break
            self.transforms[k] = node
            node = father(node)
        return key

    def add_subtree(self, transform: Any) -> None:
        self.add(transform)
        for child in transform.m_Children:
            self.add_subtree(child.read())

    def export(self, mapping: Any) -> list[dict[str, Any]]:
        exported = mapping.source_nodes

        def world(transform: Any) -> list[float] | None:
            index = exported.get(object_id(transform))
            return None if index is None else unity_from_gltf(mapping.neutral_world[index])

        out = []
        for key, transform in self.transforms.items():
            parent = father(transform)
            parent_key = str(object_id(parent)[1]) if parent is not None else None
            own = world(transform)
            parent_world = world(parent) if parent is not None else None
            p, r, s = transform.m_LocalPosition, transform.m_LocalRotation, transform.m_LocalScale
            prefab = [p.x, p.y, p.z], [r.x, r.y, r.z, r.w], [s.x, s.y, s.z]
            if own is not None and (parent is None or parent_world is not None):
                local = own if parent is None else mat_mul(inverse_affine(parent_world), own)
                position, rotation, scale = decompose(local)
            else:   # not in the GLB: its serialized local transform under its (posed) parent
                position, rotation, scale = prefab
            index = mapping.node_index(transform) if object_id(transform) in exported else None
            entry = {"id": key, "name": transform.m_GameObject.read().m_Name, "parentId": parent_key,
                     "siblingIndex": sibling_index(transform, parent),
                     "localPosition": [float(v) for v in position], "localRotation": [float(v) for v in rotation],
                     "localScale": [float(v) for v in scale], "node": index}
            if not same_local((position, rotation, scale), prefab):
                entry["prefabLocalPosition"] = [float(v) for v in prefab[0]]
                entry["prefabLocalRotation"] = [float(v) for v in prefab[1]]
                entry["prefabLocalScale"] = [float(v) for v in prefab[2]]
            out.append(entry)
        return out


def sibling_index(transform: Any, parent: Any | None) -> int | None:
    """Index of the transform in its parent's m_Children (Transform.GetSiblingIndex)."""
    if parent is None:
        return None
    key = object_id(transform)
    for index, child in enumerate(parent.m_Children):
        if child and object_id(child.read()) == key:
            return index
    raise ValueError(f"source physics transform {key[1]} is missing from its parent's children")


def same_local(a: tuple, b: tuple, tolerance: float = 1e-6) -> bool:
    """Two local transforms (position, rotation x/y/z/w, scale) agree; q and -q are the same rotation."""
    (pa, ra, sa), (pb, rb, sb) = a, b
    if any(abs(x - y) > tolerance for x, y in zip(list(pa) + list(sa), list(pb) + list(sb))):
        return False
    return abs(abs(sum(x * y for x, y in zip(ra, rb))) - 1.) <= tolerance
