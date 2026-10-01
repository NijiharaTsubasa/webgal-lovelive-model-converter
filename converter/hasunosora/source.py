"""Discover Hasunosora source bundles using the game's resource names."""

from pathlib import Path

from converter.common.unity import logical_name


def discover_inputs(input_dir: Path) -> tuple[dict[str, Path], list[Path], list[Path]]:
    try:
        input_dir.stat()
    except FileNotFoundError:
        return {}, [], []
    if not input_dir.is_dir():
        raise NotADirectoryError(input_dir)
    index = {logical_name(path): path for path in input_dir.glob("*.assetbundle") if path.is_file()}
    models = sorted((path for name, path in index.items()
                     if name.startswith("3d_costume_") and name[len("3d_costume_"):].isdigit()),
                    key=lambda path: path.name)
    motions = sorted((path for name, path in index.items() if name.startswith(("mot_", "motion_"))),
                     key=lambda path: path.name)
    return index, models, motions
