"""Select active Yohane geometry and export source textures as unlit materials."""
from converter.common.normalized_model import NormalizedModelAdapter


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
    def bind_builder(self, builder):
        self.builder = builder

    def classify_shader(self, material):
        return None

    def should_export_static_renderer(self, renderer):
        return renderer_is_active(renderer)

    def should_export_renderer(self, renderer):
        return renderer_is_active(renderer)

    def adapt_material(self, material, result):
        texture = dict(material.m_SavedProperties.m_TexEnvs).get('_BaseMap')
        if texture and texture.m_Texture:
            result['pbrMetallicRoughness']['baseColorTexture'] = {
                'index': self.builder.add_image(texture.m_Texture.read())}
        result['pbrMetallicRoughness']['baseColorFactor'] = [1, 1, 1, 1]
        result.setdefault('extensions', {})['KHR_materials_unlit'] = {}
        used = self.builder.document.setdefault('extensionsUsed', [])
        if 'KHR_materials_unlit' not in used:
            used.append('KHR_materials_unlit')
