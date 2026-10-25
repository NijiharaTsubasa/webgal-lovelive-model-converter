"""Discover source ColorVariation changes and supplement alternate model packages."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from UnityPy.classes import PPtr

from . import _package_name, build_package_config, convert_one, discover_bundle_inputs, load_bundle_assets, should_export_component, model_group
from .meteor_material_mapping import MeteorMaterialMapping, initialized_menu_layer, renderer_activity
from .meteor_source import material_snapshot
from .previews import BodyPreviews
from .default_motion import DefaultMotions
from converter.common.component_order import order_model_component
from .metadata import ModelDescriptions


def _pointer_key(pointer: Any) -> tuple[int, int, int]:
    return id(pointer.assetsfile), int(getattr(pointer, "m_FileID", 0)), int(pointer.m_PathID)


def changed_color_types(bundle: Any) -> list[int]:
    """Compare menu-active renderer slots after the original colour substitution.

    SetupColor selects Color_{AssetBundleName}_{color_type + 1:02d}; only
    renderers below a MaterialController receive that substitution. Material
    asset names are labels, so a renamed but otherwise identical asset does
    not require another exported model.
    """
    env = bundle.env
    base = MeteorMaterialMapping(env, 0)
    if base.variation_name is None:
        return []
    expected = {base.variation_name[:-2] + f"{index + 1:02d}": index for index in range(5)}
    variations: dict[int, dict[str, Any]] = {}
    for reader in env.objects:
        if reader.type.name != "MonoBehaviour":
            continue
        component = reader.read()
        script = getattr(component, "m_Script", None)
        if not script or getattr(script.deref_parse_as_object(), "m_ClassName", None) != "ColorVariation":
            continue
        tree = reader.read_typetree()
        index = expected.get(tree.get("m_Name"))
        if index is None:
            continue
        if index in variations:
            raise ValueError(f"Ambiguous ColorVariation {tree['m_Name']}")
        mapping: dict[str, Any] = {}
        for entry in tree["mapping"]:
            name = entry["Name"]
            if name in mapping:
                raise ValueError(f"Duplicate ColorVariation mapping key {name!r}")
            raw = entry["Material"]
            mapping[name] = PPtr(m_FileID=raw["m_FileID"], m_PathID=raw["m_PathID"], assetsfile=reader.assets_file)
        variations[index] = mapping

    roots = {_pointer_key(pointer) for name, pointer in env.container.items()
             if name.endswith(".prefab") and pointer.type.name == "GameObject"}
    slots = []
    layer_slots = []
    for reader in env.objects:
        if reader.type.name not in {"SkinnedMeshRenderer", "MeshRenderer"}:
            continue
        renderer = reader.read()
        active, root = renderer_activity(renderer)
        if not active or root is None:
            continue
        root_reader = root.object_reader
        if (id(root_reader.assets_file), 0, root_reader.path_id) not in roots:
            continue
        if base.context_for_renderer(renderer) is None:
            continue
        slots.extend((str(pointer.deref_parse_as_object().m_Name), pointer)
                     for pointer in renderer.m_Materials if pointer)
        game_object_pointer = getattr(renderer, "m_GameObject", None)
        game_object = game_object_pointer.deref_parse_as_object() if game_object_pointer else None
        layer = getattr(game_object, "m_Layer", None)
        materials = renderer.m_Materials
        if layer is not None and materials and materials[0]:
            pointer = materials[0]
            layer_slots.append((layer, str(pointer.deref_parse_as_object().m_Name), pointer))

    snapshots = {}

    def signature(pointer: Any) -> dict[str, Any]:
        key = _pointer_key(pointer)
        if key not in snapshots:
            snapshot = material_snapshot(pointer.deref_parse_as_object())
            snapshot.pop("name", None)
            snapshots[key] = snapshot
        return snapshots[key]

    original = variations.get(0, {})

    def changes_rendering(mapping: dict[str, Any]) -> bool:
        if any(signature(original.get(name, pointer)) != signature(mapping.get(name, pointer))
               for name, pointer in slots):
            return True
        # The menu also derives a renderer layer from its first mapped material.
        # Preserve that observable name-dependent operation while ignoring labels.
        return any(initialized_menu_layer(layer, str(original.get(name, pointer).deref_parse_as_object().m_Name))
                   != initialized_menu_layer(layer, str(mapping.get(name, pointer).deref_parse_as_object().m_Name))
                   for layer, name, pointer in layer_slots)

    return [index for index, mapping in sorted(variations.items()) if index and changes_rendering(mapping)]


def discover_variant_jobs(input_dir: Path) -> list[dict[str, Any]]:
    """Inspect each available source bundle once; retain only serializable jobs."""
    input_dir = Path(input_dir).resolve()
    packages: dict[str, dict[str, Any]] = {}
    for path, role in discover_bundle_inputs(input_dir):
        bundle = load_bundle_assets(path, expected_role=role)
        name = _package_name(bundle)
        if not should_export_component(name, role):
            continue
        package = packages.setdefault(name, {"name": name, "body_path": None, "head_path": None,
                                             "body": [], "head": [], "input_root": str(input_dir)})
        if package[f"{role}_path"] is not None:
            raise ValueError(f"Duplicate {role} source for {name}")
        package[f"{role}_path"] = str(path.resolve())
        package[role] = changed_color_types(bundle)
        del bundle
    return [package for _, package in sorted(packages.items()) if package["body_path"] and package["body"]]


def _complete(package_dir: Path, name: str, roles: set[str]) -> bool:
    try:
        config = json.loads((package_dir / "config.json").read_text(encoding="utf-8"))
        components = config["components"]
        if not isinstance(components, list) or len(components) != len(roles):
            return False
        found = set()
        for component in components:
            role = component.get("role")
            if role not in roles or role in found or any(component.get(key) != value for key, value in {
                "type": "model", "name": name, "group": model_group(name), "motionGroup": "garupa",
                "model": f"{role}.glb",
            }.items()):
                return False
            model = package_dir / f"{role}.glb"
            if not model.is_file() or model.stat().st_size == 0:
                return False
            found.add(role)
        return found == roles
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return False


_previews_by_root: dict[str, BodyPreviews] = {}
_descriptions_by_root: dict[str, ModelDescriptions] = {}
_defaults_by_root: dict[tuple[str, str | None], DefaultMotions] = {}


def convert_variant_job(job: dict[str, Any], output_dir: Path, baked_dir: Path | None) -> dict[str, Any]:
    """Convert missing alternate packages, leaving complete packages untouched."""
    output_dir = Path(output_dir)
    baked_dir = Path(baked_dir) if baked_dir is not None else None
    result: dict[str, Any] = {"name": job["name"], "generated": [], "skipped": [], "failures": []}
    preview_root = str(Path(job["input_root"]).resolve())
    defaults_key = (preview_root, str(baked_dir.resolve()) if baked_dir else None)
    if defaults_key not in _defaults_by_root:
        _defaults_by_root[defaults_key] = DefaultMotions(Path(preview_root), baked_dir)
    defaults = _defaults_by_root[defaults_key]
    default_fields = defaults.get(job['name'])
    pending = []
    for index in job["body"]:
        if isinstance(index, bool) or not isinstance(index, int) or not 1 <= index <= 4:
            raise ValueError("Alternate color type must be in 1..4")
        name = f"{job['name']}_another{index}"
        roles = ({"body", "head"} if index in job["head"] and job.get("head_path")
                 and should_export_component(job["name"], "head") else {"body"})
        if _complete(output_dir / name, name, roles):
            config_path = output_dir / name / 'config.json'
            config = json.loads(config_path.read_text(encoding='utf-8'))
            if any(any(component.get(key) != value for key, value in default_fields.items())
                   for component in config['components']):
                config['components'] = [order_model_component({**component, **default_fields})
                                        for component in config['components']]
                config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            result["skipped"].append(name)
        else:
            pending.append((index, name, roles))
    if not pending:
        return result

    bundles = {}
    for role in ("body", "head"):
        if any(role in roles for _, _, roles in pending):
            bundles[role] = load_bundle_assets(Path(job[f"{role}_path"]), expected_role=role)
            if _package_name(bundles[role]) != job["name"]:
                raise ValueError(f"Source prefab identity changed for {job['name']}/{role}")
    if preview_root not in _previews_by_root:
        _previews_by_root[preview_root] = BodyPreviews(Path(preview_root))
    previews = _previews_by_root[preview_root]
    if preview_root not in _descriptions_by_root:
        _descriptions_by_root[preview_root] = ModelDescriptions(Path(preview_root))
    descriptions = _descriptions_by_root[preview_root]
    for index, name, roles in pending:
        try:
            components = []
            for role in ("head", "body"):
                if role not in roles:
                    continue
                converted_name, component = convert_one(
                    Path(job[f"{role}_path"]), output_dir, baked_dir, expected_role=role,
                    color_type=index, loaded_bundle=bundles[role],
                )
                if converted_name != name:
                    raise ValueError(f"Unexpected converted name {converted_name}, expected {name}")
                if role == "body":
                    preview = previews.get(name)
                    if preview is not None:
                        component["preview"] = preview
                components.append(component)
            config = build_package_config(name, components, descriptions, defaults.get(name))
            config_path = output_dir / name / "config.json"
            config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            result["generated"].append(name)
            print(f"[bangdream] {name}: generated {'+'.join(sorted(roles))}", flush=True)
        except Exception as exc:
            result["failures"].append({"name": name, "error": str(exc)})
            print(f"[bangdream] {name}: failed: {exc}", flush=True)
    return result
