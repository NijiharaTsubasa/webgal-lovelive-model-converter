"""Copy LLAS model/motion bundles and their AB dependencies into curated input."""

from __future__ import annotations

import argparse
import hashlib
import shutil
from pathlib import Path

from converter.llas.source_inventory import (
    BundleIndex, active_sources, motion_kind, scan_bundle_index, scan_sources,
)


CATEGORIES = ("model", "navi", "live")
UNITY_BUILTIN_CABS = frozenset(("unity_builtin_extra", "unity default resources"))


def _digest(path: Path) -> bytes:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.digest()


def _choose(candidates: tuple[Path, ...], owner: Path, identity: str,
            digests: dict[Path, bytes]) -> Path:
    if not candidates:
        raise FileNotFoundError(f"{owner}: missing LLAS dependency {identity}")
    if len(candidates) == 1:
        return candidates[0]
    signatures = set()
    for path in candidates:
        if path not in digests:
            digests[path] = _digest(path)
        signatures.add(digests[path])
    if len(signatures) == 1:
        return sorted(candidates)[0]
    raise ValueError(f"{owner}: ambiguous LLAS dependency {identity}: {candidates}")


def _closure(sources: list[Path], index: BundleIndex) -> set[Path]:
    by_name: dict[str, list[Path]] = {}
    for path, name in index.internal_names.items():
        by_name.setdefault(name.casefold(), []).append(path)
    own_cabs: dict[Path, set[str]] = {}
    for cab, paths in index.cab_paths.items():
        for path in paths:
            own_cabs.setdefault(path, set()).add(cab)
    digests: dict[Path, bytes] = {}
    result: set[Path] = set()
    pending = list(sources)
    while pending:
        source = pending.pop()
        if source in result:
            continue
        if source not in index.internal_names:
            raise ValueError(f"{source}: selected bundle was not indexed")
        result.add(source)
        external = (set(index.external_cabs[source]) - own_cabs.get(source, set())
                    - UNITY_BUILTIN_CABS)
        for name in index.dependencies[source]:
            candidates = tuple(by_name.get(name.casefold(), ()))
            if len(candidates) > 1 and external:
                matched = tuple(path for path in candidates if own_cabs.get(path, set()) & external)
                if matched:
                    candidates = matched
            pending.append(_choose(candidates, source, name, digests))
        for cab in external:
            pending.append(_choose(index.cab_paths.get(cab, ()), source, cab, digests))
    return result


def _copy_plan(sources: set[Path], destination: Path) -> dict[Path, Path]:
    by_name: dict[str, Path] = {}
    digests: dict[Path, bytes] = {}
    plan: dict[Path, Path] = {}
    for source in sorted(sources):
        prior = by_name.get(source.name.casefold())
        if prior is not None:
            if digests.setdefault(prior, _digest(prior)) != digests.setdefault(source, _digest(source)):
                raise ValueError(f"different LLAS bundles share destination filename: {prior}, {source}")
            continue
        by_name[source.name.casefold()] = source
        target = destination / source.name
        if target.exists() and _digest(target) != digests.setdefault(source, _digest(source)):
            raise FileExistsError(f"{target}: existing classified input differs from {source}")
        if not target.exists():
            plan[source] = target
    return plan


def classify(source_root: Path, input_root: Path, categories: set[str]) -> dict[str, int]:
    if not categories or not categories <= set(CATEGORIES):
        raise ValueError(f"categories must be selected from {CATEGORIES}")
    source_root = source_root.resolve(strict=True)
    input_root = input_root.resolve()
    character_dir = input_root / "character"
    motion_dir = input_root / "motion"
    excluded = (character_dir, motion_dir)
    if source_root.is_relative_to(character_dir) or source_root.is_relative_to(motion_dir):
        raise ValueError("source must not be a curated character or motion directory")
    inventory = scan_sources(source_root, excluded)
    selected_models = list(inventory.models) if "model" in categories else []
    selected_motions = [path for path in inventory.motions
                        if motion_kind(inventory, path) in categories]
    if not selected_models and not selected_motions:
        raise FileNotFoundError(f"no LLAS inputs match {sorted(categories)} in {source_root}")
    index = scan_bundle_index(source_root, excluded)
    character_files = _closure(selected_models, index) if selected_models else set()
    motion_files = _closure(selected_motions, index) if selected_motions else set()
    character_plan = _copy_plan(character_files, character_dir)
    motion_plan = _copy_plan(motion_files, motion_dir)
    for source, destination in (*character_plan.items(), *motion_plan.items()):
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_name(destination.name + ".part")
        if temporary.exists():
            raise FileExistsError(f"temporary copy already exists: {temporary}")
        try:
            shutil.copyfile(source, temporary)
            temporary.replace(destination)
        finally:
            temporary.unlink(missing_ok=True)
    scan_sources.cache_clear()
    active_sources.cache_clear()
    return {"models": len(selected_models), "motions": len(selected_motions),
            "character_bundles": len(character_files), "motion_bundles": len(motion_files),
            "copied": len(character_plan) + len(motion_plan)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("input_llas"),
                        help="LLAS input root containing optional db, character and motion directories")
    parser.add_argument("--source", type=Path,
                        help="Directory to scan; defaults to --input")
    parser.add_argument("--category", choices=CATEGORIES, action="append",
                        help="Repeat to combine model, navi and live; default is all")
    args = parser.parse_args()
    result = classify(args.source or args.input, args.input, set(args.category or CATEGORIES))
    print(f"[llas:classify] {result}")


if __name__ == "__main__":
    main()
