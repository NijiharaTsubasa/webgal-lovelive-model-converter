"""Conversion-time MagicaCloth2 build (converter/common/magica_prebuild.py), with the Node.js tool mocked."""

import io
import json
import unittest
from contextlib import redirect_stdout
from types import SimpleNamespace as NS
from unittest.mock import patch

from converter.common.magica_prebuild import prebuild_magica_cloth2


def physics():
    renderer = {"transformId": 5, "class": "SkinnedMeshRenderer", "mesh": {"name": "skirt"}, "meshData": {"vertexCount": 3}}
    return {"source": {"magicaCloth2": {"transforms": [], "components": [
        {"class": "MagicaCapsuleCollider", "transformId": 2, "fields": {}},
        {"class": "MagicaCloth", "transformId": 3, "fields": {"serializeData": {"clothType": 0, "sourceRenderers": [renderer, None]}}},
        {"class": "MagicaCloth", "transformId": 4, "fields": {"serializeData": {"clothType": 1}}},
        {"class": "MagicaCloth", "transformId": 6, "fields": {"serializeData": {"clothType": 0, "sourceRenderers": [dict(renderer)]}}},
    ]}}}


def node_result(stdout=b"", returncode=0, stderr=b""):
    return NS(returncode=returncode, stdout=stdout, stderr=stderr)


class MagicaPrebuildTest(unittest.TestCase):
    def test_stores_runtime_prebuild_and_drops_mesh_data_of_built_cloths(self):
        data = physics()
        output = {"report": [
            {"transformId": 3, "clothType": 0, "status": "built"},
            {"transformId": 4, "clothType": 1, "status": "built"},
            {"transformId": 6, "clothType": 0, "status": "error", "error": "MagicaCloth2: paint-map selection is not supported"},
        ], "components": {"1": {"version": 1, "sharePreBuildData": {"a": 1}}, "2": {"version": 1, "sharePreBuildData": {"b": 2}}}}
        with patch("converter.common.magica_prebuild.subprocess.run", return_value=node_result(json.dumps(output).encode())) as run, \
                redirect_stdout(io.StringIO()) as log:
            counts = prebuild_magica_cloth2(data, "costume")
        self.assertEqual(counts, {"built": 2, "error": 1})
        sent = json.loads(run.call_args.kwargs["input"].decode("utf-8"))
        self.assertEqual(sent, physics()["source"]["magicaCloth2"])
        components = data["source"]["magicaCloth2"]["components"]
        self.assertNotIn("runtimePreBuild", components[0])
        self.assertEqual(components[1]["runtimePreBuild"], {"version": 1, "sharePreBuildData": {"a": 1}})
        self.assertNotIn("meshData", components[1]["fields"]["serializeData"]["sourceRenderers"][0])
        self.assertEqual(components[2]["runtimePreBuild"]["sharePreBuildData"], {"b": 2})
        self.assertNotIn("runtimePreBuild", components[3])                       # failed: keeps meshData
        self.assertIn("meshData", components[3]["fields"]["serializeData"]["sourceRenderers"][0])
        self.assertIn("paint-map", log.getvalue())

    def test_without_node_or_renderer_support_the_data_stays_buildable(self):
        for side_effect in (FileNotFoundError("node"), None):
            data = physics()
            failed = node_result(returncode=1, stderr=b"Error [ERR_MODULE_NOT_FOUND]: Cannot find module prebuild.js")
            with patch("converter.common.magica_prebuild.subprocess.run", side_effect=side_effect, return_value=failed), \
                    redirect_stdout(io.StringIO()) as log:
                self.assertEqual(prebuild_magica_cloth2(data, "costume"), {})
            self.assertEqual(data, physics())
            self.assertIn("WARNING", log.getvalue())

    def test_models_without_magica_cloth_do_not_run_node(self):
        with patch("converter.common.magica_prebuild.subprocess.run") as run:
            self.assertEqual(prebuild_magica_cloth2(None, "costume"), {})
            self.assertEqual(prebuild_magica_cloth2({"bones": []}, "costume"), {})
            only_colliders = {"source": {"magicaCloth2": {"components": [{"class": "MagicaSphereCollider"}]}}}
            self.assertEqual(prebuild_magica_cloth2(only_colliders, "costume"), {})
        run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
