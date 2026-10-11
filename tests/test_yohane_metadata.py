import tempfile
import unittest
from pathlib import Path

import lz4.block
import msgpack

from converter.yohane.metadata import (
    decode_master_tables,
    descriptions_from_tables,
    model_descriptions,
)


def fixture():
    return {
        'Costume': [
            {'ID': 'boss_outfit', 'CharacterID': 'yohane', 'CostumeSetID': 'night',
             'Prefab': 'Costume/CH_yohane_greatmaster01'},
            {'ID': 'christmas', 'CharacterID': 'yohane', 'CostumeSetID': '',
             'Prefab': 'Costume/CH_yohane_xmas01'},
        ],
        'CostumeSet': [
            {'ID': 'night_chika', 'GroupID': 'night', 'CharacterID': 'chika',
             'Prefab': 'Costume/CH_chika_dinosaur01_inv'},
        ],
        'CharaBook': [
            {'ID': 'boss', 'Model': 'EnemyPrefab/CH_yohane_greatmaster01'},
            {'ID': 'chika', 'Model': 'Costume/CH_chika_normal01'},
        ],
        'Glossary': [
            {'MasterID': key, 'Laungage': language, 'Name': name}
            for key, language, name in [
                ('yohane', 'zh_CN', '夜羽'), ('chika', 'zh_CN', '千歌'),
                ('boss_outfit', 'zh_CN', '暗夜恶魔・夜晚'),
                ('boss_outfit', 'en_US', 'English outfit'),
                ('christmas', 'zh_CN', '闪闪发光☆圣诞节!!'),
                ('boss', 'zh_CN', '大天师夜羽'),
            ]
        ],
    }


class YohaneMetadataTests(unittest.TestCase):
    def test_costume_priority_group_link_locale_and_explicit_model_labels(self):
        descriptions = descriptions_from_tables(fixture())
        self.assertEqual(descriptions['CH_yohane_greatmaster01'], '夜羽 暗夜恶魔・夜晚')
        self.assertEqual(descriptions['EN_yohane_greatmaster01'], '大天师夜羽')
        self.assertEqual(descriptions['CH_chika_dinosaur01_inv'], '千歌 暗夜恶魔・夜晚')
        self.assertEqual(descriptions['CH_chika_normal01'], '千歌')
        self.assertNotIn('CH_unknown_normal01', descriptions)

    def test_christmas_alias_preserves_original_localized_name(self):
        descriptions = descriptions_from_tables(fixture())
        self.assertEqual(descriptions['CH_yohane_christmas01'], '夜羽 闪闪发光☆圣诞节!!')
        self.assertNotIn('CH_yohane_xmas01', descriptions)

    def test_master_archive_decodes_plain_and_lz4_tables(self):
        expected = fixture()
        chunks = []
        header = {}
        offset = 0
        for index, (name, rows) in enumerate(expected.items()):
            raw = msgpack.packb(rows, use_bin_type=True)
            if index % 2:
                raw = msgpack.packb(msgpack.ExtType(
                    99, b'\xd2' + len(raw).to_bytes(4, 'big')
                    + lz4.block.compress(raw, store_size=False)))
            header[name] = [offset, len(raw)]
            chunks.append(raw)
            offset += len(raw)
        archive = msgpack.packb(header, use_bin_type=True) + b''.join(chunks)
        self.assertEqual(decode_master_tables(archive), expected)
        bad_header = dict(header, Costume=[offset + 1, 10])
        with self.assertRaisesRegex(ValueError, 'invalid byte range'):
            decode_master_tables(msgpack.packb(bad_header) + b''.join(chunks))

    def test_conflicting_group_names_are_not_resolved_by_iteration_order(self):
        tables = fixture()
        tables['Costume'].append({'ID': 'other', 'CharacterID': 'yohane',
                                  'CostumeSetID': 'night', 'Prefab': 'other'})
        tables['Glossary'].append({'MasterID': 'other', 'Laungage': 'zh_CN', 'Name': '其他'})
        with self.assertRaisesRegex(ValueError, 'conflicting localized names'):
            descriptions_from_tables(tables)

    def test_input_without_metadata_has_no_invented_labels(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(model_descriptions(Path(directory)), {})
