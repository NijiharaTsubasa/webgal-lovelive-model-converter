from __future__ import annotations

from typing import Any

from ..common import pointer_id
from ..common.normalized_model import FaceBonesCopierAdapter


class _RendererWithMaterials:
    """Read-only renderer view with source-authoritative material slots."""

    def __init__(self, source: Any, materials: list[Any]) -> None:
        self._source = source
        self._materials = materials

    def __getattr__(self, attr: str) -> Any:
        if attr == "m_Materials":
            return self._materials
        return getattr(self._source, attr)


class BangDreamModelAdapter(FaceBonesCopierAdapter):
    """Contain Bang Dream's runtime model adjustments behind one seam."""

    def __init__(self, environment: Any) -> None:
        super().__init__(environment)
        self.textured_materials_by_mesh: dict[tuple[int, int], list[Any]] = {}
        for obj in environment.objects:
            if obj.type.name != "SkinnedMeshRenderer":
                continue
            renderer = obj.read()
            if not getattr(renderer, "m_Mesh", None):
                continue
            for material_pointer in renderer.m_Materials:
                # Unity serializes an empty material slot as a non-None PPtr
                # whose PathID is zero.  Such pointers are falsy and cannot be
                # dereferenced.
                if not material_pointer:
                    continue
                material = material_pointer.deref_parse_as_object()
                if any(
                    getattr(entry[1], "m_Texture", None)
                    and entry[1].m_Texture.m_PathID != 0
                    for entry in material.m_SavedProperties.m_TexEnvs
                ):
                    self.textured_materials_by_mesh.setdefault(
                        pointer_id(renderer.m_Mesh), []
                    ).append(material_pointer)

    def adapt_renderer(self, renderer: Any) -> Any:
        textured_materials = self.textured_materials_by_mesh.get(pointer_id(renderer.m_Mesh))
        original_materials = list(getattr(renderer, "m_Materials", []))
        if not original_materials or not textured_materials:
            return renderer

        candidates: dict[str, list[Any]] = {}
        for material_pointer in textured_materials:
            material = material_pointer.deref_parse_as_object()
            name = str(material.m_Name).removesuffix("_01")
            candidates.setdefault(name, []).append(material_pointer)

        swapped: list[Any] = []
        used_candidates: set[Any] = set()
        for material_pointer in original_materials:
            if not material_pointer:
                swapped.append(material_pointer)
                continue
            material = material_pointer.deref_parse_as_object()
            name = str(material.m_Name).removesuffix("_01")
            replacement = next(
                (
                    candidate
                    for candidate in candidates.get(name, [])
                    if candidate not in used_candidates
                ),
                None,
            )
            if replacement is not None:
                used_candidates.add(replacement)
            swapped.append(replacement if replacement is not None else material_pointer)
        return _RendererWithMaterials(renderer, swapped)
