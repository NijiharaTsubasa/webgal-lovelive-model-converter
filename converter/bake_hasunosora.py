from __future__ import annotations

import argparse
import os
import subprocess
import tempfile
import time
from collections import deque
from pathlib import Path

from converter.common.unity import bundle_metadata, logical_name
from converter.hasunosora.source import discover_inputs
from converter.common.cli import configure_output


def select_roots(roots: list[Path], requested: list[str] | None, label: str) -> list[Path]:
    if not requested:
        return roots
    by_name = {path.stem: path for path in roots}
    missing = sorted(set(requested) - by_name.keys())
    if missing:
        raise SystemExit(f"Unknown Hasunosora {label}: {', '.join(missing)}")
    return [by_name[name] for name in sorted(set(requested))]


class BundleClosures:
    """Read each AssetBundle's source dependencies once for bounded batches."""

    def __init__(self, index: dict[str, Path]) -> None:
        self.index = index
        self.dependencies: dict[str, list[str]] = {}

    def for_root(self, root: Path) -> set[str]:
        result: set[str] = set()
        pending = deque([logical_name(root)])
        while pending:
            name = pending.popleft()
            if name in result:
                continue
            path = self.index.get(name)
            if path is None:
                raise FileNotFoundError(f"{root.name}: AssetBundle dependency not found: {name}")
            result.add(name)
            if name not in self.dependencies:
                _, names = bundle_metadata(path)
                self.dependencies[name] = [dependency.lower() for dependency in names]
            pending.extend(self.dependencies[name])
        return result


def batches(
    roots: list[Path], closures: BundleClosures, *, max_roots: int,
    max_bundles: int, shared: set[str] | None = None, progress_label: str = "",
) -> list[tuple[list[Path], set[str]]]:
    shared = set(shared or ())
    if len(shared) >= max_bundles:
        raise ValueError(f"Shared reference needs {len(shared)} bundles; limit is {max_bundles}")
    result: list[tuple[list[Path], set[str]]] = []
    selected: list[Path] = []
    names = set(shared)
    for index, root in enumerate(roots, 1):
        closure = closures.for_root(root)
        if progress_label and (index % 25 == 0 or index == len(roots)):
            print(f"[hasunosora:bake] {progress_label} dependencies {index}/{len(roots)}", flush=True)
        if len(shared | closure) > max_bundles:
            raise ValueError(f"{root.name} needs {len(shared | closure)} bundles; limit is {max_bundles}")
        combined = names | closure
        if selected and (len(selected) >= max_roots or len(combined) > max_bundles):
            result.append((selected, names))
            selected = []
            names = set(shared)
            combined = names | closure
        selected.append(root)
        names = combined
    if selected:
        result.append((selected, names))
    return result


def relay_progress(log: Path, position: int) -> int:
    if not log.is_file():
        return position
    with log.open("r", encoding="utf-8", errors="replace") as stream:
        stream.seek(position)
        while True:
            line = stream.readline()
            if not line or not line.endswith("\n"):
                break
            position = stream.tell()
            marker = "[HASUNOSORA_PROGRESS]"
            if marker in line:
                print(line[line.index(marker):].strip(), flush=True)
    return position


def run_batch(
    unity: Path, project: Path, input_dir: Path, index: dict[str, Path], output: Path,
    label: str, roots: list[Path], names: set[str], sample_rate: int,
    *, models_only: bool,
) -> None:
    descriptor, log_name = tempfile.mkstemp(
        prefix=f"unity-hasunosora-{label}-", suffix=".log", dir=output,
    )
    os.close(descriptor)
    log = Path(log_name)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", newline="\n", suffix=".txt",
        prefix=f"unity-hasunosora-{label}-", dir=output, delete=False,
    ) as bundle_list:
        for name in sorted(names):
            bundle_list.write(f"{index[name].resolve()}\n")
    bundle_list_path = Path(bundle_list.name)
    try:
        command = [
            str(unity), "-batchmode", "-quit", "-nographics", "-buildTarget", "Android",
            "-projectPath", str(project), "-executeMethod", "BakePipeline.Run",
            "-game", "hasunosora", "-input", str(input_dir),
            "-bundleList", str(bundle_list_path), "-output", str(output),
            "-sampleRate", str(sample_rate), "-logFile", str(log),
        ]
        if models_only:
            command.extend(["-modelsOnly", "true"])
        print(f"[hasunosora:bake] {label}: {len(roots)} roots, {len(names)} bundles", flush=True)
        with subprocess.Popen(command) as process:
            position = 0
            while process.poll() is None:
                position = relay_progress(log, position)
                time.sleep(0.5)
            relay_progress(log, position)
            if process.returncode:
                raise SystemExit(
                    f"Unity baking failed in {label} ({process.returncode}). See {log}"
                )
    finally:
        bundle_list_path.unlink(missing_ok=True)
    log.unlink(missing_ok=True)


def main() -> None:
    configure_output()
    parser = argparse.ArgumentParser(description="Batch Hasunosora Humanoid model and motion baking.")
    from converter.common.unity_editor import default_unity_editor
    parser.add_argument("--unity", type=Path, default=default_unity_editor())
    parser.add_argument("--input", type=Path, default=Path("input_hasunosora"))
    parser.add_argument("--output", type=Path, default=Path("baked_motions"))
    parser.add_argument("--sample-rate", type=int, default=30)
    parser.add_argument("--model-batch-size", type=int, default=8)
    parser.add_argument("--motion-batch-size", type=int, default=64)
    parser.add_argument("--max-bundles-per-batch", type=int, default=1024)
    parser.add_argument("--model", action="append", help="Exact 3d_costume bundle name; repeatable.")
    parser.add_argument("--motion", action="append", help="Exact mot bundle name; repeatable.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--models-only", action="store_true")
    mode.add_argument("--motions-only", action="store_true")
    args = parser.parse_args()
    if args.sample_rate <= 0 or args.model_batch_size <= 0 or args.motion_batch_size <= 0:
        parser.error("sample rate and batch sizes must be positive")
    if args.max_bundles_per_batch < 2:
        parser.error("--max-bundles-per-batch must be at least 2")
    unity = args.unity.resolve()
    input_dir = args.input.resolve()
    output = args.output.resolve()
    project = Path(__file__).resolve().parent / "unity_baker"
    index, models, motions = discover_inputs(input_dir)
    selected_models = select_roots(models, args.model, "model")
    selected_motions = select_roots(motions, args.motion, "motion")
    if ((args.models_only and not selected_models)
            or (args.motions_only and not selected_motions)
            or (not selected_models and not selected_motions)):
        print(f"[hasunosora:bake] 输入为空: {input_dir}", flush=True)
        return
    if not selected_models:
        raise SystemExit(f"Hasunosora motions require a character reference bundle in {input_dir}")
    if not unity.is_file():
        raise SystemExit(f"Unity Editor not found: {unity}")
    if not (project / "Assets").is_dir():
        raise SystemExit(f"Unity baker project not found: {project}")
    reference = selected_models[0]
    closures = BundleClosures(index)
    output.mkdir(parents=True, exist_ok=True)

    if not args.motions_only:
        model_batches = batches(
            selected_models, closures, max_roots=args.model_batch_size,
            max_bundles=args.max_bundles_per_batch, progress_label="models",
        )
        print(f"[hasunosora:bake] models: {len(selected_models)} roots, {len(model_batches)} batches", flush=True)
        for number, (roots, names) in enumerate(model_batches, 1):
            run_batch(unity, project, input_dir, index, output,
                      f"models-{number:04d}-of-{len(model_batches):04d}",
                      roots, names, args.sample_rate, models_only=True)

    if not args.models_only and selected_motions:
        shared = closures.for_root(reference)
        motion_batches = batches(
            selected_motions, closures, max_roots=args.motion_batch_size,
            max_bundles=args.max_bundles_per_batch, shared=shared, progress_label="motions",
        )
        print(f"[hasunosora:bake] motions: {len(selected_motions)} roots, "
              f"{len(motion_batches)} batches; reference {reference.stem}", flush=True)
        for number, (roots, names) in enumerate(motion_batches, 1):
            label = f"motions-{number:04d}-of-{len(motion_batches):04d}"
            before = {root.stem: (output / f"{root.stem}.baked.json").stat().st_mtime_ns
                      if (output / f"{root.stem}.baked.json").is_file() else None for root in roots}
            run_batch(unity, project, input_dir, index, output, label, roots, names, args.sample_rate,
                      models_only=False)
            unchanged = [root.stem for root in roots
                         if not (output / f"{root.stem}.baked.json").is_file()
                         or (output / f"{root.stem}.baked.json").stat().st_mtime_ns == before[root.stem]]
            if unchanged:
                raise SystemExit(f"Unity did not bake {label}: {', '.join(unchanged)}")
    print(f"[hasunosora:bake] complete: {len(selected_models) if not args.motions_only else 0} "
          f"models, {len(selected_motions) if not args.models_only else 0} motions", flush=True)


if __name__ == "__main__":
    main()
