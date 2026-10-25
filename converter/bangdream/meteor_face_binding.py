"""Bind original controller Head directions to the normalized body Head."""
from __future__ import annotations

import math

from UnityPy.classes import PPtr

from ..common.normalized_model import _mat4_inverse, _mat4_mul, _trs_to_mat
from ..common.unity import component_pointer


def _unit(vector):
    length = math.sqrt(sum(value * value for value in vector))
    if not math.isfinite(length) or length <= 1e-12:
        raise ValueError("Invalid Head rotation axis")
    return [value / length for value in vector]


def _dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def _cross(a, b):
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]


def _rotation_only(matrix):
    axes = [_unit(matrix[column * 4:column * 4 + 3]) for column in range(3)]
    if max(abs(_dot(axes[a], axes[b])) for a, b in [(0, 1), (0, 2), (1, 2)]) > 1e-4:
        raise ValueError("Source Head local matrix contains unresolved shear")
    if _dot(_cross(axes[0], axes[1]), axes[2]) < 0.9999:
        raise ValueError("Source Head local matrix has unresolved reflected scale")
    # Remove only accumulated float noise after validating the matrix is TRS.
    x = axes[0]
    y = _unit([axes[1][i] - x[i] * _dot(x, axes[1]) for i in range(3)])
    z = _cross(x, y)
    return [*x, 0.0, *y, 0.0, *z, 0.0, 0.0, 0.0, 0.0, 1.0]


def head_local_face_frame(nodes, head_index, neutral_world):
    """Return source world axes expressed in canonical Head rotation space.

    Native Transform.up/forward use world rotation, so extract each source
    local TRS before dropping scale; normalizing world-matrix columns would
    retain shear from nonuniform ancestor scale. Canonical rotation is composed
    from node quaternions, independently of translations and all node scales.
    """
    parents = {}
    for index, node in enumerate(nodes):
        for child in node.get("children", []):
            if child in parents:
                raise ValueError("Head hierarchy has multiple parents")
            parents[child] = index
    chain = []
    cursor = head_index
    while cursor is not None:
        if cursor in chain:
            raise ValueError("Cycle in Head hierarchy")
        chain.append(cursor)
        cursor = parents.get(cursor)
    identity = _trs_to_mat([0, 0, 0], [0, 0, 0, 1], [1, 1, 1])
    source_rotation = canonical_rotation = identity
    for index in reversed(chain):
        parent = parents.get(index)
        local = neutral_world[index] if parent is None else _mat4_mul(
            _mat4_inverse(neutral_world[parent]), neutral_world[index],
        )
        source_rotation = _mat4_mul(source_rotation, _rotation_only(local))
        quaternion = nodes[index].get("rotation", [0, 0, 0, 1])
        magnitude = math.sqrt(sum(float(value) ** 2 for value in quaternion))
        if not math.isfinite(magnitude) or magnitude <= 1e-12:
            raise ValueError("Invalid canonical Head quaternion")
        rotation = _trs_to_mat([0, 0, 0], [float(v) / magnitude for v in quaternion], [1, 1, 1])
        canonical_rotation = _mat4_mul(canonical_rotation, rotation)
    def to_local(column):
        world = source_rotation[column * 4:column * 4 + 3]
        return [_dot(canonical_rotation[c * 4:c * 4 + 3], world) for c in range(3)]
    return {"up": to_local(1), "forward": to_local(2)}


def native_body_face_transform_available(prefab_pointer):
    """Follow body.serialized materialController, then its same-GO Animator."""
    if not prefab_pointer:
        return False
    prefab = prefab_pointer.deref_parse_as_object()
    characters = []
    for entry in getattr(prefab, "m_Component", []):
        pointer = component_pointer(entry)
        if not pointer or pointer.type.name != "MonoBehaviour":
            continue
        data = pointer.deref_parse_as_object()
        script = getattr(data, "m_Script", None)
        if script and script.deref_parse_as_object().m_ClassName == "SkinnedMeshCharacter":
            tree = pointer.deref().read_typetree()
            characters.append((pointer, tree))
    if not characters:
        return False
    references = [tree.get("materialController") for _, tree in characters]
    if any(reference != references[0] for reference in references):
        raise ValueError("Ambiguous body serialized MaterialController")
    reference = references[0]
    if not reference or not reference["m_PathID"]:
        return False
    controller = PPtr(m_FileID=reference["m_FileID"], m_PathID=reference["m_PathID"],
                      assetsfile=characters[0][0].assetsfile).deref_parse_as_object()
    game_object = controller.m_GameObject.deref_parse_as_object()
    animators = [component_pointer(entry) for entry in game_object.m_Component
                 if component_pointer(entry) and component_pointer(entry).type.name == "Animator"]
    if len(animators) > 1:
        raise ValueError("Ambiguous Animator on body MaterialController GameObject")
    return bool(animators and getattr(animators[0].deref_parse_as_object(), "m_Avatar", None))


def finalize_body_face_frame(exported, *, role, prefab_pointer):
    if role != "body":
        return
    head = exported.standard_bones.get("Head")
    if head is None or not native_body_face_transform_available(prefab_pointer):
        return
    nodes = exported.builder.document["nodes"]
    nodes[head].setdefault("extras", {})["meteorFaceFrame"] = head_local_face_frame(
        nodes, head, exported.node_mapping.neutral_world,
    )
