"""UnityChan SpringBone data exported verbatim for the renderer's source-faithful solver.

physics.source.unitySpringBone = {"transforms": [...], "components": [...]} (see the renderer's
docs/model_physics_spec.md).  Every SpringManager / SpringBone / SpringBonePivot / Spring*Collider component of
the exported prefab keeps all serialized fields; references to other objects become {"transformId": id}.
The transform table (source_common.TransformTable) describes the GLB rest pose in Unity's frame.
"""

from __future__ import annotations

from typing import Any

from .source_common import TransformTable, in_model, unity_from_gltf
from .unity import game_object_transform

_unity_from_gltf = unity_from_gltf   # kept for callers of the first version

FAMILY = {"SpringManager", "SpringBone", "SpringBonePivot", "SpringSphereCollider", "SpringCapsuleCollider",
          "SpringPanelCollider"}
SKIP = {"m_ObjectHideFlags", "m_CorrespondingSourceObject", "m_PrefabInstance", "m_PrefabAsset", "m_Script",
        "m_EditorHideFlags", "m_EditorClassIdentifier", "m_Name", "m_GameObject"}


def _class(component: Any) -> str:
    return str(component.m_Script.read().m_ClassName)


def unity_springbone_source(readers: Any, mapping: Any) -> dict[str, Any] | None:
    """Collect the prefab's SpringBone family verbatim; None when it has no enabled SpringManager."""
    readers = list(readers)
    transform_by_pid = {reader.path_id: reader for reader in readers if reader.type.name == "Transform"}
    found, transform_of_component = [], {}
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
        if not in_model(transform, mapping):
            continue   # another prefab in the same AssetBundle
        found.append((cls, reader, transform))
        transform_of_component[reader.path_id] = transform
    if not any(cls == "SpringManager" and reader.read().m_Enabled for cls, reader, _ in found):
        return None

    table = TransformTable()

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
                return {"transformId": table.add(target)}
            return {k: convert(v) for k, v in value.items() if k not in SKIP}
        if isinstance(value, list):
            return [convert(v) for v in value]
        return value

    components = []
    for cls, reader, transform in found:
        components.append({"class": cls, "transformId": table.add(transform),
                           "fields": convert({k: v for k, v in reader.read_typetree().items() if k not in SKIP})})
        if cls == "SpringBone":   # ComputeChildPosition reads the bone's children (chain tips have no component)
            for child in transform.m_Children:
                table.add(child.read())
    return {"transforms": table.export(mapping), "components": components}
