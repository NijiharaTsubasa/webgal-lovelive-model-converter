"""Select active Yohane geometry and retain BX material draws."""
from copy import deepcopy

from converter.common.normalized_model import NormalizedModelAdapter
from .materials import material_extras
from converter.common.unity import object_id


def renderer_is_active(renderer):
    if not renderer.m_Enabled:
        return False
    game_object = renderer.m_GameObject.read()
    while True:
        if not game_object.m_IsActive:
            return False
        transform = next(pair.component.read() for pair in game_object.m_Component
                         if pair.component.deref().type.name == 'Transform')
        if not transform.m_Father.path_id:
            return True
        game_object = transform.m_Father.read().m_GameObject.read()


class YohaneModelAdapter(NormalizedModelAdapter):
    def __init__(self):
        self.renderer_materials = []
        self.renderer_meshes = {}

    def bind_builder(self, builder):
        self.builder = builder

    def classify_shader(self, material):
        return None

    def should_export_static_renderer(self, renderer):
        return renderer_is_active(renderer)

    def should_export_renderer(self, renderer):
        return renderer_is_active(renderer)

    def adapt_renderer(self, renderer):
        self.renderer_meshes[object_id(renderer)] = len(self.builder.document['meshes'])
        self.renderer_materials.append((len(self.builder.document['meshes']),
                                        list(renderer.m_Materials)))
        return renderer

    def finalize(self):
        # Unity repeats the last submesh for surplus renderer material slots.
        # Keep this game-local, without changing shared skin or mesh emission.
        for mesh_index, materials in self.renderer_materials:
            primitives = self.builder.document['meshes'][mesh_index]['primitives']
            count = len(primitives)
            if not count:
                raise ValueError('Yohane renderer has no submeshes')
            for pointer in materials[count:]:
                primitive = deepcopy(primitives[count - 1])
                primitive['material'] = self.builder.add_material(pointer)
                primitives.append(primitive)

    def adapt_material(self, material, result):
        texture = dict(material.m_SavedProperties.m_TexEnvs).get('_BaseMap')
        if texture and texture.m_Texture:
            result['pbrMetallicRoughness']['baseColorTexture'] = {
                'index': self.builder.add_image(texture.m_Texture.read())}
        result['pbrMetallicRoughness']['baseColorFactor'] = [1, 1, 1, 1]
        result['extras'] = material_extras(material, self.builder)
