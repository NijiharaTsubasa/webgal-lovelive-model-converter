from __future__ import annotations

from typing import Any

from ..common.normalized_model import FaceBonesCopierAdapter
from .meteor_material_mapping import MeteorMaterialMapping, initialized_menu_layer, renderer_activity
from .meteor_face_binding import finalize_body_face_frame
from .meteor_material import MeteorMaterialExporter
from .meteor_bounds import attach_renderer_bounds


class _RendererWithMaterials:
    """Read-only initialized view; serialized objects and PPtrs stay untouched."""

    def __init__(self, source: Any, materials: list[Any]) -> None:
        self.source_renderer = source
        self.original_materials = tuple(getattr(source, "m_Materials", []))
        self.m_Materials = materials
        pointer = getattr(source, "m_GameObject", None)
        game_object = pointer.deref_parse_as_object() if pointer else None
        self.original_layer = getattr(game_object, "m_Layer", None)
        first_name = str(materials[0].deref_parse_as_object().m_Name) if materials and materials[0] else ""
        self.initialized_layer = (initialized_menu_layer(self.original_layer, first_name)
                                  if self.original_layer is not None else None)

    def __getattr__(self, attr: str) -> Any:
        return getattr(self.source_renderer, attr)


class BangDreamModelAdapter(FaceBonesCopierAdapter):
    """Apply selected ColorVariation before exporting each source renderer."""

    def __init__(self, environment: Any, color_type: int = 0, *, role: str = "", prefab_pointer: Any = None) -> None:
        super().__init__(environment)
        self.material_mapping = MeteorMaterialMapping(environment, color_type)
        self.role = role
        self.prefab_pointer = prefab_pointer
        self._exported_renderers = []

    def bind_builder(self, builder: Any) -> None:
        self.material_exporter = MeteorMaterialExporter(builder)

    def classify_shader(self, material: Any) -> None:
        return None

    def adapt_material(self, material: Any, result: dict) -> None:
        self.material_exporter.adapt_material(material, result)

    def finalize_export(self, exported: Any) -> None:
        finalize_body_face_frame(exported, role=self.role, prefab_pointer=self.prefab_pointer)
        attach_renderer_bounds(exported, self._exported_renderers, role=self.role)

    def adapt_renderer(self, renderer: Any) -> Any:
        context = self.material_mapping.context_for_renderer(renderer)
        return _RendererWithMaterials(renderer, [
            self.material_mapping.bind(pointer, category_context=context)
            for pointer in getattr(renderer, "m_Materials", [])
        ])

    def should_export_renderer(self, renderer: Any) -> bool:
        return renderer_activity(renderer)[0]

    def adapt_exported_renderer(self, renderer: Any, mesh_node: int, builder: Any) -> None:
        self._exported_renderers.append((renderer, mesh_node))
        if renderer.initialized_layer is not None:
            builder.document["nodes"][mesh_node].setdefault("extras", {})["meteorLayer"] = renderer.initialized_layer
