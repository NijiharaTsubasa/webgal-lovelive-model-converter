"""Export native Unity transform constraints at the normalized bone seam."""

from __future__ import annotations

import math
from collections import Counter
from typing import Any

from ..common.unity import component_pointer, game_object_transform, object_id


def _walk(transform: Any):
    yield transform
    for child in transform.m_Children:
        if child:
            yield from _walk(child.deref_parse_as_object())


def _active(transform: Any) -> bool:
    while transform is not None:
        if not transform.m_GameObject.deref_parse_as_object().m_IsActive:
            return False
        transform = transform.m_Father.deref_parse_as_object() if transform.m_Father else None
    return True


def _number(value: Any) -> float:
    value = float(value)
    if not math.isfinite(value):
        raise ValueError("TransformConstraint requires finite numeric parameters")
    return value


def _vector(value: Any) -> list[float]:
    # Euler rest/offset values retain Unity's coordinates and degree units.
    return [_number(getattr(value, axis)) for axis in "xyz"]


def extract_transform_constraint_behavior(root: Any, exported: Any) -> list[dict[str, Any]]:
    """Retain source component and source-list order, independent of bone names.

    A frame's basis maps its canonical glTF bone world matrix to the source
    neutral frame: sourceWorld = canonicalWorld * basis. Parent frames supply
    the source local axes used by the native constraint's rest/offset controls.
    """
    if root is None:
        return []
    hierarchy = list(_walk(game_object_transform(root)))
    constraints = []
    for transform in hierarchy:
        for entry in transform.m_GameObject.deref_parse_as_object().m_Component:
            pointer = component_pointer(entry)
            if pointer and pointer.type.name in {"RotationConstraint", "PositionConstraint", "ParentConstraint"}:
                constraints.append((transform, pointer.type.name, pointer.deref_parse_as_object()))
    if not constraints:
        return []

    mapping = exported.node_mapping
    nodes = exported.builder.document["nodes"]
    counts = Counter(node.get("name") for node in nodes)
    frames, frame_ids = [], {}

    def frame(transform: Any) -> int:
        key = object_id(transform)
        if key in frame_ids:
            return frame_ids[key]
        node = mapping.node_index(transform)
        name = nodes[node].get("name")
        if not isinstance(name, str) or not name:
            raise ValueError("TransformConstraint requires a named exported node")
        if counts[name] != 1:
            # Name lookup must retain the exact serialized Transform identity.
            # Canonical Humanoid names stay on their designated core node.
            if node in exported.standard_bones.values():
                duplicates = [i for i, item in enumerate(nodes)
                              if i != node and item.get("name") == name]
            else:
                duplicates = [node]
            for duplicate in duplicates:
                suffix = 0
                stem = f"{name}__TransformConstraint_{duplicate}"
                unique = stem
                while counts[unique]:
                    suffix += 1
                    unique = f"{stem}_{suffix}"
                counts[name] -= 1
                counts[unique] += 1
                nodes[duplicate]["name"] = unique
            name = nodes[node]["name"]
        index = len(frames)
        frame_ids[key] = index
        hint = getattr(transform, "m_LocalEulerAnglesHint", None)
        frames.append({"node": name, "basis": mapping._local_matrix(transform, node)})
        if hint is not None and any(_vector(hint)):
            frames[index]["eulerHint"] = _vector(hint)
        parent = transform.m_Father.deref_parse_as_object() if transform.m_Father else None
        frames[index]["parent"] = frame(parent) if parent is not None else None
        return index

    rules = []
    for transform, native_type, constraint in constraints:
        rule = {
            "type": {"RotationConstraint": "rotation", "PositionConstraint": "position",
                     "ParentConstraint": "parent"}[native_type],
            "target": frame(transform),
            "sources": [{
                "frame": frame(source.sourceTransform.deref_parse_as_object())
                if source.sourceTransform else None,
                "weight": _number(source.weight),
            } for source in constraint.m_Sources],
            "weight": _number(constraint.m_Weight),
            "enabled": bool(constraint.m_Enabled) and _active(transform),
            "active": bool(constraint.m_Active),
        }
        if native_type == "RotationConstraint":
            rule.update(
                rotationAtRest=_vector(constraint.m_RotationAtRest),
                rotationOffset=_vector(constraint.m_RotationOffset),
                axes=[bool(getattr(constraint, f"m_AffectRotation{axis}")) for axis in "XYZ"],
            )
        elif native_type == "PositionConstraint":
            rule.update(
                translationAtRest=_vector(constraint.m_TranslationAtRest),
                translationOffset=_vector(constraint.m_TranslationOffset),
                axes=[bool(getattr(constraint, f"m_AffectTranslation{axis}")) for axis in "XYZ"],
            )
        else:
            rule.update(
                translationAtRest=_vector(constraint.m_TranslationAtRest),
                rotationAtRest=_vector(constraint.m_RotationAtRest),
                translationOffsets=[_vector(value) for value in constraint.m_TranslationOffsets],
                rotationOffsets=[_vector(value) for value in constraint.m_RotationOffsets],
                translationAxes=[bool(getattr(constraint, f"m_AffectTranslation{axis}")) for axis in "XYZ"],
                rotationAxes=[bool(getattr(constraint, f"m_AffectRotation{axis}")) for axis in "XYZ"],
            )
        rules.append(rule)
    return [{"name": "Garupa.TransformConstraint", "required": True,
             "parameters": {"frames": frames, "constraints": rules}}]
