"""Run every registered game's converter entry point in sequence.

Each game ships its own converter.convert_<game> module. The list below is the
single source of truth for which games are wired into the build — add a
new entry here when you bring a new game on board.

Layout after running:
    output_packages/
        hasunosora/
            3d_costume_1001103101/...
            motions/...
            index.json
        bangdream/
            018_cos_base/...
            motions/...
            index.json
        llas/
            ch0001_co0002_member/...
            motions/...
        config.json        (lightweight preview catalog, written here)
        index.json         (validation-tool index, written here)
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import os
from pathlib import Path


GAMES: list[str] = [
    "hasunosora",
    "bangdream",
    "llas",
]


def _run_game(game: str, root: Path, *, clean: bool = False) -> int:
    code_root = Path(__file__).resolve().parent
    script = code_root / "converter" / f"convert_{game}.py"
    if not script.exists():
        print(f"[skip] {game}: {script.name} missing", file=sys.stderr)
        return 1
    print(f"[convert:{game}] running converter.{script.stem}")
    command = [sys.executable, "-m", f"converter.{script.stem}"]
    if clean:
        command.append("--clean")
    env = dict(os.environ)
    env['PYTHONPATH'] = str(code_root) + os.pathsep + env.get('PYTHONPATH', '')
    return subprocess.call(command, cwd=root, env=env)


def _merge_top_level_index(root: Path) -> int:
    """Build the preview catalog without copying large per-model runtime data."""
    output_root = root / "output_packages"
    output_root.mkdir(parents=True, exist_ok=True)
    configs = sorted(path.relative_to(output_root).as_posix()
                     for path in output_root.rglob("config.json")
                     if path.is_file() and path != output_root / "config.json"
                     and path.relative_to(output_root).parts[0] != "runtime")
    top_level = {"configs": configs}

    catalog = []
    model_fields = ("type", "name", "description", "group", "role", "model",
                    "humanoidScale", "motionGroup", "defaultMotion")
    for relative in configs:
        manifest = json.loads((output_root / relative).read_text(encoding="utf-8"))
        for component in manifest["components"]:
            if component["type"] == "model":
                entry = {key: component[key] for key in model_fields if key in component}
            else:
                entry = dict(component)
            entry["sourceConfig"] = relative
            catalog.append(entry)

    (output_root / "config.json").write_text(
        json.dumps({"components": catalog}, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )

    (output_root / "index.json").write_text(
        json.dumps(top_level, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"[convert] indexed {len(configs)} resource manifests and {len(catalog)} preview components")
    return 0


def main(workspace_root: Path | None = None) -> int:
    parser = argparse.ArgumentParser(description="Convert registered games and refresh the preview catalog.")
    parser.add_argument(
        "--merge-only",
        action="store_true",
        help="Rebuild the preview config.json and validation index.json without converting assets.",
    )
    parser.add_argument("--game", choices=GAMES, help="Convert only this game, then refresh the PoC index.")
    parser.add_argument("--clean", action="store_true", help="Rebuild selected games' outputs before conversion.")
    args = parser.parse_args()
    if args.merge_only and (args.game or args.clean):
        parser.error("--merge-only cannot be combined with --game or --clean")
    root = workspace_root or Path(__file__).resolve().parent
    if args.merge_only:
        return _merge_top_level_index(root)

    games = [args.game] if args.game else GAMES
    failures: list[str] = []
    for game in games:
        rc = _run_game(game, root, clean=args.clean)
        if rc:
            failures.append(game)

    merge_rc = _merge_top_level_index(root)

    if failures:
        print(f"[done] {len(games) - len(failures)}/{len(games)} games succeeded; failed: {failures}", file=sys.stderr)
        return 1
    print(f"[done] {len(games)}/{len(games)} games succeeded")
    return merge_rc


if __name__ == "__main__":
    sys.exit(main())
