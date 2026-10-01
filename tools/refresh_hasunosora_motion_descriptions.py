"""Refresh published Hasunosora motion descriptions without rebaking motions."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from converter.hasunosora.motion import MOTION_DESCRIPTIONS_CSV, load_motion_descriptions


def refresh(config_path: Path, csv_path: Path) -> tuple[int, int]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    descriptions = load_motion_descriptions(csv_path)
    count = filled = 0
    for index, component in enumerate(config["components"]):
        if component["type"] != "motion":
            continue
        description = descriptions.get(component["name"].removeprefix("hasunosora/"), "")
        config["components"][index] = {
            "type": component["type"],
            "name": component["name"],
            "description": description,
            **{key: value for key, value in component.items() if key not in {"type", "name", "description"}},
        }
        count += 1
        filled += bool(description)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="\n", dir=config_path.parent,
            prefix=".motion-descriptions-", suffix=".tmp", delete=False,
        ) as stream:
            temporary = Path(stream.name)
            stream.write(json.dumps(config, ensure_ascii=False, indent=2) + "\n")
        os.replace(temporary, config_path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return count, filled


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    config = root / "output_packages" / "hasunosora" / "motions" / "config.json"
    count, filled = refresh(config, MOTION_DESCRIPTIONS_CSV)
    print(f"{config}: {filled}/{count} motion descriptions")


if __name__ == "__main__":
    main()
