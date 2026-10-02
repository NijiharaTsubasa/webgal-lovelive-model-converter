"""Character domains from the game's CostumeModels and Characters master data."""

from pathlib import Path

import yaml


# Characters.Id -> LatinAlphabetNameFirst, verified against source master data.
# Only the eleven audited principal face rigs belong to these adapter domains.
CHARACTER_SLUGS = {
    1021: "kozue", 1022: "tsuzuri", 1023: "megumi",
    1031: "kaho", 1032: "sayaka", 1033: "rurino",
    1041: "ginko", 1042: "kosuzu", 1043: "hime",
    1051: "izumi", 1052: "ceras",
}


def load_costume_motion_groups(input_dir: Path) -> dict[str, str]:
    """Join exact CostumeModels.Id to CharactersId; unknown characters stay ungrouped."""
    source = input_dir / "CostumeModels.yaml"
    if not source.is_file():
        return {}
    records = yaml.safe_load(source.read_text(encoding="utf-8"))
    if not isinstance(records, list):
        raise ValueError(f"{source}: expected a list of costume records")
    groups: dict[str, str] = {}
    for record in records:
        if not isinstance(record, dict) or type(record.get("Id")) is not int:
            continue
        character_id = record.get("CharactersId")
        slug = CHARACTER_SLUGS.get(character_id) if type(character_id) is int else None
        if slug is not None:
            name = f"3d_costume_{record['Id']}"
            domain = f"hasunosora.{slug}"
            if name in groups and groups[name] != domain:
                raise ValueError(f"{source}: conflicting character identity for {name}")
            groups[name] = domain
    return groups
