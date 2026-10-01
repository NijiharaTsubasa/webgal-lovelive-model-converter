import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from converter.llas.metadata import description_for_source, model_descriptions


class LlasMetadataTests(unittest.TestCase):
    def test_description_comes_from_original_databases_not_filename(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_root = root / "db"
            db_root.mkdir(parents=True)
            with closing(sqlite3.connect(db_root / "masterdata.db")) as db:
                db.execute("CREATE TABLE m_member (id INTEGER, name TEXT)")
                db.execute("CREATE TABLE m_suit (id INTEGER, member_m_id INTEGER, name TEXT, model_asset_path TEXT)")
                db.execute("CREATE TABLE m_suit_view (suit_master_id INTEGER, model_asset_path TEXT)")
                db.execute("CREATE TABLE m_suit_non_playable (id INTEGER, member_m_id INTEGER, name TEXT, model_asset_path TEXT)")
                db.execute("INSERT INTO m_member VALUES (1, 'k.member_1')")
                db.execute("INSERT INTO m_suit VALUES (12345, 1, 'k.suit_12345', 'asset-1')")
                db.commit()
            with closing(sqlite3.connect(db_root / "asset_a_ja.db")) as db:
                db.execute("CREATE TABLE member_model (asset_path TEXT, pack_name TEXT, head INTEGER)")
                db.execute("INSERT INTO member_model VALUES ('asset-1', 'original-pack', 24)")
                db.commit()
            with closing(sqlite3.connect(db_root / "dictionary_ja_k.db")) as db:
                db.execute("CREATE TABLE m_dictionary (id TEXT, message TEXT)")
                db.executemany("INSERT INTO m_dictionary VALUES (?, ?)", [
                    ("member_1", "高坂 穂乃果"),
                    ("suit_12345", "音ノ木坂学院制服"),
                ])
                db.commit()

            names = model_descriptions(root)
            source = Path("original-pack__24.unity3d")
            self.assertEqual(description_for_source(source, names),
                             "高坂 穂乃果 / 音ノ木坂学院制服")
            self.assertEqual(description_for_source(Path("agent-renamed-model.unity3d"), names), "")

    def test_missing_original_database_is_not_silently_replaced_by_catalog_csv(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(model_descriptions(Path(tmp)).by_asset, {})


if __name__ == "__main__":
    unittest.main()
