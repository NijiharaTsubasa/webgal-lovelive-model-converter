"""Conversion-time MagicaCloth2 build: runs the renderer's port of the game's runtime build once, here, instead of
every time a model loads.

The game builds a MagicaCloth without (usable) PreBuild data at Start; the renderer does the same from the transform
table (BoneCloth) and from sourceRenderers[i].meshData (MeshCloth), which costs 150-220 ms per costume on a cold
start.  tools/prebuild-magica-cloth2.mjs runs that build with the renderer dependency
(webgal-lovelive-gltf-renderer/magica-cloth2/prebuild.js) and returns, per built cloth, "runtimePreBuild": the build
results in the encoding of the game's PreBuild data (renderer docs/model_physics_spec.md).  They are stored on the
MagicaCloth component, and a built MeshCloth's renderers drop "meshData", which only the build needs.

When Node.js or a renderer with prebuild.js is missing, the model keeps its meshData and the renderer builds at
load time, as before; a warning says so.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

TOOL = Path(__file__).resolve().parents[2] / "tools" / "prebuild-magica-cloth2.mjs"


def prebuild_magica_cloth2(physics: dict[str, Any] | None, label: str, *, node: str = "node") -> dict[str, int]:
    """Add runtimePreBuild to physics.source.magicaCloth2 in place; returns the number of cloths per status."""
    source = ((physics or {}).get("source") or {}).get("magicaCloth2")
    if not source or not any(c.get("class") == "MagicaCloth" for c in source.get("components", [])):
        return {}
    try:
        result = subprocess.run([node, str(TOOL)], cwd=TOOL.parents[1], check=False, capture_output=True,
                                input=json.dumps(source, ensure_ascii=False).encode("utf-8"))
    except OSError as error:
        print(f"[magica:prebuild] WARNING: {label}: cannot run Node.js ({error}); cloths are built at load time",
              flush=True)
        return {}
    if result.returncode:
        message = result.stderr.decode("utf-8", "replace").strip().splitlines()
        print(f"[magica:prebuild] WARNING: {label}: prebuild failed ({message[-1] if message else result.returncode});"
              f" cloths are built at load time", flush=True)
        return {}
    output = json.loads(result.stdout.decode("utf-8"))
    components = source["components"]
    for index, runtime_prebuild in output["components"].items():
        component = components[int(index)]
        component["runtimePreBuild"] = runtime_prebuild
        for renderer in component["fields"]["serializeData"].get("sourceRenderers") or []:
            if isinstance(renderer, dict):
                renderer.pop("meshData", None)
    counts: dict[str, int] = {}
    for entry in output["report"]:
        counts[entry["status"]] = counts.get(entry["status"], 0) + 1
        if entry["status"] == "error":
            print(f"[magica:prebuild] WARNING: {label}: MagicaCloth on transform {entry['transformId']}: "
                  f"{entry['error']}", flush=True)
    return counts
