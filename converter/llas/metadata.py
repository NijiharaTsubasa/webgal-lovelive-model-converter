"""Resolve LLAS model labels from original game databases."""

import sqlite3
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ModelDescriptions:
    by_asset: dict[tuple[str, int], str]


def _database(path: Path) -> sqlite3.Connection:
    return sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)


def model_descriptions(input_root: Path) -> ModelDescriptions:
    db_root = input_root / "db"
    asset_path = db_root / "asset_a_ja.db"
    master_path = db_root / "masterdata.db"
    dictionary_path = db_root / "dictionary_ja_k.db"
    if not all(path.is_file() for path in (asset_path, master_path, dictionary_path)):
        return ModelDescriptions({})

    with closing(_database(asset_path)) as asset_db, closing(_database(master_path)) as master_db, closing(_database(dictionary_path)) as dictionary_db:
        packs = {
            asset_path: (pack_name, head)
            for asset_path, pack_name, head in asset_db.execute(
                "SELECT asset_path, pack_name, head FROM member_model"
            )
        }
        messages = dict(dictionary_db.execute("SELECT id, message FROM m_dictionary"))
        candidates: dict[tuple[str, int], list[tuple[int, int, str]]] = {}
        queries = (
            (0, "SELECT s.id, m.name, s.name, s.model_asset_path "
                "FROM m_suit AS s JOIN m_member AS m ON m.id = s.member_m_id"),
            (1, "SELECT s.id, m.name, s.name, v.model_asset_path "
                "FROM m_suit_view AS v JOIN m_suit AS s ON s.id = v.suit_master_id "
                "JOIN m_member AS m ON m.id = s.member_m_id"),
            (2, "SELECT s.id, m.name, s.name, s.model_asset_path "
                "FROM m_suit_non_playable AS s JOIN m_member AS m ON m.id = s.member_m_id"),
        )
        for priority, query in queries:
            for suit_id, member_key, suit_key, model_asset_path in master_db.execute(query):
                asset = packs.get(model_asset_path)
                if asset is None:
                    continue
                member = messages.get(str(member_key).removeprefix("k."))
                suit = messages.get(str(suit_key).removeprefix("k."))
                if member and suit:
                    candidates.setdefault(asset, []).append(
                        (priority, suit_id, f"{member} / {suit}")
                    )

    return ModelDescriptions({asset: min(rows)[2] for asset, rows in candidates.items()})


def description_for_source(source: Path, descriptions: ModelDescriptions) -> str:
    # The canonical decrypted path preserves the original asset DB key
    # pack_name + section offset. Arbitrarily renamed ABs still convert, but
    # have no reliable path back to a masterdata suit row.
    stem = source.name.removesuffix(".unity3d")
    pack, separator, offset = stem.rpartition("__")
    if not separator or not offset.isdecimal():
        return ""
    return descriptions.by_asset.get((pack, int(offset)), "")
