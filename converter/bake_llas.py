"""Batch LLAS Generic bundles through Unity's Humanoid AvatarBuilder.

The source bundles remain Generic inputs.  Every exported skeleton and motion
is produced only after the LLAS adapter has built and validated a Humanoid
Avatar; there is no Generic output or renderer path.
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Iterable
from converter.llas import select_model_sources
from converter.llas.face_batch import bake_faces_and_boards
from converter.llas.node_scaling import scaling_for_source
from converter.llas.source_inventory import active_sources
from converter.common.unity_editor import resolve_unity_editor
from converter.common.cli import configure_output


def verify_body_motion(baked_file: Path) -> None:
    """Validate sampled Humanoid tracks, including static poses and root motion."""
    data = json.loads(baked_file.read_text(encoding="utf-8"))
    clips = data.get("clips")
    if not isinstance(clips, list) or not clips:
        raise RuntimeError(f"{baked_file}: contains no playable clips")

    def valid_samples(values: object, count: int) -> bool:
        return isinstance(values, list) and len(values) == count and all(
            not isinstance(value, bool) and isinstance(value, (int, float))
            and math.isfinite(value) for value in values
        )

    for clip in clips:
        label = f"{baked_file}: clip {clip.get('name')}"
        frames = clip.get("frames")
        if isinstance(frames, bool) or not isinstance(frames, int) or frames < 2:
            raise RuntimeError(f"{label} has invalid frame count")
        tracks = clip.get("tracks")
        if not isinstance(tracks, list) or not tracks:
            raise RuntimeError(f"{label} has no Humanoid tracks")
        for track in tracks:
            values = track.get("rotation")
            if not valid_samples(values, frames * 4):
                raise RuntimeError(f"{label} has invalid rotation samples")
            if any(not any(values[offset:offset + 4]) for offset in range(0, len(values), 4)):
                raise RuntimeError(f"{label} has a zero rotation quaternion")
            translation = track.get("translation")
            if translation is not None and translation != [] and (
                track.get("bone") != "Hips" or not valid_samples(translation, frames * 3)
            ):
                raise RuntimeError(f"{label} has invalid Hips translation samples")


def batches(items: list[Path], size: int) -> Iterable[list[Path]]:
    if size <= 0:
        raise ValueError("batch size must be positive")
    for offset in range(0, len(items), size):
        yield items[offset:offset + size]


def _run_unity(
    unity: Path,
    project: Path,
    output: Path,
    staged: list[tuple[str, Path]],
    log: Path,
    sample_rate: int,
    *,
    models_only: bool,
) -> None:
    temp_root = Path(".tmp").resolve()
    temp_root.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix="llas_bake_", dir=temp_root))
    try:
        for staged_name, source in staged:
            shutil.copyfile(source, stage / f"{staged_name}.assetbundle")
        scaling_path = stage / "node-scaling.json"
        scaling_path.write_text(json.dumps({"members": [
            scaling_for_source(source)
            for name, source in staged if name.startswith("model__")
        ]}), encoding="utf-8")
        command = [
            str(unity), "-batchmode", "-quit", "-nographics",
            "-buildTarget", "Android",
            "-projectPath", str(project),
            "-executeMethod", "BakePipeline.Run",
            "-game", "llas",
            "-llasNodeScaling", str(scaling_path),
            "-input", str(stage),
            "-output", str(output),
            "-sampleRate", str(sample_rate),
            "-logFile", str(log),
        ]
        if models_only:
            command.extend(["-modelsOnly", "true"])
        result = subprocess.run(command, check=False)
        if result.returncode:
            raise RuntimeError(f"Unity baking failed ({result.returncode}); see {log}")
    finally:
        shutil.rmtree(stage, ignore_errors=True)


def main() -> None:
    configure_output()
    parser = argparse.ArgumentParser(
        description="Build LLAS Humanoid skeletons and bake skeletal motions."
    )
    parser.add_argument("--unity", type=Path)
    parser.add_argument("--input", type=Path, default=Path("input_llas"))
    parser.add_argument("--output", type=Path, default=Path("baked_motions/llas"))
    parser.add_argument("--sample-rate", type=int, default=30)
    parser.add_argument("--model-batch-size", type=int, default=64)
    parser.add_argument("--motion-batch-size", type=int, default=64)
    parser.add_argument("--model", action="append", help="Exact member prefab name; may be repeated.")
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument("--models-only", action="store_true")
    selection.add_argument("--motions-only", action="store_true")
    args = parser.parse_args()

    project = Path(__file__).resolve().parent / "unity_baker"
    input_root = args.input.resolve()
    output = args.output.resolve()
    if args.sample_rate <= 0:
        raise SystemExit("sample rate must be positive")
    inventory = active_sources(input_root)
    models = select_model_sources(list(inventory.models), args.model, inventory.model_names)
    motions = list(inventory.motions)
    if ((args.models_only and not models) or (args.motions_only and not motions)
            or (not models and not motions)):
        print("[llas:bake] 输入为空")
        return
    if not models:
        raise SystemExit("at least one LLAS model is required as the Humanoid reference rig")
    unity = resolve_unity_editor(args.unity)
    output.mkdir(parents=True, exist_ok=True)

    generated_logs: list[Path] = []
    if not args.motions_only:
        for index, batch in enumerate(batches(models, args.model_batch_size), 1):
            log = output / f"unity-models-{index:03d}.log"
            generated_logs.append(log)
            staged = [(f"model__{inventory.model_names[item]}", item) for item in batch]
            print(f"[llas:bake] model batch {index}: {len(batch)} bundles")
            _run_unity(unity, project, output, staged, log, args.sample_rate, models_only=True)
        bake_faces_and_boards(models, output, unity, project, inventory.cab_paths)

    if not args.models_only:
        reference = models[0]
        for index, batch in enumerate(batches(motions, args.motion_batch_size), 1):
            log = output / f"unity-motions-{index:03d}.log"
            generated_logs.append(log)
            staged = [(f"model__{inventory.model_names[reference]}", reference)]
            staged.extend((f"motion__{inventory.motion_names[item]}", item) for item in batch)
            print(f"[llas:bake] motion batch {index}: {len(batch)} bundles")
            _run_unity(unity, project, output, staged, log, args.sample_rate, models_only=False)
            for source in batch:
                verify_body_motion(output / f"motion__{inventory.motion_names[source]}.baked.json")

    normalized_count = len(list((output / "normalized").glob("*.skeleton.json")))
    baked_count = len(list(output.glob("motion__*.baked.json")))
    if not args.motions_only and normalized_count < len(models):
        raise RuntimeError(
            f"only {normalized_count}/{len(models)} selected model skeletons were produced"
        )
    if not args.models_only and baked_count < len(motions):
        raise RuntimeError(f"only {baked_count}/{len(motions)} selected motions were produced")
    for log in generated_logs:
        log.unlink(missing_ok=True)
    print(f"[llas:bake] complete: {normalized_count} skeletons, {baked_count} motions")


if __name__ == "__main__":
    main()
