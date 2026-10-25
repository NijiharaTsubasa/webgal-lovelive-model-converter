import base64
import json
import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from PIL import Image

import converter.bangdream as bangdream
from converter.bangdream.previews import BodyPreviews, costume_thumbnail_ids


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


def master_data(extra_dresses=()):
    # Dress IDs, group IDs and thumbnail colour IDs deliberately differ.
    dresses = [
        (900, uint(3, 70) + message(4, 'original') + uint(10, 51)),
        (901, uint(3, 70) + message(4, 'another1') + uint(10, 52)),
        (902, uint(3, 70) + message(4, 'original') + uint(10, 51)),
        *extra_dresses,
    ]
    groups = [(70, message(2, 'Costume') + uint(5, 1) + message(9, '001_costume'))]
    characters = [(1, message(3, 'Character'))]
    return (message(3, table(characters)) + message(123, b'unrelated') + message(2006, table(dresses))
            + message(2037, table(groups)))


def texture(name):
    image = Image.new('RGBA', (2, 2), (20, 70, 110, 255))
    image.putpixel((0, 0), (0, 0, 0, 0))
    return SimpleNamespace(type=SimpleNamespace(name='Texture2D'),
                           read=lambda: SimpleNamespace(m_Name=name, image=image))


class BangDreamPreviewTests(unittest.TestCase):
    def prepare(self, root, directory='thumb/costume3ddress'):
        (root / 'masterdata.pb').write_bytes(master_data())
        thumbnails = root / directory
        thumbnails.mkdir(parents=True)
        (thumbnails / 'group1').write_bytes(b'fixture bundle')
        return thumbnails

    def test_links_group_and_original_colour_instead_of_dress_id(self):
        self.assertEqual(costume_thumbnail_ids(master_data()), {'001_costume': 51, '001_costume_another1': 52})

    def test_rejects_conflicting_original_colour_rows(self):
        conflicting = (903, uint(3, 70) + message(4, 'original') + uint(10, 53))
        with self.assertRaisesRegex(ValueError, 'Conflicting'):
            costume_thumbnail_ids(master_data([conflicting]))

    def test_rejects_missing_tables_and_truncated_wire_data(self):
        for data in [b'', message(2006, b''), b'\x12\x05a', b'\x80', b'\x00']:
            with self.subTest(data=data), self.assertRaises(ValueError):
                costume_thumbnail_ids(data)

    def test_missing_optional_inputs_produce_no_preview(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertIsNone(BodyPreviews(root).get('001_costume'))
            (root / 'masterdata.pb').write_bytes(b'not read without thumbnails')
            self.assertIsNone(BodyPreviews(root).get('001_costume'))
            (root / 'masterdata.pb').unlink()
            (root / 'thumb/costume3ddress').mkdir(parents=True)
            self.assertIsNone(BodyPreviews(root).get('001_costume'))

    def test_decodes_expected_texture_once_as_transparent_lossless_webp(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            thumbnails = self.prepare(root)
            environment = SimpleNamespace(objects=[texture('dress51'), texture('dress52')])
            with patch('converter.bangdream.previews.UnityPy.load', return_value=environment) as load:
                previews = BodyPreviews(root)
                result = previews.get('001_costume')
                self.assertEqual(result, previews.get('001_costume'))
                self.assertIsNone(previews.get('unmapped'))
                load.assert_called_once_with(str(thumbnails / 'group1'))
            self.assertTrue(result.startswith('data:image/webp;base64,'))
            with Image.open(BytesIO(base64.b64decode(result.split(',', 1)[1]))) as image:
                self.assertEqual(image.format, 'WEBP')
                self.assertEqual(image.size, (2, 2))
                self.assertEqual(image.convert('RGBA').getpixel((0, 0))[3], 0)
                self.assertEqual(image.convert('RGBA').getpixel((1, 1)), (20, 70, 110, 255))

    def test_falls_back_only_when_primary_directory_does_not_exist(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fallback = self.prepare(root, 'costume3ddress')
            environment = SimpleNamespace(objects=[texture('dress51')])
            with patch('converter.bangdream.previews.UnityPy.load', return_value=environment) as load:
                self.assertIsNotNone(BodyPreviews(root).get('001_costume'))
                load.assert_called_once_with(str(fallback / 'group1'))
            (root / 'thumb/costume3ddress').mkdir(parents=True)
            with patch('converter.bangdream.previews.UnityPy.load') as load:
                self.assertIsNone(BodyPreviews(root).get('001_costume'))
                load.assert_not_called()

    def test_missing_texture_leaves_preview_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.prepare(root)
            with patch('converter.bangdream.previews.UnityPy.load',
                       return_value=SimpleNamespace(objects=[texture('dress52')])):
                self.assertIsNone(BodyPreviews(root).get('001_costume'))

    def test_batch_adds_preview_to_new_body_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            inputs, output = root / 'input', root / 'output'
            inputs.mkdir()
            self.prepare(inputs)
            for role in ['head', 'costume']:
                (inputs / role).mkdir()
                (inputs / role / 'bundle').write_bytes(b'fixture')

            def convert(entry, destination, baked, occupied, expected_role):
                package = destination / '001_costume'
                package.mkdir(exist_ok=True)
                (package / f'{expected_role}.glb').write_bytes(b'fixture')
                return '001_costume', {'role': expected_role, 'model': f'{expected_role}.glb',
                                       'humanoidScale': 1, 'morphPoses': [], 'expressionGroups': []}

            environment = SimpleNamespace(objects=[texture('dress51')])
            with patch.object(bangdream, 'convert_one', side_effect=convert), \
                 patch('converter.bangdream.previews.UnityPy.load', return_value=environment):
                configs = bangdream.convert_all(inputs, output)
            components = configs[0]['components']
            self.assertNotIn('preview', components[0])
            self.assertTrue(components[1]['preview'].startswith('data:image/webp;base64,'))
            written = json.loads((output / '001_costume/config.json').read_text(encoding='utf-8'))
            self.assertEqual(written['components'][1]['preview'], components[1]['preview'])


if __name__ == '__main__':
    unittest.main()
