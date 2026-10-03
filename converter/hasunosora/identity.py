"""Parameter-face domains and costume metadata for Hasunosora models."""

from pathlib import Path

import yaml


# Characters.Id -> shared neutral-face recipe.
CHARACTER_FACE_GROUPS = {
    1021: "old", 1022: "old", 1023: "old",
    1031: "kaho", 1032: "old", 1033: "old",
    1041: "new", 1042: "new", 1043: "new",
    1051: "new", 1052: "new",
    9007: "new", 9008: "new", 9011: "new",
}

# These two source bundles have no records in the supplied CostumeModels master.
# Their DeA body assets and IndoorShoes materials identify winter school uniforms.
SUPPLEMENTAL_COSTUMES = {
    "3d_costume_1001901201": "制服(冬)_上靴_錦上マイカ",
    "3d_costume_1001901301": "制服(冬)_上靴_令沢葵",
}


def load_costume_motion_groups(input_dir: Path) -> dict[str, str]:
    """Resolve audited face domains by master character id or exact source bundle."""
    groups = {name: "hasunosora.new" for name in SUPPLEMENTAL_COSTUMES}
    source = input_dir / "CostumeModels.yaml"
    if not source.is_file():
        return groups
    records = yaml.safe_load(source.read_text(encoding="utf-8"))
    if not isinstance(records, list):
        raise ValueError(f"{source}: expected a list of costume records")
    identities: dict[int, int] = {}
    for record in records:
        if not isinstance(record, dict) or type(record.get("Id")) is not int:
            continue
        character_id = record.get("CharactersId")
        if type(character_id) is not int:
            continue
        costume_id = record["Id"]
        if costume_id in identities and identities[costume_id] != character_id:
            raise ValueError(f"{source}: conflicting character identity for 3d_costume_{costume_id}")
        identities[costume_id] = character_id
        group = CHARACTER_FACE_GROUPS.get(character_id)
        if group is not None:
            name = f"3d_costume_{record['Id']}"
            domain = f"hasunosora.{group}"
            if name in groups and groups[name] != domain:
                raise ValueError(f"{source}: conflicting character identity for {name}")
            groups[name] = domain
    return groups
