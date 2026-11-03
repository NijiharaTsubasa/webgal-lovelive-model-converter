"""Discover Hasunosora source bundles using the game's resource names."""

from pathlib import Path
import time
from collections.abc import Callable

from converter.common.unity import logical_name


def discover_inputs(input_dir: Path, *, progress: Callable[[str], None] | None = None) -> tuple[dict[str, Path], list[Path], list[Path]]:
    try:
        input_dir.stat()
    except FileNotFoundError:
        return {}, [], []
    if not input_dir.is_dir():
        raise NotADirectoryError(input_dir)
    index = {}
    last_report = time.monotonic()
    for number, path in enumerate(input_dir.glob("*.assetbundle"), 1):
        if path.is_file():
            index[logical_name(path)] = path
        now = time.monotonic()
        if progress and (number == 1 or number % 100 == 0 or now - last_report >= 5):
            progress(f"[hasunosora:scan] 已检查 {number} 个文件: {path.name}")
            last_report = now
    models = sorted((path for name, path in index.items()
                     if name.startswith("3d_costume_") and name[len("3d_costume_"):].isdigit()),
                    key=lambda path: path.name)
    motions = sorted((path for name, path in index.items() if name.startswith(("mot_", "motion_"))),
                     key=lambda path: path.name)
    return index, models, motions
