"""Convert BanG Dream models and already baked motions into resource packages."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from converter.bangdream import convert_all, discover_bundle_inputs
from converter.bangdream.color_variants import discover_variant_jobs, convert_variant_job
from converter.bake_bangdream_motion import package_existing_motions
from converter.bangdream.motion import discover_motion_bundles
from converter.common.cli import configure_output


def clean_game_output(output: Path) -> None:
    if output.exists():
        shutil.rmtree(output)


def convert_variants(input_root: Path, output_root: Path, baked_root: Path,
                     *, overwrite: bool = False) -> None:
    jobs = discover_variant_jobs(input_root)
    count = sum(len(job["body"]) for job in jobs)
    print(f"[bangdream] 异色模型: {count} 个包，{len(jobs)} 套服装", flush=True)
    failures = []
    for job in jobs:
        result = convert_variant_job(job, output_root, baked_root, overwrite=overwrite)
        failures.extend(result["failures"])
    if output_root.exists():
        configs = sorted(path.relative_to(output_root).as_posix()
                         for path in output_root.glob("*/config.json"))
        (output_root / "index.json").write_text(
            json.dumps({"configs": configs}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if failures:
        raise RuntimeError("异色模型转换失败: " + "; ".join(
            f"{item['name']}: {item['error']}" for item in failures))


def main() -> None:
    configure_output()
    parser = argparse.ArgumentParser(
        description="Convert Bang Dream AssetBundles to standardized character packages."
    )
    parser.add_argument("--input", type=Path, default=Path("input_bangdream"))
    parser.add_argument("--output", type=Path, default=Path("output_packages/bangdream"))
    parser.add_argument("--baked", type=Path, default=Path("baked_motions"),
                        help="Unity-baked model skeleton and motion data root.")
    parser.add_argument("--clean", action="store_true", help="Rebuild this game's model and motion packages.")
    parser.add_argument("--variants-only", action="store_true",
                        help="Supplement missing alternate-colour model packages using existing baked skeletons.")
    args = parser.parse_args()
    if args.variants_only and args.clean:
        parser.error("--variants-only cannot be combined with --clean")
    input_root = args.input.resolve()
    output_root = args.output.resolve()
    baked_root = args.baked.resolve()
    if args.variants_only:
        convert_variants(input_root, output_root, baked_root)
        return
    models = discover_bundle_inputs(input_root)
    motions = discover_motion_bundles(input_root)
    if not models and not motions:
        print(f"[bangdream:convert] 输入为空: {input_root}")
        return
    if not models:
        raise FileNotFoundError(f"no Bang Dream model bundles found under {input_root}")

    if args.clean:
        clean_game_output(output_root)
        clean_game_output(output_root.parent / "motion" / "garupa")

    convert_all(input_root, output_root, baked_root)
    convert_variants(input_root, output_root, baked_root, overwrite=True)
    if motions:
        package_existing_motions(input_root, baked_root / "bangdream", output_root.parent / "motion" / "garupa")


if __name__ == "__main__":
    main()
