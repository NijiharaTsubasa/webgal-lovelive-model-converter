"""Authored LLAS body adjustments supplied to the Unity preprocessing step.

Native CommonCoreMember.Initialize (0x27C2B90) and LiveCoreMember.Initialize
(0x2FE0FD4) apply NodeScaling.ApplyScale(1) after merging an ordinary face.
ApplyScale (0x2FE1E00) writes scale, position, then local Euler rotation arrays.
At t=1 the original Vector3.Lerp selects each serialized scaledValue.
"""

from pathlib import Path
from types import SimpleNamespace

import UnityPy

from converter.common.physics import _class
from converter.common.unity import object_id, component_pointer, game_object_transform
from converter.llas.face_source import _pointer
from converter.llas.face_composition import needs_face_graft


def scaling_for_member(face):
    root = game_object_transform(face.root.read())
    paths = {}

    def visit(transform, path):
        paths[object_id(transform)] = path
        for index, pointer in enumerate(p for p in transform.m_Children if p):
            visit(pointer.read(), path + [index])

    visit(root, [])
    result = {"name": face.name, "scaleValues": [], "positionValues": [], "rotationValues": []}
    if not needs_face_graft(face.head_all, face.needs_merging_face):
        return result
    for entry in face.root.read().m_Component:
        pointer = component_pointer(entry)
        if not pointer or pointer.type.name != "MonoBehaviour":
            continue
        component = pointer.read()
        if not component.m_Script or _class(component) != "LiveCoreMemberNodeScaling":
            continue
        if object_id(game_object_transform(component.m_GameObject.read())) != object_id(root):
            continue
        reader = component.object_reader
        fields = reader.read_typetree()
        for field in ("scaleValues", "positionValues", "rotationValues"):
            for entry in fields[field]:
                target = _pointer(reader, entry["target"]).read()
                result[field].append({
                    "path": paths[object_id(target)],
                    "value": [float(entry["scaledValue"][axis]) for axis in "xyz"],
                })
        # Native GetComponent selects the scaling component on the member root.
        break
    return result


def scaling_for_source(source: Path):
    environment = UnityPy.load(source.read_bytes())
    roots = [pointer for name, pointer in environment.container.items()
             if name.lower().endswith("_member.prefab") and pointer.type.name == "GameObject"]
    root, = roots
    member = root.read()
    managers = [pointer.read() for entry in member.m_Component
                if (pointer := component_pointer(entry)) and pointer.type.name == "MonoBehaviour"
                and _class(pointer.read()) == "BodyPartManager"]
    manager, = managers
    reader = manager.object_reader
    head_all = _pointer(reader, reader.read_typetree()["headAll"]).read()
    return scaling_for_member(SimpleNamespace(environment=environment, root=root,
        name=member.m_Name, head_all=game_object_transform(head_all), needs_merging_face=True))
