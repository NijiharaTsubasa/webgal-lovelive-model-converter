"""LLAS normal SafeCorrect inputs in the normalized model's coordinate frames."""

from __future__ import annotations

import math
from typing import Any

from converter.common.physics import _class, _transform, _vector
from converter.common.unity import object_id


def skirt_flags(name: str) -> int:
    # SwingBone.SetupSkirtInfo, LLAS RVA 0x2CB2D84.
    if "Skirt" not in name or "2_Dyna" in name:
        return 0
    if name.startswith("SkirtA1_Dyna"):
        return 7
    if name.startswith("SkirtE1_Dyna"):
        return 3
    for side, flag in (("Left", 1), ("Right", 2)):
        if any(name.startswith(f"{side}Skirt{part}1_Dyna") for part in "BCD"):
            return flag
    return 0


def _walk(transform: Any):
    yield transform
    for pointer in transform.m_Children:
        yield from _walk(pointer.read())


def source_frame(mapping: Any, transform: Any) -> list[float]:
    """Column-major source Unity local axes -> normalized node local frame.

    The frame includes the handedness reflection; it is a general affine
    matrix, not a quaternion. Native local Y rotations and negative-X edits
    must both pass through this same frame.
    """
    columns = [mapping.direction(transform, axis) for axis in
               ([1., 0., 0.], [0., 1., 0.], [0., 0., 1.])]
    return [value for column in columns for value in (*column, 0.)] + [
        *mapping.point(transform, [0., 0., 0.]), 1.]


def build_skirt_behavior(environment: Any, exported: Any) -> dict[str, Any] | None:
    mapping = exported.node_mapping
    document = exported.builder.document
    name_of = lambda transform: document["nodes"][mapping.node_index(transform)]["name"]
    groups = []
    for reader in environment.objects:
        if reader.type.name != "MonoBehaviour":
            continue
        manager = reader.read()
        if not manager.m_Script or _class(manager) != "SwingBoneManager" or not manager.m_Enabled:
            continue
        root = _transform(manager)
        if object_id(root) not in mapping.source_nodes:
            continue
        knees = [None, None]
        # SetupKneeInfo (0x2CB9628) rebuilds these references at initialization.
        for transform in _walk(root):
            source_name = transform.m_GameObject.read().m_Name
            for index, marker in enumerate(("LeftUpLeg", "RightUpLeg")):
                if marker in source_name:
                    knees[index] = transform
        bones = []
        for pointer in manager.bones:
            if not pointer:
                continue
            component = pointer.read()
            transform = _transform(component)
            flags = skirt_flags(transform.m_GameObject.read().m_Name)
            if not (component.m_Enabled and component.skirtSafeEnable and flags and component.child):
                continue
            parent = transform.m_Father.read()
            child = component.child.read()
            start = mapping.source_world[mapping.source_nodes[object_id(transform)]][12:15]
            end = mapping.source_world[mapping.source_nodes[object_id(child)]][12:15]
            # Missing serialized fields retain SwingBone..ctor defaults in the
            # current APK (0x2CB55AC, constants at 0x56ED2C0).
            offset = (getattr(component, "kneeSpaceOffsetFront", .02) if flags & 4
                      else getattr(component, "kneeSpaceOffsetOther", .04))
            bones.append({
                "node": name_of(transform), "parent": name_of(parent), "child": name_of(child),
                "parentFrame": source_frame(mapping, parent),
                "axis": mapping.direction(transform, _vector(component.boneAxis)),
                "length": math.dist(start, end),
                "knees": [i for i, mask in enumerate((1, 2)) if flags & mask],
                "dotMin": float(component.skirtLimitDotMin),
                "dotMax": float(component.skirtLimitDotMax),
                "rotationDegrees": float(component.skirtRotDegMax),
                "kneeSpaceOffset": float(offset),
            })
        if not bones:
            continue
        if any(knee is None for knee in knees):
            raise ValueError("LLAS skirt correction requires both source UpperLeg transforms")
        groups.append({
            "knees": [{"node": name_of(knee), "right": mapping.direction(knee, [1., 0., 0.])}
                      for knee in knees],
            "bones": bones,
        })
    if not groups:
        return None
    return {"name": "LLAS.SkirtSafe", "required": True, "parameters": {"managers": groups}}
