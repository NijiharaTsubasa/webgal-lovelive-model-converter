"""Bake BanG Dream model bundles through Unity's Humanoid Avatar."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from converter.common.unity_editor import default_unity_editor
from converter.bangdream import discover_bundle_inputs
from converter.common.cli import configure_output


def select_template(bundles, batch_size, probe):
    """Use Unity's native Avatar verdict, not bundle order, to select a template."""
    for offset in range(0, len(bundles), batch_size):
        candidates = bundles[offset:offset + batch_size]
        selected = probe(candidates, f"template-discovery-{offset // batch_size + 1:04d}")
        if not selected:
            continue
        matches = [entry for entry in candidates if entry[0] == selected]
        if len(matches) != 1:
            raise RuntimeError(f"Unity selected an unknown Avatar template: {selected}")
        return matches[0]
    raise SystemExit("No bundled valid Humanoid Avatar is available as a BanG Dream template")


def main() -> None:
    configure_output()
    parser = argparse.ArgumentParser(
        description="Bake BanG Dream model bundles; --models-only skips their embedded clips."
    )
    parser.add_argument("--unity", type=Path, default=default_unity_editor(),
                        help="Unity Editor executable; defaults to UNITY_EDITOR or PATH.")
    parser.add_argument("--input", type=Path, default=Path("input_bangdream"))
    parser.add_argument("--output", type=Path, default=Path("baked_motions"))
    parser.add_argument("--sample-rate", type=int, default=30)
    parser.add_argument("--models-only", action="store_true",
                        help="Normalize model skeletons without baking motion clips.")
    parser.add_argument("--model-batch-size", type=int, default=32,
                        help="Maximum bundles loaded per Unity batch, including the shared Avatar template (minimum 2).")
    args = parser.parse_args()
    unity = args.unity.resolve()
    if args.model_batch_size < 2:
        parser.error("--model-batch-size must be at least 2 (one template plus one model)")
    if args.sample_rate <= 0:
        parser.error("--sample-rate must be positive")
    output = args.output.resolve()
    project = Path(__file__).resolve().parent / "unity_baker"

    # Bang Dream ships AssetBundles without the `.assetbundle` extension,
    # so the Unity-side BakePipeline's `Directory.GetFiles(input, "*.assetbundle")`
    # glob finds nothing. Stage each bundle under a temp dir with the suffix
    # so Unity can pick them up; clean up afterwards.
    bundles = []
    for entry, role in discover_bundle_inputs(args.input):
        directory_name = "head" if role == "head" else "costume"
        # Prefix same-named head/body files so they coexist in the Unity stage.
        bundles.append((f"{directory_name}__{entry.name}.assetbundle", entry.resolve()))
    bundles.sort(key=lambda item: item[0])
    if not bundles:
        print(f"[bangdream:bake:models] 输入为空: {args.input.resolve()}", flush=True)
        return
    if not unity.is_file():
        raise SystemExit(f"Unity Editor not found: {unity}")
    if not (project / "Assets").is_dir():
        raise SystemExit(f"Unity baker project not found: {project}")
    output.mkdir(parents=True, exist_ok=True)
    # Keep logs on the output drive until every batch succeeds.
    log_dir = Path(tempfile.mkdtemp(prefix="bangdream-bake-logs-", dir=output))

    def run_batch(entries: list[tuple[str, Path]], label: str, models_only: bool, *, probe=False):
        stage_dir = Path(tempfile.mkdtemp(prefix="bangdream-bake-stage-", dir=output)).resolve()
        if not stage_dir.is_relative_to(output) or stage_dir == output:
            raise RuntimeError(f"Unsafe staging directory: {stage_dir}")
        log = log_dir / f"{label}.log"
        try:
            for name, source in entries:
                shutil.copyfile(source, stage_dir / name)
            command = [
                str(unity), "-batchmode", "-quit", "-nographics", "-buildTarget", "Android",
                "-projectPath", str(project),
                "-executeMethod", "BakePipeline.FindAvatarTemplate" if probe else "BakePipeline.Run",
                "-game", "bangdream", "-input", str(stage_dir), "-output", str(output),
                "-sampleRate", str(args.sample_rate), "-logFile", str(log),
            ]
            report = stage_dir / "template.json"
            if probe:
                command.extend(["-templateReport", str(report)])
            elif models_only:
                command.extend(["-modelsOnly", "true"])
            print(f"{label}: {len(entries)} bundles; log: {log}", flush=True)
            result = subprocess.run(command, check=False)
            if result.returncode:
                raise SystemExit(f"Unity baking failed in {label} ({result.returncode}). See {log}")
            if probe:
                return json.loads(report.read_text(encoding="utf-8"))["bundle"]
        finally:
            # Only this task-created, resolved child of output is disposable.
            if stage_dir.resolve() != stage_dir or not stage_dir.is_relative_to(output):
                raise RuntimeError(f"Staging directory changed unexpectedly: {stage_dir}")
            shutil.rmtree(stage_dir)

    template = select_template(bundles, args.model_batch_size,
                               lambda entries, label: run_batch(entries, label, True, probe=True))
    print(f"Verifying shared Humanoid template: {template[1]}", flush=True)
    run_batch([template], "template-preflight", True)
    remaining = [entry for entry in bundles if entry != template]
    capacity = args.model_batch_size - 1
    total_batches = (len(remaining) + capacity - 1) // capacity
    for offset in range(0, len(remaining), capacity):
        batch_index = offset // capacity + 1
        run_batch(
            [template, *remaining[offset:offset + capacity]],
            f"models-{batch_index:04d}-of-{total_batches:04d}",
            args.models_only,
        )
    label = "Normalized model skeletons" if args.models_only else "Baked motions"
    if not log_dir.resolve().is_relative_to(output) or log_dir.resolve() == output:
        raise RuntimeError(f"Unsafe log directory: {log_dir}")
    shutil.rmtree(log_dir)
    print(f"{label} written to {output}")


if __name__ == "__main__":
    main()
