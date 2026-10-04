"""Convert Unity-baked LLAS Humanoid assets into browser packages."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from converter.llas import convert_all, select_model_sources
from converter.llas.source_inventory import active_sources


def main() -> None:
    # Source filenames contain Japanese characters not representable in GBK.
    # Keep CLI output UTF-8 even when Windows redirects it to a build log.
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Convert LLAS Humanoid models and motions.")
    parser.add_argument("--input", type=Path, default=Path("input_llas"))
    parser.add_argument("--output", type=Path, default=Path("output_packages/llas"))
    parser.add_argument("--baked", type=Path, default=Path("baked_motions/llas"))
    parser.add_argument("--model", action="append", help="Exact member prefab name; may be repeated.")
    parser.add_argument("--clean", action="store_true")
    args = parser.parse_args()
    inventory = active_sources(args.input.resolve())
    select_model_sources(list(inventory.models), args.model, inventory.model_names)
    if not inventory.models and not inventory.motions:
        print("[llas] 输入为空")
        return
    if not inventory.models:
        raise SystemExit("LLAS motions require a character model as the Humanoid reference rig")
    if args.clean and args.output.exists():
        shutil.rmtree(args.output)
    motion_output = args.output.resolve().parent / "motion" / "llas"
    if args.clean and motion_output.exists():
        shutil.rmtree(motion_output)
    convert_all(
        args.input.resolve(), args.output.resolve(), args.baked.resolve(),
        model_names=args.model,
    )


if __name__ == "__main__":
    main()
