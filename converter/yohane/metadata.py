"""Resolve model labels from the original MessagePack/LZ4 master table archive."""
from __future__ import annotations

from pathlib import Path

import lz4.block
import msgpack
import UnityPy


# The source master table calls the unreferenced Christmas prefab "xmas".
PREFAB_ALIASES = {'CH_yohane_xmas01': 'CH_yohane_christmas01'}
MODEL_LABELS = {'EN_yohane_greatmaster01': '大天师夜羽'}


def decode_master_tables(raw: bytes) -> dict[str, list[dict]]:
    unpacker = msgpack.Unpacker(raw=False, strict_map_key=False)
    unpacker.feed(raw)
    header = next(unpacker)
    start = unpacker.tell()
    tables = {}
    for name in ('Costume', 'CostumeSet', 'CharaBook', 'Glossary'):
        offset, size = header[name]
        if offset < 0 or size < 0 or start + offset + size > len(raw):
            raise ValueError(f'Yohane master table {name}: invalid byte range')
        value = msgpack.unpackb(raw[start + offset:start + offset + size],
                                raw=False, strict_map_key=False)
        if isinstance(value, msgpack.ExtType):
            if value.code != 99 or len(value.data) < 5 or value.data[0] != 0xd2:
                raise ValueError(f'Yohane master table {name}: unsupported compression header')
            length = int.from_bytes(value.data[1:5], 'big')
            value = msgpack.unpackb(lz4.block.decompress(value.data[5:], uncompressed_size=length),
                                    raw=False, strict_map_key=False)
        tables[name] = value
    return tables


def descriptions_from_tables(tables: dict[str, list[dict]]) -> dict[str, str]:
    glossary = {row['MasterID']: row['Name'] for row in tables['Glossary']
                if row['Laungage'] == 'zh_CN' and row['Name']}
    descriptions = {}
    for row in tables['CharaBook']:
        if row['ID'] in glossary:
            descriptions[Path(row['Model']).name] = glossary[row['ID']]
    groups = {}
    for row in tables['Costume']:
        title = glossary.get(row['ID'])
        if not title:
            continue
        character = glossary[row['CharacterID']]
        prefab = Path(row['Prefab']).name
        descriptions[PREFAB_ALIASES.get(prefab, prefab)] = f'{character} {title}'
        if row['CostumeSetID']:
            group = row['CostumeSetID']
            if group in groups and groups[group] != title:
                raise ValueError(f'Yohane costume set {group}: conflicting localized names')
            groups[group] = title
    for row in tables['CostumeSet']:
        title = groups.get(row['GroupID'])
        if title:
            descriptions[Path(row['Prefab']).name] = f"{glossary[row['CharacterID']]} {title}"
    descriptions.update(MODEL_LABELS)
    return descriptions


def model_descriptions(input_dir: Path) -> dict[str, str]:
    master = None
    for path in sorted(input_dir.rglob('*.bundle')):
        environment = UnityPy.load(str(path))
        for obj in environment.objects:
            if obj.type.name != 'AssetBundle':
                continue
            for asset_path, entry in obj.read().m_Container:
                if not asset_path.lower().endswith('/master/masterdata.bytes'):
                    continue
                if entry.asset.m_FileID != 0:
                    continue
                if master is not None:
                    raise ValueError('Yohane input contains multiple masterdata assets')
                script = entry.asset.deref().read_typetree()['m_Script']
                master = script.encode('utf-8', 'surrogateescape') if isinstance(script, str) else script
    return descriptions_from_tables(decode_master_tables(master)) if master is not None else {}
