"""Discover LLAS bundles from their Unity contents, independent of disk names."""

from __future__ import annotations

from dataclasses import dataclass, field
from contextlib import closing
from functools import lru_cache
import hashlib
from pathlib import Path
import sqlite3

import UnityPy


UNITY_VERSION = "2018.4.23f1"
UNITY_SIGNATURES = (b"UnityFS\0", b"UnityWeb\0", b"UnityRaw\0", b"UnityArchive\0")
ASSET_TABLES = ("member_model", "navi_motion", "live_timeline",
                "shader", "navi_timeline", "skill_timeline")
SCAN_TABLES = frozenset(("member_model", "navi_motion", "live_timeline", "shader"))


@dataclass(frozen=True)
class SourceInventory:
    models: tuple[Path, ...]
    motions: tuple[Path, ...]
    model_names: dict[Path, str]
    motion_names: dict[Path, str]
    internal_names: dict[Path, str]
    cab_paths: dict[str, tuple[Path, ...]]
    dependencies: dict[Path, tuple[str, ...]] = field(default_factory=dict)
    external_cabs: dict[Path, tuple[str, ...]] = field(default_factory=dict)


@dataclass(frozen=True)
class BundleIndex:
    internal_names: dict[Path, str]
    dependencies: dict[Path, tuple[str, ...]]
    external_cabs: dict[Path, tuple[str, ...]]
    cab_paths: dict[str, tuple[Path, ...]]


def _external_cabs(environment: UnityPy.Environment) -> tuple[str, ...]:
    return tuple(dict.fromkeys(
        external.path.replace("\\", "/").rsplit("/", 1)[-1].casefold()
        for asset in environment.assets for external in asset.externals
    ))


def _bundle_info(environment: UnityPy.Environment, source: Path) -> tuple[str, tuple[str, ...]]:
    bundles = [reader.read() for reader in environment.objects if reader.type.name == "AssetBundle"]
    if len(bundles) != 1:
        raise ValueError(f"{source}: expected one nonempty internal AssetBundle name")
    name = str(bundles[0].m_Name).replace("\\", "/").rsplit("/", 1)[-1]
    if not name:
        raise ValueError(f"{source}: expected one nonempty internal AssetBundle name")
    dependencies = tuple(str(value).replace("\\", "/").rsplit("/", 1)[-1]
                         for value in getattr(bundles[0], "m_Dependencies", ()))
    return name, dependencies


def _safe_resource_name(internal: str, source: Path) -> str:
    name = internal.removesuffix(".unity3d")
    if name in ("", ".", "..") or Path(name).name != name or "/" in name or "\\" in name:
        raise ValueError(f"{source}: invalid internal resource name {internal!r}")
    return name


def _scan_candidates(root: Path, files: list[Path]) -> tuple[list[Path], dict[Path, str]]:
    """Use the original asset DB as a reproducible search index when possible.

    The AB contents, not the table name, still determine whether a candidate
    is a model or skeletal motion. Unnamed or independently renamed bundles
    fall back to a full structural scan.
    """
    database = root / "db/asset_a_ja.db"
    if not database.is_file() and root.name in ("raw", "character", "motion"):
        database = root.parent / "db/asset_a_ja.db"
    if not database.is_file():
        return files, {}
    with closing(sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True)) as db:
        tables = {name for (name,) in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if not set(ASSET_TABLES) <= tables:
            return files, {}
        identities: dict[tuple[str, int], str] = {}
        for table in ASSET_TABLES:
            for pack, offset in db.execute(f"SELECT pack_name, head FROM {table}"):
                identity = (pack, offset)
                if identity in identities:
                    return files, {}
                identities[identity] = table

    selected: list[Path] = []
    tables_by_path: dict[Path, str] = {}
    for source in files:
        with source.open("rb") as stream:
            if not stream.read(16).startswith(UNITY_SIGNATURES):
                continue
        pack, separator, offset = source.stem.rpartition("__")
        if not separator or not offset.isdecimal():
            return files, {}
        table = identities.get((pack, int(offset)))
        if table is None:
            return files, {}
        if table in SCAN_TABLES:
            selected.append(source)
            tables_by_path[source] = table
    print(f"[llas:scan] original asset DB narrowed {len(files)} paths to {len(selected)} candidates", flush=True)
    return selected, tables_by_path


@lru_cache(maxsize=4)
def scan_sources(root: Path, exclude: tuple[Path, ...] = ()) -> SourceInventory:
    root = root.resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"LLAS input directory missing: {root}")
    UnityPy.config.FALLBACK_UNITY_VERSION = UNITY_VERSION
    models: list[Path] = []
    motions: list[Path] = []
    model_names: dict[Path, str] = {}
    motion_names: dict[Path, str] = {}
    internal_names: dict[Path, str] = {}
    cab_paths: dict[str, list[Path]] = {}
    dependencies: dict[Path, tuple[str, ...]] = {}
    external_cabs: dict[Path, tuple[str, ...]] = {}
    excluded = tuple(path.resolve() for path in exclude)
    files = sorted(path for path in root.rglob("*") if path.is_file()
                   and not any(path.is_relative_to(directory) for directory in excluded))
    files, tables_by_path = _scan_candidates(root, files)
    for index, source in enumerate(files, 1):
        if index % 100 == 0 or index == len(files):
            print(f"[llas:scan] {index}/{len(files)} files", flush=True)
        with source.open("rb") as stream:
            if not stream.read(16).startswith(UNITY_SIGNATURES):
                continue
            stream.seek(0)
            # Keep the source open only while UnityPy resolves its lazy objects.
            # A path-backed environment retains the handle on Windows.
            environment = UnityPy.load(stream)
            if not any(reader.type.name == "AssetBundle" for reader in environment.objects):
                continue
            internal, declared_dependencies = _bundle_info(environment, source)
            internal_names[source] = internal
            dependencies[source] = declared_dependencies
            external_cabs[source] = _external_cabs(environment)
            for asset in environment.assets:
                cab = asset.name.replace("\\", "/").rsplit("/", 1)[-1].casefold()
                if source not in cab_paths.setdefault(cab, []):
                    cab_paths[cab].append(source)
            table = tables_by_path.get(source)
            if table == "member_model":
                if internal.casefold().endswith("_member.prefab.unity3d"):
                    name = internal[:-len(".prefab.unity3d")]
                    models.append(source)
                    model_names[source] = name
            elif table in ("navi_motion", "live_timeline"):
                # Navi clips use an AB name ending .unity3d without .anim;
                # live performance clips use .fbx.unity3d. Both channels must
                # actually carry an AnimationClip object.
                expected = (internal.casefold().endswith(".unity3d")
                            if table == "navi_motion" else internal.casefold().endswith(".fbx.unity3d"))
                if expected and any(reader.type.name == "AnimationClip"
                                    for reader in environment.objects):
                    motions.append(source)
                    motion_names[source] = _safe_resource_name(internal, source)
            elif table is None:
                member_roots = [
                    pointer for name, pointer in environment.container.items()
                    if name.casefold().endswith("_member.prefab") and pointer.type.name == "GameObject"
                ]
                if member_roots:
                    if len(member_roots) != 1:
                        raise ValueError(f"{source}: multiple member prefab roots")
                    name = str(member_roots[0].read().m_Name)
                    models.append(source)
                    model_names[source] = name
                if any(name.casefold().endswith((".anim", ".fbx"))
                       for name in environment.container) and any(
                    reader.type.name == "AnimationClip"
                    and reader.read_typetree().get("m_MuscleClipSize", 0) > 0
                    for reader in environment.objects
                ):
                    motions.append(source)
                    motion_names[source] = _safe_resource_name(internal, source)
    for kind, names in (("model", model_names), ("motion", motion_names)):
        values = list(names.values())
        if len(values) != len(set(values)):
            raise ValueError(f"Duplicate LLAS {kind} identity in {root}")
    return SourceInventory(
        tuple(sorted(models, key=lambda path: model_names[path])),
        tuple(sorted(motions, key=lambda path: motion_names[path])),
        model_names, motion_names, internal_names,
        {cab: tuple(paths) for cab, paths in cab_paths.items()},
        dependencies, external_cabs,
    )


def scan_bundle_index(root: Path, exclude: tuple[Path, ...] = ()) -> BundleIndex:
    """Index every original Unity AB for self-contained classified copies.

    The asset DB is intentionally not required here: manually decrypted input
    may be arbitrarily named and may not include any database.
    """
    root = root.resolve()
    excluded = tuple(path.resolve() for path in exclude)
    UnityPy.config.FALLBACK_UNITY_VERSION = UNITY_VERSION
    internal_names: dict[Path, str] = {}
    dependencies: dict[Path, tuple[str, ...]] = {}
    external_cabs: dict[Path, tuple[str, ...]] = {}
    cab_paths: dict[str, list[Path]] = {}
    files = sorted(path for path in root.rglob("*") if path.is_file()
                   and not any(path.is_relative_to(directory) for directory in excluded))
    for index, source in enumerate(files, 1):
        if index % 500 == 0 or index == len(files):
            print(f"[llas:classify] indexing {index}/{len(files)} files", flush=True)
        with source.open("rb") as stream:
            if not stream.read(16).startswith(UNITY_SIGNATURES):
                continue
            stream.seek(0)
            environment = UnityPy.load(stream)
            bundles = [reader for reader in environment.objects if reader.type.name == "AssetBundle"]
            if not bundles:
                continue
            internal, declared_dependencies = _bundle_info(environment, source)
            internal_names[source] = internal
            dependencies[source] = declared_dependencies
            external_cabs[source] = _external_cabs(environment)
            for asset in environment.assets:
                cab = asset.name.replace("\\", "/").rsplit("/", 1)[-1].casefold()
                if source not in cab_paths.setdefault(cab, []):
                    cab_paths[cab].append(source)
    return BundleIndex(internal_names, dependencies, external_cabs,
                       {key: tuple(paths) for key, paths in cab_paths.items()})


def motion_kind(inventory: SourceInventory, source: Path) -> str:
    if source not in inventory.motions:
        raise ValueError(f"{source}: not a discovered LLAS skeletal motion")
    return "live" if inventory.internal_names[source].casefold().endswith(".fbx.unity3d") else "navi"


@lru_cache(maxsize=2)
def active_sources(input_root: Path) -> SourceInventory:
    """Prefer manually curated inputs; otherwise discover unclassified inputs."""
    input_root = input_root.resolve()
    try:
        input_root.stat()
    except FileNotFoundError:
        return SourceInventory((), (), {}, {}, {}, {})
    character_dir = input_root / "character"
    motion_dir = input_root / "motion"
    characters = scan_sources(character_dir) if character_dir.is_dir() else None
    motions = scan_sources(motion_dir) if motion_dir.is_dir() else None
    if not ((characters and characters.models) or (motions and motions.motions)):
        return scan_sources(input_root, (character_dir, motion_dir))

    selected_models = characters.models if characters else ()
    selected_motions = motions.motions if motions else ()
    if characters and characters.motions:
        raise ValueError("LLAS character directory contains skeletal motions; put them in motion")
    if motions and motions.models:
        raise ValueError("LLAS motion directory contains member models; put them in character")
    inventories = tuple(value for value in (characters, motions) if value is not None)
    cab_paths: dict[str, list[Path]] = {}
    for inventory in inventories:
        for cab, paths in inventory.cab_paths.items():
            cab_paths.setdefault(cab, []).extend(paths)
    for cab, paths in cab_paths.items():
        if len(paths) <= 1:
            continue
        hashes = {hashlib.sha256(path.read_bytes()).digest() for path in paths}
        if len(hashes) == 1:
            cab_paths[cab] = [sorted(paths)[0]]

    return SourceInventory(
        selected_models, selected_motions,
        {path: name for inventory in inventories for path, name in inventory.model_names.items()
         if path in selected_models},
        {path: name for inventory in inventories for path, name in inventory.motion_names.items()
         if path in selected_motions},
        {path: name for inventory in inventories for path, name in inventory.internal_names.items()},
        {cab: tuple(paths) for cab, paths in cab_paths.items()},
        {path: deps for inventory in inventories for path, deps in inventory.dependencies.items()},
        {path: cabs for inventory in inventories for path, cabs in inventory.external_cabs.items()},
    )
