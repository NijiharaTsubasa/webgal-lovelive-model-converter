"""Mesh paint resampling and exported node/index integrity, without large ABs."""

import copy
import unittest
from types import SimpleNamespace as NS
from unittest.mock import patch

from converter.common.physics import _merge_mesh_cloth_regions, _mesh_cloth_entries, _resample_mesh_fixed
from converter.common.normalized_model import NormalizedNodeMapping
from converter.common.unity import object_id
from tests.test_physics_export import PhysicsFixture, Ptr, vec


IDENTITY = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]


class MeshClothExportTests(unittest.TestCase):
    def test_disjoint_source_regions_share_one_output_primitive(self):
        document = {"nodes": [{"mesh": 0}], "meshes": [{"primitives": [
            {"attributes": {"POSITION": 0}}]}], "accessors": [{"count": 5}]}
        base = {"node": 0, "primitive": 0, "radius": .003,
                "stiffness": 12., "damping": .8, "gravity": [0., 0., 0.]}
        left = {**base, "fixed": [0, 2, 3, 4], "colliders": [1, 2]}
        right = {**base, "fixed": [0, 1, 2, 4], "colliders": [2, 3]}
        result = _merge_mesh_cloth_regions([left, right], document)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["fixed"], [0, 2, 4])
        self.assertEqual(result[0]["colliders"], [1, 2, 3])
        self.assertEqual(left["fixed"], [0, 2, 3, 4])
        overlapping = {**right, "fixed": [0, 2, 4]}
        with self.assertRaisesRegex(ValueError, "overlap"):
            _merge_mesh_cloth_regions([left, overlapping], document)

    def test_kaho_saved_paint_is_in_cloth_local_space(self):
        # Four actual vertices and their nearest saved proxy paint positions
        # from 3d_costume_1001103101 / Skirt. The reduced proxy has 154 points;
        # the render mesh has 1191, so its paint is not a per-vertex array.
        vertices = [(-.0501492135, .9648382068, .0823465437),
                    (.0000203928, .6896176338, -.1367898285),
                    (-.1142446026, .6434724927, .0814258009),
                    (-.1982339323, .6132673621, -.0928283557)]
        selection = NS(positions=[vec(-.1513097584, .0832887590, .0412812643),
                                  vec(.1341088265, -.1357873231, -.0000112417),
                                  vec(.1841162145, .0779071897, .1317425072),
                                  vec(.2056906819, -.0840614289, .2178708017)],
                       attributes=[NS(Value=n) for n in (1, 2, 2, 2)],
                       maxConnectionDistance=.0949230045)
        # Reflection of source toProxyMatrix: cloth-local
        # Unity (0.8083963394 - y, z, -x) -> reflected glTF.
        matrix = [0, 0, 1, 0, 1, 0, 0, 0, 0, 1, 0, 0, -.8083963394, 0, 0, 1]
        self.assertEqual(_resample_mesh_fixed(vertices, matrix, selection), [0])
        # Duplicate render vertices at UV seams keep their own original index.
        self.assertEqual(_resample_mesh_fixed(vertices + [vertices[0]], matrix, selection), [0, 4])
        with self.assertRaisesRegex(ValueError, "outside saved paint coverage"):
            _resample_mesh_fixed(vertices, IDENTITY, selection)

    def test_resampling_keeps_unselected_vertices_on_their_skinned_pose(self):
        selection = NS(positions=[vec(), vec(0, 1, 0), vec(0, 2, 0)],
                       attributes=[NS(Value=n) for n in (0, 1, 2)],
                       maxConnectionDistance=.1)
        self.assertEqual(_resample_mesh_fixed([[0, 0, 0], [0, 1, 0], [0, 2, 0]],
                                               IDENTITY, selection), [0, 1])
        selection.attributes = [NS(Value=n) for n in (8, 9, 10)]
        self.assertEqual(_resample_mesh_fixed([[0, 0, 0], [0, 1, 0], [0, 2, 0]],
                                               IDENTITY, selection), [0, 1])

    def test_resampling_rejects_unrepresented_selection_modes_and_coverage(self):
        selection = NS(positions=[vec(), vec(0, 1, 0)],
                       attributes=[NS(Value=1), NS(Value=2)], maxConnectionDistance=.1)
        vertices = [[0, 0, 0], [0, 1, 0]]
        self.assertEqual(_resample_mesh_fixed(vertices, IDENTITY, selection), [0])
        for invalid in (16, 18):
            with self.subTest(attribute=invalid):
                altered = copy.deepcopy(selection)
                altered.attributes[1].Value = invalid
                with self.assertRaisesRegex(ValueError, "unsupported selection attribute"):
                    _resample_mesh_fixed(vertices, IDENTITY, altered)
        with self.assertRaisesRegex(ValueError, "outside saved paint coverage"):
            _resample_mesh_fixed([[0, 0, 0], [0, 1.2, 0]], IDENTITY, selection)
        with self.assertRaisesRegex(ValueError, "both fixed and moving"):
            _resample_mesh_fixed([[0, 0, 0]], IDENTITY, selection)

    def test_original_mesh_indices_bind_to_exported_renderer_and_shared_colliders(self):
        fixture = PhysicsFixture()
        cloth_node = fixture.node([0, 0, 0])
        renderer_node = fixture.node([0, 0, 0])
        mesh = NS(m_Name="Skirt")
        renderer = NS(m_GameObject=renderer_node.m_GameObject, m_Mesh=Ptr(mesh))
        component = fixture.component(cloth_node, "MagicaCloth",
            serializeData=NS(sourceRenderers=[Ptr(renderer)]),
            serializeData2=NS(selectionData=NS(positions=[vec(), vec(0, 1, 0)],
                attributes=[NS(Value=1), NS(Value=2)], maxConnectionDistance=.2)))
        document = {"nodes": [{}, {}, {"name": "Skirt Renderer", "mesh": 0}],
                    "meshes": [{"name": "Skirt", "primitives": [{"mode": 4, "attributes": {"POSITION": 0}}]}],
                    "accessors": [{"count": 3}]}
        scaled_attachment = [2, 0, 0, 0, 0, 2, 0, 0, 0, 0, 2, 0, 0, 0, 0, 1]
        mapping = NormalizedNodeMapping(
            source_nodes={object_id(n): n.index for n in fixture.nodes},
            canonical_world=[IDENTITY, scaled_attachment],
            neutral_world=[IDENTITY, scaled_attachment],
            source_world=[IDENTITY, IDENTITY], redirects={})
        # The skeleton attachment's inverse scale would incorrectly cancel the
        # source's 2x scale. An independent root renderer requires radius .006.
        self.assertEqual(mapping.radius(renderer_node, .003), .003)
        exported = NS(builder=NS(document=document), node_mapping=mapping)
        decoded = NS(m_Vertices=[[0, 0, 0], [0, 1, 0], [.01, 0, 0]], process=lambda: None)
        with patch("converter.common.physics.MeshHandler", return_value=decoded):
            result = _mesh_cloth_entries(component, exported, [2, 5])
            self.assertEqual(result, [{"node": 2, "primitive": 0, "fixed": [0, 2],
                "radius": .006, "stiffness": 12., "damping": .8,
                "gravity": [0., 0., 0.], "colliders": [2, 5]}])
            document["nodes"][2]["scale"] = [.5, .5, .5]
            self.assertAlmostEqual(_mesh_cloth_entries(component, exported, [])[0]["radius"], .012)
            del document["nodes"][2]["scale"]
            document["accessors"][0]["count"] = 4
            with self.assertRaisesRegex(ValueError, "vertex counts"):
                _mesh_cloth_entries(component, exported, [])
            document["accessors"][0]["count"] = 3
            document["nodes"].append(document["nodes"][-1])
            with self.assertRaisesRegex(ValueError, "unambiguous"):
                _mesh_cloth_entries(component, exported, [])


if __name__ == "__main__":
    unittest.main()
