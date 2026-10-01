"""Keep source Texture2D sampling state through the common glTF exporter."""

from pathlib import Path
from types import SimpleNamespace
import unittest

from PIL import Image
import UnityPy

from converter.common.glb import GlbBuilder


def texture(*, mode=1, mips=2, wrap_u=0, wrap_v=0):
    return SimpleNamespace(
        object_reader=SimpleNamespace(assets_file=object(), path_id=1),
        m_Name="sampling-test", m_ColorSpace=1, m_MipCount=mips,
        m_TextureSettings=SimpleNamespace(
            m_FilterMode=mode, m_WrapU=wrap_u, m_WrapV=wrap_v,
        ),
        image=Image.new("RGBA", (2, 2)),
    )


class UnityTextureSamplerTests(unittest.TestCase):
    def test_filter_modes_preserve_mip_selection_and_non_mip_sampling(self):
        for mode, mips, mag, minimum in (
            (0, 1, 9728, 9728), (1, 1, 9729, 9729), (2, 1, 9729, 9729),
            (0, 2, 9728, 9984), (1, 2, 9729, 9985), (2, 2, 9729, 9987),
        ):
            with self.subTest(mode=mode, mips=mips):
                builder = GlbBuilder()
                builder.add_image(texture(mode=mode, mips=mips))
                self.assertEqual(builder.document["samplers"], [{
                    "magFilter": mag, "minFilter": minimum,
                    "wrapS": 10497, "wrapT": 10497,
                }])

    def test_independent_wrap_axes_and_sampler_reuse(self):
        builder = GlbBuilder()
        sources = [texture(wrap_u=u, wrap_v=v) for u, v in ((1, 2), (0, 0), (1, 2))]
        for source in sources:
            builder.add_image(source)
        self.assertEqual(len(builder.document["samplers"]), 2)
        self.assertEqual(builder.document["samplers"][0]["wrapS"], 33071)
        self.assertEqual(builder.document["samplers"][0]["wrapT"], 33648)
        self.assertEqual([t["sampler"] for t in builder.document["textures"]], [0, 1, 0])

    def test_unsupported_source_sampling_fails_before_adding_image(self):
        for source in (texture(mode=3), texture(mips=0), texture(wrap_u=3)):
            with self.subTest(source=source):
                builder = GlbBuilder()
                with self.assertRaisesRegex(ValueError, "unsupported"):
                    builder.add_image(source)
                self.assertEqual(builder.document["images"], [])
                self.assertEqual(builder.document["samplers"], [])




if __name__ == "__main__":
    unittest.main()
