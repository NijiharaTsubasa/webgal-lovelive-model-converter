"""UnityChan SpringBone data exported verbatim for the renderer's source-faithful solver.

physics.source.unitySpringBone = {"transforms": [...], "components": [...]} (see the renderer's
docs/model_physics_spec.md).  Every SpringManager / SpringBone / SpringBonePivot / Spring*Collider component of
the exported prefab keeps all serialized fields; references to other objects become {"transformId": id}.
Transform ids are path ids as decimal strings (64-bit values do not survive JSON numbers in JavaScript).

The transforms are the Unity local transforms of the pose the GLB rest pose was exported in: exported nodes take
their Unity-baked neutral pose (mapping.neutral_world, reflected back to Unity's left-handed frame), nodes absent
from the GLB (pivots, collider holders) keep their serialized local transform under that parent.  The renderer
fits Unity <-> GLB from these and binds every node by its "node" index.
"""

from __future__ import annotations

import math
from typing import Any

from .unity import game_object_transform, object_id

FAMILY = {"SpringManager", "SpringBone", "SpringBonePivot", "SpringSphereCollider", "SpringCapsuleCollider",
          "SpringPanelCollider"}
SKIP = {"m_ObjectHideFlags", "m_CorrespondingSourceObject", "m_PrefabInstance", "m_PrefabAsset", "m_Script",
        "m_EditorHideFlags", "m_EditorClassIdentifier", "m_Name", "m_GameObject"}
_FLIP = (-1., 1., 1., 1.)


def _unity_from_gltf(matrix: list[float]) -> list[float]:
    """Column-major glTF (X-reflected) matrix -> column-major Unity matrix: F M F."""
    return [matrix[c * 4 + r] * _FLIP[r] * _FLIP[c] for c in range(4) for r in range(4)]


def _mul(a: list[float], b: list[float]) -> list[float]:
    return [sum(a[k * 4 + r] * b[c * 4 + k] for k in range(4)) for c in range(4) for r in range(4)]


def _inverse_affine(m: list[float]) -> list[float]:
    a, b, c = m[0], m[4], m[8]
    d, e, f = m[1], m[5], m[9]
    g, h, i = m[2], m[6], m[10]
    det = a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g)
    if abs(det) < 1e-20:
        raise ValueError("singular transform in SpringBone hierarchy")
    k = 1. / det
    r = [(e * i - f * h) * k, -(b * i - c * h) * k, (b * f - c * e) * k,
         -(d * i - f * g) * k, (a * i - c * g) * k, -(a * f - c * d) * k,
         (d * h - e * g) * k, -(a * h - b * g) * k, (a * e - b * d) * k]
    tx, ty, tz = m[12], m[13], m[14]
    t = [-(r[0] * tx + r[1] * ty + r[2] * tz), -(r[3] * tx + r[4] * ty + r[5] * tz), -(r[6] * tx + r[7] * ty + r[8] * tz)]
    # r is row-major; back to column-major
    return [r[0], r[3], r[6], 0., r[1], r[4], r[7], 0., r[2], r[5], r[8], 0., t[0], t[1], t[2], 1.]


def _decompose(m: list[float]) -> tuple[list[float], list[float], list[float]]:
    """Column-major affine matrix (no shear) -> Unity localPosition, localRotation (x, y, z, w), localScale."""
    cols = [[m[c * 4 + r] for r in range(3)] for c in range(3)]
    scale = [math.sqrt(sum(v * v for v in col)) for col in cols]
    if min(scale) < 1e-12:
        raise ValueError("degenerate scale in SpringBone hierarchy")
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


def _class(component: Any) -> str:
    return str(component.m_Script.read().m_ClassName)


def unity_springbone_source(readers: Any, mapping: Any) -> dict[str, Any] | None:
    """Collect the prefab's SpringBone family verbatim; None when it has no enabled SpringManager."""
    # component path id -> (class, component, typetree, Transform)
    found = []
    transform_of_component: dict[int, Any] = {}
    exported = mapping.source_nodes

    def in_model(transform: Any) -> bool:
        node = transform
        while node is not None:
            if object_id(node) in exported:
                return True
            node = node.m_Father.read() if node.m_Father else None
        return False

    readers = list(readers)
    transform_by_pid: dict[int, Any] = {}
    for reader in readers:
        if reader.type.name == "Transform":
            transform_by_pid[reader.path_id] = reader
    for reader in readers:
        if reader.type.name != "MonoBehaviour":
            continue
        component = reader.read()
        if not component.m_Script:
            continue
        cls = _class(component)
        if cls not in FAMILY:
            continue
        transform = game_object_transform(component.m_GameObject.read())
        if not in_model(transform):
            continue   # another prefab in the same AssetBundle
        found.append((cls, component, reader, transform))
        transform_of_component[reader.path_id] = transform
    if not any(cls == "SpringManager" and component.m_Enabled for cls, component, _, _ in found):
        return None

    transforms: dict[str, Any] = {}

    def tid(transform: Any) -> str:
        key = str(object_id(transform)[1])
        if key in transforms and transforms[key] is not transform and object_id(transforms[key]) != object_id(transform):
            raise ValueError(f"SpringBone transform path id {key} is not unique")
        node = transform
        while node is not None:   # register the transform and all its ancestors
            k = str(object_id(node)[1])
            if k in transforms:
                break
            transforms[k] = node
            node = node.m_Father.read() if node.m_Father else None
        return key

    def convert(value: Any) -> Any:
        if isinstance(value, dict):
            if set(value) == {"m_FileID", "m_PathID"}:
                pid = value["m_PathID"]
                if not pid:
                    return None
                target = transform_of_component.get(pid)
                if target is None and pid in transform_by_pid:   # a direct Transform reference
                    target = transform_by_pid[pid].read()
                if target is None:
                    raise ValueError(f"SpringBone reference {pid} does not resolve to a component of this model")
                return {"transformId": tid(target)}
            return {k: convert(v) for k, v in value.items() if k not in SKIP}
        if isinstance(value, list):
            return [convert(v) for v in value]
        return value

    components = []
    for cls, component, reader, transform in found:
        components.append({"class": cls, "transformId": tid(transform),
                           "fields": convert({k: v for k, v in reader.read_typetree().items() if k not in SKIP})})
        if cls == "SpringBone":   # ComputeChildPosition reads the bone's children (chain tips have no component)
            for child in transform.m_Children:
                tid(child.read())

    def world(key: str) -> list[float] | None:
        transform = transforms[key]
        source_index = exported.get(object_id(transform))
        return None if source_index is None else _unity_from_gltf(mapping.neutral_world[source_index])

    out = []
    for key, transform in transforms.items():
        father = transform.m_Father.read() if transform.m_Father else None
        parent_key = str(object_id(father)[1]) if father is not None else None
        own = world(key)
        if own is not None and (parent_key is None or world(parent_key) is not None):
            local = own if parent_key is None else _mul(_inverse_affine(world(parent_key)), own)
            position, rotation, scale = _decompose(local)
        else:   # not in the GLB: its serialized local transform under its (posed) parent
            p, r, s = transform.m_LocalPosition, transform.m_LocalRotation, transform.m_LocalScale
            position, rotation, scale = [p.x, p.y, p.z], [r.x, r.y, r.z, r.w], [s.x, s.y, s.z]
        index = mapping.node_index(transform) if object_id(transform) in exported else None
        out.append({"id": key, "name": transform.m_GameObject.read().m_Name, "parentId": parent_key,
                    "localPosition": [float(v) for v in position], "localRotation": [float(v) for v in rotation],
                    "localScale": [float(v) for v in scale], "node": index})
    return {"transforms": out, "components": components}
