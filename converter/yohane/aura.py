"""Retain AuraArc source instances and their unreordered sampling geometry."""
from converter.common.unity import component_pointer, game_object_transform, object_id


def export_aura_arc(prefab, exported, renderer_meshes):
    document = exported.builder.document
    mapping = exported.node_mapping
    rows = []

    def walk(pointer, active=True):
        game_object = pointer.read()
        active = active and bool(game_object.m_IsActive)
        transform = game_object_transform(game_object)
        for entry in game_object.m_Component:
            component = component_pointer(entry)
            if not active or component.type.name != 'VisualEffect':
                continue
            effect = component.read()
            if not effect.m_Enabled or not effect.m_Asset or effect.m_Asset.read().m_Name != 'AuraArc':
                continue
            sheet = effect.m_PropertySheet
            overrides = {}
            renderer = None
            for kind in ('Float', 'Vector2f', 'Vector3f', 'Vector4f', 'Uint', 'Int', 'Matrix4x4f', 'Bool'):
                for item in getattr(sheet, 'm_' + kind).m_Array:
                    if not item.m_Overridden:
                        continue
                    value = item.m_Value
                    if kind.startswith('Vector'):
                        value = [float(getattr(value, axis)) for axis in 'xyzw'[:int(kind[6])]]
                    elif kind == 'Matrix4x4f':
                        value = [float(getattr(value, f'e{row}{column}')) for column in range(4) for row in range(4)]
                    overrides[item.m_Name] = {'type': kind, 'value': value}
            for item in sheet.m_NamedObject.m_Array:
                if item.m_Name == 'SkinnedMeshRenderer' and item.m_Overridden and item.m_Value:
                    renderer = item.m_Value.read()
            if renderer is None:
                raise ValueError('AuraArc has no overridden source SkinnedMeshRenderer')
            mesh_index = renderer_meshes.get(object_id(renderer))
            nodes = [(i, node) for i, node in enumerate(document['nodes']) if node.get('mesh') == mesh_index]
            if mesh_index is None or len(nodes) != 1:
                raise ValueError('AuraArc source renderer does not identify one exported mesh node')
            node_index, mesh_node = nodes[0]
            primitive = document['meshes'][mesh_index]['primitives'][0]
            count = document['accessors'][primitive['attributes']['POSITION']]['count']
            mesh = renderer.m_Mesh.read()
            if count != mesh.m_VertexData.m_VertexCount:
                raise ValueError('AuraArc original and exported vertex counts differ')
            # Shared normalization preserves vertex order; only indices winding
            # and the coordinate reflection change, not the POSITION ordering.
            mesh_node.setdefault('extras', {})['yohaneAuraSourceNode'] = node_index
            if not renderer.m_RootBone:
                raise ValueError('AuraArc source renderer has no rootBone')
            skin_root = renderer.m_RootBone.read()
            skin_root_node = mapping.node_index(skin_root)
            document['nodes'][skin_root_node].setdefault('extras', {})['yohaneAuraSkinRootNode'] = skin_root_node
            effect_node = mapping.node_index(transform)
            document['nodes'][effect_node].setdefault('extras', {})['yohaneAuraArcNode'] = effect_node
            channels = mesh.m_VertexData.m_Channels
            position = channels[0]
            if position.format != 0 or position.dimension != 3:
                raise ValueError('AuraArc source POSITION must be Float32x3')
            # GetVertexBuffer positions are in rootBone space, unlike BakeMesh
            # positions in renderer space. Preserve the original rootBone axes.
            source = {'node': node_index, 'primitive': 0, 'vertexCount': count,
                      'skinRoot': {'node': skin_root_node,
                                   'toSourceFrame': mapping._local_matrix(skin_root, skin_root_node)}}
            rows.append({'node': effect_node, 'source': source,
                         'initialEvent': effect.m_InitialEventName,
                         'resetSeedOnPlay': bool(effect.m_ResetSeedOnPlay),
                         'startSeed': int(effect.m_StartSeed), 'overrides': overrides})
        for child in transform.m_Children:
            walk(child.read().m_GameObject, active)

    walk(prefab)
    if rows:
        document['scenes'][0].setdefault('extras', {})['yohaneAuraArc'] = rows
    return rows
