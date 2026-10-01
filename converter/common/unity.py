from __future__ import annotations

import re
import zlib
from collections import deque
from pathlib import Path
from typing import Any

import UnityPy


COMPONENT_FLOAT = 5126
COMPONENT_UNSIGNED_BYTE = 5121
COMPONENT_UNSIGNED_SHORT = 5123
COMPONENT_UNSIGNED_INT = 5125


def safe_name(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())
    return value.strip("._") or "unnamed"


def logical_name(path: Path) -> str:
    return path.name.removesuffix(".assetbundle").lower()


def crc(value: str) -> int:
    return zlib.crc32(value.encode("utf-8")) & 0xFFFFFFFF


def pointer_id(pointer: Any) -> tuple[int, int]:
    assets_file = pointer.assetsfile
    return id(assets_file), pointer.m_PathID


def object_id(obj: Any) -> tuple[int, int]:
    reader = obj.object_reader
    return id(reader.assets_file), reader.path_id


def component_pointer(entry: Any) -> Any:
    return entry[1] if isinstance(entry, tuple) else entry.component


def game_object_transform(game_object: Any) -> Any:
    for entry in game_object.m_Component:
        pointer = component_pointer(entry)
        if pointer and pointer.type.name in {"Transform", "RectTransform"}:
            return pointer.deref_parse_as_object()
    raise ValueError(f"GameObject {game_object.m_Name!r} has no Transform")


def bundle_metadata(path: Path) -> tuple[str, list[str]]:
    env = UnityPy.load(str(path))
    for obj in env.objects:
        if obj.type.name == "AssetBundle":
            data = obj.read()
            return (
                getattr(data, "m_AssetBundleName", "") or logical_name(path),
                list(getattr(data, "m_Dependencies", [])),
            )
    return logical_name(path), []


def dependency_closure(start: Path, index: dict[str, Path]) -> list[Path]:
    """Walk the AssetBundle dependency graph from `start` and return all bundles
    reachable by name, in BFS order."""
    result: list[Path] = []
    seen: set[str] = set()
    queue = deque([logical_name(start)])
    while queue:
        name = queue.popleft().lower()
        if name in seen:
            continue
        seen.add(name)
        path = index.get(name)
        if not path:
            raise FileNotFoundError(f"AssetBundle dependency not found: {name}")
        result.append(path)
        _, dependencies = bundle_metadata(path)
        queue.extend(dependency.lower() for dependency in dependencies)
    return result


def vec3(value: Any, reflect: bool = False) -> list[float]:
    return [-float(value.x), float(value.y), float(value.z)] if reflect else [float(value.x), float(value.y), float(value.z)]


def rotation(value: Any) -> list[float]:
    return [float(value.x), -float(value.y), -float(value.z), float(value.w)]


def matrix(value: Any) -> list[float]:
    rows = [
        [value.e00, value.e01, value.e02, value.e03],
        [value.e10, value.e11, value.e12, value.e13],
        [value.e20, value.e21, value.e22, value.e23],
        [value.e30, value.e31, value.e32, value.e33],
    ]
    signs = [-1.0, 1.0, 1.0, 1.0]
    return [float(rows[row][column] * signs[row] * signs[column]) for column in range(4) for row in range(4)]


def controller_clip_objects(controller_obj: Any, tree: dict[str, Any]) -> list[Any]:
    """Resolve the AnimatorController's m_AnimationClips (frequently external
    references into sibling .anim bundles) into read AnimationClip objects,
    preserving the controller's order. Pure Unity primitive — Animator allows
    clip references both inline (m_FileID == 0) and external (m_FileID > 0,
    pointing at a sibling CAB listed in assets_file.externals)."""
    environment = controller_obj.assets_file.environment
    assets_by_name: dict[str, Any] = {}
    for asset in environment.assets:
        assets_by_name[Path(asset.name).name] = asset
    externals = controller_obj.assets_file.externals
    result: list[Any] = []
    for pointer in tree.get("m_AnimationClips", []):
        file = int(pointer.get("m_FileID", 0))
        path_id = int(pointer.get("m_PathID", 0))
        asset: Any = controller_obj.assets_file if file == 0 else None
        if file != 0 and 0 <= file - 1 < len(externals):
            asset = assets_by_name.get(Path(externals[file - 1].name).name)
        obj = asset.objects.get(path_id) if asset is not None else None
        if obj is None:
            raise ValueError(
                f"AnimatorController clip reference could not be resolved: "
                f"file={file}, path={path_id}"
            )
        result.append(obj.read())
    return result
