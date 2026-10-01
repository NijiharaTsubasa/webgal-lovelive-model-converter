"""Resolve original LLAS face references without applying merge/runtime semantics."""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import UnityPy
from UnityPy.classes.PPtr import PPtr

from converter.common.unity import component_pointer, game_object_transform


@dataclass(frozen=True)
class MemberFaceSource:
    environment: Any
    root: Any  # The original member GameObject PPtr, suitable for the exporter.
    name: str
    manager: Any
    face: Any
    head: Any  # Original Transform objects; no reparenting or TRS changes.
    head_all: Any
    head_material: Any  # Original Material PPtr, not a copied/replaced material.
    face_root: Any
    needs_merging_face: bool
    face_source_path: Path
    cab_paths: dict[str, tuple[Path, ...]] | None


def _cab_name(name: str) -> str:
    return name.replace("\\", "/").rsplit("/", 1)[-1].lower()


def _is_component(pointer: Any, class_name: str) -> bool:
    if not pointer or pointer.type.name != "MonoBehaviour":
        return False
    script = pointer.read().m_Script.read()
    return script.m_ClassName == class_name and script.m_Namespace == "LLAS.Components.Members"


def _pointer(reader: Any, value: dict[str, int]) -> Any:
    return PPtr(m_FileID=value["m_FileID"], m_PathID=value["m_PathID"], assetsfile=reader.assets_file)


def _directory_snapshot(directory: Path) -> tuple[tuple[str, int, int], ...]:
    result = []
    for file in directory.iterdir():
        if file.is_file():
            stat = file.stat()
            result.append((file.name, stat.st_size, stat.st_mtime_ns))
    return tuple(sorted(result))


@lru_cache(maxsize=4)
def _cab_index(directory: str, snapshot: tuple[tuple[str, int, int], ...]) -> dict[str, tuple[Path, ...]]:
    """Index actual embedded CABs once per directory snapshot, without keeping environments."""
    index: dict[str, list[Path]] = {}
    for name, _, _ in snapshot:
        path = Path(directory) / name
        with path.open("rb") as stream:
            signature = stream.read(12)
        if not signature.startswith((b"UnityFS\0", b"UnityWeb\0", b"UnityRaw\0", b"UnityArchive\0")):
            continue
        environment = UnityPy.load(path.read_bytes())
        for asset in environment.assets:
            key = _cab_name(asset.name)
            if path not in index.setdefault(key, []):
                index[key].append(path)
    return {key: tuple(paths) for key, paths in index.items()}


def _load_face_dependency(environment: Any, source: Path, reader: Any, pointer: Any,
                          cab_paths: dict[str, tuple[Path, ...]] | None = None) -> Path:
    external_id = pointer.m_FileID - 1
    if external_id < 0 or external_id >= len(reader.assets_file.externals):
        raise ValueError(f"{source.name}: face has invalid external FileID {pointer.m_FileID}")
    cab = _cab_name(reader.assets_file.externals[external_id].path)
    if environment.get_cab(cab) is not None:
        return source

    if cab_paths is not None:
        candidates = cab_paths.get(cab, ())
        if len(candidates) != 1:
            if not candidates:
                raise FileNotFoundError(f"{source.name}: face dependency CAB {cab} is missing")
            raise ValueError(f"{source.name}: ambiguous face dependency CAB {cab}: {candidates}")
        candidate = candidates[0]
        environment.load_file(candidate.read_bytes(), name=str(candidate))
        if environment.get_cab(cab) is None:
            raise ValueError(f"{source.name}: dependency did not register expected face CAB {cab}")
        return candidate

    # Physical names are a fast way to locate declared dependencies, never the
    # identity check. Every result must register the precise CAB requested by face.
    dependencies = []
    for asset_reader in environment.objects:
        if asset_reader.type.name == "AssetBundle":
            dependencies.extend(getattr(asset_reader.read(), "m_Dependencies", []))
    local_files = {file.name.casefold(): file for file in source.parent.iterdir() if file.is_file()}
    for dependency in dict.fromkeys(dependencies):
        candidate = local_files.get(str(dependency).replace("\\", "/").rsplit("/", 1)[-1].casefold())
        if candidate is None or candidate == source:
            continue
        environment.load_file(candidate.read_bytes(), name=str(candidate))
        if environment.get_cab(cab) is not None:
            return candidate

    # Renamed bundles need structural discovery, not guessed character prefixes.
    index = _cab_index(str(source.parent), _directory_snapshot(source.parent))
    candidates = index.get(cab, ())
    if not candidates:
        raise FileNotFoundError(f"{source.name}: face dependency CAB {cab} is missing from {source.parent}")
    if len(candidates) != 1:
        raise ValueError(f"{source.name}: ambiguous face dependency CAB {cab}: {candidates}")
    environment.load_file(candidates[0].read_bytes(), name=str(candidates[0]))
    if environment.get_cab(cab) is None:
        raise ValueError(f"{source.name}: dependency did not register expected face CAB {cab}")
    return candidates[0]


def load_member_with_face(source: Path, *, cab_paths: dict[str, tuple[Path, ...]] | None = None) -> MemberFaceSource:
    """Load precise source objects; caller owns all subsequent face merge behavior.

    No metadata manifest is required. A face may be local or externally referenced;
    neither model names nor needsMergingFace are used to guess an asset association.
    """
    source = Path(source).resolve(strict=True)
    # Byte-backed readers leave no source-file handles alive with the returned
    # objects, which also permits callers to relocate their own input afterward.
    environment = UnityPy.Environment(source.read_bytes(), path=str(source.parent))
    roots = [pointer for name, pointer in environment.container.items()
             if name.lower().endswith("_member.prefab") and pointer.type.name == "GameObject"]
    if len(roots) != 1:
        raise ValueError(f"{source.name}: expected one original member root, got {len(roots)}")
    root = roots[0]
    member = root.read()
    managers = [pointer for entry in member.m_Component
                if _is_component(pointer := component_pointer(entry), "BodyPartManager")]
    if len(managers) != 1:
        raise ValueError(f"{source.name}: expected one root BodyPartManager, got {len(managers)}")
    manager = managers[0].read()
    reader = manager.object_reader
    fields = reader.read_typetree()
    pointers = {key: _pointer(reader, fields[key]) for key in ("face", "head", "headAll", "headMaterial")}
    face_pointer = pointers["face"]
    if not face_pointer.m_PathID:
        raise ValueError(f"{source.name}: BodyPartManager.face is null")
    face_source_path = source
    if face_pointer.m_FileID:
        face_source_path = _load_face_dependency(environment, source, reader, face_pointer, cab_paths)
    # This dereference checks PathID in the exact CAB, not merely a matching filename.
    try:
        face_reader = face_pointer.deref()
    except (KeyError, FileNotFoundError) as error:
        raise ValueError(f"{source.name}: face PathID {face_pointer.m_PathID} does not resolve in its declared CAB") from error
    if not _is_component(face_pointer, "MemberFace"):
        raise ValueError(f"{source.name}: BodyPartManager.face does not reference MemberFace")
    face = face_reader.read()
    merge = face_reader.read_typetree()["memberFaceData"]["needsMergingFace"]
    if merge not in (0, 1):
        raise ValueError(f"{source.name}: invalid needsMergingFace {merge!r}")
    for key in ("head", "headAll"):
        if pointers[key].type.name != "GameObject":
            raise ValueError(f"{source.name}: {key} must reference a GameObject")
    if pointers["headMaterial"].type.name != "Material":
        raise ValueError(f"{source.name}: headMaterial must reference a Material")
    return MemberFaceSource(environment, root, member.m_Name, manager, face,
                            game_object_transform(pointers["head"].read()),
                            game_object_transform(pointers["headAll"].read()),
                            pointers["headMaterial"], game_object_transform(face.m_GameObject.read()),
                            bool(merge), face_source_path, cab_paths)
