"""Read the FaceController actually attached to the exported head prefab."""

from __future__ import annotations

import math
from copy import deepcopy
from typing import Any

from UnityPy.classes.PPtr import PPtr

from ..common.unity import component_pointer


def _reference(owner: Any, value: dict[str, Any], label: str) -> Any:
    """Resolve a serialized PPtr in its owning file, including external CABs."""
    try:
        pointer = PPtr(
            m_FileID=value["m_FileID"],
            m_PathID=value["m_PathID"],
            assetsfile=owner.assets_file,
        )
        return pointer.deref()
    except (KeyError, TypeError, ValueError, FileNotFoundError) as error:
        raise ValueError(f"FaceController {label}: unresolved source reference {value!r}") from error


def load_face_controller(prefab: Any) -> dict[str, Any] | None:
    """Preserve serialized map order and resolve explicit renderer/channel targets.

    Layer Shapes are offsets into BlendShapes, not the maps' Type values. Targets
    are renderer references plus channel indices, not names inferred from a pose.
    Empty targets and zero ranges are intentional and remain in the result.
    """
    if prefab is None:
        return None
    controllers = []
    for entry in prefab.m_Component:
        pointer = component_pointer(entry)
        if not pointer or pointer.type.name != "MonoBehaviour":
            continue
        reader = pointer.deref()
        tree = reader.read_typetree()
        script = _reference(reader, tree["m_Script"], "script").read_typetree()
        if script.get("m_ClassName") == "FaceController":
            controllers.append((reader, tree))
    if not controllers:
        return None
    if len(controllers) != 1:
        raise ValueError(f"{prefab.m_Name}: multiple FaceControllers attached to exported prefab root")

    reader, tree = controllers[0]
    maps = []
    # Several maps target the same renderer; avoid reparsing its Mesh per channel.
    mesh_cache: dict[tuple[int, int], dict[str, Any]] = {}
    for offset, source in enumerate(tree["BlendShapes"]):
        label = f"BlendShapes[{offset}] ({source['Name']})"
        minimum, maximum = float(source["RangeMin"]), float(source["RangeMax"])
        if not math.isfinite(minimum) or not math.isfinite(maximum):
            raise ValueError(f"FaceController {label}: non-finite source range")
        if minimum != 0:
            raise ValueError(f"FaceController {label}: nonzero RangeMin is not supported")
        targets = []
        for target in source["Targets"]:
            renderer = _reference(reader, target["Renderer"], f"{label} renderer")
            if renderer.type.name != "SkinnedMeshRenderer":
                raise ValueError(f"FaceController {label}: target is not a SkinnedMeshRenderer")
            key = (id(renderer.assets_file), renderer.path_id)
            if key not in mesh_cache:
                renderer_tree = renderer.read_typetree()
                mesh = _reference(renderer, renderer_tree["m_Mesh"], f"{label} mesh")
                if mesh.type.name != "Mesh":
                    raise ValueError(f"FaceController {label}: renderer mesh reference is not a Mesh")
                mesh_cache[key] = mesh.read_typetree()
            mesh_tree = mesh_cache[key]
            channels = mesh_tree["m_Shapes"]["channels"]
            index = target["Index"]
            if isinstance(index, bool) or not isinstance(index, int) or not 0 <= index < len(channels):
                raise ValueError(f"FaceController {label}: invalid target channel index {index!r}")
            full_name = channels[index]["name"]
            if not isinstance(full_name, str) or not full_name:
                raise ValueError(f"FaceController {label}: target channel has no name")
            targets.append({"mesh": mesh_tree["m_Name"], "morph": full_name.split(".", 1)[-1]})
        maps.append({
            "Name": source["Name"], "RangeMin": minimum, "RangeMax": maximum,
            "Type": source["Type"], "Targets": targets,
        })

    layers = deepcopy(tree["Layers"])
    for layer in layers:
        for mixer in layer["Mixers"]:
            for index in mixer["Shapes"]:
                if isinstance(index, bool) or not isinstance(index, int) or not 0 <= index < len(maps):
                    raise ValueError(
                        f"FaceController {layer['Name']}/{mixer['Name']}: "
                        f"invalid BlendShapes list offset {index!r}"
                    )
    return {"Layers": layers, "BlendShapes": maps}
