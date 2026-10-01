"""Bang Dream → standardized character package.

This is the per-game converter for Bang Dream (Bushiroad). Each AssetBundle
file is a complete character asset (a "costume"). Costumes split into two
logical halves:
    - head bundles  : carry the face mesh, facial morph targets, expression
                      controllers (Prefab FaceController). No AvatarScaler.
    - body bundles  : carry the body mesh, breast morph, AvatarScaler with
                      the AvatarBody bone ratio + breast size. No facial
                      morphs.

Both halves ship a complete Humanoid skeleton (Hips → Toes). The game-data
layout is authoritative: files below input_bangdream/head are heads and files
below input_bangdream/costume are bodies. Package contents are still inspected
to extract FaceController and AvatarScaler data, but do not override that role.

A new game's converter should live in its own subpackage under converter/<game>/
and reuse everything in converter.common. Bang Dream-specific behavior stays in
this package:

    - load_bundle_assets:       extract the assets required by the converter
    - extract_head_expression:  FaceController → Morph recipes, groups and presets
    - model_adapter:            `_01` materials and FaceBonesCopier redirects

Anything outside this package is generic Unity → glTF plumbing or a top-level
command-line entry point.
"""

from __future__ import annotations

import json
import math
import re
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import UnityPy

from ..common.component_order import order_model_component
from ..common.physics import extract_model_physics
from ..common.normalized_model import (
    _mat4_inverse,
    _mat4_mul,
    _source_world_matrices,
    _trs_to_mat,
    _world_matrices,
    export_normalized_model,
)
from ..common.unity import game_object_transform
from .model_adapter import BangDreamModelAdapter
from .face_source import load_face_controller


UNITY_VERSION = "2021.3.22f1"
INPUT_ROLE_DIRS = (("head", "head"), ("costume", "body"))


# ---------------------------------------------------------------------------
# Bundle classification
# ---------------------------------------------------------------------------

@dataclass
class BundleAssets:
    """Snapshot of one AssetBundle's relevant objects.

    `env` is the loaded UnityPy environment. `prefab` is the GameObject root
    (skinned mesh + transforms). The other fields are pre-resolved references
    used by the converter — keeping them as plain Python fields makes the
    downstream code trivially mockable."""

    path: Path
    env: Any
    prefab: Any
    has_avatar_scaler: bool = False
    face_controller: Any | None = None
    avatar_scaler: Any | None = None
    avatar_description: Any | None = None
    avatar_json: Any | None = None
    kind: str = ""  # "head" | "body" | "unknown"


def load_bundle_assets(path: Path, *, expected_role: str | None = None) -> BundleAssets:
    """Load the prefab and metadata needed by the Bang Dream converter.

    The input directory supplies the component role. Bundle contents are not
    used to guess whether a file is a head or body."""
    UnityPy.config.FALLBACK_UNITY_VERSION = UNITY_VERSION
    env = UnityPy.load(str(path))

    prefab = None
    for name, ptr in env.container.items():
        if name.endswith(".prefab") and ptr.type.name == "GameObject":
            prefab = ptr.deref_parse_as_object()
            break

    avatar_json = None
    has_avatar_scaler = False
    avatar_scaler = None
    avatar_descriptions: list[dict[str, Any]] = []

    for obj in env.objects:
        if obj.type.name == "TextAsset":
            data = obj.read()
            text_name = str(data.m_Name).lower()
            if text_name != "avatar":
                continue
            try:
                txt = data.m_Script if isinstance(data.m_Script, str) else data.m_Script.decode("utf-8")
                payload = json.loads(txt)
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue
            if text_name == "avatar":
                avatar_json = payload
        elif obj.type.name == "MonoBehaviour":
            tree = obj.read_typetree()
            if "BreastSize" in tree and "_boneParts" in tree:
                has_avatar_scaler = True
                avatar_scaler = tree
            elif "BreastSize" in tree and "BoneSettings" in tree:
                avatar_descriptions.append(tree)

    avatar_description = None
    if len(avatar_descriptions) == 1:
        avatar_description = avatar_descriptions[0]
    elif avatar_descriptions:
        prefab_reader = getattr(prefab, "object_reader", None)
        prefab_path_id = getattr(prefab_reader, "path_id", None)
        attached = [
            description
            for description in avatar_descriptions
            if int(description.get("m_GameObject", {}).get("m_FileID", 0)) == 0
            and description.get("m_GameObject", {}).get("m_PathID") == prefab_path_id
        ]
        if len(attached) != 1:
            raise RuntimeError(
                f"{path.name}: multiple AvatarDescription objects without one unique "
                "description attached to the exported prefab root"
            )
        avatar_description = attached[0]

    return BundleAssets(
        path=path,
        env=env,
        prefab=prefab,
        has_avatar_scaler=has_avatar_scaler,
        face_controller=(
            load_face_controller(prefab)
            if prefab is not None and expected_role != "body" else None
        ),
        avatar_scaler=avatar_scaler,
        avatar_description=avatar_description,
        avatar_json=avatar_json,
    )


# ---------------------------------------------------------------------------
# Mesh + morph extraction
# ---------------------------------------------------------------------------

def mesh_morph_names(env: Any) -> dict[str, list[str]]:
    """Return {mesh_name: [morph_name_short, ...]} for every mesh with morphs.

    Morph names come back as the long `prefix.short` form; we strip the
    blendShape prefix because Bang Dream stores them as e.g.
    `face_main_blendShape.face_main_eye_joy_L`. The renderer will match by
    short name within each mesh node."""
    out: dict[str, list[str]] = {}
    for obj in env.objects:
        if obj.type.name != "Mesh":
            continue
        data = obj.read()
        tree = obj.read_typetree()
        channels = tree.get("m_Shapes", {}).get("channels", [])
        if not channels:
            continue
        names: list[str] = []
        for ch in channels:
            full = ch.get("name", "")
            short = full.split(".", 1)[1] if "." in full else full
            names.append(short)
        out[data.m_Name] = names
    return out


# ---------------------------------------------------------------------------
# Head expression extraction
# ---------------------------------------------------------------------------

def _find_layer(face: dict[str, Any], name: str) -> dict[str, Any] | None:
    for layer in face["Layers"]:
        if layer.get("Name") == name:
            return layer
    return None


def _mixer_shapes(layer: dict[str, Any], mixer_name: str) -> list[int]:
    for m in layer.get("Mixers", []):
        if m.get("Name") == mixer_name:
            return m["Shapes"]
    return []


def _mixer_override_blink(layer: dict[str, Any], mixer_name: str) -> bool:
    for m in layer.get("Mixers", []):
        if m.get("Name") == mixer_name:
            return bool(m.get("OverrideBlink", False))
    return False


def _morph_targets_for_shapes(
    shape_indices: list[int],
    mesh_morphs: dict[str, list[str]],
    blendshape_table: dict[int, dict[str, Any]],
) -> dict[str, dict[str, float]]:
    """Resolve the controller's explicit target slots, never morph-name guesses."""
    result: dict[str, dict[str, float]] = {}
    for index in shape_indices:
        if index not in blendshape_table:
            raise ValueError(f"FaceController references missing BlendShapes index {index}")
        bs = blendshape_table[index]
        # Unity serializes percentages; the contract preserves finite source
        # coefficients without silently clipping them to a unit interval.
        weight = float(bs["RangeMax"]) / 100.0
        if not math.isfinite(weight):
            raise ValueError(f"Non-finite source Morph weight for {bs['Name']!r}")
        for target in bs["Targets"]:
            mesh, morph = target["mesh"], target["morph"]
            if morph not in mesh_morphs.get(mesh, []):
                raise ValueError(f"FaceController target {mesh}/{morph} missing from exported Morph inventory")
            bound = result.setdefault(mesh, {})
            if morph in bound and bound[morph] != weight:
                raise ValueError(f"Conflicting FaceController weights for {mesh}/{morph}")
            bound[morph] = weight
    return result


def extract_head_expression(
    bundle: BundleAssets,
    *,
    exported_mesh_morphs: dict[str, list[str]] | None = None,
) -> dict[str, Any]:
    """Preserve source mixer recipes and expose independent face/mouth states.

    The discrete controls are consumer adaptations. In particular, the raw
    weighted-sum API does not reproduce source OverrideBlink scheduling.
    """
    result: dict[str, Any] = {"morphPoses": [], "expressionGroups": [], "expressions": []}
    if bundle.kind != "head":
        return result
    if bundle.face_controller is None:
        raise ValueError(f"{bundle.path.name}: head prefab has no FaceController")
    face = bundle.face_controller
    # Native Initialize uses List.get_Item(Shapes[i]), not the map's Type.
    by_index = dict(enumerate(face["BlendShapes"]))
    mesh_morphs = (
        exported_mesh_morphs
        if exported_mesh_morphs is not None
        else mesh_morph_names(bundle.env)
    )
    if not any(mesh_morphs.values()):
        # Static heads can carry the ordinary face mixer table without any
        # source Morph geometry. They have no expression capability. Confirm
        # the source too when the empty inventory came from the exporter.
        if exported_mesh_morphs is not None and any(mesh_morph_names(bundle.env).values()):
            raise ValueError('BanG Dream source Morph targets are missing from the exported mesh inventory')
        return result
    expressions_layer = _find_layer(face, "Expressions")
    eyes_layer = _find_layer(face, "Eyes")
    lipsync_layer = _find_layer(face, "Lipsync")

    recipes: dict[str, dict[str, dict[str, float]]] = {}

    def add_pose(name: str, shape_indices: list[int]) -> str:
        targets = _morph_targets_for_shapes(shape_indices, mesh_morphs, by_index)
        if name in recipes:
            raise ValueError(f"Duplicate BanG Dream Morph recipe {name!r}")
        recipes[name] = targets
        result["morphPoses"].append({"name": name, "targets": targets})
        return name

    layer_poses: dict[str, dict[str, str]] = {}
    for prefix, layer in (("face", expressions_layer), ("eyes", eyes_layer), ("mouth", lipsync_layer)):
        layer_poses[prefix] = {
            mixer["Name"]: add_pose(f"{prefix}.{mixer['Name']}",
                                    _mixer_shapes(layer, mixer["Name"]))
            for mixer in (layer or {}).get("Mixers", []) if mixer.get("Name")
        }

    close_shapes = _mixer_shapes(eyes_layer, "Close") if eyes_layer else []
    face_states: list[dict[str, Any]] = []
    mouth_states: list[dict[str, Any]] = []
    visemes = {p: {layer_poses["mouth"][p.upper()]: 1}
               for p in "aiueo" if p.upper() in layer_poses["mouth"]}
    for name, face_pose in layer_poses["face"].items():
        blocked = _mixer_override_blink(expressions_layer, name)
        for variant in (None, "Close", "WinkL", "WinkR"):
            if variant and variant not in layer_poses["eyes"]:
                continue
            state_name = name if variant is None else f"{name}-{variant}"
            poses = {face_pose: 1}
            if variant and not blocked:
                poses[layer_poses["eyes"][variant]] = 1
            state: dict[str, Any] = {"name": state_name, "poses": poses}
            # Consumer blink leaves an already-closed eye unchanged. Source
            # Expressions.OverrideBlink suppresses the entire Eyes layer.
            if not blocked and variant != "Close" and close_shapes:
                indices = [index for index in close_shapes
                           if not (variant == "WinkL" and by_index[index]["Name"] == "close_l")
                           and not (variant == "WinkR" and by_index[index]["Name"] == "close_r")]
                if indices:
                    blink_name = "eyes.Close" if variant is None else f"eyes.CloseAfter{variant}"
                    if blink_name not in recipes:
                        add_pose(blink_name, indices)
                    state["controls"] = {"blink": {blink_name: 1}}
            face_states.append(state)
            result["expressions"].append({"name": state_name,
                                          "selections": {"face": state_name, "mouth": name}})

        named_mouth = layer_poses["mouth"].get(name)
        if named_mouth is not None and not recipes[named_mouth]:
            named_mouth = None
        # Consumer speech adaptation, not source-game scheduling: Sad/Serious
        # retain their user-reviewed base while adding A. Smile/Kime fade the
        # teeth pose towards A instead of stacking both at full strength.
        retain = name in {"Sad", "Serious", "Smile", "Kime"}
        if retain and (named_mouth is None or "a" not in visemes):
            raise ValueError(f"{name} speech requires source {name} and A Morph recipes")
        mouth_state: dict[str, Any] = {"name": name, "poses": {named_mouth: 1} if retain else {}}
        controls: dict[str, Any] = {}
        if visemes:
            controls["visemes"] = deepcopy(visemes)
        speech = visemes.get("a") if retain or named_mouth is None else {named_mouth: 1}
        if name in {"Smile", "Kime"}:
            speech = {named_mouth: 0, **visemes["a"]}
        if speech:
            controls["speech"] = deepcopy(speech)
        if controls:
            mouth_state["controls"] = controls
        mouth_states.append(mouth_state)

    if face_states:
        result["expressionGroups"] = [{"name": "face", "states": face_states},
                                      {"name": "mouth", "states": mouth_states}]
        result["defaultExpression"] = result["expressions"][0]["name"]
    return result


def bind_expression_nodes(
    expressions: dict[str, Any],
    exported: Any,
) -> dict[str, Any]:
    """Replace source mesh names with the GLB nodes that actually own them.

    The normalized exporter emits skinned meshes as scene-root nodes because
    parent transforms do not participate in glTF skinning.  Their node names
    therefore differ from the source GameObject / mesh name used while reading
    FaceController. Standard expression maps must point at those emitted GLB nodes,
    not at the now mesh-less skeleton attachment nodes.
    """
    document = exported.builder.document
    meshes = document.get("meshes", [])
    nodes_by_mesh: dict[str, list[str]] = {}
    morphs_by_node: dict[str, set[str]] = {}
    for node in document.get("nodes", []):
        mesh_index = node.get("mesh")
        if not isinstance(mesh_index, int) or not 0 <= mesh_index < len(meshes):
            continue
        mesh_name = meshes[mesh_index].get("name")
        node_name = node.get("name")
        if not mesh_name or not node_name:
            continue
        target_names = meshes[mesh_index].get("extras", {}).get("targetNames", [])
        if any(not isinstance(name, str) or not name.strip() for name in target_names):
            raise RuntimeError(f"GLB mesh {mesh_name!r} has an empty morph target name")
        if len(set(target_names)) != len(target_names):
            raise RuntimeError(f"GLB mesh {mesh_name!r} repeats a morph target name")
        if node_name in morphs_by_node:
            raise RuntimeError(f"GLB repeats morph node name {node_name!r}")
        names = nodes_by_mesh.setdefault(mesh_name, [])
        if node_name not in names:
            names.append(node_name)
        morphs_by_node[node_name] = set(target_names)

    def remap(targets: dict[str, dict[str, float]], label: str) -> dict[str, dict[str, float]]:
        result: dict[str, dict[str, float]] = {}
        for mesh_name, morphs in targets.items():
            node_names = nodes_by_mesh.get(mesh_name)
            if not node_names and mesh_name in morphs_by_node:
                node_names = [mesh_name]
            if not node_names:
                raise RuntimeError(
                    f"{label}: expression mesh {mesh_name!r} has no emitted GLB node"
                )
            for node_name in node_names:
                missing = set(morphs).difference(morphs_by_node[node_name])
                if missing:
                    raise RuntimeError(
                        f"{label}: GLB node {node_name!r} is missing morphs {sorted(missing)!r}"
                    )
                bound = result.setdefault(node_name, {})
                overlap = set(bound).intersection(morphs)
                if any(bound[name] != morphs[name] for name in overlap):
                    raise RuntimeError(
                        f"{label}: conflicting morph weights for GLB node {node_name!r}"
                    )
                bound.update(morphs)
        return result

    bound_expressions = deepcopy(expressions)
    for pose in bound_expressions["morphPoses"]:
        pose["targets"] = remap(pose["targets"], f"Morph pose {pose['name']}")

    return bound_expressions


def exported_mesh_morph_names(exported: Any) -> dict[str, list[str]]:
    """Read the authoritative mesh/morph inventory from an exported GLB."""
    result: dict[str, list[str]] = {}
    for mesh in exported.builder.document.get("meshes", []):
        mesh_name = mesh.get("name")
        if not mesh_name:
            continue
        names = result.setdefault(mesh_name, [])
        for morph_name in mesh.get("extras", {}).get("targetNames", []):
            if morph_name not in names:
                names.append(morph_name)
    return result


# ---------------------------------------------------------------------------
# GLB export
# ---------------------------------------------------------------------------

def _package_name(bundle: BundleAssets) -> str:
    """Derive a stable per-bundle package name from the file's container path.

    Bang Dream files have no extension, so we can't rely on `.stem`. The
    container's last path segment is the canonical id (e.g.
    `assets/star/forassetbundle/asneeded/star3d/character/head/ch_018/018_cos_base/`
    → `018_cos_base`)."""
    for name, ptr in bundle.env.container.items():
        if name.endswith(".prefab") and ptr.type.name == "GameObject":
            package_name = Path(name).parent.name
            if package_name:
                return package_name
    raise ValueError(f"No canonical prefab container path in {bundle.path.name}")


def export_glb(bundle: BundleAssets, normalized_skeleton: dict[str, Any] | None = None) -> Any:
    """Reuse the common normalized exporter to write a head/body GLB.

    Bang Dream's characters need to pass through Unity-side normalisation
    (`BakePipeline.Run` writing `baked_motions/normalized/<name>.skeleton.json`)
    before they can share the standard Hasu motion set. A standardized package
    also needs the same Unity Animator `humanScale` used by motion baking, so
    raw export is rejected instead of emitting a plausible but incorrect
    manifest value.
    """
    if normalized_skeleton is None:
        raise ValueError(
            f"{bundle.path.name}: normalized skeleton with Unity humanScale is required"
        )

    root_pointer = None
    for name, ptr in bundle.env.container.items():
        if name.endswith(".prefab") and ptr.type.name == "GameObject":
            root_pointer = ptr
            break
    if root_pointer is None:
        raise ValueError(f"No prefab found in {bundle.path.name}")

    return export_normalized_model(
        bundle.env,
        root_pointer,
        normalized_skeleton,
        BangDreamModelAdapter(bundle.env),
    )


# ---------------------------------------------------------------------------
# Package config emission
# ---------------------------------------------------------------------------

BREAST_PARAMETER_VALUES = (0.0, 50.0, 100.0)


def breast_size_value(value: Any) -> float:
    """Preserve AvatarDescription.BreastSize as finite model-supplied data."""
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"expected finite BreastSize, got {value!r}") from exc
    if not math.isfinite(number):
        raise ValueError(f"expected finite BreastSize, got {value!r}")
    return number


def breast_morph_endpoint(name: str) -> float | None:
    """Recognize the endpoint aliases present in the retained source corpus."""
    match = re.search(r"(?:^|_)b?reast_?([sml])(?:shape|\d+)?$", name, re.IGNORECASE)
    if not match:
        return None
    return {"S": 0.0, "M": 50.0, "L": 100.0}[match.group(1).upper()]


def _gltf_morph_nodes(exported: Any) -> dict[str, list[tuple[int, list[str]]]]:
    document = exported.builder.document
    meshes = document.get("meshes", [])
    result: dict[str, list[tuple[int, list[str]]]] = {}
    for node_index, node in enumerate(document.get("nodes", [])):
        mesh_index = node.get("mesh")
        if not isinstance(mesh_index, int) or not 0 <= mesh_index < len(meshes):
            continue
        mesh = meshes[mesh_index]
        mesh_name = mesh.get("name")
        target_names = mesh.get("extras", {}).get("targetNames", [])
        if mesh_name and target_names:
            result.setdefault(mesh_name, []).append((node_index, target_names))
    return result


def _breast_behavior_binding(bundle: BundleAssets, exported: Any) -> dict[str, Any]:
    """Extract UpdateBreasts renderer slots without baking a glTF animation."""
    scaler = bundle.avatar_scaler
    if not scaler:
        raise ValueError(f"{bundle.path.name}: missing AvatarScaler breast binding")
    renderer_refs = scaler.get("_bodyRenderers", [])
    if not isinstance(renderer_refs, list):
        raise ValueError(f"{bundle.path.name}: invalid AvatarScaler body renderers")

    try:
        default_index = int(scaler["DefaultBreastSize"])
        default_value = BREAST_PARAMETER_VALUES[default_index]
        breast_size_value(scaler["BreastSize"])
        blendshape_max = scaler["_blendShapeMax"]
        maxima = (float(blendshape_max["x"]), float(blendshape_max["y"]))
    except (KeyError, TypeError, ValueError, IndexError) as exc:
        raise ValueError(f"{bundle.path.name}: invalid AvatarScaler breast profile") from exc
    if not all(math.isfinite(value) for value in maxima):
        raise ValueError(f"{bundle.path.name}: invalid _blendShapeMax {maxima!r}")

    source_objects = {obj.path_id: obj for obj in bundle.env.objects}
    gltf_nodes_by_mesh = _gltf_morph_nodes(exported)
    non_default_sizes = [
        value for value in BREAST_PARAMETER_VALUES if value != default_value
    ]
    targets_by_node: dict[int, tuple[list[str], dict[float, int]]] = {}

    for reference in renderer_refs:
        if reference.get("m_FileID", 0) != 0:
            raise RuntimeError(f"{bundle.path.name}: external body renderer reference")
        source = source_objects.get(reference.get("m_PathID"))
        if source is None or source.type.name != "SkinnedMeshRenderer":
            raise RuntimeError(f"{bundle.path.name}: unresolved body renderer reference")
        renderer = source.read()
        if not renderer.m_Mesh:
            raise RuntimeError(f"{bundle.path.name}: body renderer has no mesh")
        source_mesh = renderer.m_Mesh.deref_parse_as_object()
        mesh_name = source_mesh.m_Name
        candidates = gltf_nodes_by_mesh.get(mesh_name, [])
        source_shapes = getattr(source_mesh, "m_Shapes", None)
        source_channels = getattr(source_shapes, "channels", None) if source_shapes else None
        if not candidates and not source_channels:
            continue
        if len(candidates) != 1:
            raise RuntimeError(
                f"{bundle.path.name}: body mesh {mesh_name!r} resolves to "
                f"{len(candidates)} GLB morph nodes"
            )
        node_index, target_names = candidates[0]
        if len(target_names) < 2:
            raise RuntimeError(
                f"{bundle.path.name}: body mesh {mesh_name!r} has fewer than "
                "the two BlendShape slots written by AvatarScaler.UpdateBreasts"
            )
        endpoints = {
            value: target_index
            for target_index, value in enumerate(non_default_sizes)
        }
        previous = targets_by_node.get(node_index)
        current = (target_names, endpoints)
        if previous is not None and previous != current:
            raise RuntimeError(f"{bundle.path.name}: conflicting duplicate body renderer binding")
        targets_by_node[node_index] = current

    renderers: list[dict[str, Any]] = []
    for node_index, (target_names, endpoints) in sorted(targets_by_node.items()):
        node_name = exported.builder.document["nodes"][node_index].get("name")
        if not isinstance(node_name, str) or not node_name:
            raise RuntimeError(f"{bundle.path.name}: body renderer node has no name")
        renderers.append({
            "target": node_name,
            "morphs": [
                {"value": value, "index": endpoints[value]}
                for value in non_default_sizes
            ],
        })
    return {
        "defaultValue": default_value,
        "blendShapeMax": list(maxima),
        "renderers": renderers,
    }


AVATAR_SCALER_BEHAVIOR = "Garupa.AvatarScaler"


def _number(source: dict[str, Any], key: str, label: str) -> float:
    try:
        value = float(source[key])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"{label}: invalid {key}") from exc
    if not math.isfinite(value):
        raise ValueError(f"{label}: invalid {key}")
    return value


def _vector3(source: Any, label: str) -> list[float]:
    if not isinstance(source, dict):
        raise ValueError(f"AvatarScaler {label}: invalid Vector3")
    values = []
    for axis in "xyz":
        try:
            value = float(source[axis])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"AvatarScaler {label}: invalid Vector3") from exc
        if not math.isfinite(value):
            raise ValueError(f"AvatarScaler {label}: invalid Vector3")
        values.append(value)
    return values


def _avatar_profile_parameters(source: dict[str, Any]) -> dict[str, Any]:
    """Normalize an AvatarDescription-shaped profile for the JS Behavior."""
    if not isinstance(source, dict):
        raise ValueError("AvatarScaler profile must be an object")
    settings = source.get("BoneSettings", [])
    if not isinstance(settings, list):
        raise ValueError("AvatarScaler profile has invalid BoneSettings")
    normalized_settings: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, raw in enumerate(settings):
        if not isinstance(raw, dict) or not isinstance(raw.get("Name"), str) or not raw["Name"]:
            raise ValueError(f"AvatarScaler profile has invalid BoneSettings[{index}]")
        name = raw["Name"]
        if name in seen:
            raise ValueError(f"AvatarScaler profile repeats BoneSettings {name}")
        seen.add(name)
        normalized_settings.append({
            "name": name,
            "heightInfluence": _number(raw, "HeightInfluence", name),
            "length": _number(raw, "Length", name),
            "thickness": _number(raw, "Thickness", name),
        })
    height = _number(source, "Height", "AvatarScaler profile")
    if height <= 0:
        raise ValueError("AvatarScaler profile has invalid Height")
    return {
        "height": height,
        "breastSize": _number(source, "BreastSize", "AvatarScaler profile"),
        "legSpacing": _number(source, "LegSpacing", "AvatarScaler profile"),
        "headScaling": _number(source, "HeadScaling", "AvatarScaler profile"),
        "hipScaling": _number(source, "HipScaling", "AvatarScaler profile"),
        "shoulderSpacing": _number(source, "ShoulderSpacing", "AvatarScaler profile"),
        "boneSettings": normalized_settings,
    }


def _pointer_transform_name(
    pointer: dict[str, Any],
    transform_names: dict[int, str],
    label: str,
) -> str | None:
    if not isinstance(pointer, dict):
        raise RuntimeError(f"{label}: invalid Transform reference")
    file_id = int(pointer.get("m_FileID", 0))
    path_id = int(pointer.get("m_PathID", 0))
    if path_id == 0:
        return None
    if file_id != 0:
        raise RuntimeError(f"{label}: external Transform {file_id}:{path_id}")
    name = transform_names.get(path_id)
    if name is None:
        raise RuntimeError(f"{label}: unresolved Transform path id {path_id}")
    return name


def _avatar_binding_parameters(
    scaler: dict[str, Any],
    transform_names: dict[int, str],
    secondary_offsets: list[dict[str, Any]] | None = None,
    breast: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Normalize body-local AvatarScaler bindings to public glTF node names."""
    if not isinstance(scaler, dict):
        raise ValueError("AvatarScaler binding must be an object")
    bone_parts = scaler.get("_boneParts", [])
    accessories = scaler.get("_accessories", [])
    if not isinstance(bone_parts, list) or not isinstance(accessories, list):
        raise ValueError("AvatarScaler binding arrays are invalid")

    normalized_parts: list[dict[str, Any]] = []
    fallback_settings: list[dict[str, Any]] = []
    for index, raw in enumerate(bone_parts):
        if not isinstance(raw, dict) or not isinstance(raw.get("Name"), str) or not raw["Name"]:
            raise ValueError(f"AvatarScaler binding has invalid _boneParts[{index}]")
        name = raw["Name"]
        bones = raw.get("Bones", [])
        targets = raw.get("Targets", [])
        if not isinstance(bones, list) or not isinstance(targets, list) or len(bones) != len(targets):
            raise ValueError(f"AvatarScaler {name} has invalid Bones/Targets")
        normalized_bones: list[str] = []
        normalized_targets: list[str] = []
        for pair_index, (bone_pointer, target_pointer) in enumerate(zip(bones, targets)):
            target_name = _pointer_transform_name(
                target_pointer, transform_names, f"AvatarScaler {name} Targets[{pair_index}]"
            )
            if target_name is None:
                continue
            bone_name = _pointer_transform_name(
                bone_pointer, transform_names, f"AvatarScaler {name} Bones[{pair_index}]"
            )
            if bone_name is None:
                continue
            normalized_bones.append(bone_name)
            normalized_targets.append(target_name)
        height_influence = _number(raw, "HeightInfluence", name)
        length = _number(raw, "Length", name)
        thickness = _number(raw, "Thickness", name)
        normalized_parts.append({
            "name": name,
            "heightInfluence": height_influence,
            "length": length,
            "thickness": thickness,
            "bones": normalized_bones,
            "targets": normalized_targets,
        })
        fallback_settings.append({
            "name": name,
            "heightInfluence": height_influence,
            "length": 1.0,
            "thickness": 1.0,
        })

    normalized_accessories: list[str] = []
    for index, pointer in enumerate(accessories):
        name = _pointer_transform_name(
            pointer, transform_names, f"AvatarScaler _accessories[{index}]"
        )
        if name is not None:
            normalized_accessories.append(name)
    hip = _pointer_transform_name(scaler.get("_hip", {}), transform_names, "AvatarScaler _hip")
    if hip is None:
        raise RuntimeError("AvatarScaler _hip is null")

    leg_spacing = _number(scaler, "LegSpacing", "AvatarScaler binding")
    head_scaling = _number(scaler, "HeadScaling", "AvatarScaler binding")
    hip_scaling = _number(scaler, "HipScaling", "AvatarScaler binding")
    shoulder_spacing = _number(scaler, "ShoulderSpacing", "AvatarScaler binding")
    height = _number(scaler, "Height", "AvatarScaler binding")
    fallback_profile = {
        "height": height,
        "breastSize": _number(scaler, "BreastSize", "AvatarScaler binding"),
        "legSpacing": 1.0,
        "headScaling": head_scaling,
        "hipScaling": 1.0,
        "shoulderSpacing": 1.0,
        "boneSettings": fallback_settings,
    }
    binding = {
        "useScaling": bool(scaler.get("UseScaling")),
        "legSpacing": leg_spacing,
        "hipScaling": hip_scaling,
        "shoulderSpacing": shoulder_spacing,
        "upperLegs": ["LeftUpperLeg", "RightUpperLeg"],
        "shoulders": ["LeftShoulder", "RightShoulder"],
        "head": "Head",
        "hip": hip,
        "leftLeg": ["LeftUpperLeg", "LeftLowerLeg", "LeftFoot"],
        "accessories": normalized_accessories,
        "secondaryOffsets": secondary_offsets or [],
        "positionOffset": _vector3(scaler.get("_positionOffset"), "_positionOffset"),
        "propPositionOffset": _number(scaler, "_propPositionOffset", "AvatarScaler binding"),
        "adjustOffsetRatio": _vector3(scaler.get("_adjustOffsetRatio"), "_adjustOffsetRatio"),
        "boneParts": normalized_parts,
        "profile": fallback_profile,
    }
    if breast is not None:
        binding["breast"] = breast
    return binding


def _normalized_transform_context(
    bundle: BundleAssets,
    normalized_skeleton: dict[str, Any],
) -> tuple[
    dict[int, str],
    dict[int, tuple[Any, int]],
    list[list[float]],
    list[list[float]],
]:
    bones = normalized_skeleton.get("bones", [])
    by_path = {
        tuple(int(part) for part in bone.get("hierarchyPath", [])): (index, bone.get("name"))
        for index, bone in enumerate(bones)
    }
    if bundle.prefab is None:
        raise RuntimeError(f"{bundle.path.name}: AvatarScaler binding requires prefab root")
    root = game_object_transform(bundle.prefab)
    names: dict[int, str] = {}
    transforms: dict[int, tuple[Any, int]] = {}

    def visit(transform: Any, path: tuple[int, ...]) -> None:
        match = by_path.get(path)
        if match is None:
            raise RuntimeError(f"{bundle.path.name}: normalized skeleton misses path {path}")
        node_index, name = match
        if not isinstance(name, str) or not name:
            raise RuntimeError(f"{bundle.path.name}: normalized skeleton misses path {path}")
        path_id = int(transform.object_reader.path_id)
        names[path_id] = name
        transforms[path_id] = (transform, node_index)
        children = [child for child in getattr(transform, "m_Children", []) if child]
        for child_index, child in enumerate(children):
            visit(child.deref_parse_as_object(), path + (child_index,))

    visit(root, ())
    indexed_transforms = list(transforms.values())
    return (
        names,
        transforms,
        _source_world_matrices(indexed_transforms, bones),
        _world_matrices(bones),
    )


def _secondary_offsets(
    scaler: dict[str, Any],
    normalized_skeleton: dict[str, Any],
    names: dict[int, str],
    transforms: dict[int, tuple[Any, int]],
    source_world: list[list[float]],
    canonical_world: list[list[float]],
) -> list[dict[str, Any]]:
    offsets = scaler.get("_secondaryOffsets", [])
    if not isinstance(offsets, list):
        raise ValueError("AvatarScaler binding has invalid _secondaryOffsets")
    bones = normalized_skeleton["bones"]
    output: list[dict[str, Any]] = []
    for index, raw in enumerate(offsets):
        if not isinstance(raw, dict):
            raise ValueError(f"AvatarScaler _secondaryOffsets[{index}] is invalid")
        pointer = raw.get("Target", {})
        target_name = _pointer_transform_name(
            pointer, names, f"AvatarScaler _secondaryOffsets[{index}].Target"
        )
        if target_name is None:
            continue
        path_id = int(pointer.get("m_PathID", 0))
        if path_id not in transforms:
            raise RuntimeError(
                f"AvatarScaler _secondaryOffsets[{index}] target is not normalized"
            )
        transform, node_index = transforms[path_id]
        parent_index = int(bones[node_index]["parentIndex"])
        source_parent = (
            source_world[parent_index] if parent_index >= 0
            else [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0,
                  0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0]
        )
        canonical_parent = (
            canonical_world[parent_index] if parent_index >= 0
            else [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0,
                  0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0]
        )
        source_position = transform.m_LocalPosition
        source_rotation = transform.m_LocalRotation
        source_scale = transform.m_LocalScale
        position = [float(source_position.x), float(source_position.y), float(source_position.z)]
        quaternion = [float(source_rotation.x), float(source_rotation.y),
                      float(source_rotation.z), float(source_rotation.w)]
        scale = [float(source_scale.x), float(source_scale.y), float(source_scale.z)]
        axis = _vector3(raw.get("OffsetAxis"), f"_secondaryOffsets[{index}].OffsetAxis")
        serialized_default = _vector3(
            raw.get("Default"), f"_secondaryOffsets[{index}].Default"
        )
        offset_range = raw.get("OffsetRange")
        if not isinstance(offset_range, dict):
            raise ValueError(f"AvatarScaler _secondaryOffsets[{index}].OffsetRange is invalid")
        ranges = [float(offset_range[key]) for key in ("x", "y")]
        if not all(math.isfinite(value) for value in ranges):
            raise ValueError(f"AvatarScaler _secondaryOffsets[{index}].OffsetRange is invalid")
        use_rotation = bool(raw.get("UseRotation"))
        runtime_default = (
            [float(value) for value in bones[node_index]["sourceUnityEulerAngles"]]
            if use_rotation else position
        )
        output.append({
            "target": target_name,
            "useRotation": use_rotation,
            "default": runtime_default,
            "serializedDefault": serialized_default,
            "axis": axis,
            "range": ranges,
            "source": {
                "position": position,
                "rotation": quaternion,
                "scale": scale,
            },
            "projection": {
                "left": _mat4_mul(_mat4_inverse(canonical_parent), source_parent),
                "right": _mat4_mul(
                    _mat4_inverse(source_world[node_index]), canonical_world[node_index]
                ),
            },
        })
    return output


def _source_position_frame(
    transform: Any,
    node_index: int,
    bones: list[dict[str, Any]],
    source_world: list[list[float]],
    canonical_world: list[list[float]],
) -> dict[str, Any]:
    """Describe one serialized Unity local frame at the canonical glTF seam."""
    parent_index = int(bones[node_index]["parentIndex"])
    identity = [
        1.0, 0.0, 0.0, 0.0,
        0.0, 1.0, 0.0, 0.0,
        0.0, 0.0, 1.0, 0.0,
        0.0, 0.0, 0.0, 1.0,
    ]
    source_parent = source_world[parent_index] if parent_index >= 0 else identity
    canonical_parent = canonical_world[parent_index] if parent_index >= 0 else identity
    position = transform.m_LocalPosition
    rotation = transform.m_LocalRotation
    scale = transform.m_LocalScale
    return {
        "source": {
            "position": [float(position.x), float(position.y), float(position.z)],
            "rotation": [
                float(rotation.x), float(rotation.y), float(rotation.z), float(rotation.w)
            ],
            "scale": [float(scale.x), float(scale.y), float(scale.z)],
        },
        "projection": {
            "left": _mat4_mul(_mat4_inverse(canonical_parent), source_parent),
            "right": _mat4_mul(
                _mat4_inverse(source_world[node_index]), canonical_world[node_index]
            ),
        },
    }


def _source_scale_frame(
    transform: Any,
    node_index: int,
    bones: list[dict[str, Any]],
    canonical_world: list[list[float]],
) -> dict[str, Any]:
    """Map a zero-muscle Unity bone-local scale into canonical joint frames."""
    position = transform.m_LocalPosition
    rotation = transform.m_LocalRotation
    scale = transform.m_LocalScale
    return {
        "source": {
            "position": [float(position.x), float(position.y), float(position.z)],
            "rotation": [
                float(rotation.x), float(rotation.y), float(rotation.z), float(rotation.w)
            ],
            "scale": [float(scale.x), float(scale.y), float(scale.z)],
        },
        "projection": {
            "left": [
                1.0, 0.0, 0.0, 0.0,
                0.0, 1.0, 0.0, 0.0,
                0.0, 0.0, 1.0, 0.0,
                0.0, 0.0, 0.0, 1.0,
            ],
            "right": _mat4_mul(
                _mat4_inverse([
                    float(value) for value in bones[node_index]["neutralWorldMatrix"]
                ]),
                canonical_world[node_index],
            ),
        },
    }


def _source_direction_frame(
    transform: Any,
    node_index: int,
    bones: list[dict[str, Any]],
    canonical_world: list[list[float]],
) -> dict[str, Any]:
    """Map a zero-muscle Unity parent-local direction into canonical axes."""
    parent_index = int(bones[node_index]["parentIndex"])
    identity = [
        1.0, 0.0, 0.0, 0.0,
        0.0, 1.0, 0.0, 0.0,
        0.0, 0.0, 1.0, 0.0,
        0.0, 0.0, 0.0, 1.0,
    ]
    source_parent = (
        [float(value) for value in bones[parent_index]["neutralWorldMatrix"]]
        if parent_index >= 0 else identity
    )
    canonical_parent = canonical_world[parent_index] if parent_index >= 0 else identity
    position = transform.m_LocalPosition
    return {
        "sourcePosition": [float(position.x), float(position.y), float(position.z)],
        "projection": _mat4_mul(_mat4_inverse(canonical_parent), source_parent),
    }


def _avatar_behavior_declarations(
    bundle: BundleAssets,
    normalized_skeleton: dict[str, Any],
    exported: Any,
) -> list[dict[str, Any]]:
    if bundle.kind == "head" and bundle.avatar_description is not None:
        parameters = {"profile": _avatar_profile_parameters(bundle.avatar_description)}
    elif bundle.kind == "body" and bundle.avatar_scaler is not None:
        transform_names, transforms, source_world, canonical_world = (
            _normalized_transform_context(bundle, normalized_skeleton)
        )
        secondary_offsets = _secondary_offsets(
            bundle.avatar_scaler,
            normalized_skeleton,
            transform_names,
            transforms,
            source_world,
            canonical_world,
        )
        breast = _breast_behavior_binding(bundle, exported)
        binding = _avatar_binding_parameters(
            bundle.avatar_scaler, transform_names, secondary_offsets, breast
        )
        by_name = {
            transform_names[path_id]: value
            for path_id, value in transforms.items()
            if path_id in transform_names
        }
        for part in binding["boneParts"]:
            part["boneFrames"] = [
                _source_scale_frame(
                    by_name[bone][0], by_name[bone][1],
                    normalized_skeleton["bones"], canonical_world,
                )
                for bone in part["bones"]
            ]
            if part["name"] != "Feets":
                continue
            part["targetFrames"] = [
                _source_position_frame(
                    by_name[target][0], by_name[target][1],
                    normalized_skeleton["bones"], source_world, canonical_world,
                )
                for target in part["targets"]
            ]
        binding["shoulderFrames"] = [
            _source_direction_frame(
                by_name[shoulder][0], by_name[shoulder][1],
                normalized_skeleton["bones"], canonical_world,
            )
            for shoulder in binding["shoulders"]
        ]
        parameters = {"binding": binding}
    else:
        return []
    return [{
        "name": AVATAR_SCALER_BEHAVIOR,
        "required": True,
        "parameters": parameters,
    }]

def build_component_config(
    bundle: BundleAssets,
    expressions: dict[str, Any],
    model_filename: str,
    *,
    human_scale: float,
    behaviors: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Compose one GLB entry for a standardized model manifest.

    Each source GLB retains the Unity-baked Animator.humanScale used by the
    standardized motion contract. Facial fields belong only to head entries;
    body entries omit them entirely."""
    scale = float(human_scale)
    if not math.isfinite(scale) or scale <= 0:
        raise ValueError(
            f"{bundle.path.name}: normalized Unity humanScale must be a positive finite number"
        )
    component: dict[str, Any] = {
        "role": bundle.kind,
        "model": model_filename,
        "humanoidScale": scale,
    }
    if bundle.kind == "head":
        component.update(expressions)
    if behaviors:
        component["behaviors"] = behaviors
    return component


def build_package_config(
    package_name: str,
    components: list[dict[str, Any]],
) -> dict[str, Any]:
    """Compose a self-contained manifest for one logical model directory."""
    return {
        "components": [
            order_model_component({
                "type": "model",
                "name": package_name,
                "group": "garupa",
                "motionGroup": "garupa",
                **component,
            })
            for component in components
        ],
    }


def _load_normalized(
    baked_dir: Path | None,
    package_name: str,
    bundle: BundleAssets | None = None,
) -> dict[str, Any] | None:
    """Pick up the Unity-baked normalized skeleton if available.

    Body bundles use their serialized Avatar. Head bundles have no serialized
    Avatar, so the Unity baker builds and validates one from the compatible
    HumanDescription before applying the same official Humanoid solver."""
    if not baked_dir:
        return None
    normalized_dir = baked_dir / "normalized"
    if not normalized_dir.exists():
        print(f"[bangdream] error: normalized skeleton directory missing for {package_name}")
        return None

    # Skeleton identity comes from the prefab root, not the source filename.
    # Keep role-specific candidates separate: a head and costume may share the
    # same package name and must never consume each other's normalized bind.
    if bundle is None:
        candidates = [normalized_dir / f"{package_name}.skeleton.json"]
    elif bundle.kind == "head":
        candidates = [normalized_dir / f"Head_{package_name}.skeleton.json"]
    elif bundle.kind == "body":
        candidates = [normalized_dir / f"CH_{package_name}_Body.skeleton.json"]
    else:
        candidates = []
    for candidate in candidates:
        if candidate.exists():
            return json.loads(candidate.read_text(encoding="utf-8"))

    print(f"[bangdream] error: normalized skeleton for {package_name} is required; "
          f"run `npm run bake:bangdream` first.")
    return None


def convert_one(
    bundle_path: Path,
    output_dir: Path,
    baked_dir: Path | None = None,
    occupied_roles: set[tuple[str, str]] | None = None,
    expected_role: str | None = None,
) -> tuple[str, dict[str, Any]]:
    """Convert one AssetBundle to one entry in a model directory.

    Writes `<role>.glb` into `<output_dir>/<package_name>/` and returns the
    package name plus its manifest entry. The caller aggregates entries and
    writes exactly one config.json after duplicate-role validation.
    """
    if expected_role not in {"head", "body"}:
        raise ValueError("Bang Dream component role must come from head/ or costume/")
    bundle = load_bundle_assets(bundle_path, expected_role=expected_role)
    bundle.kind = expected_role

    package_name = _package_name(bundle)
    role_key = (package_name, bundle.kind)
    if occupied_roles is not None:
        if role_key in occupied_roles:
            raise ValueError(
                f"duplicate {bundle.kind} component for bangdream/{package_name}; "
                "refusing to overwrite the first source"
            )
        occupied_roles.add(role_key)
    normalized = _load_normalized(baked_dir, package_name, bundle)
    exported = export_glb(bundle, normalized)
    physics = extract_model_physics(bundle.env, exported)
    behaviors = _avatar_behavior_declarations(bundle, normalized, exported)
    if bundle.kind == "head":
        expressions = extract_head_expression(
            bundle,
            exported_mesh_morphs=exported_mesh_morph_names(exported),
        )
    else:
        expressions = {"morphPoses": [], "expressionGroups": [], "expressions": []}
    if bundle.kind == "head":
        expressions = bind_expression_nodes(
            expressions,
            exported,
        )

    package_dir = output_dir / package_name
    package_dir.mkdir(parents=True, exist_ok=True)
    model_filename = f"{bundle.kind}.glb"
    component = build_component_config(
        bundle,
        expressions,
        model_filename,
        human_scale=exported.human_scale,
        behaviors=behaviors,
    )
    if physics:
        component["physics"] = physics
    exported.builder.write(package_dir / model_filename)
    return package_name, component


def discover_bundle_inputs(input_dir: Path) -> list[tuple[Path, str]]:
    """Return files from the available head/ and costume/ role directories."""
    try:
        input_dir.stat()
    except FileNotFoundError:
        return []
    if not input_dir.is_dir():
        raise NotADirectoryError(input_dir)
    discovered: list[tuple[Path, str]] = []
    for directory_name, expected_role in INPUT_ROLE_DIRS:
        role_dir = input_dir / directory_name
        if role_dir.exists() and not role_dir.is_dir():
            raise NotADirectoryError(role_dir)
        if not role_dir.is_dir():
            continue
        discovered.extend(
            (entry, expected_role)
            for entry in sorted(role_dir.iterdir())
            if entry.is_file() and not entry.name.startswith(".")
        )
    return discovered


def _load_existing_components(
    output_dir: Path,
) -> dict[str, dict[str, dict[str, Any]]]:
    """Load previously generated components for incremental conversion.

    Source bundles are a working set, not the lifetime inventory. A normal
    conversion updates roles present in the current input while retaining
    already generated roles and packages whose source bundle is no longer in
    ``input_bangdream``. ``--clean`` remains the explicit rebuild boundary.
    """
    components_by_name: dict[str, dict[str, dict[str, Any]]] = {}
    if not output_dir.exists():
        return components_by_name

    for package_dir in sorted(path for path in output_dir.iterdir() if path.is_dir()):
        if package_dir.name == "motions":
            continue
        config_path = package_dir / "config.json"
        if not config_path.is_file():
            continue
        try:
            config = json.loads(config_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"existing config is not valid JSON: {config_path}") from exc
        if set(config) != {"components"} or not isinstance(config.get("components"), list):
            raise ValueError(f"existing Bang Dream config has an invalid identity: {config_path}")

        by_role: dict[str, dict[str, Any]] = {}
        for component in config["components"]:
            if (
                not isinstance(component, dict)
                or component.get("type") != "model"
                or component.get("name") != package_dir.name
                or component.get("group") != "garupa"
                or component.get("motionGroup") != "garupa"
            ):
                raise ValueError(f"existing Bang Dream config has an invalid model entry: {config_path}")
            role = component.get("role") if isinstance(component, dict) else None
            if role not in {"head", "body"}:
                raise ValueError(f"existing Bang Dream config has invalid role {role!r}: {config_path}")
            if role in by_role:
                raise ValueError(f"existing Bang Dream config repeats role {role!r}: {config_path}")
            model = component.get("model")
            if not isinstance(model, str) or Path(model).name != model:
                raise ValueError(f"existing Bang Dream config has invalid model path: {config_path}")
            if not (package_dir / model).is_file():
                raise FileNotFoundError(
                    f"existing Bang Dream component is missing {package_dir / model}"
                )
            by_role[role] = {
                key: value
                for key, value in component.items()
                if key not in {"type", "name", "group", "motionGroup"}
            }
        if by_role:
            components_by_name[package_dir.name] = by_role
    return components_by_name


def convert_all(
    input_dir: Path,
    output_dir: Path,
    baked_dir: Path | None = None,
) -> list[dict[str, Any]]:
    """Convert AssetBundles from `input_dir/head` and `input_dir/costume`.

    Bang Dream ships bundles without a file extension. Head files are read
    from `head/`; body files are read from `costume/`. Files with the same
    name aggregate into one self-contained model directory with `head.glb`
    and `body.glb` entries in a single config.json.

    Multi-game layout:
        output_packages/
            hasunosora/
                SCSch011KahDeA/...
            bangdream/
                018_cos_base/...
                motions/...
                index.json
        index.json         (top-level merge, written by convert.py)
    """
    UnityPy.config.FALLBACK_UNITY_VERSION = UNITY_VERSION
    inputs = discover_bundle_inputs(input_dir)
    if not inputs:
        print(f"[bangdream:convert] 输入为空: {input_dir}")
        return []
    output_dir.mkdir(parents=True, exist_ok=True)
    components_by_name = _load_existing_components(output_dir)
    occupied_roles: set[tuple[str, str]] = set()
    for entry, expected_role in inputs:
        result = convert_one(
            entry,
            output_dir,
            baked_dir,
            occupied_roles,
            expected_role,
        )
        package_name, component = result
        role = component["role"]
        package_components = components_by_name.setdefault(package_name, {})
        package_components[role] = component
        print(f"[bangdream] {entry.name} -> {package_name}/{component['model']} "
              f"({len(component.get('expressions', []))} expressions)")

    role_order = {"head": 0, "body": 1}
    configs: list[dict[str, Any]] = []
    for package_name, by_role in sorted(components_by_name.items()):
        components = sorted(
            by_role.values(),
            key=lambda component: role_order[component["role"]],
        )
        config = build_package_config(package_name, components)
        package_dir = output_dir / package_name
        (package_dir / "config.json").write_text(
            json.dumps(config, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        configs.append(config)

    config_paths = [
        f"{cfg['components'][0]['name']}/config.json"
        for cfg in configs
    ]
    (output_dir / "index.json").write_text(
        json.dumps({"configs": config_paths}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return configs
