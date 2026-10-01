"""Convert BanG Dream models and already baked motions into resource packages."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from converter.bangdream import convert_all, discover_bundle_inputs
from converter.bake_bangdream_motion import package_existing_motions
from converter.bangdream.motion import discover_motion_bundles
from converter.common.cli import configure_output


def clean_game_output(output: Path) -> None:
    if output.exists():
        shutil.rmtree(output)


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
    args = parser.parse_args()
    input_root = args.input.resolve()
    output_root = args.output.resolve()
    baked_root = args.baked.resolve()
    models = discover_bundle_inputs(input_root)
    motions = discover_motion_bundles(input_root)
    if not models and not motions:
        print(f"[bangdream:convert] 输入为空: {input_root}")
        return
    if not models:
        raise FileNotFoundError(f"no Bang Dream model bundles found under {input_root}")

    if args.clean:
        clean_game_output(output_root)

    convert_all(input_root, output_root, baked_root)
    if motions:
        package_existing_motions(input_root, baked_root / "bangdream", output_root / "motions")
    index_path = output_root / "index.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    if (output_root / "motions" / "config.json").is_file():
        index["configs"].append("motions/config.json")
    index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
