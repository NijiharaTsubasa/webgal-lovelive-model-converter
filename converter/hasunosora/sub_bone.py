"""Export source SubBoneController rules and frames as Hasunosora.SubBoneController."""

from __future__ import annotations

import math
from collections import Counter
from typing import Any

from ..common.normalized_model import _mat4_inverse, _mat4_mul
from ..common.unity import component_pointer, game_object_transform, object_id


def _walk_paths(transform: Any, path: tuple[int, ...] = ()):
    yield transform, path
    for index, child in enumerate(transform.m_Children):
        yield from _walk_paths(child.read(), path + (index,))


def _active(transform: Any) -> bool:
    while transform is not None:
        if not transform.m_GameObject.read().m_IsActive:
            return False
        transform = transform.m_Father.read() if transform.m_Father else None
    return True


def _vector(value: Any, axes: str) -> list[float]:
    result = [float(getattr(value, axis)) for axis in axes]
    if not all(math.isfinite(component) for component in result):
        raise ValueError("SubBoneController has a non-finite initialization vector")
    if axes == "xyzw" and sum(component * component for component in result) < 1e-12:
        raise ValueError("SubBoneController has a zero initialization quaternion")
    return result


def _rotation_basis(matrix: list[float]) -> bool:
    return all(abs(sum(matrix[a * 4 + k] * matrix[b * 4 + k] for k in range(3))
                   - (1. if a == b else 0.)) <= 1e-5
               for a in range(3) for b in range(3))


def build_sub_bone_parameters(controller: Any, exported: Any) -> dict[str, Any]:
    """Resolve names once in the source controller's child-index DFS domain.

    Runtime names refer to unique exported nodes. Each basis converts that
    node's canonical local frame to its corresponding source zero-muscle frame.
    """
    mapping = exported.node_mapping
    nodes = exported.builder.document["nodes"]
    counts = Counter(node.get("name") for node in nodes)
    paths = list(_walk_paths(game_object_transform(controller.m_GameObject.read())))
    domain = [transform for transform, _path in paths]
    source_paths = {object_id(transform): path for transform, path in paths}
    by_name = {}
    for transform in domain:
        by_name.setdefault(transform.m_GameObject.read().m_Name, transform)
    hips = [transform for transform in domain
            if mapping.node_index(transform) == exported.standard_bones.get("Hips")]
    if len(hips) != 1:
        raise ValueError("SubBoneController requires one mapped Humanoid Hips in its search domain")
    prefix = hips[0].m_GameObject.read().m_Name.split("_")[0] + "_"

    def prefixed(name):
        return name[:10] + prefix + name[10:] if "Extension_" in name else prefix + name

    frames, frame_ids = [], {}

    def frame(transform):
        key = object_id(transform)
        if key in frame_ids:
            return frame_ids[key]
        index = mapping.node_index(transform)
        name = nodes[index].get("name")
        if not name:
            raise ValueError("SubBoneController requires a named exported node")
        if counts[name] != 1:
            if index in exported.standard_bones.values():
                raise ValueError(f"SubBoneController core node name is ambiguous: {name!r}")
            # Name-based runtime lookup must still identify the exact source
            # Transform chosen by the controller's child-index DFS.
            path = "_".join(map(str, source_paths[key])) or "root"
            stem = f"{name}__SubBone_{path}"
            unique = stem
            suffix = 1
            while counts[unique]:
                unique = f"{stem}_{suffix}"
                suffix += 1
            counts[name] -= 1
            counts[unique] += 1
            nodes[index]["name"] = name = unique
        basis = mapping._local_matrix(transform, index)
        frame_id = len(frames)
        frame_ids[key] = frame_id
        frames.append({"node": name, "basis": basis})
        return frame_id

    def local_frame(transform):
        index = frame(transform)
        parent = transform.m_Father.read() if transform.m_Father else None
        frames[index]["parent"] = frame(parent) if parent is not None else None
        return index

    definitions = controller.master.read().definitions
    if len(definitions) != len(controller.data):
        raise ValueError("SubBoneController master/data count mismatch")
    rules = []
    for definition, data in zip(definitions, controller.data):
        category = int(definition.category)
        if category not in (1, 2, 7):
            raise ValueError(f"SubBoneController category {category} has not been recovered")
        if not definition.inputs or not definition.outputs:
            raise ValueError("SubBoneController rule requires input and output nodes")
        input_name = prefixed(definition.inputs[0])
        output_names = [prefixed(name) for name in definition.outputs]
        # The source associates metadata by index, not by these labels.
        # Only master names participate in its Transform lookup.
        try:
            input_transform = by_name[input_name]
            outputs = [by_name[name] for name in output_names]
        except KeyError as error:
            raise ValueError(f"SubBoneController source Transform missing: {error.args[0]}") from error
        for output in outputs:
            key = object_id(output)
            index = mapping.node_index(output)
            if index in exported.standard_bones.values() or mapping.source_nodes[key] != index:
                raise ValueError("SubBoneController output must be an unredirected auxiliary node")
            parent = output.m_Father.read() if output.m_Father else None
            parent_index = mapping.node_index(parent) if parent else None
            actual_parent = next((i for i, node in enumerate(nodes)
                                  if index in node.get("children", [])), None)
            if actual_parent != parent_index:
                raise ValueError("SubBoneController output requires its original direct parent")
            basis = mapping._local_matrix(output, index)
            parent_basis = mapping._local_matrix(parent, parent_index) if parent else None
            # Source local position/rotation map separately only with a rotation
            # basis at the same pivot. Reject affine cases requiring channel mixing.
            if (max(abs(basis[i]) for i in (12, 13, 14)) > 1e-5
                    or not _rotation_basis(basis)
                    or (parent_basis is not None and not _rotation_basis(parent_basis))):
                raise ValueError("SubBoneController output requires a rigid basis at the source pivot")
        magnification = float(definition.magnification)
        if not math.isfinite(magnification):
            raise ValueError("SubBoneController magnification must be finite")
        rule = {"category": category, "input": local_frame(input_transform),
                "outputs": [local_frame(output) for output in outputs],
                "magnification": magnification,
                "initialMainRotation": _vector(data.initialMainRotation, "xyzw")}
        if category == 1:
            rule.update(initialMainRight=_vector(data.initialMainRight, "xyz"),
                        initialSubRotation=_vector(data.initialSubRotation, "xyzw"))
        elif category == 7:
            minimum, maximum = float(definition.minAngle), float(definition.maxAngle)
            input_axis, output_axis = int(definition.inputAxis), int(definition.outputAxis)
            if input_axis not in range(4) or output_axis not in range(4):
                raise ValueError("SubBoneController Move axis has not been recovered")
            if not math.isfinite(minimum) or not math.isfinite(maximum) or minimum > maximum:
                raise ValueError("SubBoneController Move angle range is invalid")
            rule.update(initialSubPosition=_vector(data.initialSubPosition, "xyz"),
                        inputAxis=input_axis, outputAxis=output_axis,
                        minAngle=minimum, maxAngle=maximum)
        rules.append(rule)
    parents = {child: index for index, node in enumerate(nodes) for child in node.get("children", [])}
    by_exported_name = {node.get("name"): index for index, node in enumerate(nodes)}

    def ancestors(index):
        result = set()
        while index is not None:
            if index in result:
                raise ValueError("SubBoneController canonical hierarchy contains a cycle")
            result.add(index)
            index = parents.get(index)
        return result

    first_writer = {}
    for rule_index, rule in enumerate(rules):
        channel = "position" if rule["category"] == 7 else "rotation"
        for output in rule["outputs"]:
            first_writer.setdefault((by_exported_name[frames[output]["node"]], channel), rule_index)
    for rule_index, rule in enumerate(rules):
        input_frame = frames[rule["input"]]
        input_node = by_exported_name[input_frame["node"]]
        parent_node = (by_exported_name[frames[input_frame["parent"]]["node"]]
                       if input_frame["parent"] is not None else None)
        # Shared ancestors cancel in inverse(sourceParentWorld)*sourceWorld.
        # Every other written dependency must be rebuilt before this read;
        # otherwise restoring animation-owned channels erases source feedback.
        for dependency in ancestors(input_node) ^ ancestors(parent_node):
            if any(node == dependency and first >= rule_index
                   for (node, _channel), first in first_writer.items()):
                raise ValueError("SubBoneController cross-frame feedback requires source state semantics")
    return {"frames": frames, "rules": rules}


def extract_sub_bone_behavior(root: Any, exported: Any) -> list[dict[str, Any]]:
    controllers = []
    for transform, _path in _walk_paths(game_object_transform(root)):
        if not _active(transform):
            continue
        for entry in transform.m_GameObject.read().m_Component:
            pointer = component_pointer(entry)
            if not pointer or pointer.type.name != "MonoBehaviour":
                continue
            component = pointer.read()
            if component.m_Script.read().m_ClassName == "SubBoneController" and component.m_Enabled:
                controllers.append(component)
    if not controllers:
        return []
    if len(controllers) != 1:
        raise ValueError("Multiple active SubBoneControllers require source execution-order evidence")
    return [{"name": "Hasunosora.SubBoneController", "required": True,
             "parameters": build_sub_bone_parameters(controllers[0], exported)}]
