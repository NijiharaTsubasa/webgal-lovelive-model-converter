from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from converter.common.motion import controller_program
from converter.common.motion_binary import encode_motion


MOTION_DESCRIPTIONS_CSV = Path(__file__).resolve().parents[2] / "docs" / "hasunosora" / "motion-descriptions.csv"


def load_motion_descriptions(csv_path: Path) -> dict[str, str]:
    if not csv_path.is_file():
        return {}
    with csv_path.open(encoding="utf-8-sig", newline="") as stream:
        return {
            row[0]: row[3] if len(row) > 3 else ""
            for row in csv.reader(stream)
            if row and row[0] != "motion"
        }


def collect_baked_motions(baked_dir: Path | None, input_dir: Path, output: Path) -> list[dict[str, Any]]:
    """Copy Unity-baked motion files to the output directory and build index entries.

    Returns index entries for motion bundles present in the current input. Each
    selected input must have a baked file; caches without a current input are skipped.

    For each baked file the matching motion controller bundle is resolved from
    `input_dir` using the `sourceBundle` + an optional `mot*` sibling CAB
    convention (used by Hasu). The controller is then compiled into a flat
    state graph that the renderer can execute."""
    motions = sorted(
        path for path in input_dir.glob("*.assetbundle")
        if path.stem.startswith(("mot_", "motion_")) and path.is_file()
    )
    if not motions:
        return []
    descriptions = load_motion_descriptions(MOTION_DESCRIPTIONS_CSV)
    output.mkdir(parents=True, exist_ok=True)
    entries: list[dict[str, Any]] = []
    for bundle_path in motions:
        if baked_dir is None:
            raise FileNotFoundError(f"Missing baked motion directory for {bundle_path.name}")
        baked_names = [bundle_path.stem]
        if bundle_path.stem.startswith("mot_"):
            baked_names.append(f"m_{bundle_path.stem[4:]}")
        baked_file = next(
            (baked_dir / f"{name}.baked.json" for name in baked_names
             if (baked_dir / f"{name}.baked.json").is_file()),
            baked_dir / f"{baked_names[0]}.baked.json",
        )
        if not baked_file.is_file():
            raise FileNotFoundError(f"Missing baked motion: {baked_file} ({bundle_path.name})")
        try:
            data = json.loads(baked_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            raise ValueError(f"Invalid baked motion file: {baked_file}") from exc
        if not isinstance(data, dict) or data.get("schemaVersion") != 8:
            raise ValueError(f"Unsupported baked motion schema: {baked_file}")
        source_bundle = str(data.get("sourceBundle", ""))
        bundle_names = [f"{source_bundle}.assetbundle"]
        if source_bundle.startswith("m_"):
            bundle_names.append(f"mot{source_bundle[1:]}.assetbundle")
        if bundle_path.name not in bundle_names:
            raise ValueError(f"Baked motion source does not match {bundle_path.name}: {source_bundle!r}")
        program = controller_program(bundle_path, data)
        if program is None:
            raise ValueError(f"Could not build a motion program from {bundle_path.name}")
        data["program"] = program
        for field in (
            "schemaVersion", "coordinateSystem", "hipsTranslationSpace", "boneNaming",
            "sourceBundle", "referenceAvatar", "referenceHumanScale",
        ):
            data.pop(field, None)
        for collection in ("clips", "auxiliaryClips", "leftHandPoses", "rightHandPoses"):
            for clip in data.get(collection, []):
                for track in clip.get("tracks", []):
                    if not track.get("translation"):
                        track.pop("translation", None)
                for track in clip.get("groupTracks", []):
                    track.pop("path", None)
        motion_name = source_bundle or baked_file.name.removesuffix(".baked.json")
        dest_name = f"{motion_name}.motionbin"
        metadata = {
            "type": "motion",
            "name": motion_name,
            "description": descriptions.get(motion_name, ""),
            "motionGroup": "hasunosora",
        }
        (output / dest_name).write_bytes(encode_motion({**metadata, **data}))
        entries.append({**metadata, "src": dest_name})
    return entries
