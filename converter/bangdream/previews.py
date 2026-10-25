"""Resolve costume thumbnails from the game's master tables."""
from __future__ import annotations

import base64
from io import BytesIO
from pathlib import Path

import UnityPy


def _varint(data: memoryview, offset: int) -> tuple[int, int]:
    value = 0
    for shift in range(0, 70, 7):
        if offset >= len(data):
            raise ValueError('Truncated Bang Dream master-data varint')
        byte = data[offset]
        offset += 1
        if shift == 63 and byte > 1:
            break
        value |= (byte & 127) << shift
        if not byte & 128:
            return value, offset
    raise ValueError('Invalid Bang Dream master-data varint')


def _fields(data: memoryview):
    """Read wire fields without copying the large, mostly unused master file."""
    offset = 0
    while offset < len(data):
        tag, offset = _varint(data, offset)
        number, wire = tag >> 3, tag & 7
        if not number:
            raise ValueError('Invalid Bang Dream master-data field number')
        if wire == 0:
            value, offset = _varint(data, offset)
        elif wire in (1, 2, 5):
            if wire == 2:
                size, offset = _varint(data, offset)
            else:
                size = 8 if wire == 1 else 4
            end = offset + size
            if end > len(data):
                raise ValueError('Truncated Bang Dream master-data field')
            value = data[offset:end]
            offset = end
        else:
            raise ValueError(f'Unsupported Bang Dream master-data wire type {wire}')
        yield number, wire, value


def _records(table: memoryview):
    for number, wire, entry in _fields(table):
        if number != 1 or wire != 2:
            continue
        key = 0
        row = None
        for field, kind, value in _fields(entry):
            if field == 1 and kind == 0:
                key = value
            elif field == 2 and kind == 2:
                row = value
        if row is not None:
            yield key, row


def costume_thumbnail_ids(raw: bytes) -> dict[str, int]:
    # SuiteMasterGetResponse fields 2006/2037 are DressMap/GroupMap.
    tables = {number: value for number, wire, value in _fields(memoryview(raw))
              if number in (2006, 2037) and wire == 2}
    if set(tables) != {2006, 2037}:
        raise ValueError('Bang Dream masterdata.pb is missing costume tables; provide decrypted, decompressed Protobuf')
    groups = {}
    for key, row in _records(tables[2037]):
        for number, wire, value in _fields(row):
            if number == 9 and wire == 2:
                groups[key] = bytes(value).decode('utf-8')
    thumbnails = {}
    for _, row in _records(tables[2006]):
        fields = {number: value for number, wire, value in _fields(row)
                  if (number in (3, 10) and wire == 0) or (number == 4 and wire == 2)}
        color_name = bytes(fields.get(4, b'')).decode('utf-8')
        if color_name not in ('original', 'another1', 'another2', 'another3', 'another4'):
            continue
        name = groups.get(fields.get(3))
        color_id = fields.get(10, 0)
        if not name or not color_id:
            continue
        if color_name != 'original':
            name = f'{name}_{color_name}'
        previous = thumbnails.get(name)
        if previous is not None and previous != color_id:
            raise ValueError(f'Conflicting Bang Dream costume thumbnail: {name}')
        thumbnails[name] = color_id
    return thumbnails


class BodyPreviews:
    def __init__(self, input_dir: Path):
        self.directory = input_dir / 'thumb' / 'costume3ddress'
        if not self.directory.exists():
            self.directory = input_dir / 'costume3ddress'
        master = input_dir / 'masterdata.pb'
        self.ids = costume_thumbnail_ids(master.read_bytes()) if master.is_file() and self.directory.is_dir() else {}
        self.groups: dict[int, dict[int, str]] = {}

    def get(self, package_name: str) -> str | None:
        color_id = self.ids.get(package_name)
        if color_id is None:
            return None
        group = color_id // 50
        if group not in self.groups:
            self.groups[group] = self._read_group(group)
        return self.groups[group].get(color_id)

    def _read_group(self, group: int) -> dict[int, str]:
        source = self.directory / f'group{group}'
        if not source.is_file():
            return {}
        environment = UnityPy.load(str(source))
        images = {}
        wanted = set(self.ids.values())
        for obj in environment.objects:
            if obj.type.name != 'Texture2D':
                continue
            texture = obj.read()
            if not texture.m_Name.startswith('dress') or not texture.m_Name[5:].isdigit():
                continue
            color_id = int(texture.m_Name[5:])
            if color_id not in wanted:
                continue
            buffer = BytesIO()
            texture.image.save(buffer, format='WEBP', lossless=True)
            images[color_id] = 'data:image/webp;base64,' + base64.b64encode(buffer.getvalue()).decode('ascii')
        return images
