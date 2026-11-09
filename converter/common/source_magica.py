"""MagicaCloth2 data exported verbatim for the renderer's source-faithful cloth solver.

physics.source.magicaCloth2 = {"transforms": [...], "components": [...]} (renderer docs/model_physics_spec.md):
  components  every MagicaCloth / MagicaCapsuleCollider / MagicaSphereCollider / MagicaPlaneCollider /
              ExtendClothSettings (game addition) of the exported prefab, all serialized fields kept;
  transforms  the Unity transform table of source_common (GLB rest pose in Unity's frame, GLB node indices),
              including every bone below a BoneCloth root.
References become objects instead of path ids:
  Transform / GameObject           {"transformId"}
  component (MonoBehaviour)        {"transformId", "class"}
  SkinnedMeshRenderer / Renderer   {"transformId", "class", "mesh": {"name", "node", "primitives"}}
  Mesh                             {"mesh": {"name", "node", "primitives"}}  (node = the GLB renderer node, or null)
  asset (ScriptableObject)         {"asset", "class"}
  Texture2D                        {"texture"}
Raw byte arrays (ExSimpleNativeArray arrayBytes and the VirtualMesh / RenderSetupData byte[] fields) are
{"base64": ...}: little-endian structs exactly as MagicaCloth2 serializes them (layouts: MagicaCloth2 source,
VirtualMeshSerialization.cs / RenderSetupDataSerialization.cs).
PreBuild: MagicaCloth.serializeData2.preBuildData keeps "enabled", "buildId", "uniquePreBuildData"; its
"preBuildScriptableObject" reference becomes {"asset", "class"} and the matching SharePreBuildData entry of that
asset (same buildId) is embedded as "sharePreBuildData".  Its renderSetupDataList entries drop the copy of the
original mesh (localPositions / localNormals / localTangents / bindPoseList / bonesPerVertexArray /
boneWeightArray, 250+ KB per skirt): the GLB carries that mesh, and the render-vertex -> proxy mapping with the
mesh-space vertex positions is in renderMeshList.
Floats are float32 values written in their shortest round-trip form (Math.fround recovers the exact float32).
"""

from __future__ import annotations

import base64
import struct
from typing import Any

from .normalized_model import renderer_node_name
from .source_common import TransformTable, in_model
from .unity import game_object_transform

FAMILY = {"MagicaCloth", "MagicaCapsuleCollider", "MagicaSphereCollider", "MagicaPlaneCollider", "ExtendClothSettings"}
SKIP = {"m_ObjectHideFlags", "m_CorrespondingSourceObject", "m_PrefabInstance", "m_PrefabAsset", "m_Script",
        "m_EditorHideFlags", "m_EditorClassIdentifier", "m_Name", "m_GameObject"}
BYTE_FIELDS = {
    "arrayBytes",
    # VirtualMesh.ShareSerializationData (proxy mesh)
    "vertexToTriangles", "vertexToVertexIndexArray", "vertexToVertexDataArray", "edges", "edgeFlags",
    "vertexBindPosePositions", "vertexBindPoseRotations", "vertexToTransformRotations", "vertexDepths",
    "vertexRootIndices", "vertexParentIndices", "vertexChildIndexArray", "vertexChildDataArray",
    "vertexLocalPositions", "vertexLocalRotations", "normalAdjustmentRotations", "baseLineFlags",
    "baseLineStartDataIndices", "baseLineDataCounts", "baseLineData",
    # RenderSetupData.ShareSerializationData
    "bonesPerVertexArray", "boneWeightArray",
}


MESH_COPY = {"localPositions", "localNormals", "localTangents", "bindPoseList", "bonesPerVertexArray", "boneWeightArray"}


def _f32(value: float) -> float:
    """A float32 value in its shortest decimal form that still parses back to the same float32."""
    single = struct.unpack("<f", struct.pack("<f", value))[0]
    if single != value:      # not a float32 (a double field): keep it
        return value
    for digits in range(6, 10):
        text = f"{value:.{digits}g}"
        if struct.unpack("<f", struct.pack("<f", float(text)))[0] == single:
            return float(text)
    return value


def _class(component: Any) -> str:
    return str(component.m_Script.read().m_ClassName)


def _kind(obj: Any) -> str:
    return obj.object_reader.type.name


def magica_cloth2_source(readers: Any, mapping: Any, document: dict[str, Any] | None = None) -> dict[str, Any] | None:
    """Collect the prefab's MagicaCloth2 components verbatim; None when it has no enabled MagicaCloth."""
    found = []
    for reader in readers:
        if reader.type.name != "MonoBehaviour":
            continue
        component = reader.read()
        if not component.m_Script or not component.m_GameObject:
            continue
        cls = _class(component)
        if cls not in FAMILY:
            continue
        transform = game_object_transform(component.m_GameObject.read())
        if not in_model(transform, mapping):
            continue   # another prefab in the same AssetBundle
        found.append((cls, reader, component, transform))
    if not any(cls == "MagicaCloth" and component.m_Enabled for cls, _, component, _ in found):
        return None

    table = TransformTable()
    nodes = (document or {}).get("nodes", [])
    meshes = (document or {}).get("meshes", [])

    def mesh_ref(mesh: Any) -> dict[str, Any]:
        name = str(mesh.m_Name)
        node = next((i for i, n in enumerate(nodes) if n.get("name") == renderer_node_name(name) and "mesh" in n
                     and meshes[n["mesh"]].get("name") == name), None)
        return {"name": name, "node": node,
                "primitives": len(meshes[nodes[node]["mesh"]]["primitives"]) if node is not None else None}

    def ref(pointer: Any) -> dict[str, Any] | None:
        if not pointer or not pointer.m_PathID:
            return None
        target = pointer.read()
        kind = _kind(target)
        if kind in ("Transform", "RectTransform"):
            return {"transformId": table.add(target)}
        if kind == "GameObject":
            return {"transformId": table.add(game_object_transform(target))}
        if kind in ("SkinnedMeshRenderer", "MeshRenderer"):
            holder = game_object_transform(target.m_GameObject.read())
            out = {"transformId": table.add(holder), "class": kind}
            if kind == "SkinnedMeshRenderer" and target.m_Mesh:
                out["mesh"] = mesh_ref(target.m_Mesh.read())
            return out
        if kind == "Mesh":
            return {"mesh": mesh_ref(target)}
        if kind == "MonoBehaviour":
            cls = _class(target)
            if target.m_GameObject:
                return {"transformId": table.add(game_object_transform(target.m_GameObject.read())), "class": cls}
            return {"asset": str(target.m_Name), "class": cls}
        if kind == "Texture2D":
            return {"texture": str(target.m_Name)}
        return {"ref": kind, "name": str(getattr(target, "m_Name", ""))}

    def convert(tree: Any, obj: Any, key: str | None = None) -> Any:
        if isinstance(tree, dict):
            if set(tree) == {"m_FileID", "m_PathID"}:
                return ref(obj)
            return {k: convert(v, getattr(obj, k, None), k) for k, v in tree.items() if k not in SKIP}
        if key in BYTE_FIELDS and isinstance(tree, (list, bytes, bytearray)) \
                and all(isinstance(x, int) and 0 <= x < 256 for x in tree):
            return {"base64": base64.b64encode(bytes(tree)).decode("ascii")}
        if isinstance(tree, list):
            objects = obj if isinstance(obj, (list, tuple)) and len(obj) == len(tree) else [None] * len(tree)
            return [convert(v, o) for v, o in zip(tree, objects)]
        if isinstance(tree, float):
            return _f32(tree)
        return tree

    components = []
    for cls, reader, component, transform in found:
        tree = {k: v for k, v in reader.read_typetree().items() if k not in SKIP}
        fields = convert(tree, component)
        if cls == "MagicaCloth":
            data = component.serializeData
            if int(data.clothType) != 0:   # BoneCloth / BoneSpring: every bone below a root is simulated
                for root in data.rootBones:
                    if root and root.m_PathID:
                        table.add_subtree(root.read())
            build = fields["serializeData2"].get("preBuildData")
            pointer = component.serializeData2.preBuildData.preBuildScriptableObject if build else None
            if build and pointer and pointer.m_PathID:
                asset = pointer.read()
                shared_tree = asset.object_reader.read_typetree()["sharePreBuildDataList"]
                shared_objects = asset.sharePreBuildDataList
                match = [i for i, s in enumerate(shared_tree) if s.get("buildId") == build["buildId"]]
                if len(match) != 1:
                    raise ValueError(f"MagicaCloth PreBuild {build['buildId']!r}: {len(match)} matching entries")
                shared = convert(shared_tree[match[0]], shared_objects[match[0]])
                for setup in shared.get("renderSetupDataList") or []:
                    for k in MESH_COPY:
                        setup.pop(k, None)
                build["sharePreBuildData"] = shared
        components.append({"class": cls, "transformId": table.add(transform), "fields": fields})
    return {"transforms": table.export(mapping), "components": components}
