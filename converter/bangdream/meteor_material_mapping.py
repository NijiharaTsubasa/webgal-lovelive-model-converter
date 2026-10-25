"""Original ColorVariation mapping; no source asset mutations.

SetupColor RVA 0x3121570, MaterialController.Setup 0x311DA84,
color resource getter 0x3B20414 and menu initialization 0x33D1018.
"""
from __future__ import annotations

from types import SimpleNamespace
from dataclasses import dataclass
from typing import Any

from UnityPy.classes import PPtr


@dataclass(frozen=True)
class MaterialCategory:
    category: str | None
    force_specular_blend_7: bool = False


def classify_setup_material(original_name: str, *, controller_has_prop: bool) -> MaterialCategory:
    """MaterialController.Setup's ordered tests on the original slot name."""
    if controller_has_prop:
        return MaterialCategory("prop")
    name = original_name.lower()
    if "eye" in name:
        return MaterialCategory("eyes")
    if "_base" in name:
        if "face" in name:
            return MaterialCategory("face", True)
        if "body" in name or "acce" in name:
            return MaterialCategory("body", True)
        if "hair" in name:
            return MaterialCategory("hair")
        return MaterialCategory(None)
    if "mask" in name or "transparent" in name:
        return MaterialCategory("body" if "body" in name or "acce" in name else None)
    if ("nooutline" in name or "offset" in name) and "face" in name:
        return MaterialCategory("faceNoOutline")
    return MaterialCategory(None)


@dataclass(frozen=True)
class MaterialControllerContext:
    identity: tuple[int, int]
    controller_has_prop: bool


def _pointer_key(pointer: Any) -> tuple[int, int]:
    return id(pointer.assetsfile), int(pointer.m_PathID)


def _ancestor_pointer_keys(pointer: Any):
    seen = set()
    while pointer:
        key = _pointer_key(pointer)
        if key in seen:
            raise ValueError("Cycle in renderer GameObject ancestor chain")
        seen.add(key)
        yield key
        game_object = pointer.deref_parse_as_object()
        transforms = []
        for entry in getattr(game_object, "m_Component", []):
            component = entry[1] if isinstance(entry, tuple) else entry.component
            if component and component.type.name in ("Transform", "RectTransform"):
                transforms.append(component)
        if not transforms:
            return
        if len(transforms) != 1:
            raise ValueError("Renderer ancestor must have one Transform")
        father = transforms[0].deref_parse_as_object().m_Father
        if not father:
            return
        pointer = father.deref_parse_as_object().m_GameObject


def initialized_menu_layer(layer: int, first_material_name: str) -> int:
    return layer + 5 if "Offset" in first_material_name and 20 <= layer < 25 else layer


def renderer_activity(renderer: Any) -> tuple[bool, Any]:
    """Enabled plus activeSelf at every ancestor, terminating at null m_Father."""
    enabled = bool(getattr(renderer, "m_Enabled", True))
    pointer = getattr(renderer, "m_GameObject", None)
    if not pointer:
        return enabled, None
    game_object = pointer.deref_parse_as_object()
    active = enabled
    seen = set()
    while True:
        reader = getattr(game_object, "object_reader", None)
        identity = (id(reader.assets_file), reader.path_id) if reader else id(game_object)
        if identity in seen:
            raise ValueError("Cycle in renderer GameObject ancestor chain")
        seen.add(identity)
        active = active and bool(getattr(game_object, "m_IsActive", True))
        transforms = []
        for entry in getattr(game_object, "m_Component", []):
            component = entry[1] if isinstance(entry, tuple) else entry.component
            if component and component.type.name in ("Transform", "RectTransform"):
                transforms.append(component)
        if not transforms:
            return active, game_object
        if len(transforms) != 1:
            raise ValueError("Renderer ancestor must have one Transform")
        transform = transforms[0].deref_parse_as_object()
        father = getattr(transform, "m_Father", None)
        if not father:
            return active, game_object
        game_object = father.deref_parse_as_object().m_GameObject.deref_parse_as_object()


class _MaterialInstance:
    def __init__(self, source: Any, identity: object, setup: MaterialCategory) -> None:
        self._source = source
        self._meteor_setup = setup
        reader = getattr(source, "object_reader", None)
        self.object_reader = SimpleNamespace(assets_file=identity, path_id=getattr(reader, "path_id", 0))

    def __getattr__(self, name: str) -> Any:
        return getattr(self._source, name)


class _MaterialInstancePointer:
    """Source PPtr remains inspectable; clone cache identity is separate."""
    def __init__(self, source_pointer: Any, setup: MaterialCategory) -> None:
        self.source_pointer = source_pointer
        self._identity = object()
        self._meteor_setup = setup
        self._material = _MaterialInstance(source_pointer.deref_parse_as_object(), self._identity, setup)

    def __bool__(self) -> bool:
        return bool(self.source_pointer)

    def __getattr__(self, name: str) -> Any:
        return getattr(self.source_pointer, name)

    def deref_parse_as_object(self) -> Any:
        return self._material


class MeteorMaterialMapping:
    def __init__(self, environment: Any, color_type: int = 0) -> None:
        if isinstance(color_type, bool) or not isinstance(color_type, int) or not 0 <= color_type <= 4:
            raise ValueError("Color type must be the original enum in 0..4")
        readers = list(environment.objects)
        bundles = [o.read() for o in readers if o.type.name == "AssetBundle"]
        names = {str(b.m_Name).rsplit("/", 1)[-1] for b in bundles}
        if len(names) > 1:
            raise ValueError(f"Expected one character bundle, got {sorted(names)}")
        self.variation_name = f"Color_{next(iter(names))}_{color_type + 1:02d}" if names else None
        self.mapping: dict[str, Any] = {}
        self.variation_pointer = None
        self.selection_status = "absent"  # SetupColor(null) adds no entries.
        self._instances: dict[tuple[tuple[int, int], str], Any] = {}
        self._controllers: dict[tuple[int, int], MaterialControllerContext] = {}
        self._controller_equivalences: dict[tuple[int, int], list[int]] = {}
        components = []
        prop_game_objects = set()
        for reader in readers:
            if reader.type.name != "MonoBehaviour" or not hasattr(reader, "read"):
                continue
            component = reader.read()
            script_pointer = getattr(component, "m_Script", None)
            if not script_pointer:
                continue
            class_name = getattr(script_pointer.deref_parse_as_object(), "m_ClassName", None)
            pointer = getattr(component, "m_GameObject", None)
            if pointer and class_name == "PropController":
                prop_game_objects.add(_pointer_key(pointer))
            if pointer and class_name == "MaterialController":
                components.append((reader, pointer))
        controller_trees = {}
        for reader, pointer in components:
            key = _pointer_key(pointer)
            if key in self._controllers:
                tree = reader.read_typetree() if hasattr(reader, "read_typetree") else None
                if tree is None or controller_trees[key] is None or tree != controller_trees[key]:
                    raise ValueError("Multiple MaterialControllers on one GameObject have unrecovered differing state")
                # All serialized state, same GO/Animator/Prop scope and mapping
                # inputs agree. This represents their observable equivalence,
                # not an assumption about native GetComponent selection order.
                self._controller_equivalences[key].append(reader.path_id)
                continue
            controller_trees[key] = reader.read_typetree() if hasattr(reader, "read_typetree") else None
            self._controller_equivalences[key] = [reader.path_id]
            self._controllers[key] = MaterialControllerContext(
                key, key in prop_game_objects,
            )
        if self.variation_name is None:
            return
        for reader in readers:
            if reader.type.name != "MonoBehaviour":
                continue
            component = reader.read()
            script_pointer = getattr(component, "m_Script", None)
            if not script_pointer:
                continue
            if getattr(script_pointer.deref_parse_as_object(), "m_ClassName", None) != "ColorVariation":
                continue
            tree = reader.read_typetree()
            if tree["m_Name"] != self.variation_name:
                continue
            if self.selection_status == "selected":
                raise ValueError(f"Ambiguous ColorVariation {self.variation_name}")
            self.selection_status = "selected"
            self.variation_pointer = PPtr(m_FileID=0, m_PathID=reader.path_id, assetsfile=reader.assets_file)
            for entry in tree["mapping"]:
                name = entry["Name"]
                if name in self.mapping:
                    raise ValueError(f"Duplicate ColorVariation mapping key {name!r}")
                raw = entry["Material"]
                self.mapping[name] = PPtr(m_FileID=raw["m_FileID"], m_PathID=raw["m_PathID"], assetsfile=reader.assets_file)

    def context_for_renderer(self, renderer: Any) -> MaterialControllerContext | None:
        contexts = [self._controllers[key] for key in _ancestor_pointer_keys(getattr(renderer, "m_GameObject", None))
                    if key in self._controllers]
        if len(contexts) > 1:
            raise ValueError("Overlapping MaterialController scopes: Setup order not recovered")
        return contexts[0] if contexts else None

    def bind(self, pointer: Any, *, category_context: MaterialControllerContext | None = None) -> Any:
        if not pointer:
            return pointer
        if category_context is None:
            return pointer  # No evidenced MaterialController.Setup caller.
        name = str(pointer.deref_parse_as_object().m_Name)
        key = category_context.identity, name
        if key not in self._instances:
            mapped = self.mapping.get(name, pointer)
            if not mapped:
                raise ValueError(f"ColorVariation maps {name!r} to a null Material")
            setup = classify_setup_material(name, controller_has_prop=category_context.controller_has_prop)
            self._instances[key] = _MaterialInstancePointer(mapped, setup)
        return self._instances[key]
