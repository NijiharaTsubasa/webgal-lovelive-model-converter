"""BanG Dream motion discovery and standardized-package helpers."""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from typing import Any

import UnityPy

from converter.common.motion import controller_program, motion_clip_ids
from converter.common.motion_binary import encode_motion
from converter.common.normalized_model import renderer_node_name

from . import UNITY_VERSION


CLIP_COLLECTIONS = ("clips", "auxiliaryClips", "leftHandPoses", "rightHandPoses")
MOTION_FAMILIES = ("charactertype", "characterunique", "cutin3d")
_PLACEHOLDER_NAMES = {
    "tpose",
    "bindpose",
    "calibration",
    "calibrationpose",
    "referencepose",
    "placeholder",
}
_ACTOR_SLOT = re.compile(r"(?:^|[-_])([ab])(?=_(?:in|lp|out)$)", re.IGNORECASE)
_PHASE = re.compile(r"(?:^|[-_])(in|lp|out)$", re.IGNORECASE)


def _bind_group_track_nodes(data: dict[str, Any]) -> None:
    """Point baked morph tracks at normalized GLB renderer nodes in place."""
    for collection in CLIP_COLLECTIONS:
        for clip in data.get(collection, []):
            for track in clip.get("groupTracks", []):
                if track.get("kind") != "morph":
                    continue
                node = track.get("node")
                if not isinstance(node, str) or not node:
                    raise ValueError("Morph group track must declare a non-empty node")
                if not node.endswith(" Renderer"):
                    track["node"] = renderer_node_name(node)


def discover_motion_bundles(input_root: Path) -> list[tuple[str, Path]]:
    """Return every supported source bundle using its stable relative name."""
    try:
        input_root.stat()
    except FileNotFoundError:
        return []
    if not input_root.is_dir():
        raise NotADirectoryError(input_root)
    motion_root = input_root / "motions"
    result: list[tuple[str, Path]] = []
    for family in MOTION_FAMILIES:
        family_root = motion_root / family
        if family_root.exists() and not family_root.is_dir():
            raise NotADirectoryError(family_root)
        if not family_root.is_dir():
            continue
        for path in sorted(item for item in family_root.rglob("*") if item.is_file()):
            if any(part.startswith(".") for part in path.relative_to(family_root).parts):
                continue
            result.append((path.relative_to(motion_root).as_posix(), path))
    return result


def is_placeholder_clip_name(name: str) -> bool:
    compact = "".join(character.lower() for character in name if character.isalnum())
    return compact in _PLACEHOLDER_NAMES


def actor_slot(name: str) -> str | None:
    match = _ACTOR_SLOT.search(name)
    return match.group(1).upper() if match else None


def _clip_phase(name: str) -> str | None:
    match = _PHASE.search(name)
    return match.group(1).lower() if match else None


def _semantic_actor_name(relative_name: str, slot: str) -> str:
    parts = relative_name.replace("\\", "/").split("/")
    if len(parts) >= 5 and parts[0] == "cutin3d" and parts[1] == "centercoupling":
        first, second = parts[-3], parts[-2]
        if first.casefold() != second.casefold():
            return f"{relative_name}-{first if slot == 'A' else second}"
    return f"{relative_name}-{slot}"


def split_actor_motions(
    data: dict[str, Any],
    relative_name: str,
) -> list[tuple[str, dict[str, Any]]]:
    """Split explicit A/B actor clips while retaining unscoped shared clips."""
    slots = {
        slot
        for field in CLIP_COLLECTIONS
        for clip in data.get(field, [])
        if (slot := actor_slot(str(clip.get("name", ""))))
    }
    if slots != {"A", "B"}:
        return [(relative_name, data)]

    results: list[tuple[str, dict[str, Any]]] = []
    for slot in ("A", "B"):
        actor_data = copy.deepcopy(data)
        for field in CLIP_COLLECTIONS:
            actor_data[field] = [
                clip
                for clip in actor_data.get(field, [])
                if actor_slot(str(clip.get("name", ""))) in {None, slot}
            ]
        results.append((_semantic_actor_name(relative_name, slot), actor_data))
    return results


def _filter_placeholders(data: dict[str, Any]) -> list[str]:
    skipped: list[str] = []
    for field in CLIP_COLLECTIONS:
        retained = []
        for clip in data.get(field, []):
            name = str(clip.get("name", ""))
            if is_placeholder_clip_name(name):
                skipped.append(name)
            else:
                retained.append(clip)
        data[field] = retained
    return skipped


def _validate_group_tracks(clip: dict[str, Any]) -> None:
    frames = int(clip.get("frames", 0))
    for track in clip.get("groupTracks", []):
        kind = track.get("kind")
        expected = {
            "morph": ("values", frames),
            "visibility": ("values", frames),
            "transform": ("rotation", frames * 4),
        }.get(kind)
        if expected is None:
            raise ValueError(f"Unsupported group track: {kind!r}")
        field, length = expected
        if len(track.get(field, [])) != length:
            raise ValueError(
                f"{clip.get('name')}: {kind} {field} has "
                f"{len(track.get(field, []))} values, expected {length}"
            )


def _simple_program(data: dict[str, Any]) -> dict[str, Any]:
    """Build a deterministic program for bundles without an AnimatorController."""
    clips = list(data.get("clips", []))
    if not clips:
        raise ValueError("Motion contains no playable clips")
    phase_order = {"in": 0, "lp": 1, "out": 2}
    clips.sort(key=lambda clip: (
        phase_order.get(_clip_phase(str(clip.get("name", ""))), 1),
        str(clip.get("name", "")),
    ))
    data["clips"] = clips
    motion_clip_ids(data)

    out_index = next(
        (index for index, clip in enumerate(clips) if _clip_phase(str(clip.get("name", ""))) == "out"),
        None,
    )
    loop_index = next(
        (index for index, clip in enumerate(clips) if _clip_phase(str(clip.get("name", ""))) == "lp"),
        None,
    )
    has_stop = loop_index is not None and out_index is not None
    states: list[dict[str, Any]] = []
    for index, clip in enumerate(clips):
        phase = _clip_phase(str(clip.get("name", "")))
        transitions: list[dict[str, Any]] = []
        if phase == "lp" and has_stop:
            transitions.append({
                "to": clips[out_index]["id"],
                "exitTime": None,
                "duration": 0.0,
                "offset": 0.0,
                "conditions": [{"parameter": "exitRequested", "operator": "isTrue"}],
            })
        elif index + 1 < len(clips) and phase != "lp":
            transitions.append({
                "to": clips[index + 1]["id"],
                "exitTime": 1.0,
                "duration": 0.0,
                "offset": 0.0,
                "conditions": [],
            })
        states.append({
            "id": clip["id"],
            "clip": clip["id"],
            "speed": 1.0,
            "loop": phase == "lp",
            "transitions": transitions,
        })

    return {
        "parameters": ([{"id": "exitRequested", "type": "bool", "default": False}]
                       if has_stop else []),
        "commands": {
            "stop": ([{"parameter": "exitRequested", "value": True}]
                     if has_stop else []),
        },
        "baseLayer": "Base Layer",
        "layers": [{
            "id": "Base Layer",
            "blend": "override",
            "weight": 1.0,
            "initialState": clips[0]["id"],
            "states": states,
        }],
        "poseSlots": [],
    }


def _strip_bake_metadata(data: dict[str, Any]) -> str:
    reference_avatar = str(data.get("referenceAvatar", ""))
    for field in (
        "schemaVersion",
        "coordinateSystem",
        "hipsTranslationSpace",
        "boneNaming",
        "sourceBundle",
        "referenceAvatar",
        "referenceHumanScale",
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
    return reference_avatar


def package_motion(
    baked_file: Path,
    source_bundle: Path,
    relative_name: str,
    output_root: Path,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Turn one Unity-baked source bundle into one or two playable packages."""
    data = json.loads(baked_file.read_text(encoding="utf-8"))
    if data.get("schemaVersion") != 8:
        raise ValueError(f"Unsupported baked motion schema: {baked_file}")
    skipped = _filter_placeholders(data)
    for collection in CLIP_COLLECTIONS:
        for clip in data.get(collection, []):
            _validate_group_tracks(clip)
    _bind_group_track_nodes(data)
    if not data.get("clips"):
        return [], skipped

    UnityPy.config.FALLBACK_UNITY_VERSION = UNITY_VERSION
    entries: list[dict[str, Any]] = []
    for package_name, package_data in split_actor_motions(data, relative_name):
        program = controller_program(source_bundle, package_data)
        if program is None:
            program = _simple_program(package_data)
        _strip_bake_metadata(package_data)
        motion = {**package_data, "program": program}
        folder_name = package_name.replace("/", "_").replace("\\", "_")
        destination_dir = output_root / folder_name
        destination_dir.mkdir(parents=True, exist_ok=True)
        destination = destination_dir / "motion.motionbin"
        destination.write_bytes(encode_motion(motion))
        entries.append({
            "type": "motion",
            "name": package_name,
            "description": "BanG Dream motion",
            "motionGroup": "garupa",
            "src": f"{folder_name}/motion.motionbin",
        })
    return entries, skipped
