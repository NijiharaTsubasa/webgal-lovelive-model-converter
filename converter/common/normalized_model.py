"""Bake a Unity Humanoid skin into the canonical neutral glTF skeleton.

The source inverse bind matrices are used only while evaluating the mesh at
Unity's zero-muscle pose. The resulting geometry is stored as the new reference
geometry and receives inverse bind matrices for the final canonical hierarchy.
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from UnityPy.helpers.MeshHelper import MeshHandler

from .glb import GlbBuilder, mesh_morphs, trim_unused_trailing_renderer_bones
from .shader import renderer_uses_eye_shader
from .unity import (
    COMPONENT_FLOAT,
    COMPONENT_UNSIGNED_BYTE,
    COMPONENT_UNSIGNED_SHORT,
    COMPONENT_UNSIGNED_INT,
    component_pointer,
    crc,
    game_object_transform,
    object_id,
    pointer_id,
)


class NormalizedModelAdapter:
    """Source-specific adjustments at the normalized Unity-to-glTF seam.

    The common exporter owns hierarchy validation, skinning and glTF emission.
    A game adapter may only redirect source bones or replace a renderer object;
    it cannot bypass the common skeleton invariants.
    """

    def bone_redirects(self, standard_bones: dict[str, int]) -> dict[tuple[int, int], int]:
        return {}

    def copied_bone_keys(self, redirects: dict[tuple[int, int], int]) -> frozenset[tuple[int, int]]:
        return frozenset()

    def local_rotation_copy_keys(
        self, redirects: dict[tuple[int, int], int], standard_bones: dict[str, int],
    ) -> frozenset[tuple[int, int]]:
        return frozenset()

    def adapt_renderer(self, renderer: Any) -> Any:
        return renderer

    def should_export_renderer(self, renderer: Any) -> bool:
        return True


class FaceBonesCopierAdapter(NormalizedModelAdapter):
    """Redirect the duplicate face rig to the Humanoid bones it mirrors."""

    _FIELDS = {
        "spine03": "UpperChest",
        "neck": "Neck",
        "head": "Head",
        "leftEye": "LeftEye",
        "rightEye": "RightEye",
    }

    def __init__(self, environment: Any) -> None:
        self.environment = environment

    def bone_redirects(self, standard_bones: dict[str, int]) -> dict[tuple[int, int], int]:
        redirects: dict[tuple[int, int], int] = {}
        for reader in self.environment.objects:
            if reader.type.name != "MonoBehaviour":
                continue
            try:
                component = reader.read()
                script_pointer = getattr(component, "m_Script", None)
                if not script_pointer:
                    continue
                script = script_pointer.deref_parse_as_object()
                class_name = getattr(script, "m_ClassName", None) or getattr(script, "m_Name", None)
                if class_name != "FaceBonesCopier":
                    continue
                for field, standard_name in self._FIELDS.items():
                    target_pointer = getattr(component, field, None)
                    target_node = standard_bones.get(standard_name)
                    if not target_pointer or target_node is None:
                        continue
                    key = object_id(target_pointer.deref_parse_as_object())
                    previous = redirects.get(key)
                    if previous is not None and previous != target_node:
                        raise RuntimeError(
                            f"FaceBonesCopier target {field!r} has conflicting body bone mappings"
                        )
                    redirects[key] = target_node
            except (AttributeError, FileNotFoundError, ValueError):
                continue
        return redirects


def _lowest_common_node_ancestor(
    node_indices: list[int],
    nodes: list[dict[str, Any]],
) -> int:
    """Return the deepest hierarchy node shared by every indexed node.

    glTF's optional ``skin.skeleton`` must be a common root of all joints.
    Unity's ``SkinnedMeshRenderer.rootBone`` is not guaranteed to satisfy that
    after adapter redirects or when a renderer also uses auxiliary branches.
    """
    if not node_indices:
        raise ValueError("cannot find a common ancestor for an empty node list")

    parents: dict[int, int] = {}
    for parent_index, node in enumerate(nodes):
        for child in node.get("children", []):
            child_index = int(child)
            previous = parents.get(child_index)
            if previous is not None and previous != parent_index:
                raise RuntimeError(f"glTF node {child_index} has multiple parents")
            parents[child_index] = parent_index

    def ancestor_chain(index: int) -> list[int]:
        chain: list[int] = []
        seen: set[int] = set()
        while index not in seen:
            if not 0 <= index < len(nodes):
                raise RuntimeError(f"glTF node index {index} is out of range")
            seen.add(index)
            chain.append(index)
            if index not in parents:
                return chain
            index = parents[index]
        raise RuntimeError("glTF node hierarchy contains a cycle")

    first_chain = ancestor_chain(int(node_indices[0]))
    common = set(first_chain)
    for node_index in node_indices[1:]:
        common.intersection_update(ancestor_chain(int(node_index)))
    for candidate in first_chain:
        if candidate in common:
            return candidate
    raise RuntimeError("skin joints do not share a common hierarchy root")


def _singular_branch_redirect(
    bones: list[dict[str, Any]],
    node_index: int,
    standard_indices: set[int],
) -> int | None:
    """Redirect a helper below a collapsed transform to its Humanoid ancestor.

    Some Unity rigs keep an active twist joint below an almost-zero-scale
    dummy and compensate with enormous child transforms. That hierarchy is
    visually meaningful in Unity's original bind pose but cannot be stored
    robustly in float32 glTF matrices. Standard motions do not animate these
    helpers, so baking their neutral offset and binding them to the closest
    Humanoid ancestor preserves the rendered pose without unstable matrices.
    """
    cursor = node_index
    crossed_singular = False
    seen: set[int] = set()
    while cursor >= 0 and cursor not in seen:
        seen.add(cursor)
        scale = [abs(float(value)) for value in bones[cursor]["scale"]]
        crossed_singular = crossed_singular or min(scale) < 1e-8
        if cursor in standard_indices:
            return cursor if crossed_singular and cursor != node_index else None
        cursor = int(bones[cursor]["parentIndex"])
    return None


@dataclass
class NormalizedNodeMapping:
    """Convert source-local Unity geometry into the exported node's frame.

    These mappings are converter state, not published model metadata. A radius
    uses maximum linear stretch: under nonuniform scale it bounds the resulting
    ellipsoid rather than claiming it remains an exact sphere.
    """

    source_nodes: dict[tuple[int, int], int]
    canonical_world: list[list[float]]
    neutral_world: list[list[float]]
    source_world: list[list[float]]
    redirects: dict[tuple[int, int], int]
    copied_face_bones: frozenset[tuple[int, int]] = frozenset()

    def _key(self, source: Any) -> tuple[int, int]:
        if hasattr(source, "deref_parse_as_object"):
            if not source:
                raise ValueError("Cannot map a null source Transform")
            source = source.deref_parse_as_object()
        try:
            key = object_id(source)
        except AttributeError as exc:
            raise ValueError("Expected a source Transform or Transform pointer") from exc
        if key not in self.source_nodes:
            raise ValueError(f"Source Transform {key} is absent from the exported skeleton")
        return key

    def node_index(self, source: Any) -> int:
        key = self._key(source)
        return self.redirects.get(key, self.source_nodes[key])

    def _local_matrix(self, source: Any, target_node: int | None) -> list[float]:
        key = self._key(source)
        source_node = self.source_nodes[key]
        mapped_node = self.redirects.get(key, source_node)
        target_node = mapped_node if target_node is None else target_node
        if (isinstance(target_node, bool) or not isinstance(target_node, int)
                or not 0 <= target_node < len(self.canonical_world)):
            raise ValueError(f"Invalid exported target node {target_node!r}")
        neutral = self.neutral_world[source_node]
        if mapped_node != source_node and key not in self.copied_face_bones:
            neutral = _mat4_mul(
                _mat4_mul(self.neutral_world[mapped_node],
                          _mat4_inverse(self.source_world[mapped_node])),
                self.source_world[source_node],
            )
        return _mat4_mul(_mat4_inverse(self.canonical_world[target_node]), neutral)

    @staticmethod
    def _reflected(value: Any) -> tuple[float, float, float]:
        try:
            values = tuple(float(component) for component in value)
        except (TypeError, ValueError) as exc:
            raise ValueError("Expected a finite three-component vector") from exc
        if len(values) != 3 or not all(math.isfinite(component) for component in values):
            raise ValueError("Expected a finite three-component vector")
        return -values[0], values[1], values[2]

    def point(self, source: Any, value: Any, target_node: int | None = None) -> list[float]:
        return list(_mat4_transform_point(self._local_matrix(source, target_node),
                                         self._reflected(value)))

    def direction(self, source: Any, value: Any, target_node: int | None = None) -> list[float]:
        """Transform a direction, retaining its length and any linear scaling."""
        return list(_mat4_transform_direction(self._local_matrix(source, target_node),
                                             self._reflected(value)))

    def radius_scale(self, source: Any, target_node: int | None = None) -> float:
        matrix = self._local_matrix(source, target_node)
        # Largest eigenvalue of A^T A gives maximum stretch, including shear.
        gram = [[sum(matrix[i * 4 + k] * matrix[j * 4 + k] for k in range(3))
                 for j in range(3)] for i in range(3)]
        off_diagonal = gram[0][1] ** 2 + gram[0][2] ** 2 + gram[1][2] ** 2
        if off_diagonal == 0:
            return math.sqrt(max(gram[i][i] for i in range(3)))
        mean = sum(gram[i][i] for i in range(3)) / 3
        spread = math.sqrt((sum((gram[i][i] - mean) ** 2 for i in range(3))
                            + 2 * off_diagonal) / 6)
        b = [[(gram[i][j] - (mean if i == j else 0)) / spread
              for j in range(3)] for i in range(3)]
        determinant = (b[0][0] * (b[1][1] * b[2][2] - b[1][2] * b[2][1])
                       - b[0][1] * (b[1][0] * b[2][2] - b[1][2] * b[2][0])
                       + b[0][2] * (b[1][0] * b[2][1] - b[1][1] * b[2][0]))
        angle = math.acos(max(-1.0, min(1.0, determinant / 2))) / 3
        return math.sqrt(max(0.0, mean + 2 * spread * math.cos(angle)))

    def normal(self, source: Any, value: Any, target_node: int | None = None) -> list[float]:
        """Map a plane normal by inverse transpose, including nonuniform scale."""
        inverse = _mat4_inverse(self._local_matrix(source, target_node))
        reflected = self._reflected(value)
        result = [sum(inverse[row * 4 + k] * reflected[k] for k in range(3)) for row in range(3)]
        length = math.sqrt(sum(v * v for v in result))
        if length < 1e-12:
            raise ValueError("Plane normal must be nonzero")
        return [v / length for v in result]

    def radius(self, source: Any, value: float, target_node: int | None = None) -> float:
        value = float(value)
        if not math.isfinite(value) or value < 0:
            raise ValueError("Radius must be finite and nonnegative")
        return value * self.radius_scale(source, target_node)


@dataclass
class NormalizedExport:
    builder: GlbBuilder
    mesh_names: list[str]
    standard_bones: dict[str, int]
    morph_targets: dict[int, list[tuple[int, int, str]]]
    human_scale: float
    node_mapping: NormalizedNodeMapping


def renderer_node_name(mesh_name: str) -> str:
    """Return the public glTF node name used for an extracted renderer."""
    return f"{mesh_name} Renderer"


def _attach_copied_face_helpers(
    nodes: list[dict[str, Any]],
    transform_to_node: dict[tuple[int, int], int],
    redirects: dict[tuple[int, int], int],
    copied_bones: frozenset[tuple[int, int]],
    canonical_world: list[list[float]],
    neutral_world: list[list[float]],
    source_parents: list[int],
    local_scales: list[list[float]],
    local_rotation_keys: frozenset[tuple[int, int]],
) -> None:
    """Attach non-copied face helpers to the body bone that drives their parent.

    FaceBonesCopier moves its duplicate spine in world space and copies local
    rotations farther down the face rig. A static glTF duplicate would leave
    its eye helpers at the serialized position and fail to follow head motion.
    """
    copied_nodes = {
        transform_to_node[key]: redirects[key]
        for key in copied_bones
    }
    rotation_nodes = {transform_to_node[key] for key in local_rotation_keys}
    source_children: dict[int, list[int]] = defaultdict(list)
    locals_before_copy: list[list[float]] = []
    for node, parent in enumerate(source_parents):
        source_children[parent].append(node)
        locals_before_copy.append(neutral_world[node] if parent < 0 else _mat4_mul(
            _mat4_inverse(neutral_world[parent]), neutral_world[node],
        ))

    # Evaluate the source copy operations in hierarchy order before redirecting
    # skin joints. Copying localRotation must not copy the donor's eye spacing.
    for source_node, target_node in sorted(copied_nodes.items()):
        desired_world = neutral_world[target_node]
        if source_node in rotation_nodes:
            local = list(locals_before_copy[source_node])
            donor = locals_before_copy[target_node]
            for column in range(3):
                start = column * 4
                source_scale = math.copysign(
                    math.sqrt(sum(local[start + row] ** 2 for row in range(3))),
                    local_scales[source_node][column],
                )
                donor_scale = math.copysign(
                    math.sqrt(sum(donor[start + row] ** 2 for row in range(3))),
                    local_scales[target_node][column],
                )
                for row in range(3):
                    local[start + row] = donor[start + row] * source_scale / donor_scale
            parent = source_parents[source_node]
            desired_world = local if parent < 0 else _mat4_mul(neutral_world[parent], local)
        delta = _mat4_mul(desired_world, _mat4_inverse(neutral_world[source_node]))
        stack = [source_node]
        while stack:
            descendant = stack.pop()
            neutral_world[descendant] = _mat4_mul(delta, neutral_world[descendant])
            stack.extend(source_children[descendant])

    for source_node, target_node in sorted(copied_nodes.items()):
        for child in list(nodes[source_node].get("children", [])):
            if child in copied_nodes:
                continue
            nodes[source_node]["children"].remove(child)
            if not nodes[source_node]["children"]:
                del nodes[source_node]["children"]
            nodes[target_node].setdefault("children", []).append(child)
            child_local = _mat4_mul(_mat4_inverse(canonical_world[target_node]), neutral_world[child])
            nodes[child].pop("translation", None)
            nodes[child].pop("rotation", None)
            nodes[child].pop("scale", None)
            nodes[child]["matrix"] = child_local


def _node_world_matrices(nodes: list[dict[str, Any]]) -> list[list[float]]:
    parents = {
        child: parent
        for parent, node in enumerate(nodes)
        for child in node.get("children", [])
    }
    world: list[list[float] | None] = [None] * len(nodes)

    def compute(index: int) -> list[float]:
        existing = world[index]
        if existing is not None:
            return existing
        node = nodes[index]
        local = node.get("matrix") or _trs_to_mat(
            node.get("translation", [0.0, 0.0, 0.0]),
            node.get("rotation", [0.0, 0.0, 0.0, 1.0]),
            node.get("scale", [1.0, 1.0, 1.0]),
        )
        parent = parents.get(index)
        result = local if parent is None else _mat4_mul(compute(parent), local)
        world[index] = result
        return result

    return [compute(index) for index in range(len(nodes))]


def export_normalized_model(
    environment: Any,
    root_pointer: Any,
    skeleton_json: dict[str, Any],
    adapter: NormalizedModelAdapter | None = None,
    *,
    include_vertex_colors: bool = False,
) -> NormalizedExport:
    _validate_skeleton(skeleton_json)

    builder = GlbBuilder()
    builder.include_vertex_colors = include_vertex_colors
    bones = skeleton_json["bones"]
    root_idx = int(skeleton_json["rootIndex"])
    standard_bones: dict[str, int] = {}

    for index, bone in enumerate(bones):
        builder.document["nodes"].append({
            "name": bone["name"],
            "translation": list(bone["translation"]),
            "rotation": list(bone["rotation"]),
            "scale": list(bone["scale"]),
        })
        if bone["isHumanoidCore"]:
            standard_bones[bone["name"]] = index

    for index, bone in enumerate(bones):
        parent_index = int(bone["parentIndex"])
        if parent_index >= 0:
            builder.document["nodes"][parent_index].setdefault("children", []).append(index)
    builder.document["scenes"][0]["nodes"].append(root_idx)

    canonical_world_mats = _world_matrices(bones)
    neutral_world_mats = [
        [float(value) for value in bone["neutralWorldMatrix"]]
        for bone in bones
    ]
    path_to_node = {
        tuple(int(part) for part in bone["hierarchyPath"]): index
        for index, bone in enumerate(bones)
    }

    root = game_object_transform(root_pointer.deref_parse_as_object())
    transforms: list[tuple[Any, int]] = []
    transform_to_node: dict[tuple[int, int], int] = {}

    def visit(transform: Any, hierarchy_path: tuple[int, ...]) -> None:
        if hierarchy_path not in path_to_node:
            raise RuntimeError(f"Normalized skeleton is missing hierarchy path {hierarchy_path}")
        node_index = path_to_node[hierarchy_path]
        transforms.append((transform, node_index))
        transform_to_node[object_id(transform)] = node_index
        children = [child for child in getattr(transform, "m_Children", []) if child]
        for child_index, child in enumerate(children):
            visit(child.deref_parse_as_object(), hierarchy_path + (child_index,))

    visit(root, ())
    if len(transforms) != len(bones):
        raise RuntimeError(
            f"Skeleton hierarchy mismatch: UnityPy found {len(transforms)} transforms, "
            f"Unity normalizer emitted {len(bones)}"
        )

    source_world_mats = _source_world_matrices(transforms, bones)

    # FaceBonesCopier is a shared runtime convention: Hasunosora and Bang Dream
    # both use a duplicate facial rig whose transforms mirror Humanoid bones.
    source_adapter = adapter or FaceBonesCopierAdapter(environment)
    if hasattr(source_adapter, "classify_shader"):
        builder.shader_classifier = source_adapter.classify_shader
    if hasattr(source_adapter, "adapt_material"):
        builder.material_adapter = source_adapter.adapt_material
    bone_redirects = source_adapter.bone_redirects(standard_bones)
    copied_face_bones = source_adapter.copied_bone_keys(bone_redirects)
    standard_indices = set(standard_bones.values())
    for transform, node_index in transforms:
        target_node = _singular_branch_redirect(bones, node_index, standard_indices)
        if target_node is not None:
            bone_redirects.setdefault(object_id(transform), target_node)

    if copied_face_bones:
        source_parents = [
            path_to_node.get(tuple(bone["hierarchyPath"])[:-1], -1)
            if bone["hierarchyPath"] else -1 for bone in bones
        ]
        local_scales = [[1.0, 1.0, 1.0] for _ in bones]
        for transform, node_index in transforms:
            scale = transform.m_LocalScale
            local_scales[node_index] = [float(scale.x), float(scale.y), float(scale.z)]
        _attach_copied_face_helpers(
            builder.document["nodes"], transform_to_node,
            bone_redirects, copied_face_bones, canonical_world_mats,
            neutral_world_mats,
            source_parents, local_scales,
            source_adapter.local_rotation_copy_keys(bone_redirects, standard_bones),
        )
        canonical_world_mats = _node_world_matrices(builder.document["nodes"])

    morph_targets: dict[int, list[tuple[int, int, str]]] = defaultdict(list)
    mesh_names: list[str] = []
    emitted_mesh_paths: set[tuple[int, int]] = set()
    for transform, attachment_node in transforms:
        game_object = transform.m_GameObject.deref_parse_as_object()
        active = getattr(game_object, "m_IsActive", True)
        for entry in game_object.m_Component:
            pointer = component_pointer(entry)
            if not pointer or pointer.type.name != "SkinnedMeshRenderer":
                continue
            renderer = pointer.deref_parse_as_object()
            if not getattr(renderer, "m_Mesh", None):
                continue
            if not source_adapter.should_export_renderer(renderer):
                continue
            renderer = source_adapter.adapt_renderer(renderer)
            mesh_path = pointer_id(renderer.m_Mesh)
            if not active and (
                mesh_path in emitted_mesh_paths or not renderer_uses_eye_shader(renderer)
            ):
                continue

            result = _add_normalized_renderer(
                renderer,
                attachment_node,
                builder,
                transform_to_node,
                canonical_world_mats,
                neutral_world_mats,
                source_world_mats,
                bone_redirects,
                copied_face_bones,
            )
            emitted_mesh_paths.add(mesh_path)
            morphs, mesh_name, mesh_node = result
            mesh_names.append(mesh_name)
            for crc_value, target_index, name in morphs:
                morph_targets[crc_value].append((mesh_node, target_index, name))

    return NormalizedExport(
        builder,
        mesh_names,
        standard_bones,
        morph_targets,
        float(skeleton_json["humanScale"]),
        NormalizedNodeMapping(transform_to_node, canonical_world_mats,
                              neutral_world_mats, source_world_mats, bone_redirects,
                              copied_face_bones),
    )


def _validate_skeleton(data: dict[str, Any]) -> None:
    expected = {
        "schemaVersion": 4,
        "producer": "unity-humanoid-normalizer",
        "coordinateSystem": "gltf-yup-zfwd-right-handed",
        "pose": "mecanim-zero-muscles",
    }
    for key, value in expected.items():
        actual = data.get(key)
        if isinstance(value, tuple):
            if actual not in value:
                raise ValueError(
                    f"Unsupported normalized skeleton {key}: "
                    f"expected one of {value!r}, got {actual!r}"
                )
        elif actual != value:
            raise ValueError(
                f"Unsupported normalized skeleton {key}: "
                f"expected {value!r}, got {actual!r}"
            )

    bones = data.get("bones")
    if not isinstance(bones, list) or not bones:
        raise ValueError("Normalized skeleton has no bones")
    if not 0 <= int(data.get("rootIndex", -1)) < len(bones):
        raise ValueError("Normalized skeleton has an invalid rootIndex")
    try:
        human_scale = float(data["humanScale"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("Normalized skeleton has no valid humanScale") from exc
    if not math.isfinite(human_scale) or human_scale <= 0:
        raise ValueError("Normalized skeleton humanScale must be a positive finite number")

    seen_paths: set[tuple[int, ...]] = set()
    for index, bone in enumerate(bones):
        hierarchy_path = tuple(int(part) for part in bone.get("hierarchyPath", []))
        if hierarchy_path in seen_paths:
            raise ValueError(f"Duplicate hierarchy path {hierarchy_path}")
        seen_paths.add(hierarchy_path)
        parent_index = int(bone.get("parentIndex", -1))
        if parent_index >= index:
            raise ValueError(f"Bone {index} is not in parent-first order")
        neutral_world = bone.get("neutralWorldMatrix")
        if not isinstance(neutral_world, list) or len(neutral_world) != 16:
            raise ValueError(f"Bone {index} has no valid neutralWorldMatrix")
        source_euler = bone.get("sourceUnityEulerAngles")
        if (not isinstance(source_euler, list) or len(source_euler) != 3
                or not all(math.isfinite(float(value)) for value in source_euler)):
            raise ValueError(f"Bone {index} has no valid sourceUnityEulerAngles")


def _world_matrices(bones: list[dict[str, Any]]) -> list[list[float]]:
    results: list[list[float] | None] = [None] * len(bones)

    def compute(index: int) -> list[float]:
        cached = results[index]
        if cached is not None:
            return cached
        bone = bones[index]
        local = _trs_to_mat(
            list(bone["translation"]),
            list(bone["rotation"]),
            list(bone["scale"]),
        )
        parent_index = int(bone["parentIndex"])
        result = local if parent_index < 0 else _mat4_mul(compute(parent_index), local)
        results[index] = result
        return result

    for index in range(len(bones)):
        compute(index)
    return [matrix for matrix in results if matrix is not None]


def _source_world_matrices(
    transforms: list[tuple[Any, int]],
    bones: list[dict[str, Any]],
) -> list[list[float]]:
    """Reconstruct the serialized Unity hierarchy in glTF coordinates."""
    local_mats: list[list[float] | None] = [None] * len(bones)
    for transform, node_index in transforms:
        position = transform.m_LocalPosition
        rotation = transform.m_LocalRotation
        scale = transform.m_LocalScale
        local_mats[node_index] = _trs_to_mat(
            [-float(position.x), float(position.y), float(position.z)],
            [
                float(rotation.x),
                -float(rotation.y),
                -float(rotation.z),
                float(rotation.w),
            ],
            [float(scale.x), float(scale.y), float(scale.z)],
        )

    path_to_node = {
        tuple(int(part) for part in bone["hierarchyPath"]): index
        for index, bone in enumerate(bones)
    }
    results: list[list[float]] = []
    for index, bone in enumerate(bones):
        local = local_mats[index]
        if local is None:
            raise RuntimeError(f"Missing source transform for skeleton node {index}")
        path = tuple(int(part) for part in bone["hierarchyPath"])
        parent_index = path_to_node.get(path[:-1], -1) if path else -1
        results.append(
            local if parent_index < 0 else _mat4_mul(results[parent_index], local)
        )
    return results


def _unity_matrix_to_gltf(value: Any) -> list[float]:
    """Convert a Unity Matrix4x4 to reflected, column-major glTF storage."""
    rows = [
        [value.e00, value.e01, value.e02, value.e03],
        [value.e10, value.e11, value.e12, value.e13],
        [value.e20, value.e21, value.e22, value.e23],
        [value.e30, value.e31, value.e32, value.e33],
    ]
    signs = [-1.0, 1.0, 1.0, 1.0]
    return [
        float(rows[row][column] * signs[row] * signs[column])
        for column in range(4)
        for row in range(4)
    ]


def _trs_to_mat(
    translation: list[float],
    rotation: list[float],
    scale: list[float],
) -> list[float]:
    qx, qy, qz, qw = rotation
    sx, sy, sz = scale
    xx, yy, zz = qx * qx, qy * qy, qz * qz
    xy, xz, yz = qx * qy, qx * qz, qy * qz
    wx, wy, wz = qw * qx, qw * qy, qw * qz
    return [
        (1 - 2 * (yy + zz)) * sx,
        (2 * (xy + wz)) * sx,
        (2 * (xz - wy)) * sx,
        0.0,
        (2 * (xy - wz)) * sy,
        (1 - 2 * (xx + zz)) * sy,
        (2 * (yz + wx)) * sy,
        0.0,
        (2 * (xz + wy)) * sz,
        (2 * (yz - wx)) * sz,
        (1 - 2 * (xx + yy)) * sz,
        0.0,
        translation[0],
        translation[1],
        translation[2],
        1.0,
    ]


def _mat4_mul(a: list[float], b: list[float]) -> list[float]:
    return [
        sum(a[k * 4 + row] * b[column * 4 + k] for k in range(4))
        for column in range(4)
        for row in range(4)
    ]


def _mat4_inverse(matrix: list[float]) -> list[float]:
    m00, m10, m20, m30 = matrix[0], matrix[1], matrix[2], matrix[3]
    m01, m11, m21, m31 = matrix[4], matrix[5], matrix[6], matrix[7]
    m02, m12, m22, m32 = matrix[8], matrix[9], matrix[10], matrix[11]
    m03, m13, m23, m33 = matrix[12], matrix[13], matrix[14], matrix[15]

    a0 = m00 * m11 - m01 * m10
    a1 = m00 * m12 - m02 * m10
    a2 = m00 * m13 - m03 * m10
    a3 = m01 * m12 - m02 * m11
    a4 = m01 * m13 - m03 * m11
    a5 = m02 * m13 - m03 * m12
    b0 = m20 * m31 - m21 * m30
    b1 = m20 * m32 - m22 * m30
    b2 = m20 * m33 - m23 * m30
    b3 = m21 * m32 - m22 * m31
    b4 = m21 * m33 - m23 * m31
    b5 = m22 * m33 - m23 * m32

    determinant = a0 * b5 - a1 * b4 + a2 * b3 + a3 * b2 - a4 * b1 + a5 * b0
    if abs(determinant) < 1e-20:
        raise ValueError("Singular skeleton matrix")
    inv_det = 1.0 / determinant

    result = [0.0] * 16
    result[0] = (m11 * b5 - m12 * b4 + m13 * b3) * inv_det
    result[1] = (m12 * b2 - m10 * b5 - m13 * b1) * inv_det
    result[2] = (m10 * b4 - m11 * b2 + m13 * b0) * inv_det
    result[3] = (-m10 * b3 + m11 * b1 - m12 * b0) * inv_det
    result[4] = (m02 * b4 - m01 * b5 - m03 * b3) * inv_det
    result[5] = (m00 * b5 - m02 * b2 + m03 * b1) * inv_det
    result[6] = (m01 * b2 - m00 * b4 - m03 * b0) * inv_det
    result[7] = (m00 * b3 - m01 * b1 + m02 * b0) * inv_det
    result[8] = (m31 * a5 - m32 * a4 + m33 * a3) * inv_det
    result[9] = (m32 * a2 - m30 * a5 - m33 * a1) * inv_det
    result[10] = (m30 * a4 - m31 * a2 + m33 * a0) * inv_det
    result[11] = (-m30 * a3 + m31 * a1 - m32 * a0) * inv_det
    result[12] = (m22 * a4 - m21 * a5 - m23 * a3) * inv_det
    result[13] = (m20 * a5 - m22 * a2 + m23 * a1) * inv_det
    result[14] = (m21 * a2 - m20 * a4 - m23 * a0) * inv_det
    result[15] = (m20 * a3 - m21 * a1 + m22 * a0) * inv_det
    return result


def _mat4_transform_point(matrix: list[float], value: tuple[float, ...] | list[float]) -> tuple[float, float, float]:
    x, y, z = value[:3]
    return (
        matrix[0] * x + matrix[4] * y + matrix[8] * z + matrix[12],
        matrix[1] * x + matrix[5] * y + matrix[9] * z + matrix[13],
        matrix[2] * x + matrix[6] * y + matrix[10] * z + matrix[14],
    )


def _normalize3(value: tuple[float, float, float]) -> tuple[float, float, float]:
    length = sum(component * component for component in value) ** 0.5
    if length < 1e-20:
        return (0.0, 1.0, 0.0)
    return tuple(component / length for component in value)


def _mat4_transform_direction(
    matrix: list[float],
    value: tuple[float, ...] | list[float],
) -> tuple[float, float, float]:
    x, y, z = value[:3]
    return (
        matrix[0] * x + matrix[4] * y + matrix[8] * z,
        matrix[1] * x + matrix[5] * y + matrix[9] * z,
        matrix[2] * x + matrix[6] * y + matrix[10] * z,
    )


def _mat4_transform_normal(
    matrix: list[float],
    value: tuple[float, ...] | list[float],
) -> tuple[float, float, float]:
    inverse = _mat4_inverse(matrix)
    x, y, z = value[:3]
    return _normalize3((
        inverse[0] * x + inverse[1] * y + inverse[2] * z,
        inverse[4] * x + inverse[5] * y + inverse[6] * z,
        inverse[8] * x + inverse[9] * y + inverse[10] * z,
    ))


def _blend_skin_matrices(
    joints: list[list[int]],
    weights: list[list[float]],
    bone_matrices: list[list[float]],
) -> list[list[float]]:
    result: list[list[float]] = []
    for vertex_joints, vertex_weights in zip(joints, weights):
        matrix = [0.0] * 16
        for joint, weight in zip(vertex_joints, vertex_weights):
            if weight == 0.0:
                continue
            source = bone_matrices[joint]
            for index in range(16):
                matrix[index] += weight * source[index]
        result.append(matrix)
    return result


def _deduplicate_skin_joints(
    joint_nodes: list[int],
    vertex_joints: list[list[int]],
    vertex_weights: list[list[float]],
) -> tuple[list[int], list[list[int]], list[list[float]]]:
    """Collapse redirected renderer bones that target the same glTF node."""
    unique_nodes: list[int] = []
    node_to_slot: dict[int, int] = {}
    source_to_unique: list[int] = []
    for node in joint_nodes:
        if node not in node_to_slot:
            node_to_slot[node] = len(unique_nodes)
            unique_nodes.append(node)
        source_to_unique.append(node_to_slot[node])
    remapped_joints: list[list[int]] = []
    remapped_weights: list[list[float]] = []
    for slots, weights in zip(vertex_joints, vertex_weights):
        combined: dict[int, float] = {}
        for source_slot, weight in zip(slots, weights):
            unique_slot = source_to_unique[source_slot]
            combined[unique_slot] = combined.get(unique_slot, 0.0) + weight
        nonzero = [(slot, weight) for slot, weight in combined.items() if weight > 0.0]
        total = sum(weight for _, weight in nonzero) or 1.0
        out_joints = [slot for slot, _ in nonzero]
        out_weights = [weight / total for _, weight in nonzero]
        remapped_joints.append((out_joints + [0, 0, 0, 0])[:4])
        remapped_weights.append((out_weights + [0.0, 0.0, 0.0, 0.0])[:4])
    return unique_nodes, remapped_joints, remapped_weights


def _add_normalized_renderer(
    renderer: Any,
    attachment_node: int,
    builder: GlbBuilder,
    transform_to_node: dict[tuple[int, int], int],
    canonical_world_mats: list[list[float]],
    neutral_world_mats: list[list[float]],
    source_world_mats: list[list[float]],
    bone_redirects: dict[tuple[int, int], int],
    copied_face_bones: frozenset[tuple[int, int]],
) -> tuple[list[tuple[int, int, str]], str, int]:
    mesh = renderer.m_Mesh.deref_parse_as_object()

    decoded = MeshHandler(mesh)
    decoded.process()
    positions = [(-x, y, z) for x, y, z in decoded.m_Vertices]
    normals = [(-x, y, z) for x, y, z in decoded.m_Normals]
    # Unity meshes may omit tangents when their material does not use tangent-
    # space shading. glTF permits the TANGENT accessor to be absent.
    tangents = (
        [(-x, y, z, -w) for x, y, z, w in decoded.m_Tangents]
        if decoded.m_Tangents else None
    )

    bind_poses = list(getattr(mesh, "m_BindPose", []))
    renderer_bones = trim_unused_trailing_renderer_bones(
        mesh.m_Name,
        list(getattr(renderer, "m_Bones", [])),
        bind_poses,
        decoded.m_BoneIndices or [],
        decoded.m_BoneWeights or [],
    )
    skin_index: int | None = None
    joints: list[list[int]] = []
    weights: list[list[float]] = []
    bind_to_neutral_per_vertex: list[list[float]] | None = None
    if renderer_bones and decoded.m_BoneIndices:
        joint_nodes: list[int] = []
        source_joint_nodes: list[int] = []
        redirected: list[bool] = []
        copied: list[bool] = []
        for bone_pointer in renderer_bones:
            if not bone_pointer:
                raise RuntimeError(f"{mesh.m_Name}: renderer contains a null bone")
            bone_transform = bone_pointer.deref_parse_as_object()
            bone_key = object_id(bone_transform)
            source_node = transform_to_node.get(bone_key)
            if source_node is None:
                bone_name = bone_transform.m_GameObject.deref_parse_as_object().m_Name
                raise RuntimeError(f"{mesh.m_Name}: bone {bone_name!r} is absent from normalized skeleton")
            node_index = bone_redirects.get(bone_key)
            if node_index is None:
                node_index = source_node
            joint_nodes.append(node_index)
            source_joint_nodes.append(source_node)
            redirected.append(node_index != source_node)
            copied.append(bone_key in copied_face_bones)

        raw_weights = decoded.m_BoneWeights or []
        for vertex_index, raw_indices in enumerate(decoded.m_BoneIndices):
            values = list(raw_indices if isinstance(raw_indices, (tuple, list)) else [raw_indices])
            value_weights = list(raw_weights[vertex_index]) if raw_weights else [1.0]
            values = (values + [0, 0, 0, 0])[:4]
            value_weights = (value_weights + [0.0, 0.0, 0.0, 0.0])[:4]
            for bone_index, weight in zip(values, value_weights):
                if weight and not 0 <= bone_index < len(joint_nodes):
                    raise RuntimeError(
                        f"{mesh.m_Name}: vertex {vertex_index} references bone {bone_index}, "
                        f"but renderer has {len(joint_nodes)} bones"
                    )
            total = sum(value_weights) or 1.0
            joints.append(values)
            weights.append([float(weight) / total for weight in value_weights])

        if len(bind_poses) != len(renderer_bones):
            raise RuntimeError(
                f"{mesh.m_Name}: mesh has {len(bind_poses)} bind poses, "
                f"but renderer has {len(renderer_bones)} bones"
            )
        canonical_mesh_inverse = _mat4_inverse(canonical_world_mats[attachment_node])
        bind_to_neutral: list[list[float]] = []
        for bind_pose, source_node, joint_node, is_redirected, is_copied in zip(
            bind_poses, source_joint_nodes, joint_nodes, redirected, copied
        ):
            inverse_bind = _unity_matrix_to_gltf(bind_pose)
            neutral_joint_world = neutral_world_mats[source_node]
            if is_redirected and not is_copied:
                # Preserve a redirected auxiliary bone's original offset while
                # making it follow the adapter-selected canonical bone.
                neutral_joint_world = _mat4_mul(
                    _mat4_mul(
                        neutral_world_mats[joint_node],
                        _mat4_inverse(source_world_mats[joint_node]),
                    ),
                    source_world_mats[source_node],
                )
            bind_to_neutral.append(
                _mat4_mul(
                    _mat4_mul(canonical_mesh_inverse, neutral_joint_world),
                    inverse_bind,
                )
            )

        bind_to_neutral_per_vertex = _blend_skin_matrices(
            joints, weights, bind_to_neutral
        )
        positions = [
            _mat4_transform_point(matrix, position)
            for matrix, position in zip(bind_to_neutral_per_vertex, positions)
        ]
        if normals:
            normals = [
                _mat4_transform_normal(matrix, normal)
                for matrix, normal in zip(bind_to_neutral_per_vertex, normals)
            ]
        if tangents:
            tangents = [
                (*_normalize3(_mat4_transform_direction(matrix, tangent)), tangent[3])
                for matrix, tangent in zip(bind_to_neutral_per_vertex, tangents)
            ]

        joint_nodes, joints, weights = _deduplicate_skin_joints(
            joint_nodes, joints, weights
        )

        inverse_bind_matrices = [
            _mat4_mul(
                _mat4_inverse(canonical_world_mats[joint_node]),
                canonical_world_mats[attachment_node],
            )
            for joint_node in joint_nodes
        ]
        inverse_accessor = builder.add_accessor(
            inverse_bind_matrices, "MAT4", COMPONENT_FLOAT
        )
        skin: dict[str, Any] = {
            "name": f"{mesh.m_Name} Skin",
            "joints": joint_nodes,
            "inverseBindMatrices": inverse_accessor,
        }
        skin["skeleton"] = _lowest_common_node_ancestor(
            joint_nodes,
            builder.document["nodes"],
        )
        builder.document["skins"].append(skin)
        skin_index = len(builder.document["skins"]) - 1

    minimum = [min(value[axis] for value in positions) for axis in range(3)]
    maximum = [max(value[axis] for value in positions) for axis in range(3)]
    attributes: dict[str, int] = {
        "POSITION": builder.add_accessor(
            positions,
            "VEC3",
            COMPONENT_FLOAT,
            target=34962,
            minimum=minimum,
            maximum=maximum,
        )
    }
    if normals:
        attributes["NORMAL"] = builder.add_accessor(
            normals, "VEC3", COMPONENT_FLOAT, target=34962
        )
    if decoded.m_UV0:
        attributes["TEXCOORD_0"] = builder.add_accessor(
            [(u, 1.0 - v) for u, v, *_ in decoded.m_UV0],
            "VEC2",
            COMPONENT_FLOAT,
            target=34962,
        )
    if getattr(builder, "include_vertex_colors", False) and decoded.m_Colors:
        if len(decoded.m_Colors) != len(positions):
            raise ValueError(f"{mesh.m_Name}: vertex color count differs from position count")
        # These source bytes are LLAS shader controls, not glTF base-color
        # multipliers. A custom attribute keeps ordinary PBR fallback usable.
        attributes["_SHADER_COLOR"] = builder.add_accessor(
            [tuple(float(channel) / 255.0 for channel in color) for color in decoded.m_Colors],
            "VEC4", COMPONENT_FLOAT, target=34962,
        )
    if tangents:
        attributes["TANGENT"] = builder.add_accessor(
            tangents, "VEC4", COMPONENT_FLOAT, target=34962
        )
    if joints:
        max_bone_index = max((max(values) for values in joints), default=0)
        joint_type = (
            COMPONENT_UNSIGNED_SHORT
            if max_bone_index > 255
            else COMPONENT_UNSIGNED_BYTE
        )
        attributes["JOINTS_0"] = builder.add_accessor(
            joints, "VEC4", joint_type, target=34962
        )
        attributes["WEIGHTS_0"] = builder.add_accessor(
            weights, "VEC4", COMPONENT_FLOAT, target=34962
        )

    targets, target_names = mesh_morphs(
        mesh,
        len(positions),
        builder,
        bind_to_normal_per_vertex=bind_to_neutral_per_vertex,
    )
    materials = list(getattr(renderer, "m_Materials", []))
    primitives = []
    for submesh_index, triangles in enumerate(decoded.get_triangles()):
        indices = [
            value
            for triangle in triangles
            for value in (triangle[0], triangle[2], triangle[1])
        ]
        index_type = (
            COMPONENT_UNSIGNED_SHORT
            if max(indices, default=0) <= 65535
            else COMPONENT_UNSIGNED_INT
        )
        primitive: dict[str, Any] = {
            "attributes": attributes,
            "indices": builder.add_accessor(
                indices, "SCALAR", index_type, target=34963
            ),
            "material": builder.add_material(
                materials[submesh_index]
                if submesh_index < len(materials)
                else None
            ),
            "mode": 4,
        }
        if targets:
            primitive["targets"] = targets
        primitives.append(primitive)

    gltf_mesh: dict[str, Any] = {"name": mesh.m_Name, "primitives": primitives}
    if target_names:
        gltf_mesh["weights"] = [0.0] * len(target_names)
        gltf_mesh["extras"] = {"targetNames": target_names}
    builder.document["meshes"].append(gltf_mesh)
    mesh_index = len(builder.document["meshes"]) - 1

    attachment = builder.document["nodes"][attachment_node]
    if skin_index is not None:
        # In glTF, transforms above a skinned-mesh node do not participate in
        # skinning. Emit the mesh as a scene root and let its inverse bind
        # matrices carry the original attachment transform explicitly.
        mesh_node = len(builder.document["nodes"])
        builder.document["nodes"].append({
            "name": renderer_node_name(mesh.m_Name),
            "mesh": mesh_index,
            "skin": skin_index,
        })
        builder.document["scenes"][0]["nodes"].append(mesh_node)
    else:
        mesh_node = attachment_node
        if "mesh" in attachment:
            mesh_node = len(builder.document["nodes"])
            builder.document["nodes"].append({
                "name": renderer_node_name(mesh.m_Name),
                "mesh": mesh_index,
            })
            attachment.setdefault("children", []).append(mesh_node)
        else:
            attachment["mesh"] = mesh_index

    morphs = [(crc(name), index, name) for index, name in enumerate(target_names)]
    return morphs, mesh.m_Name, mesh_node
