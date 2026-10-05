"""LLAS AssetBundle to standard Humanoid model and motion packages."""

from __future__ import annotations

import json
import math
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import UnityPy

from converter.common.motion import motion_clip_ids
from converter.common.motion_binary import encode_motion
from converter.common.normalized_model import export_normalized_model
from converter.common.unity import game_object_transform
from converter.llas.face_source import load_member_with_face
from converter.llas.face_composition import HeadMaterialAdapter, append_face, append_rigid_renderers, needs_face_graft
from converter.llas.facial_bake import face_pose_path
from converter.llas.facial_controls import build_facial_expressions
from converter.llas.board_controls import append_board_controls
from converter.llas.face_companions import build_face_behavior
from converter.llas.materials import attach_llas_materials
from converter.llas.metadata import description_for_source, model_descriptions
from converter.llas.source_inventory import active_sources
from converter.common.component_order import order_model_component
from converter.common.idle_pose import sample_baked_pose
from converter.common.physics import extract_model_physics
from .skirt import build_skirt_behavior


UNITY_VERSION = "2018.4.23f1"
CLIP_COLLECTIONS = ("clips", "auxiliaryClips", "leftHandPoses", "rightHandPoses")


def motion_resource_name(name: str) -> str:
    parts = name.split("_", 2)
    if len(parts) == 3 and re.fullmatch(r"ch\d{4}", parts[0]):
        return f"llas/{parts[0]}_{parts[1]}/{parts[2]}"
    return f"llas/{name}"


@lru_cache(maxsize=64)
def _idle_defaults_for_character(character: str, input_root: Path, baked_root: Path) -> dict[str, Any]:
    if not re.fullmatch(r"ch\d{4}", character):
        return {}
    if character == "ch9999":
        character = "ch0209"  # Rina-board models use Rina's ordinary Humanoid idle.
    inventory = active_sources(input_root)
    sources = [source for source, name in inventory.motion_names.items()
               if name.casefold().startswith(f"{character}_") and name.casefold().endswith("_idle1_l")]
    if not sources:
        return {}
    if len(sources) != 1:
        raise ValueError(f"{character}: multiple idle1_l motion sources")
    motion_name = inventory.motion_names[sources[0]]
    baked_file = baked_root / f"motion__{motion_name}.baked.json"
    if not baked_file.is_file():
        return {}
    data = json.loads(baked_file.read_text(encoding="utf-8"))
    clips = data.get("clips", [])
    if len(clips) != 1:
        raise ValueError(f"{baked_file}: expected one idle1_l clip")
    return {
        "defaultMotion": motion_resource_name(motion_name),
        "idlePose": sample_baked_pose(baked_file, clips[0]["name"], 0),
    }


def discover_models(input_root: Path) -> list[Path]:
    result = list(active_sources(input_root).models)
    if not result:
        raise FileNotFoundError(f"no LLAS member model bundles found in {input_root}")
    return result


def select_model_sources(models: list[Path], names: list[str] | None,
                         model_names: dict[Path, str] | None = None) -> list[Path]:
    if not names:
        return models
    selected = []
    for name in dict.fromkeys(names):
        matches = [path for path in models if (model_names[path] if model_names is not None
                                               else inspect_model(path)) == name]
        if len(matches) != 1:
            raise ValueError(f"Expected one LLAS model source for {name}, got {len(matches)}")
        selected.append(matches[0])
    return selected


def discover_motions(input_root: Path) -> list[Path]:
    result = list(active_sources(input_root).motions)
    if not result:
        raise FileNotFoundError(f"no LLAS Humanoid motion bundles found in {input_root}")
    return result


def _model_root(environment: Any, source: Path) -> tuple[Any, str]:
    candidates = [
        (name, pointer)
        for name, pointer in environment.container.items()
        if name.lower().endswith("_member.prefab") and pointer.type.name == "GameObject"
    ]
    if len(candidates) != 1:
        raise RuntimeError(
            f"{source.name}: expected exactly one *_member.prefab root, got {len(candidates)}"
        )
    pointer = candidates[0][1]
    name = str(pointer.read().m_Name)
    if not name:
        raise RuntimeError(f"{source.name}: model root has no name")
    return pointer, name


@lru_cache(maxsize=2048)
def inspect_model(source: Path) -> str:
    UnityPy.config.FALLBACK_UNITY_VERSION = UNITY_VERSION
    environment = UnityPy.load(source.read_bytes())
    _, name = _model_root(environment, source)
    return name


def convert_model(source: Path, output_root: Path, baked_root: Path, description: str,
                  input_root: Path | None = None) -> dict[str, Any]:
    UnityPy.config.FALLBACK_UNITY_VERSION = UNITY_VERSION
    inventory = active_sources(input_root) if input_root is not None else None
    face_source = load_member_with_face(source, cab_paths=inventory.cab_paths if inventory else None)
    environment, root, name = face_source.environment, face_source.root, face_source.name
    skeleton_path = baked_root / "normalized" / f"{name}.skeleton.json"
    if not skeleton_path.is_file():
        raise FileNotFoundError(
            f"{source.name}: missing Humanoid skeleton {skeleton_path}; run python -m converter.bake_llas first"
        )
    skeleton = json.loads(skeleton_path.read_text(encoding="utf-8"))
    board = None
    if not face_source.needs_merging_face:
        board_path = baked_root / 'boards' / f'{name}.json'
        if not board_path.is_file():
            raise FileNotFoundError(f'{name}: missing Unity board samples {board_path}; run python -m converter.bake_llas_faces --model {name}')
        board = json.loads(board_path.read_text(encoding='utf-8'))
    graft = needs_face_graft(face_source.head_all, face_source.needs_merging_face)
    adapter = HeadMaterialAdapter(face_source.head_all, face_source.head_material) if graft else None
    exported = export_normalized_model(
        environment, root, skeleton, adapter=adapter, include_vertex_colors=True,
    )
    board_nodes = {node for domain in board['domains'] for node in domain['defaults']} if board else set()
    append_rigid_renderers(exported, skeleton, game_object_transform(root.read()), adapter,
                           include_hidden=board_nodes)
    if graft:
        append_face(exported, skeleton, game_object_transform(root.read()),
                    face_source.head_all, face_source.face_root, face_source.head_material)
    face_definition = {'morphPoses': [], 'expressionGroups': []}
    if board:
        face_definition = append_board_controls(exported.builder, board)
    if graft:
        pose_path = face_pose_path(face_source, baked_root)
        if not pose_path.is_file():
            raise FileNotFoundError(f'{source.name}: missing Unity facial endpoints {pose_path}; run python -m converter.bake_llas_faces --model {name}')
        poses = json.loads(pose_path.read_text(encoding='utf-8'))
        if 'expressions' not in poses:
            raise ValueError(f'{source.name}: missing Unity facial expression samples in {pose_path}; run python -m converter.bake_llas_faces --model {name}')
        face_definition = build_facial_expressions(exported.builder.document, poses['expressions'],
                                                  poses['closed'], poses['open'])
        face_definition['behaviors'] = [build_face_behavior(exported.builder.document, poses['companions'],
                                                          face_definition['morphPoses'])]
    attach_llas_materials(exported.builder, environment)
    physics = extract_model_physics(environment, exported)
    skirt_behavior = build_skirt_behavior(environment, exported)
    if skirt_behavior:
        face_definition.setdefault("behaviors", []).append(skirt_behavior)
    scale = float(exported.human_scale)
    if not math.isfinite(scale) or scale <= 0:
        raise ValueError(f"{source.name}: invalid normalized Humanoid scale {scale}")

    package_dir = output_root / name
    package_dir.mkdir(parents=True, exist_ok=True)
    exported.builder.write(package_dir / "model.glb")
    component = order_model_component({
        "type": "model",
        "name": name,
        "description": description,
        "group": "llas",
        "role": "integrated",
        "model": "model.glb",
        **face_definition,
        "humanoidScale": scale,
        "motionGroup": "llas-rina-board" if board else "llas",
        **(_idle_defaults_for_character(name.split("_", 1)[0], input_root, baked_root)
           if input_root is not None else {}),
        **({"physics": physics} if physics else {}),
    })
    (package_dir / "config.json").write_text(
        json.dumps({"components": [component]}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return component


def _source_clip_loop_flags(source: Path) -> dict[str, bool]:
    UnityPy.config.FALLBACK_UNITY_VERSION = UNITY_VERSION
    environment = UnityPy.load(str(source))
    result: dict[str, bool] = {}
    for reader in environment.objects:
        if reader.type.name != "AnimationClip":
            continue
        tree = reader.read_typetree()
        name = str(tree.get("m_Name", ""))
        if not name:
            continue
        if name in result:
            raise ValueError(f"{source.name}: duplicate AnimationClip name {name}")
        result[name] = bool((tree.get("m_MuscleClip") or {}).get("m_LoopTime", False))
    return result


def _strip_bake_metadata(data: dict[str, Any]) -> None:
    for field in (
        "schemaVersion", "coordinateSystem",
        "hipsTranslationSpace", "boneNaming", "sourceBundle",
        "referenceAvatar", "referenceHumanScale",
    ):
        data.pop(field, None)
    for collection in CLIP_COLLECTIONS:
        for clip in data.get(collection, []):
            for track in clip.get("tracks", []):
                if not track.get("translation"):
                    track.pop("translation", None)
            for track in clip.get("groupTracks", []):
                track.pop("path", None)
                for field in ("values", "translation", "rotation", "scale"):
                    if not track.get(field):
                        track.pop(field, None)


def package_motion(
    source: Path,
    baked_file: Path,
    motion_root: Path,
    name: str,
) -> dict[str, Any]:
    data = json.loads(baked_file.read_text(encoding="utf-8"))
    if data.get("schemaVersion") != 8:
        raise ValueError(f"unsupported baked motion schema: {baked_file}")
    clips = data.get("clips")
    if not isinstance(clips, list) or not clips:
        raise ValueError(f"{baked_file}: contains no playable clips")
    if any(data.get(field) for field in CLIP_COLLECTIONS[1:]):
        raise ValueError(f"{baked_file}: unexpected auxiliary or hand-pose clips")
    loop_flags = _source_clip_loop_flags(source)
    motion_clip_ids(data)
    states = []
    for clip in clips:
        clip_name = str(clip["name"])
        if clip_name not in loop_flags:
            raise ValueError(f"{source.name}: baked clip {clip_name} is absent from source bundle")
        states.append({
            "id": clip["id"],
            "clip": clip["id"],
            "speed": 1.0,
            "loop": loop_flags[clip_name],
            "transitions": [],
        })
    program = {
        "parameters": [],
        "commands": {"stop": []},
        "baseLayer": "Base Layer",
        "layers": [{
            "id": "Base Layer",
            "blend": "override",
            "weight": 1.0,
            "initialState": states[0]["id"],
            "states": states,
        }],
        "poseSlots": [],
    }
    _strip_bake_metadata(data)
    data["program"] = program

    motion_root.mkdir(parents=True, exist_ok=True)
    metadata = {
        "type": "motion",
        "name": name,
        "description": "",
        "motionGroup": "llas",
    }
    relative_path = f"{motion_resource_name(name).removeprefix('llas/')}.motionbin"
    destination = motion_root / relative_path
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(encode_motion({**metadata, **data}))
    return {**metadata, "src": relative_path}


def package_all_motions(
    input_root: Path,
    output_root: Path,
    baked_root: Path,
) -> list[dict[str, Any]]:
    components: list[dict[str, Any]] = []
    motion_root = output_root.parent / "motion" / "llas"
    inventory = active_sources(input_root)
    for source in inventory.motions:
        name = inventory.motion_names[source]
        baked_file = baked_root / f"motion__{name}.baked.json"
        if not baked_file.is_file():
            raise FileNotFoundError(
                f"{source.name}: missing baked Humanoid motion {baked_file}; run python -m converter.bake_llas first"
            )
        component = package_motion(source, baked_file, motion_root, name)
        components.append(component)
        print(f"[llas] {source.name} -> motion/llas/{component['src']}")
    return components


def convert_all(
    input_root: Path,
    output_root: Path,
    baked_root: Path,
    *,
    model_names: list[str] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    inventory = active_sources(input_root)
    models = select_model_sources(list(inventory.models), model_names, inventory.model_names)
    if not inventory.models and not inventory.motions:
        print("[llas] 输入为空")
        return [], []
    if not inventory.models:
        raise RuntimeError("LLAS motions require a character model as the Humanoid reference rig")
    output_root.mkdir(parents=True, exist_ok=True)
    descriptions = model_descriptions(input_root)

    model_components: list[dict[str, Any]] = []
    for source in models:
        name = inspect_model(source)
        component = convert_model(source, output_root, baked_root,
                                  description_for_source(source, descriptions),
                                  input_root)
        model_components.append(component)
        print(f"[llas] {source.name} -> {name}/model.glb")

    motion_components = package_all_motions(input_root, output_root, baked_root)

    if not model_components:
        raise RuntimeError("no LLAS models were converted")
    configs = sorted(
        f"{directory.name}/config.json"
        for directory in output_root.iterdir()
        if directory.is_dir() and (directory / "config.json").is_file()
    )
    (output_root / "index.json").write_text(
        json.dumps({"configs": configs}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return model_components, motion_components
