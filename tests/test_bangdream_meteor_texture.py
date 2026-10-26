import struct
import unittest
from types import SimpleNamespace as O

from converter.bangdream.meteor_texture import extract_matcap_image


def block(values):
    return bytes.fromhex('fcfdffffffffffff') + struct.pack('<4H', *values)


def texture(**changes):
    fields = dict(m_TextureFormat=50, m_ColorSpace=1, m_ImageCount=1,
                  m_TextureDimension=2, m_Width=6, m_Height=12, m_MipCount=2,
                  get_image_data=lambda: block((12345, 23456, 34567, 65535))
                  + block((45678, 34567, 23456, 65535))
                  + block((9876, 8765, 7654, 65535)))
    return O(**(fields | changes))


class MatCapImageTests(unittest.TestCase):
    def test_selected_level_uses_source_texels_and_image_row_orientation(self):
        base = extract_matcap_image(texture(), 0)
        self.assertEqual(base.size, (6, 12))
        self.assertEqual(base.getpixel((0, 0)), (178, 135, 91, 255))
        self.assertEqual(base.getpixel((0, 11)), (48, 91, 135, 255))
        selected = extract_matcap_image(texture(), 1)
        self.assertEqual(selected.size, (3, 6))
        # The selected image comes from the third source block.
        self.assertEqual(selected.getpixel((0, 0)), (38, 34, 29, 255))

    def test_invalid_selection_fails(self):
        for level in (True, -1, 0.5, 2):
            with self.subTest(level=level), self.assertRaises(ValueError):
                extract_matcap_image(texture(), level)

    def test_bad_source_and_selected_level_truncation_fail(self):
        for changes in ({'m_TextureFormat': 4}, {'m_ColorSpace': 0},
                        {'m_ImageCount': 2}, {'m_TextureDimension': 3},
                        {'m_MipsStripped': 1}, {'m_Width': 0},
                        {'get_image_data': lambda: b'\0' * 32}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                extract_matcap_image(texture(**changes), 1)


if __name__ == '__main__':
    unittest.main()
