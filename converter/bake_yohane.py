from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
import time
from pathlib import Path

from converter.common.cli import configure_output
from converter.common.unity_editor import resolve_unity_editor
from converter.yohane.source import YohaneModelSource, discover_models


def select_models(models: list[YohaneModelSource], requested: list[str] | None) -> list[YohaneModelSource]:
    if not requested:
        return models
    by_name = {item.name: item for item in models}
    missing = sorted(set(requested) - by_name.keys())
    if missing:
        raise ValueError('Unknown Yohane model: ' + ', '.join(missing))
    return [by_name[name] for name in sorted(set(requested))]


def motion_references(models: list[YohaneModelSource]) -> list[YohaneModelSource]:
    references = {}
    for model in models:
        references.setdefault(model.controller_name, model)
    return list(references.values())


def relay_progress(log: Path, position: int) -> int:
    if not log.is_file():
        return position
    with log.open('r', encoding='utf-8', errors='replace') as stream:
        stream.seek(position)
        while True:
            line = stream.readline()
            if not line or not line.endswith('\n'):
                break
            position = stream.tell()
            marker = '[YOHANE_PROGRESS]'
            if marker in line:
                print(line[line.index(marker):].strip(), flush=True)
    return position


def run_batch(unity: Path, project: Path, output: Path, models: list[YohaneModelSource],
              sample_rate: int, label: str, *, models_only: bool, motions_only: bool) -> None:
    output.mkdir(parents=True, exist_ok=True)
    job = {
        'bundles': sorted({str(path.resolve()) for model in models for path in model.bundle_paths}),
        'models': [{'name': model.name, 'prefabPath': model.asset_path,
                    'controllerPath': model.controller_asset_path,
                    'idleClipNames': list(model.idle_clip_names),
                    'restoreRootScale': model.name.lower().startswith('ch_ruby_')}
                   for model in models],
        'output': str(output), 'sampleRate': sample_rate,
        'modelsOnly': models_only, 'motionsOnly': motions_only,
    }
    expected = ['body_baked.json'] if motions_only else (
        ['skeleton.json', 'face_samples.json', 'idle_baked.json'] if models_only else
        ['skeleton.json', 'face_samples.json', 'body_baked.json'])
    before = {(model.name, filename): (output / model.name / filename).stat().st_mtime_ns
              if (output / model.name / filename).is_file() else None
              for model in models for filename in expected}
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.json',
                                     prefix='unity-yohane-', dir=output, delete=False) as stream:
        json.dump(job, stream, ensure_ascii=False)
        job_path = Path(stream.name)
    log = job_path.with_suffix('.log')
    try:
        command = [str(unity), '-batchmode', '-quit', '-nographics', '-buildTarget', 'Android',
                   '-projectPath', str(project), '-executeMethod', 'YohaneBaker.Run',
                   '-job', str(job_path), '-logFile', str(log)]
        print(f'[yohane:bake] {label}: {len(models)} models, {len(job["bundles"])} bundles', flush=True)
        with subprocess.Popen(command) as process:
            position = 0
            while process.poll() is None:
                position = relay_progress(log, position)
                time.sleep(0.5)
            relay_progress(log, position)
            if process.returncode:
                raise RuntimeError(f'Unity Yohane baking failed ({process.returncode}). See {log}')
        missing = [f'{name}/{filename}' for (name, filename), stamp in before.items()
                   if not (output / name / filename).is_file()
                   or (output / name / filename).stat().st_mtime_ns == stamp]
        if missing:
            raise RuntimeError('Unity did not bake: ' + ', '.join(missing) + f'. See {log}')
    finally:
        job_path.unlink(missing_ok=True)
    log.unlink(missing_ok=True)


def main() -> None:
    configure_output()
    parser = argparse.ArgumentParser(description='Bake Yohane Humanoid models and story motions.')
    parser.add_argument('--unity', type=Path)
    parser.add_argument('--input', type=Path, default=Path('input_yohane'))
    parser.add_argument('--output', type=Path, default=Path('baked_motions'))
    parser.add_argument('--sample-rate', type=int, default=30)
    parser.add_argument('--batch-size', type=int, default=6)
    parser.add_argument('--model', action='append', help='Exact prefab name; repeatable.')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--models-only', action='store_true')
    mode.add_argument('--motions-only', action='store_true')
    args = parser.parse_args()
    if args.sample_rate <= 0 or args.batch_size <= 0:
        parser.error('sample rate and batch size must be positive')
    models = select_models(discover_models(args.input.resolve()), args.model)
    if not models:
        print(f'[yohane:bake] 输入为空: {args.input.resolve()}', flush=True)
        return
    if args.motions_only:
        models = motion_references(models)
    unity = resolve_unity_editor(args.unity)
    project = Path(__file__).resolve().parent / 'unity_baker'
    output = args.output.resolve() / 'yohane'
    count = (len(models) + args.batch_size - 1) // args.batch_size
    for index in range(count):
        run_batch(unity, project, output, models[index * args.batch_size:(index + 1) * args.batch_size],
                  args.sample_rate, f'batch-{index + 1:04d}-of-{count:04d}',
                  models_only=args.models_only, motions_only=args.motions_only)
    print(f'[yohane:bake] complete: {len(models)} model references', flush=True)


if __name__ == '__main__':
    main()
