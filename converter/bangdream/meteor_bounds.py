"""Export renderer-local bounds and ordered nonempty per-bone boxes."""
from __future__ import annotations

import math
from UnityPy.helpers.MeshHelper import MeshHandler

from ..common.unity import game_object_transform
from ..common.glb import trim_unused_trailing_renderer_bones


def _xyz(value):
    result = [float(getattr(value, axis)) for axis in "xyz"]
    if not all(math.isfinite(x) for x in result):
        raise ValueError("Non-finite original renderer bounds")
    return result


def _box(value):
    if hasattr(value, "m_Min") and hasattr(value, "m_Max"):
        # Original empty MinMaxAABB sentinel. Native Null-device readback in
        # webgal-lovelive-game-runtime/tests/fixtures/meteor-bounds-native.json
        # (emptyBoxCases) proves it contributes no box;
        # replacing it with a zero-size origin box changes the native result.
        if all(getattr(value.m_Min, a) == math.inf and getattr(value.m_Max, a) == -math.inf
               for a in "xyz"):
            return {"empty": True}
        lower, upper = _xyz(value.m_Min), _xyz(value.m_Max)
        if any(a > b for a, b in zip(lower, upper)):
            raise ValueError("Invalid original per-bone MinMaxAABB")
        center = [(a + b) * 0.5 for a, b in zip(lower, upper)]
        extents = [(b - a) * 0.5 for a, b in zip(lower, upper)]
    else:
        center, extents = _xyz(value.m_Center), _xyz(value.m_Extent)
    if any(x < 0 for x in extents):
        raise ValueError("Negative original bounds extents")
    return {"center": [-center[0], center[1], center[2]], "extents": extents}


def attach_renderer_bounds(exported, renderer_bindings, *, role):
    if role not in {"head", "body"}:
        return
    mapping = exported.node_mapping
    nodes = exported.builder.document["nodes"]

    def binding(transform):
        node = mapping.node_index(transform)
        if not 0 <= node < len(nodes):
            raise ValueError("Bounds bone anchor is outside exported nodes")
        anchor = f"{role}:{node}"
        extras = nodes[node].setdefault("extras", {})
        if extras.get("meteorBoundsAnchor", anchor) != anchor:
            raise ValueError("Conflicting bounds anchor identity")
        extras["meteorBoundsAnchor"] = anchor
        matrix = list(mapping._local_matrix(transform, None))
        if len(matrix) != 16 or not all(math.isfinite(float(x)) for x in matrix):
            raise ValueError("Invalid source-to-canonical bounds binding")
        return {"node": anchor, "bindMatrix": matrix}

    for renderer, mesh_node in renderer_bindings:
        source = getattr(renderer, "source_renderer", renderer)
        bones = list(source.m_Bones)
        mesh = source.m_Mesh.deref_parse_as_object()
        boxes = list(mesh.m_BonesAABB)
        bind_poses = list(mesh.m_BindPose)
        if len(boxes) != len(bind_poses) or len(bones) < len(boxes):
            raise ValueError(f"{mesh.m_Name}: {len(bones)} renderer bones, {len(bind_poses)} bind poses, {len(boxes)} original bone AABBs do not correspond")
        if len(bones) > len(boxes):
            decoded = MeshHandler(mesh)
            decoded.process()
            bones = trim_unused_trailing_renderer_bones(
                mesh.m_Name, bones, bind_poses,
                decoded.m_BoneIndices or [], decoded.m_BoneWeights or [],
            )
        root = getattr(source, "m_RootBone", None)
        if not root:
            root = game_object_transform(source.m_GameObject.deref_parse_as_object())
        local_bounds = getattr(source, "m_AABB", None)
        if local_bounds is None:
            local_bounds = source.m_LocalAABB
        entries = []
        for pointer, box in zip(bones, boxes):
            if not pointer:
                raise ValueError(f"{mesh.m_Name}: original bounds references a null bone")
            bounds = _box(box)
            if bounds.get("empty"):
                continue
            entries.append({**binding(pointer), **bounds})
        if not entries:
            raise ValueError(f"{mesh.m_Name}: original bounds have no nonempty bone boxes")
        nodes[mesh_node].setdefault("extras", {})["meteorBounds"] = {
            "rendererId": str(source.object_reader.path_id),
            "root": binding(root),
            "updateWhenOffscreen": bool(source.m_UpdateWhenOffscreen),
            "localBounds": _box(local_bounds),
            "bones": entries,
        }
