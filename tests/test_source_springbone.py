"""physics.source.unitySpringBone export (verbatim UnityChan SpringBone), with tiny source-shaped fixtures."""

import math
import unittest
from types import SimpleNamespace as NS

from converter.common.physics import extract_model_physics
from converter.common.source_springbone import unity_springbone_source, _unity_from_gltf
from converter.common.unity import object_id


def vec(x=0., y=0., z=0.):
    return NS(x=x, y=y, z=z)


def quat(x=0., y=0., z=0., w=1.):
    return NS(x=x, y=y, z=z, w=w)


class Ptr:
    def __init__(self, value, kind):
        self.value, self.type = value, NS(name=kind)

    def __bool__(self):
        return self.value is not None

    def read(self):
        return self.value

    def deref_parse_as_object(self):
        return self.value


class Fixture:
    def __init__(self):
        self.asset = object()
        self.readers = []
        self.next_pid = 1000

    def _reader(self, obj, kind, typetree=None):
        pid = self.next_pid
        self.next_pid += 1
        obj.object_reader = NS(assets_file=self.asset, path_id=pid)
        self.readers.append(NS(type=NS(name=kind), path_id=pid, read=lambda: obj,
                               read_typetree=lambda: typetree() if callable(typetree) else typetree))
        return obj

    def node(self, name, parent=None, position=(0., 0., 0.), rotation=(0., 0., 0., 1.)):
        t = NS(m_LocalPosition=vec(*position), m_LocalRotation=quat(*rotation), m_LocalScale=vec(1, 1, 1),
               m_Father=Ptr(parent, "Transform"), m_Children=[])
        go = NS(m_Name=name, m_Component=[(0, Ptr(t, "Transform"))])
        t.m_GameObject = Ptr(go, "GameObject")
        if parent is not None:
            parent.m_Children.append(Ptr(t, "Transform"))
        return self._reader(t, "Transform")

    def component(self, node, cls, **fields):
        obj = NS(m_Script=Ptr(NS(m_ClassName=cls), "MonoScript"), m_Enabled=fields.get("m_Enabled", 1),
                 m_GameObject=node.m_GameObject, collideWithGround=0)
        tree = {"m_GameObject": {"m_FileID": 0, "m_PathID": 1}, "m_Script": {"m_FileID": 0, "m_PathID": 2},
                "m_Name": "", "m_Enabled": 1, **fields}
        self._reader(obj, "MonoBehaviour", tree)
        node.m_GameObject.read().m_Component.append((0, Ptr(obj, "MonoBehaviour")))
        return obj


def pptr(obj):
    return {"m_FileID": 0, "m_PathID": object_id(obj)[1]}


def unity_trs(position, rotation):   # column-major Unity matrix
    x, y, z, w = rotation
    r = [[1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)],
         [2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)],
         [2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)]]
    return [r[0][0], r[1][0], r[2][0], 0, r[0][1], r[1][1], r[2][1], 0, r[0][2], r[1][2], r[2][2], 0, *position, 1]


def mul(a, b):
    return [sum(a[k * 4 + r] * b[c * 4 + k] for k in range(4)) for c in range(4) for r in range(4)]


class SourceSpringBoneTests(unittest.TestCase):
    def build(self):
        f = Fixture()
        root = f.node("root")
        hips = f.node("Hips", root, (0, 1, 0))
        bone = f.node("SP_Skirt_01", hips, (0, -.1, .1))
        tip = f.node("SP_Skirt_02", bone, (0, -.2, 0))
        pivot = f.node("Extension_SP_Skirt_01_Pivot", hips, (0, -.1, .1), (0, .7071068, 0, .7071068))
        holder = f.node("Extension_Capsule", hips, (.1, 0, 0))
        capsule = f.component(holder, "SpringCapsuleCollider", radius=.08, height=.3, linkedRenderer={"m_FileID": 0, "m_PathID": 0})
        f.component(pivot, "SpringBonePivot", springType=1)
        spring = f.component(bone, "SpringBone", stiffnessForce=.01, dragForce=.4, radius=.03,
                             pivotNode=pptr(pivot), capsuleColliders=[pptr(capsule)], sphereColliders=[], panelColliders=[],
                             yAngleLimits={"active": 1, "min": -30, "max": 0})
        f.component(root, "SpringManager", simulationFrameRate=30, gravity={"x": 0, "y": -10, "z": 0},
                    springBones=[pptr(spring)])
        # GLB: everything but the pivot / collider holder; neutral pose turns the hips 90 deg about Y
        exported = [root, hips, bone, tip]
        turn = (0, math.sin(math.pi / 4), 0, math.cos(math.pi / 4))
        world = {}
        world[id(root)] = unity_trs((0, 0, 0), (0, 0, 0, 1))
        world[id(hips)] = mul(world[id(root)], unity_trs((0, 1, 0), turn))
        world[id(bone)] = mul(world[id(hips)], unity_trs((0, -.1, .1), (0, 0, 0, 1)))
        world[id(tip)] = mul(world[id(bone)], unity_trs((0, -.2, 0), (0, 0, 0, 1)))
        source_nodes = {object_id(t): i for i, t in enumerate(exported)}
        mapping = NS(source_nodes=source_nodes, neutral_world=[_unity_from_gltf(world[id(t)]) for t in exported],
                     node_index=lambda t: source_nodes[object_id(t)] + 10)
        return f, mapping, dict(root=root, hips=hips, bone=bone, tip=tip, pivot=pivot, holder=holder, turn=turn)

    def test_family_exported_verbatim_with_transform_references(self):
        f, mapping, n = self.build()
        out = unity_springbone_source(f.readers, mapping)
        sid = lambda t: str(object_id(t)[1])
        transforms = {t["id"]: t for t in out["transforms"]}
        self.assertEqual(set(transforms), {sid(t) for t in n.values() if not isinstance(t, tuple)})
        self.assertEqual(transforms[sid(n["bone"])]["node"], 12)
        self.assertIsNone(transforms[sid(n["pivot"])]["node"])
        self.assertEqual(transforms[sid(n["bone"])]["parentId"], sid(n["hips"]))
        self.assertIsNone(transforms[sid(n["root"])]["parentId"])
        spring = next(c for c in out["components"] if c["class"] == "SpringBone")
        self.assertEqual(spring["transformId"], sid(n["bone"]))
        self.assertEqual(spring["fields"]["pivotNode"], {"transformId": sid(n["pivot"])})
        self.assertEqual(spring["fields"]["capsuleColliders"], [{"transformId": sid(n["holder"])}])
        self.assertEqual(spring["fields"]["yAngleLimits"], {"active": 1, "min": -30, "max": 0})
        self.assertNotIn("m_Script", spring["fields"])
        self.assertNotIn("m_GameObject", spring["fields"])
        capsule = next(c for c in out["components"] if c["class"] == "SpringCapsuleCollider")
        self.assertIsNone(capsule["fields"]["linkedRenderer"])
        manager = next(c for c in out["components"] if c["class"] == "SpringManager")
        self.assertEqual(manager["fields"]["springBones"], [{"transformId": sid(n["bone"])}])

    def test_transforms_describe_the_exported_rest_pose(self):
        f, mapping, n = self.build()
        transforms = {t["id"]: t for t in unity_springbone_source(f.readers, mapping)["transforms"]}
        hips = transforms[str(object_id(n["hips"])[1])]
        # neutral pose (from the bake), not the serialized prefab rotation
        for a, b in zip(hips["localRotation"], n["turn"]):
            self.assertAlmostEqual(abs(a), abs(b), places=6)
        self.assertAlmostEqual(hips["localPosition"][1], 1.)
        bone = transforms[str(object_id(n["bone"])[1])]
        for a, b in zip(bone["localPosition"], (0, -.1, .1)):
            self.assertAlmostEqual(a, b)
        # absent from the GLB: serialized local transform under its (posed) parent
        pivot = transforms[str(object_id(n["pivot"])[1])]
        self.assertEqual(pivot["localRotation"], [0, .7071068, 0, .7071068])

    def test_prefab_without_enabled_manager_has_no_source_data(self):
        f, mapping, n = self.build()
        for reader in f.readers:
            obj = reader.read()
            if getattr(obj, "m_Script", None) and obj.m_Script.read().m_ClassName == "SpringManager":
                obj.m_Enabled = 0
        self.assertIsNone(unity_springbone_source(f.readers, mapping))

    def test_extract_model_physics_uses_source_data_instead_of_generic_springs(self):
        f, mapping, n = self.build()
        mapping.canonical_world = [unity_trs((0, 0, 0), (0, 0, 0, 1))] * 20
        mapping.source_world = mapping.neutral_world
        result = extract_model_physics(NS(objects=f.readers), NS(node_mapping=mapping, standard_bones={}),
                                       source_springbone=True)
        self.assertEqual(result["springs"], [])
        self.assertIn("unitySpringBone", result["source"])
        self.assertEqual(len(result["source"]["unitySpringBone"]["components"]), 4)


if __name__ == "__main__":
    unittest.main()
