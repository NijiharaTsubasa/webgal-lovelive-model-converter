"""Refresh published Hasunosora motion descriptions without rebaking motions."""

from __future__ import annotations

import json
import os
import struct
import tempfile
from pathlib import Path

from converter.hasunosora.motion import MOTION_DESCRIPTIONS_CSV, load_motion_descriptions
from converter.common.motion_binary import MAGIC, PREFIX_SIZE


def refresh(motion_path: Path, csv_path: Path) -> tuple[int, int]:
    descriptions = load_motion_descriptions(csv_path)
    count = filled = 0
    files = sorted(
        file for file in motion_path.rglob("*")
        if file.is_file() and file.suffix in {".json", ".motionbin"}
    ) if motion_path.is_dir() else [motion_path] if motion_path.is_file() else []
    for file in files:
        samples = None
        if file.suffix == ".motionbin":
            binary = file.read_bytes()
            if len(binary) < PREFIX_SIZE or binary[:8] != MAGIC:
                raise ValueError(f"{file}: not a binary motion file")
            header_length = struct.unpack_from("<I", binary, 8)[0]
            header_end = PREFIX_SIZE + header_length
            data_start = (header_end + 7) // 8 * 8
            if data_start > len(binary):
                raise ValueError(f"{file}: truncated binary motion header")
            payload = json.loads(binary[PREFIX_SIZE:header_end].decode("utf-8"))
            samples = binary[data_start:]
        else:
            payload = json.loads(file.read_text(encoding="utf-8"))
        if payload.get("type") != "motion" or payload.get("motionGroup") != "hasunosora":
            continue
        description = descriptions.get(payload["name"], "")
        payload = {
            "type": payload["type"],
            "name": payload["name"],
            "description": description,
            **{key: value for key, value in payload.items() if key not in {"type", "name", "description"}},
        }
        if samples is None:
            content = (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        else:
            header = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")
            padding = (PREFIX_SIZE + len(header) + 7) // 8 * 8 - PREFIX_SIZE - len(header)
            content = MAGIC + struct.pack("<I", len(header)) + header + b"\x00" * padding + samples
        _replace(file, content)
        count += 1
        filled += bool(description)
    return count, filled


def _replace(file: Path, content: bytes) -> None:
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", dir=file.parent,
            prefix=".motion-descriptions-", suffix=".tmp", delete=False,
        ) as stream:
            temporary = Path(stream.name)
            stream.write(content)
        os.replace(temporary, file)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    motions = root / "output_packages" / "motion" / "hasunosora"
    count, filled = refresh(motions, MOTION_DESCRIPTIONS_CSV)
    print(f"{motions}: {filled}/{count} motion descriptions")


if __name__ == "__main__":
    main()
