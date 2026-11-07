import unittest
from types import SimpleNamespace

import numpy as np
from PIL import Image

from converter.bangdream.eyelid import attach_eyelid_bindings, identify_eyelid_vertices
from converter.common.glb import GlbBuilder
from converter.common.unity import object_id


class EyelidBindingsTests(unittest.TestCase):
    def setUp(self):
        self.image = Image.new("RGB", (4, 1))
        self.image.putdata([(239, 193, 193), (115, 80, 73), (229, 218, 212), (255, 255, 255)])

    def test_separate_line_and_backing_exclude_unrelated_matching_ink(self):
        plate = [(0.02, 1.4, .08), (.05, 1.4, .08), (.05, 1.41, .08), (.02, 1.41, .08)]
        line = [plate[0], plate[1], (.035, 1.402, .08)]
        second = [(.02, 1.415, .08), (.04, 1.415, .08), (.03, 1.417, .08)]
        lower_lash = [(x, y - .04, z) for x, y, z in second]
        mask = [(x, y, z - .01) for x, y, z in plate]
        positions = np.array(plate + line + second + lower_lash + mask)
        uv = np.array([[.125, .5]] * 4 + [[.375, .5]] * 9 + [[.625, .5]] * 4)
        triangles = np.array([[0, 1, 2], [0, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12], [13, 14, 15], [13, 15, 16]])
        result = identify_eyelid_vertices(positions, uv, triangles, self.image, 1.39)
        self.assertEqual(result, {"left": list(range(7))})
        # Vertex order and triangle order are not part of the input contract.
        permutation = np.arange(len(positions))[::-1]
        inverse = np.argsort(permutation)
        shuffled = identify_eyelid_vertices(positions[permutation], uv[permutation],
                                          inverse[triangles[::-1]], self.image, 1.39)
        self.assertEqual({tuple(positions[permutation][i]) for i in shuffled["left"]},
                         {tuple(positions[i]) for i in result["left"]})

    def test_lower_rosy_eyelid_rim_is_not_the_independent_crease(self):
        upper = np.array([[.02, 1.42, .08], [.04, 1.42, .08], [.03, 1.43, .08]])
        lower = upper.copy()
        lower[:, 1] -= .015
        positions = np.concatenate([upper, lower])
        result = identify_eyelid_vertices(positions, np.full((6, 2), [.125, .5]),
                                         np.array([[0, 1, 2], [3, 4, 5]]), self.image, 1.39)
        self.assertEqual(result, {"left": [0, 1, 2]})

    def test_crease_can_be_one_component_with_mixed_ink_and_skin_triangles(self):
        positions = np.array([[.02, 1.4, .08], [.04, 1.4, .08], [.04, 1.41, .08],
                              [.02, 1.41, .08], [.02, 1.412, .08]])
        # Two rosy triangles and one brown triangle in a single connected part.
        uv = np.array([[.125, .5], [.125, .5], [.125, .5], [.125, .5], [.875, .5]])
        triangles = np.array([[0, 1, 2], [0, 2, 3], [0, 3, 4]])
        result = identify_eyelid_vertices(positions, uv, triangles, self.image, 1.39)
        self.assertEqual(result, {"left": list(range(5))})

    def test_both_sides_and_unknown_geometry_are_independent(self):
        positions = np.array([[.02, 1.4, .08], [.04, 1.4, .08], [.03, 1.41, .08]])
        uv = np.full((3, 2), [.125, .5])
        mirror = positions.copy()
        mirror[:, 0] *= -1
        result = identify_eyelid_vertices(np.concatenate([positions, mirror]), np.tile(uv, (2, 1)),
                                         np.array([[0, 1, 2], [3, 4, 5]]), self.image, 1.39)
        self.assertEqual(result, {"left": [0, 1, 2], "right": [3, 4, 5]})
        self.assertEqual(identify_eyelid_vertices(positions, np.full((3, 2), [.625, .5]),
                                                np.array([[0, 1, 2]]), self.image, 1.39), {})

    def test_export_matches_material_identity_and_keeps_primitive_indices_local(self):
        class Pointer:
            def __init__(self, value):
                self.value = value

            def deref_parse_as_object(self):
                return self.value

        builder = GlbBuilder()
        materials = []
        for index, color in enumerate([(229, 218, 212), (239, 193, 193)]):
            material = SimpleNamespace(
                object_reader=SimpleNamespace(assets_file=object(), path_id=index),
                m_SavedProperties=SimpleNamespace(m_TexEnvs=[("_MainTex", SimpleNamespace(
                    m_Texture=Pointer(SimpleNamespace(image=Image.new("RGB", (1, 1), color)))))]))
            builder.materials[object_id(material)] = index
            materials.append(Pointer(material))

        def primitive(sign, material):
            return {"attributes": {
                "POSITION": builder.add_accessor([(sign * .02, 1.4, .08), (sign * .04, 1.4, .08),
                                                   (sign * .03, 1.41, .08)], "VEC3", 5126),
                "TEXCOORD_0": builder.add_accessor([(.5, .5)] * 3, "VEC2", 5126)},
                    "indices": builder.add_accessor([0, 1, 2], "SCALAR", 5123), "material": material}

        builder.document["meshes"] = [
            {"name": "eyeL_NoOutline_obj", "primitives": [primitive(-1, 0)]},
            {"name": "face_NoOutline_obj", "primitives": [primitive(-1, 1), primitive(1, 0)]}]
        builder.document["meshes"][0]["primitives"][0]["attributes"]["POSITION"] = builder.add_accessor(
            [(-.02, 1.37, .08), (-.04, 1.37, .08), (-.03, 1.39, .08)], "VEC3", 5126)
        builder.document["nodes"] = [{"mesh": 1}]
        attach_eyelid_bindings(SimpleNamespace(builder=builder),
                              [(SimpleNamespace(m_Materials=materials), 0)], role="head")
        primitives = builder.document["meshes"][1]["primitives"]
        self.assertEqual(primitives[0]["extras"]["garupaEyelid"], {"right": [0, 1, 2]})
        self.assertNotIn("extras", primitives[1])


if __name__ == "__main__":
    unittest.main()
