"""Original MemberAttachTable material variants and source-object views."""
from __future__ import annotations

from dataclasses import dataclass
import copy
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from converter.llas.face_source import _pointer, _load_dependency
from converter.llas.face_composition import HeadMaterialAdapter, _subtree
from converter.common.normalized_model import NormalizedModelAdapter
from converter.common.unity import component_pointer, game_object_transform, object_id
from converter.llas.materials import MEMBER_SHADER


@dataclass(frozen=True)
class MemberAttachment:
    key: str
    kind: int
    replacements: tuple[tuple[str, Any], ...]


def member_attachments(face_source: Any, source: Path) -> list[MemberAttachment]:
    reader = face_source.manager.object_reader
    fields = reader.read_typetree()
    value = fields.get('attachTable')
    if not value or not value.get('m_PathID'):
        return []
    pointer = _pointer(reader, value)
    if pointer.m_FileID:
        _load_dependency(face_source.environment, source,
                         reader, pointer, face_source.cab_paths, resource='attachment')
    table = pointer.deref()
    entries = []
    seen = set()
    for data in table.read_typetree()['datas']:
        key = data['attachName']
        # GetObject returns the first matching serialized entry.
        if key in seen:
            continue
        seen.add(key)
        entries.append(MemberAttachment(key, data['attachType'], tuple(
            (item['replaceBindName'], _pointer(table, item['replaceObject']))
            for item in data['replaceObjects'])))
    return entries


class _MaterialPointer:
    def __init__(self, source: Any, material: Any):
        self.source = source
        self.material = material
        self.attachment_clone = True

    def __getattr__(self, name):
        return getattr(self.source, name)

    def __bool__(self):
        return True

    def deref_parse_as_object(self):
        return self.material

    def read(self):
        return self.material


def _texture_material(pointer: Any, texture: Any) -> Any:
    """Object.Instantiate(Material), mainTexture replacement, then rim reset."""
    source = pointer.deref_parse_as_object()
    material = copy.copy(source)
    material.object_reader = SimpleNamespace(assets_file=object(), path_id=1)
    material.m_SavedProperties = copy.copy(source.m_SavedProperties)
    properties = material.m_SavedProperties
    environments = []
    found_main = False
    for key, value in source.m_SavedProperties.m_TexEnvs:
        if str(getattr(key, 'name', key)) == '_MainTex':
            value = copy.copy(value)
            value.m_Texture = texture
            found_main = True
        environments.append((key, value))
    if not found_main:
        raise NotImplementedError(f'{source.m_Name}: attachment mainTexture binding has not been restored for this Shader')
    properties.m_TexEnvs = environments
    floats = {str(getattr(key, 'name', key)): value for key, value in properties.m_Floats}
    # The recovered AS/Member Shader declares _RIMLIGHT; serialized unrelated
    # stale properties do not establish Shader.HasProperty for other shaders.
    if source.m_Shader.m_PathID == MEMBER_SHADER:
        floats['_RIMLIGHT'] = 0.0
        material.m_ShaderKeywords = ' '.join(keyword for keyword in
            str(material.m_ShaderKeywords).split() if keyword != '_RIMLIGHT_ON')
    floats['_RimglightIntensity'] = 0.0
    properties.m_Floats = list(floats.items())
    return _MaterialPointer(pointer, material)


class AttachmentMaterialAdapter(NormalizedModelAdapter):
    """Apply native first-slot replacement after the source face material merge."""

    def __init__(self, face_source: Any, graft: bool, attachment: MemberAttachment):
        super().__init__()
        self.base = HeadMaterialAdapter(face_source.head_all, face_source.head_material) if graft else None
        self.material_sources = {}
        self.renderer_materials = {}
        states = []
        self.head_materials = [face_source.head_material]
        head_end = object_id(list(_subtree(face_source.head_all))[-1]) if graft else None
        for transform in _subtree(game_object_transform(face_source.root.read())):
            for entry in transform.m_GameObject.deref_parse_as_object().m_Component:
                pointer = component_pointer(entry)
                if not pointer or not pointer.type.name.endswith('Renderer'):
                    continue
                renderer = pointer.deref_parse_as_object()
                adapted = self.base.adapt_renderer(renderer) if self.base else renderer
                materials = list(getattr(adapted, 'm_Materials', []))
                self.renderer_materials[object_id(renderer)] = materials
                if materials and materials[0]:
                    states.append(materials)
            # MergeFace appends its face beneath Head_All. Insert that shared
            # material at the same hierarchy position before later siblings.
            if graft and object_id(transform) == head_end:
                states.append(self.head_materials)
        originals = {}
        for materials in states:
            pointer = materials[0]
            originals.setdefault(pointer.deref_parse_as_object().m_Name, pointer)
        if attachment.kind != 1:
            return  # ApplyAttachData only executes the MaterialColor branch.
        for bind_name, replacement in attachment.replacements:
            # ApplyAttachData dereferences replaceObject (0x27C3AC0), and its
            # non-Texture2D branch casts to Material (0x27C3BF8..0x27C3C14).
            if not replacement or replacement.m_PathID == 0:
                raise ValueError(f'LLAS attachment {attachment.key}: replaceObject is null')
            replacement_type = replacement.type.name
            if replacement_type == 'Material':
                raise NotImplementedError(
                    f'LLAS attachment {attachment.key}: Material replacement and its runtime ambient material state have not been restored')
            if replacement_type != 'Texture2D':
                raise TypeError(f'LLAS attachment {attachment.key}: expected Texture2D or Material, got {replacement_type}')
            original = originals.get(bind_name)
            if original is None:
                continue
            updated = _texture_material(original, replacement)
            self.material_sources[object_id(updated.material)] = updated.material
            for materials in states:
                # Instantiate creates a distinct named material instance. Keep
                # its source label in glTF, without fabricating Unity's clone
                # suffix; it no longer identifies the original source binding.
                if (not getattr(materials[0], 'attachment_clone', False)
                        and materials[0].deref_parse_as_object().m_Name == bind_name):
                    materials[0] = updated

    @property
    def head_material(self):
        return self.head_materials[0]

    def adapt_renderer(self, renderer: Any) -> Any:
        materials = self.renderer_materials.get(object_id(renderer))
        if materials is None:
            return self.base.adapt_renderer(renderer) if self.base else renderer
        result = copy.copy(renderer)
        result.m_Materials = materials
        return result
