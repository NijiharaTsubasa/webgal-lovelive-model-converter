"""physics.source.magicaCloth2 export (verbatim MagicaCloth2 + PreBuild), with tiny source-shaped fixtures."""

import base64
import struct
import unittest
from unittest.mock import patch
from types import SimpleNamespace as NS

from converter.common.source_magica import magica_cloth2_source
from converter.common.source_common import unity_from_gltf
from converter.common.unity import object_id


class Ptr:
    """UnityPy-like PPtr (object API) whose typetree form is {m_FileID, m_PathID}."""

    def __init__(self, target=None):
        self.target = target
        self.m_FileID = 0
        self.m_PathID = target.object_reader.path_id if target is not None else 0
        self.type = NS(name=target.object_reader.type.name if target is not None else "None")

    def __bool__(self):
        return self.target is not None

    def read(self):
        return self.target

    def deref_parse_as_object(self):
        return self.target


def tree(value):
    """Typetree view of a fixture object: PPtrs become {m_FileID, m_PathID}."""
    if isinstance(value, Ptr):
        return {"m_FileID": 0, "m_PathID": value.m_PathID}
    if isinstance(value, NS):
        return {k: tree(v) for k, v in vars(value).items() if k != "object_reader"}
    if isinstance(value, list):
        return [tree(v) for v in value]
    return value


class Fixture:
    def __init__(self):
        self.asset = object()
        self.readers = []
        self.pid = 5000

    def obj(self, kind, **fields):
        o = NS(**fields)
        self.pid += 1
        o.object_reader = NS(assets_file=self.asset, path_id=self.pid, type=NS(name=kind),
                             read_typetree=lambda o=o: tree(o))
        self.readers.append(NS(type=NS(name=kind), path_id=self.pid, read=lambda o=o: o,
                               read_typetree=lambda o=o: tree(o)))
        return o

    def node(self, name, parent=None, position=(0., 0., 0.)):
        go = self.obj("GameObject", m_Name=name, m_Component=[])
        t = self.obj("Transform", m_LocalPosition=NS(x=position[0], y=position[1], z=position[2]),
                     m_LocalRotation=NS(x=0., y=0., z=0., w=1.), m_LocalScale=NS(x=1., y=1., z=1.),
                     m_Father=Ptr(parent), m_Children=[], m_GameObject=Ptr(go))
        go.m_Component.append((0, Ptr(t)))
        if parent is not None:
            parent.m_Children.append(Ptr(t))
        return t

    def component(self, node, cls, **fields):
        script = self.obj("MonoScript", m_ClassName=cls)
        c = self.obj("MonoBehaviour", m_GameObject=node.m_GameObject, m_Enabled=1, m_Script=Ptr(script),
                     m_Name="", **fields)
        node.m_GameObject.read().m_Component.append((0, Ptr(c)))
        return c


def cloth_fields(cloth_type, roots=(), renderers=(), colliders=(), prebuild=None):
    return dict(serializeData=NS(clothType=cloth_type, rootBones=[Ptr(r) for r in roots],
                                 sourceRenderers=[Ptr(r) for r in renderers], gravity=0.20000000298023224,
                                 colliderCollisionConstraint=NS(mode=2, colliderList=[Ptr(c) for c in colliders])),
                serializeData2=NS(selectionData=NS(positions=[NS(x=.1, y=.2, z=.3)], attributes=[NS(Value=2)]),
                                  preBuildData=prebuild or NS(enabled=0, buildId="", preBuildScriptableObject=Ptr(),
                                                              uniquePreBuildData=NS(version=0))))


class SourceMagicaTests(unittest.TestCase):
    def setUp(self):
        f = self.f = Fixture()
        self.root = f.node("root")
        self.hips = f.node("Hips", self.root, (0, 1, 0))
        self.hair = f.node("SP_Hair_01", self.hips, (0, .5, 0))
        self.hair2 = f.node("SP_Hair_02", self.hair, (0, -.1, 0))
        self.holder = f.node("Extension_CapsuleCollider", self.hips)
        self.capsule = f.component(self.holder, "MagicaCapsuleCollider", size=NS(x=.05, y=.05, z=.3), direction=2)
        f.component(self.holder, "ExtendClothSettings", clothType=2, colliderReferenceMagicaClothList=[])
        self.exported = [self.root, self.hips]   # the hair chain and the collider holder are not GLB nodes
        nodes = {object_id(t): i for i, t in enumerate(self.exported)}
        ident = [1., 0, 0, 0, 0, 1., 0, 0, 0, 0, 1., 0, 0, 0, 0, 1.]
        hips_world = ident[:12] + [0., 1., 0., 1.]
        self.mapping = NS(source_nodes=nodes, neutral_world=[unity_from_gltf(ident), unity_from_gltf(hips_world)],
                          node_index=lambda t: nodes[object_id(t)])

    def test_bone_cloth_verbatim_with_its_whole_chain(self):
        cloth = self.f.component(self.hips, "MagicaCloth",
                                 **cloth_fields(1, roots=[self.hair], colliders=[self.capsule]))
        out = magica_cloth2_source(self.f.readers, self.mapping)
        ids = {t["id"]: t for t in out["transforms"]}
        sid = lambda t: str(object_id(t)[1])
        self.assertIn(sid(self.hair2), ids)                 # below the root: simulated, must be present
        self.assertIsNone(ids[sid(self.hair2)]["node"])
        self.assertEqual(ids[sid(self.hips)]["node"], 1)
        entry = next(c for c in out["components"] if c["class"] == "MagicaCloth")
        data = entry["fields"]["serializeData"]
        self.assertEqual(data["rootBones"], [{"transformId": sid(self.hair)}])
        self.assertEqual(data["colliderCollisionConstraint"]["colliderList"],
                         [{"transformId": sid(self.holder), "class": "MagicaCapsuleCollider"}])
        self.assertEqual(data["gravity"], .2)                # float32 written in its shortest form
        self.assertNotIn("m_Script", entry["fields"])
        self.assertEqual({c["class"] for c in out["components"]},
                         {"MagicaCloth", "MagicaCapsuleCollider", "ExtendClothSettings"})
        self.assertIsNotNone(cloth)

    def test_mesh_cloth_renderer_and_prebuild_are_resolved(self):
        f = self.f
        skirt = f.node("Skirt", self.root)
        mesh = f.obj("Mesh", m_Name="Skirt")
        renderer = f.obj("SkinnedMeshRenderer", m_GameObject=skirt.m_GameObject, m_Mesh=Ptr(mesh), m_Enabled=1)
        positions = struct.pack("<6f", 0, 1, 2, 3, 4, 5)
        share = NS(version=2, buildId="Extension_MagicaCloth_Skirt",
                   proxyMesh=NS(attributes=NS(count=2, length=2, arrayBytes=[1, 2]),
                                localPositions=NS(count=2, length=2, arrayBytes=list(positions)),
                                edges=list(struct.pack("<2i", 0, 1))),
                   renderSetupDataList=[NS(name="Skirt", vertexCount=2, originalMesh=Ptr(mesh),
                                           localPositions=[NS(x=0., y=0., z=0.)] * 2, boneWeightArray=[0] * 16)],
                   renderMeshList=[],
                   bendingConstraintData=NS(trianglePairArray=[11540877774880812, 2 ** 64 - 1]))
        other = NS(version=2, buildId="Extension_MagicaCloth_Other", proxyMesh=NS(), renderSetupDataList=[], renderMeshList=[])
        asset = f.obj("MonoBehaviour", m_Name="MagicaPreBuild_Test", m_GameObject=Ptr(),
                      m_Script=Ptr(f.obj("MonoScript", m_ClassName="PreBuildScriptableObject")),
                      sharePreBuildDataList=[other, share])
        prebuild = NS(enabled=1, buildId="Extension_MagicaCloth_Skirt", preBuildScriptableObject=Ptr(asset),
                      uniquePreBuildData=NS(version=2, renderSetupDataList=[NS(renderer=Ptr(renderer), transformList=[Ptr(self.hips)])]))
        f.component(self.hips, "MagicaCloth", **cloth_fields(0, renderers=[renderer], prebuild=prebuild))
        document = {"nodes": [{"name": "root"}, {"name": "Skirt Renderer", "mesh": 0}], "meshes": [{"name": "Skirt", "primitives": [{}]}]}
        out = magica_cloth2_source(f.readers, self.mapping, document)
        entry = next(c for c in out["components"] if c["class"] == "MagicaCloth")
        sid = lambda t: str(object_id(t)[1])
        self.assertEqual(entry["fields"]["serializeData"]["sourceRenderers"],
                         [{"transformId": sid(skirt), "class": "SkinnedMeshRenderer",
                           "mesh": {"name": "Skirt", "node": 1, "primitives": 1}}])
        build = entry["fields"]["serializeData2"]["preBuildData"]
        self.assertEqual(build["preBuildScriptableObject"], {"asset": "MagicaPreBuild_Test", "class": "PreBuildScriptableObject"})
        shared = build["sharePreBuildData"]
        self.assertEqual(shared["buildId"], "Extension_MagicaCloth_Skirt")
        pos = base64.b64decode(shared["proxyMesh"]["localPositions"]["arrayBytes"]["base64"])
        self.assertEqual(struct.unpack("<6f", pos), (0, 1, 2, 3, 4, 5))
        self.assertEqual(struct.unpack("<2i", base64.b64decode(shared["proxyMesh"]["edges"]["base64"])), (0, 1))
        # ulong pairs above 2^53 survive as little-endian uint64 bytes (a JSON number would round them)
        pairs = base64.b64decode(shared["bendingConstraintData"]["trianglePairArray"]["base64"])
        self.assertEqual(struct.unpack("<2Q", pairs), (11540877774880812, 2 ** 64 - 1))
        setup = shared["renderSetupDataList"][0]
        self.assertEqual(setup["originalMesh"], {"mesh": {"name": "Skirt", "node": 1, "primitives": 1}})
        self.assertNotIn("localPositions", setup)            # the mesh copy is left to the GLB
        self.assertNotIn("boneWeightArray", setup)
        self.assertEqual(build["uniquePreBuildData"]["renderSetupDataList"][0]["transformList"], [{"transformId": sid(self.hips)}])

    def test_mesh_cloth_without_prebuild_exports_the_original_mesh(self):
        f = self.f
        skirt = f.node("Skirt", self.root)
        ident = dict(e00=1., e01=0., e02=0., e03=0., e10=0., e11=1., e12=0., e13=0., e20=0., e21=0., e22=1., e23=0.,
                     e30=0., e31=0., e32=0., e33=1.)
        bind = dict(ident, e13=-1.)   # translation y = -1 (row 1, column 3)
        mesh = f.obj("Mesh", m_Name="Skirt", m_BindPose=[NS(**ident), NS(**bind)])
        renderer = f.obj("SkinnedMeshRenderer", m_GameObject=skirt.m_GameObject, m_Mesh=Ptr(mesh), m_Enabled=1,
                         m_Bones=[Ptr(self.root), Ptr(self.hips)], m_RootBone=Ptr(self.hips))
        f.component(self.hips, "MagicaCloth", **cloth_fields(0, renderers=[renderer]))

        class FakeHandler:   # UnityPy MeshHandler stand-in: decoded vertex channels
            def __init__(self, m):
                assert m is mesh
                self.m_Vertices = [(0., 1., 2.), (3., 4., 5.), (6., 7., 8.)]
                self.m_Normals = [(0., 1., 0.)] * 3
                self.m_Tangents = [(1., 0., 0., -1.)] * 3
                self.m_UV0 = [(.25, .5), (.5, .5), (.75, .5)]
                self.m_BoneIndices = [(1, 0, 0, 0), (1, 0, 0, 0), (0, 1, 0, 0)]
                self.m_BoneWeights = [(1., 0., 0., 0.), (1., 0., 0., 0.), (.75, .25, 0., 0.)]

            def process(self):
                pass

            def get_triangles(self):
                return [[(0, 1, 2)]]

        with patch("converter.common.source_magica.MeshHandler", FakeHandler):
            out = magica_cloth2_source(f.readers, self.mapping)
            out_none = magica_cloth2_source(f.readers, self.mapping, mesh_data="none")
        sid = lambda t: str(object_id(t)[1])
        ref = next(c for c in out["components"] if c["class"] == "MagicaCloth")["fields"]["serializeData"]["sourceRenderers"][0]
        md = ref["meshData"]

        def unpack(field, code):
            raw = base64.b64decode(field["base64"])
            return struct.unpack(f"<{len(raw) // 4}{code}", raw)

        self.assertEqual(md["vertexCount"], 3)
        self.assertEqual(unpack(md["vertices"], "f"), (0, 1, 2, 3, 4, 5, 6, 7, 8))
        self.assertEqual(unpack(md["tangents"], "f")[:4], (1, 0, 0, -1))
        self.assertEqual(unpack(md["uv"], "f")[:2], (.25, .5))
        self.assertEqual(unpack(md["boneIndices"], "i")[8:10], (0, 1))
        self.assertEqual(unpack(md["boneWeights"], "f")[8:10], (.75, .25))
        self.assertEqual(unpack(md["bindposes"], "f")[16 + 13], -1)   # column-major: column 3, row 1
        self.assertEqual(unpack(md["triangles"], "i"), (0, 1, 2))
        self.assertEqual(md["submeshTriangleCounts"], [1])
        self.assertEqual(md["bones"], [sid(self.root), sid(self.hips)])
        self.assertEqual(md["rootBone"], sid(self.hips))
        ref_none = next(c for c in out_none["components"] if c["class"] == "MagicaCloth")["fields"]["serializeData"]["sourceRenderers"][0]
        self.assertNotIn("meshData", ref_none)

    def test_prefab_without_enabled_magica_cloth_has_no_source_data(self):
        cloth = self.f.component(self.hips, "MagicaCloth", **cloth_fields(1, roots=[self.hair]))
        cloth.m_Enabled = 0
        self.assertIsNone(magica_cloth2_source(self.f.readers, self.mapping))


if __name__ == "__main__":
    unittest.main()
