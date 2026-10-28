"""Human-readable component labels from the original character/costume tables."""
from __future__ import annotations

import re
from pathlib import Path

from .previews import _fields, _records


class ModelDescriptions:
    def __init__(self, input_dir: Path):
        self.characters: dict[int, str] = {}
        self.costumes: dict[str, tuple[list[str], int]] = {}
        self.colors: dict[tuple[str, str], str] = {}
        master = input_dir / 'masterdata.pb'
        if not master.is_file():
            return
        tables = {number: value for number, wire, value in _fields(memoryview(master.read_bytes()))
                  if number in (3, 2006, 2037) and wire == 2}
        if not {3, 2037}.issubset(tables):
            raise ValueError('Bang Dream masterdata.pb is missing character/costume name tables')
        for key, row in _records(tables[3]):
            for number, wire, value in _fields(row):
                if number == 3 and wire == 2:
                    self.characters[key] = bytes(value).decode('utf-8').strip()
        groups = {}
        for key, row in sorted(_records(tables[2037])):
            fields = {number: value for number, wire, value in _fields(row)
                      if (number in (2, 9) and wire == 2) or (number == 5 and wire == 0)}
            name = bytes(fields.get(9, b'')).decode('utf-8')
            title = bytes(fields.get(2, b'')).decode('utf-8').strip()
            if not name or not title:
                continue
            owner = fields.get(5, 0)
            previous = self.costumes.get(name)
            if previous is not None and previous[1] != owner:
                raise ValueError(f'Conflicting Bang Dream costume description: {name}')
            if previous is None:
                self.costumes[name] = ([title], owner)
            elif title not in previous[0]:
                previous[0].append(title)
            groups[key] = name
        if 2006 in tables:
            for _, row in _records(tables[2006]):
                fields = {number: value for number, wire, value in _fields(row)
                          if (number in (4, 5) and wire == 2) or (number == 3 and wire == 0)}
                name = groups.get(fields.get(3))
                color_type = bytes(fields.get(4, b'')).decode('utf-8')
                color_name = bytes(fields.get(5, b'')).decode('utf-8').strip()
                if name and color_name:
                    key = (name, color_type)
                    if key in self.colors and self.colors[key] != color_name:
                        raise ValueError(f'Conflicting Bang Dream costume colour name: {name}/{color_type}')
                    self.colors[key] = color_name

    def get(self, package_name: str, roles: set[str]) -> str | None:
        match = re.match(r'^(\d{3})_', package_name)
        if match is None:
            return None
        character_id = int(match[1])
        character = self.characters.get(character_id)
        if roles == {'head'}:
            return f'{character} / 基础头部（仅头部）' if character else None
        variant = re.fullmatch(r'(.+)_(another[1-4])', package_name)
        source_name, color_type = variant.groups() if variant else (package_name, 'original')
        costume = self.costumes.get(source_name)
        if costume is None:
            return None
        titles, _ = costume
        title = '／'.join(titles)
        if color_type != 'original':
            color_name = self.colors.get((source_name, color_type))
            if color_name:
                title = f'{title}（{color_name}）'
        suffix = '（仅身体）' if roles == {'body'} else ''
        return f'{title}{suffix}'
