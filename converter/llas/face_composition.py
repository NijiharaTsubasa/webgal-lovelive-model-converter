"""LLAS source face graft, expressed as standard glTF nodes and renderers.

Original operations: CommonCoreMember.MergeFace (0x27C31F4),
MergeAndCombineFaceMesh.MergeFace (0x2CB0A10), RepairRootBone (0x2CB113C).
See docs/llas/face-assembly.md for the original APK evidence.
The glTF export keeps separate meshes instead of Unity's final draw-call merge;
it does not claim to implement the original merged facial-animation controller.
"""
from __future__ import annotations

import copy
from types import SimpleNamespace
from typing import Any

from converter.common.normalized_model import (
    NormalizedModelAdapter, _add_normalized_renderer, _mat4_mul,
    _trs_to_mat, _world_matrices,
)
from converter.common.unity import component_pointer, object_id, rotation, vec3


def _name(transform: Any) -> str:
    return str(transform.m_GameObject.deref_parse_as_object().m_Name)


def _children(transform: Any) -> list[Any]:
    return [p.deref_parse_as_object() for p in transform.m_Children if p]


def _child(transform: Any, name: str) -> Any:
    matches = [child for child in _children(transform) if _name(child) == name]
    if len(matches) != 1:
        raise ValueError(f"LLAS face assembly: expected one {_name(transform)}/{name}, got {len(matches)}")
    return matches[0]


def _subtree(transform: Any):
    yield transform
    for child in _children(transform):
        yield from _subtree(child)


class HeadMaterialAdapter(NormalizedModelAdapter):
    """Original MergeFace replaces sharedMaterial throughout Head_All."""

    def __init__(self, head_all: Any, material: Any):
        self.material = material
        self.renderers = set()
        for transform in _subtree(head_all):
            for entry in transform.m_GameObject.deref_parse_as_object().m_Component:
                pointer = component_pointer(entry)
                if pointer and pointer.type.name in {"SkinnedMeshRenderer", "MeshRenderer"}:
                    self.renderers.add(object_id(pointer.deref_parse_as_object()))

    def adapt_renderer(self, renderer: Any) -> Any:
        if object_id(renderer) not in self.renderers:
            return renderer
        return with_head_material(renderer, self.material)


def with_head_material(renderer: Any, material: Any) -> Any:
    # Unity Renderer.sharedMaterial changes the first material, not the array.
    adapted = copy.copy(renderer)
    materials = list(renderer.m_Materials)
    if not materials:
        raise ValueError("LLAS face renderer has no material slot")
    materials[0] = material
    adapted.m_Materials = materials
    return adapted


def append_rigid_renderers(exported: Any, skeleton: dict, member_root: Any,
                           adapter: Any = None, *, include_hidden: set[str] | None = None) -> None:
    """Retain visible authored MeshFilter/MeshRenderer pairs (e.g. Rina board).

    These are rigid attachments, not skins. Their normalized attachment nodes
    already exist; no synthetic bones, pose solving or game runtime is needed.
    """
    by_path = {tuple(bone["hierarchyPath"]): i for i, bone in enumerate(skeleton["bones"])}

    def visit(transform, path, parent_active=True):
        game_object = transform.m_GameObject.deref_parse_as_object()
        active = parent_active and game_object.m_IsActive
        components = [component_pointer(entry) for entry in game_object.m_Component]
        renderers = [p.deref_parse_as_object() for p in components if p and p.type.name == "MeshRenderer"]
        controlled = game_object.m_Name in (include_hidden or ())
        if (active or controlled) and renderers:
            filters = [p.deref_parse_as_object() for p in components if p and p.type.name == "MeshFilter"]
            if len(renderers) != 1 or len(filters) != 1:
                raise ValueError(f"LLAS rigid renderer requires one MeshFilter: {game_object.m_Name}")
            renderer = renderers[0]
            if renderer.m_Enabled or controlled:
                if adapter is not None:
                    renderer = adapter.adapt_renderer(renderer)
                proxy = SimpleNamespace(m_Mesh=filters[0].m_Mesh, m_Materials=renderer.m_Materials, m_Bones=[])
                morphs, name, node = _add_normalized_renderer(
                    proxy, by_path[path], exported.builder, {}, [], [], [], {}, frozenset(),
                )
                exported.mesh_names.append(name)
                for crc_value, target_index, target_name in morphs:
                    exported.morph_targets.setdefault(crc_value, []).append((node, target_index, target_name))
        for index, child in enumerate(_children(transform)):
            visit(child, path + (index,), active)

    visit(member_root, ())


def needs_face_graft(head_all: Any, needs_merging_face: bool) -> bool:
    # Native CommonCoreMemberHead.NeedsMergeFace checks for this existing marker.
    if not needs_merging_face:
        return False
    head_face = _child(head_all, "Head_Face")
    return not any(_name(child) == "mesh_facedots" for child in _children(head_face))


def append_face(exported: Any, skeleton: dict, member_root: Any,
                head_all: Any, face_root: Any, head_material: Any) -> None:
    """Apply native SetParent(false) grafts without changing Humanoid bones.

    Only authored auxiliary transforms are added. Their local TRS is preserved;
    parent transforms already encode the real Unity-solved neutral pose. This
    is coordinate/asset assembly, not a muscle or retargeting solver.
    """
    builder = exported.builder
    bones = skeleton["bones"]
    canonical = _world_matrices(bones)
    neutral = [list(bone["neutralWorldMatrix"]) for bone in bones]
    source_world: list[list[float] | None] = [None] * len(bones)
    by_path = {tuple(bone["hierarchyPath"]): i for i, bone in enumerate(bones)}
    transform_nodes = {}

    def map_original(transform, hierarchy_path, parent_world=None):
        index = by_path[hierarchy_path]
        transform_nodes[object_id(transform)] = index
        local = _trs_to_mat(vec3(transform.m_LocalPosition, reflect=True),
                            rotation(transform.m_LocalRotation), vec3(transform.m_LocalScale))
        world = local if parent_world is None else _mat4_mul(parent_world, local)
        source_world[index] = world
        for child_index, child in enumerate(_children(transform)):
            map_original(child, hierarchy_path + (child_index,), world)

    map_original(member_root, ())
    # The common exporter adds mesh nodes after the skeleton. Preserve indices
    # by extending all world-matrix tables up to the next glTF node index.
    while len(canonical) < len(builder.document["nodes"]):
        canonical.append(None)
        neutral.append(None)
        source_world.append(None)
    added = []

    def graft(transform, parent_index):
        index = len(builder.document["nodes"])
        position = vec3(transform.m_LocalPosition, reflect=True)
        quaternion = rotation(transform.m_LocalRotation)
        scale = vec3(transform.m_LocalScale)
        local = _trs_to_mat(position, quaternion, scale)
        builder.document["nodes"].append({"name": _name(transform),
            "translation": position, "rotation": quaternion, "scale": scale})
        builder.document["nodes"][parent_index].setdefault("children", []).append(index)
        canonical.append(_mat4_mul(canonical[parent_index], local))
        neutral.append(_mat4_mul(neutral[parent_index], local))
        source_world.append(_mat4_mul(source_world[parent_index], local))
        transform_nodes[object_id(transform)] = index
        added.append((transform, index))
        for child in _children(transform):
            graft(child, index)

    target_head = _child(head_all, "Head_Face")
    target_mesh = _child(head_all, "mesh_face")
    source_head = _child(face_root, "Head_Face")
    # RepairRootBone sets Eye.bones[0] and rootBone to the member's Head_Face.
    transform_nodes[object_id(source_head)] = transform_nodes[object_id(target_head)]
    graft(_child(face_root, "display_OnOff"), transform_nodes[object_id(head_all)])
    graft(_child(source_head, "Face_Root"), transform_nodes[object_id(target_head)])
    for child in _children(_child(face_root, "mesh_face")):
        graft(child, transform_nodes[object_id(target_mesh)])

    for transform, attachment in added:
        game_object = transform.m_GameObject.deref_parse_as_object()
        for entry in game_object.m_Component:
            pointer = component_pointer(entry)
            if not pointer or pointer.type.name not in {"SkinnedMeshRenderer", "MeshRenderer"}:
                continue
            renderer = pointer.deref_parse_as_object()
            if pointer.type.name == "SkinnedMeshRenderer" and (
                    not game_object.m_IsActive or not renderer.m_Enabled):
                continue
            renderer = with_head_material(renderer, head_material)
            if pointer.type.name == "MeshRenderer":
                # Facial clips can enable initially hidden rigid overlays.
                # Keep their geometry; the face Behavior owns visibility.
                filters = [component_pointer(component) for component in game_object.m_Component]
                filters = [component.deref_parse_as_object() for component in filters
                           if component and component.type.name == "MeshFilter"]
                if len(filters) != 1:
                    raise ValueError(f"LLAS grafted rigid renderer requires one MeshFilter: {_name(transform)}")
                renderer = SimpleNamespace(m_Mesh=filters[0].m_Mesh,
                                           m_Materials=renderer.m_Materials, m_Bones=[])
            morphs, mesh_name, node = _add_normalized_renderer(
                renderer, attachment, builder, transform_nodes,
                canonical, neutral, source_world, {}, frozenset(),
            )
            exported.mesh_names.append(mesh_name)
            for crc_value, target_index, name in morphs:
                exported.morph_targets.setdefault(crc_value, []).append((node, target_index, name))
