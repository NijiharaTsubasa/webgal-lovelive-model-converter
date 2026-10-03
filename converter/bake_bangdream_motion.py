"""Bake or verify supported BanG Dream motion families."""

from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import tempfile
from pathlib import Path
from converter.common.unity_editor import resolve_unity_editor
from converter.common.cli import configure_output
from typing import Any

import UnityPy

from converter.bangdream import UNITY_VERSION
from converter.bangdream.motion import (
    CLIP_COLLECTIONS,
    MOTION_FAMILIES,
    actor_slot,
    discover_motion_bundles,
    is_placeholder_clip_name,
    package_motion,
)
from converter.common.motion_binary import decode_motion


def _validate_motion_payload(data: dict[str, Any], expected_name: str) -> set[str]:
    if any(field in data for field in ("type", "name", "description", "motionGroup", "schemaVersion")):
        raise ValueError(f"Invalid packaged metadata: {expected_name}")

    clip_ids: set[str] = set()
    clip_names: set[str] = set()
    for collection in CLIP_COLLECTIONS:
        if not isinstance(data.get(collection), list):
            raise ValueError(f"Missing clip collection {collection}: {expected_name}")
        for clip in data[collection]:
            clip_id = str(clip.get("id", ""))
            clip_name = str(clip.get("name", ""))
            if not clip_id or clip_id in clip_ids or not clip_name:
                raise ValueError(f"Invalid or duplicate clip id: {expected_name} :: {clip_id!r}")
            if is_placeholder_clip_name(clip_name):
                raise ValueError(f"Placeholder clip was packaged: {expected_name} :: {clip_name}")
            clip_ids.add(clip_id)
            clip_names.add(clip_name)
            frames = int(clip.get("frames", 0))
            duration = float(clip.get("duration", -1))
            sample_rate = float(clip.get("sampleRate", 0))
            expected_frames = {
                max(2, round(duration * sample_rate) + 1),
                max(2, math.ceil(duration * sample_rate) + 1),
            }
            if frames not in expected_frames:
                raise ValueError(f"Invalid frame count: {expected_name} :: {clip_name}")
            for track in clip.get("tracks", []):
                if len(track.get("rotation", [])) != frames * 4:
                    raise ValueError(f"Invalid rotation track: {expected_name} :: {clip_name}")
                translation = track.get("translation")
                if translation is not None and (
                    track.get("bone") != "Hips" or len(translation) != frames * 3
                ):
                    raise ValueError(f"Invalid translation track: {expected_name} :: {clip_name}")

    program = data.get("program", {})
    parameter_ids = {item.get("id") for item in program.get("parameters", [])}
    layers = program.get("layers", [])
    layer_ids = {layer.get("id") for layer in layers}
    if not layers or program.get("baseLayer") not in layer_ids:
        raise ValueError(f"Invalid base layer: {expected_name}")
    for actions in program.get("commands", {}).values():
        for action in actions:
            if action.get("parameter") not in parameter_ids:
                raise ValueError(f"Unknown command parameter: {expected_name}")
    for layer in layers:
        states = layer.get("states", [])
        state_ids = {state.get("id") for state in states}
        if not states or layer.get("initialState") not in state_ids:
            raise ValueError(f"Invalid initial state: {expected_name} :: {layer.get('id')}")
        for state in states:
            if state.get("clip") not in clip_ids:
                raise ValueError(f"Unknown state clip: {expected_name} :: {state.get('clip')}")
            for transition in state.get("transitions", []):
                if transition.get("to") not in state_ids:
                    raise ValueError(f"Unknown transition target: {expected_name}")
                for condition in transition.get("conditions", []):
                    if condition.get("parameter") not in parameter_ids:
                        raise ValueError(f"Unknown transition parameter: {expected_name}")
    return clip_names


def _verify_export(
    selected: list[tuple[str, Path]],
    clip_names_by_source: dict[str, list[str]],
    package_output: Path,
) -> tuple[int, int]:
    config_path = package_output / "config.json"
    if not config_path.is_file():
        raise ValueError(f"Motion config missing: {config_path}")
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if set(config) != {"components"} or not isinstance(config["components"], list):
        raise ValueError(f"Invalid motion config: {config_path}")
    entries = [
        item for item in config["components"]
        if item.get("type") == "motion" and item.get("motionGroup") == "garupa"
    ]
    entry_names = [str(item.get("name", "")) for item in entries]
    entry_files = [str(item.get("src", "")) for item in entries]
    if len(entry_names) != len(set(entry_names)) or len(entry_files) != len(set(entry_files)):
        raise ValueError("Duplicate BanG Dream motion index entries")

    packaged_names: dict[str, set[str]] = {}
    for entry in entries:
        name = str(entry["name"])
        motion_path = package_output / str(entry["src"])
        data = decode_motion(motion_path.read_bytes())
        names = _validate_motion_payload(data, name)
        packaged_names[name] = names

    verified_clips = 0
    verified_packages = 0
    for relative_name, _ in selected:
        expected = {
            name for name in clip_names_by_source[relative_name]
            if not is_placeholder_clip_name(name)
        }
        if not expected:
            continue
        matches = {
            name: clips for name, clips in packaged_names.items()
            if name == relative_name or name.startswith(relative_name + "-")
        }
        if not matches:
            raise ValueError(f"No package for source: {relative_name}")
        actual = set().union(*matches.values())
        if actual != expected:
            raise ValueError(
                f"Clip coverage mismatch: {relative_name}; "
                f"missing={sorted(expected - actual)}, extra={sorted(actual - expected)}"
            )
        if len(matches) == 2:
            slots = []
            for clips in matches.values():
                scoped = {actor_slot(name) for name in clips} - {None}
                if len(scoped) != 1:
                    raise ValueError(f"Mixed or missing actor slot: {relative_name}")
                slots.extend(scoped)
            if set(slots) != {"A", "B"}:
                raise ValueError(f"Incomplete actor split: {relative_name}")
        elif len(matches) != 1:
            raise ValueError(f"Unexpected package count for source: {relative_name}")
        verified_clips += len(expected)
        verified_packages += len(matches)
    return verified_packages, verified_clips


def _source_clip_names(path: Path) -> list[str]:
    UnityPy.config.FALLBACK_UNITY_VERSION = UNITY_VERSION
    environment = UnityPy.load(str(path))
    names = []
    for obj in environment.objects:
        if obj.type.name != "AnimationClip":
            continue
        name = str(obj.read_typetree().get("m_Name", ""))
        if name:
            names.append(name)
    return sorted(set(names))


def _select_bundles(
    input_root: Path,
    requested: list[str] | None,
) -> list[tuple[str, Path]]:
    discovered = discover_motion_bundles(input_root)
    if not requested:
        return discovered
    by_name = {name: path for name, path in discovered}
    normalized = [name.replace("\\", "/").strip("/") for name in requested]
    missing = [name for name in normalized if name not in by_name]
    if missing:
        raise SystemExit("Unknown BanG Dream motion:\n" + "\n".join(missing))
    return [(name, by_name[name]) for name in normalized]


def _has_avatar_asset(path: Path) -> bool:
    UnityPy.config.FALLBACK_UNITY_VERSION = UNITY_VERSION
    environment = UnityPy.load(str(path))
    return any(
        obj.type.name == "Avatar"
        and "face" not in str(obj.read().m_Name).casefold()
        for obj in environment.objects
    )


def select_reference_pair(input_root: Path, requested: str | None = None) -> tuple[Path, Path]:
    """Choose a matched head/body rig with a bundled Avatar for Unity to validate."""
    heads = input_root / "head"
    bodies = input_root / "costume"
    if not heads.is_dir() or not bodies.is_dir():
        raise FileNotFoundError(f"BanG Dream head and costume directories are required below {input_root}")
    names = sorted(
        {path.name for path in heads.iterdir() if path.is_file()}
        & {path.name for path in bodies.iterdir() if path.is_file()},
        key=lambda name: (not name.endswith("_cos_live_default"), name),
    )
    if requested is not None:
        if requested not in names:
            raise ValueError(f"No matched BanG Dream head/body bundles for {requested}")
        names = [requested]
    for name in names:
        body = bodies / name
        if _has_avatar_asset(body):
            return heads / name, body
    raise ValueError(f"No matched BanG Dream head/body bundles with an Avatar in {input_root}")


def _write_index(
    output_root: Path,
    new_entries: list[dict[str, Any]],
    replace_all_bangdream: bool,
) -> None:
    config_path = output_root / "config.json"
    old_config = (
        json.loads(config_path.read_text(encoding="utf-8"))
        if config_path.is_file()
        else {"components": []}
    )
    old_entries = old_config.get("components", [])
    if any(entry.get("type") != "motion" or entry.get("motionGroup") != "garupa"
           for entry in old_entries):
        raise ValueError(f"Unexpected component in Garupa motion manifest: {config_path}")
    new_files = {entry["src"] for entry in new_entries}
    preserved = [
        entry
        for entry in old_entries
        if not replace_all_bangdream and entry.get("src") not in new_files
    ]
    components = sorted(
        [*preserved, *new_entries],
        key=lambda entry: (
            str(entry.get("type", "")),
            str(entry.get("motionGroup", "")),
            str(entry.get("name", "")).casefold(),
            str(entry.get("src", "")),
        ),
    )
    output_root.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        json.dumps({"components": components}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (output_root / "index.json").write_text('{\n  "configs": ["config.json"]\n}\n', encoding="utf-8")


def package_existing_motions(
    input_root: Path,
    baked_output: Path,
    package_output: Path,
) -> tuple[int, int]:
    """Package already baked motions without launching Unity."""
    selected = _select_bundles(input_root, None)
    if not selected:
        raise ValueError(f"No supported BanG Dream motion bundles found in {input_root}")
    clip_names_by_source = {
        relative_name: _source_clip_names(source)
        for relative_name, source in selected
    }
    entries: list[dict[str, Any]] = []
    package_skips: list[dict[str, str]] = []
    dual_sources = 0
    for index, (relative_name, source) in enumerate(selected, 1):
        baked_file = baked_output / f"motion_{index:06d}.baked.json"
        playable_source_names = [
            name for name in clip_names_by_source[relative_name]
            if not is_placeholder_clip_name(name)
        ]
        if not baked_file.is_file():
            if not playable_source_names:
                package_skips.append({
                    "source": relative_name,
                    "clip": "*",
                    "reason": "no-playable-clips",
                })
                continue
            raise FileNotFoundError(f"Expected baked motion missing: {baked_file} ({relative_name})")
        package_entries, skipped_baked = package_motion(
            baked_file, source, relative_name, package_output,
        )
        if len(package_entries) == 2:
            dual_sources += 1
        entries.extend(package_entries)
        package_skips.extend(
            {"source": relative_name, "clip": name, "reason": "placeholder-or-calibration"}
            for name in skipped_baked
        )
        if index % 25 == 0 or index == len(selected):
            print(f"[package] {index}/{len(selected)} sources, {len(entries)} packages")

    names = [entry["name"] for entry in entries]
    files = [entry["src"] for entry in entries]
    if len(names) != len(set(names)):
        raise ValueError("Duplicate motion package names were generated")
    if len(files) != len(set(files)):
        raise ValueError("Duplicate motion package paths were generated")

    _write_index(package_output, entries, replace_all_bangdream=False)
    package_count, verified_clips = _verify_export(
        selected, clip_names_by_source, package_output,
    )
    print(
        f"[done] {len(selected)} sources -> {len(entries)} packages; "
        f"dual={dual_sources}, skipped={len(package_skips)}, "
        f"verified={package_count}/{verified_clips}"
    )
    return package_count, verified_clips


def main() -> None:
    configure_output()
    parser = argparse.ArgumentParser(
        description=(
            "Bake BanG Dream charactertype, characterunique, and cutin3d motions. "
            "Use --motion to run a selected subset."
        ),
    )
    parser.add_argument(
        "--unity",
        type=Path,
    )
    parser.add_argument("--input", type=Path, default=Path("input_bangdream"))
    parser.add_argument(
        "--motion",
        action="append",
        help=(
            "Motion path relative to input_bangdream/motions; repeat for multiple. "
            f"Default exports all {', '.join(MOTION_FAMILIES)} bundles."
        ),
    )
    parser.add_argument("--reference-model", help="Optional head/body basename; otherwise select a matching pair with a bundled Avatar.")
    parser.add_argument("--sample-rate", type=int, default=60)
    parser.add_argument("--baked-output", type=Path, default=Path("baked_motions/bangdream"))
    parser.add_argument("--package-output", type=Path, default=Path("output_packages/bangdream/motions"))
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Verify existing packaged output against the selected source bundles.",
    )
    args = parser.parse_args()

    input_root = args.input.resolve()
    selected = _select_bundles(input_root, args.motion)
    if not selected:
        print(f"[bangdream:bake:motions] 输入为空: {input_root}", flush=True)
        return
    if args.sample_rate <= 0:
        raise SystemExit("--sample-rate must be greater than zero")

    clip_names_by_source: dict[str, list[str]] = {}
    skipped_source_clips: list[dict[str, str]] = []
    for relative_name, source in selected:
        names = _source_clip_names(source)
        clip_names_by_source[relative_name] = names
        skipped_source_clips.extend(
            {"source": relative_name, "clip": name, "reason": "placeholder-or-calibration"}
            for name in names
            if is_placeholder_clip_name(name)
        )
    print(
        f"[discover] {len(selected)} bundles, "
        f"{sum(len(names) for names in clip_names_by_source.values())} clips, "
        f"{len(skipped_source_clips)} placeholders"
    )
    if args.verify_only:
        package_count, clip_count = _verify_export(
            selected,
            clip_names_by_source,
            args.package_output.resolve(),
        )
        print(f"[verify] {len(selected)} sources, {package_count} packages, {clip_count} clips")
        return

    unity = resolve_unity_editor(args.unity)
    baked_output = args.baked_output.resolve()
    baked_output.mkdir(parents=True, exist_ok=True)
    log = baked_output / "all-motions.unity.log"
    staged = [
        (relative_name, source, f"motion_{index:06d}")
        for index, (relative_name, source) in enumerate(selected, 1)
    ]
    reference_head, reference_body = select_reference_pair(input_root, args.reference_model)
    references = {
        "head_reference.assetbundle": reference_head,
        "body_reference.assetbundle": reference_body,
    }
    print(f"[bangdream:bake] reference model: {reference_body.name}", flush=True)

    stage = Path(tempfile.mkdtemp(prefix="bangdream_motion_batch_", dir=baked_output))
    try:
        for staged_name, source in references.items():
            shutil.copyfile(source, stage / staged_name)
        for _, source, stage_key in staged:
            shutil.copyfile(source, stage / f"{stage_key}.assetbundle")

        command = [
            str(unity),
            "-batchmode",
            "-quit",
            "-nographics",
            "-buildTarget",
            "Android",
            "-projectPath",
            str(Path(__file__).resolve().parent / "unity_baker"),
            "-executeMethod",
            "BakePipeline.Run",
            "-game",
            "bangdream",
            "-input",
            str(stage),
            "-output",
            str(baked_output),
            "-sampleRate",
            str(args.sample_rate),
            "-logFile",
            str(log),
        ]
        result = subprocess.run(command, check=False)
    finally:
        shutil.rmtree(stage, ignore_errors=True)
    if result.returncode:
        raise SystemExit(f"Unity motion bake failed ({result.returncode}). See {log}")
    log.unlink(missing_ok=True)
    print(f"[done] baked {len(selected)} motion sources; skipped {len(skipped_source_clips)} placeholders")


if __name__ == "__main__":
    main()
