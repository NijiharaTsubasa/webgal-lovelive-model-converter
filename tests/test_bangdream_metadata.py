import tempfile
import json
import unittest
from pathlib import Path

from converter.bangdream import build_package_config
from converter.bangdream.metadata import ModelDescriptions


def varint(value):
    result = bytearray()
    while value > 127:
        result.append((value & 127) | 128)
        value >>= 7
    result.append(value)
    return bytes(result)


def uint(number, value):
    return varint(number << 3) + varint(value)


def message(number, value):
    if isinstance(value, str):
        value = value.encode('utf-8')
    return varint(number << 3 | 2) + varint(len(value)) + value


def table(rows):
    return b''.join(message(1, uint(1, key) + message(2, row)) for key, row in rows)


def master_data():
    characters = [(1, message(3, '戸山 香澄')), (15, message(3, 'ミッシェル')),
                  (601, message(3, '奥沢 美咲'))]
    groups = [
        (70, message(2, 'ステージ衣装') + uint(5, 1) + message(9, '001_costume')),
        (80, message(2, '天使にラブ・ロックを') + message(9, '000_cos_monthly_2023_3')),
        (90, message(2, 'おそろい（北沢はぐみ）') + uint(5, 15) + message(9, '015_costume')),
    ]
    dresses = [(200, uint(3, 70) + message(4, 'another1') + message(5, 'アナザー1'))]
    return (message(3, table(characters)) + message(2006, table(dresses))
            + message(2037, table(groups)))


class BangDreamMetadataTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / 'masterdata.pb').write_bytes(master_data())
        self.descriptions = ModelDescriptions(self.root)

    def test_paired_components_share_original_costume_description(self):
        components = [{'role': 'head', 'model': 'head.glb'}, {'role': 'body', 'model': 'body.glb'}]
        config = build_package_config('001_costume', components, self.descriptions)
        self.assertEqual([component['description'] for component in config['components']],
                         ['ステージ衣装'] * 2)
        self.assertTrue(all('description' not in component for component in components))

    def test_head_only_uses_character_identity_without_costume_lookup(self):
        self.assertEqual(self.descriptions.get('001_cos_base', {'head'}),
                         '戸山 香澄 / 基础头部（仅头部）')
        self.assertEqual(self.descriptions.get('601_cos_base', {'head'}),
                         '奥沢 美咲 / 基础头部（仅头部）')

    def test_michelle_body_keeps_the_character_named_in_original_costume_title(self):
        self.assertEqual(self.descriptions.get('015_costume', {'body'}),
                         'おそろい（北沢はぐみ）（仅身体）')

    def test_shared_monthly_body_has_no_character_identity(self):
        self.assertEqual(self.descriptions.get('000_cos_monthly_2023_3', {'body'}),
                         '天使にラブ・ロックを（仅身体）')

    def test_alternate_colour_uses_original_costume_and_master_colour_name(self):
        self.assertEqual(self.descriptions.get('001_costume_another1', {'body'}),
                         'ステージ衣装（アナザー1）（仅身体）')

    def test_unknown_package_or_missing_optional_master_leaves_description_unset(self):
        for name in ['unknown', '999_costume', '001_unknown']:
            self.assertIsNone(self.descriptions.get(name, {'body'}))
        (self.root / 'masterdata.pb').unlink()
        self.assertIsNone(ModelDescriptions(self.root).get('001_costume', {'head', 'body'}))

    def test_invalid_master_data_is_reported(self):
        (self.root / 'masterdata.pb').write_bytes(b'\x12\x05x')
        with self.assertRaises(ValueError):
            ModelDescriptions(self.root)

    def test_same_resource_keeps_both_native_costume_names(self):
        alias = (71, message(2, 'ノーマル') + uint(5, 1) + message(9, '001_costume'))
        data = master_data()
        # A protobuf message field may be extended by another map entry.
        # Build one GroupMap carrying the original and alias groups.
        from converter.bangdream.previews import _fields
        tables = {number: bytes(value) for number, wire, value in _fields(memoryview(data)) if wire == 2}
        tables[2037] += table([alias])
        (self.root / 'masterdata.pb').write_bytes(b''.join(message(number, value) for number, value in tables.items()))
        descriptions = ModelDescriptions(self.root)
        self.assertEqual(descriptions.get('001_costume', {'head', 'body'}),
                         'ステージ衣装／ノーマル')

    def test_missing_description_preserves_an_existing_explicit_description(self):
        config = build_package_config('unknown', [{'role': 'body', 'description': 'Custom'}], self.descriptions)
        self.assertEqual(config['components'][0]['description'], 'Custom')

    def test_refresh_updates_only_descriptions_and_retains_previews_and_other_components(self):
        from tools.refresh_bangdream_model_descriptions import refresh
        folder = self.root / 'output/001_costume'
        folder.mkdir(parents=True)
        file = folder / 'config.json'
        models = [{'type': 'model', 'name': '001_costume', 'group': 'garupa', 'role': role,
                   'model': f'{role}.glb', 'preview': 'data:image/webp;base64,QUJD',
                   'description': '戸山 香澄 / ステージ衣装'} for role in ['head', 'body']]
        original = {'components': [*models, {'type': 'custom', 'name': 'untouched'}]}
        file.write_text(json.dumps(original), encoding='utf-8')
        self.assertEqual(refresh(folder.parent, self.root), (1, 1))
        expected = json.loads(json.dumps(original))
        for model in expected['components'][:2]:
            model['description'] = 'ステージ衣装'
        self.assertEqual(json.loads(file.read_text(encoding='utf-8')), expected)
        self.assertEqual(refresh(folder.parent, self.root), (1, 0))


if __name__ == '__main__':
    unittest.main()
