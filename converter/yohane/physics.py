"""Yohane source geometry adapted to the existing generic physics solver.

Call after export_normalized_model, including Ruby's root-scale preprocessing.
Saved MC1 proxy influences determine direct-render-vertex cloth regions; the
generic solver does not reproduce Magica's proxy interpolation dynamics.
"""
from __future__ import annotations

import math
from collections import Counter
from dataclasses import replace

from converter.common.physics import extract_model_physics, capsule_endpoints
from converter.common.normalized_model import renderer_node_name, _trs_to_mat, _mat4_mul
from converter.common.unity import game_object_transform, object_id
from .model_adapter import renderer_is_active


def unsupported_cloth(name, reason):
    print(f'[yohane:physics] WARNING: {name}: mesh cloth not exported: {reason}', flush=True)


def extract_physics(environment, exported):
    """Return the established generic bone/collider contract, or None.

    The shared extractor uses the selected prefab's source_nodes and normalized
    point/radius mapping, not global asset names or uncorrected prefab scales.
    """
    result = extract_model_physics(environment, exported) or {'colliders': [], 'springs': []}
    regions = mesh_cloth_regions(environment, exported)
    document = exported.builder.document
    mapping = exported.node_mapping
    parents = {child: parent for parent, item in enumerate(document['nodes'])
               for child in item.get('children', [])}
    def world(index):
        if index < len(mapping.canonical_world):
            return mapping.canonical_world[index]
        item = document['nodes'][index]
        local = item.get('matrix') or _trs_to_mat(item.get('translation', [0., 0., 0.]),
                    item.get('rotation', [0., 0., 0., 1.]), item.get('scale', [1., 1., 1.]))
        return _mat4_mul(world(parents[index]), local) if index in parents else local
    output_mapping = replace(mapping, canonical_world=mapping.canonical_world + [
        world(i) for i in range(len(mapping.canonical_world), len(document['nodes']))])
    counts = Counter(object_id(region['renderComponent']) for region in regions)
    for region in regions:
        mesh = region['mesh']
        if counts[object_id(region['renderComponent'])] > 1:
            unsupported_cloth(mesh.m_Name, 'multiple independent cloth regions share one render mesh')
            continue
        candidates = [(i, node) for i, node in enumerate(document['nodes'])
                      if node.get('name') == renderer_node_name(mesh.m_Name)
                      and 'mesh' in node and document['meshes'][node['mesh']].get('name') == mesh.m_Name]
        if len(candidates) != 1:
            unsupported_cloth(mesh.m_Name, 'render mesh does not identify one exported renderer')
            continue
        node_index, node = candidates[0]
        primitives = document['meshes'][node['mesh']]['primitives']
        if len(primitives) != 1:
            unsupported_cloth(mesh.m_Name, 'source cloth spans multiple material primitives; independent solvers would split its constraints')
            continue
        if any(primitive.get('mode', 4) != 4 for primitive in primitives):
            unsupported_cloth(mesh.m_Name, 'render topology is not triangles')
            continue
        if any(document['accessors'][primitive['attributes']['POSITION']]['count'] != len(region['influences'])
               for primitive in primitives):
            unsupported_cloth(mesh.m_Name, 'saved child mapping and exported vertex counts disagree')
            continue
        if not region['fixed']:
            unsupported_cloth(mesh.m_Name, 'source cloth has no fixed render vertices')
            continue
        if len(region['fixed']) == len(region['influences']):
            continue
        c = region['component']
        indices = []
        try:
            if c.clothParams.useCollision:
                for pointer in c.teamData.colliderList:
                    for entry in collider_geometry(pointer, mapping):
                        if entry not in result['colliders']:
                            result['colliders'].append(entry)
                        index = result['colliders'].index(entry)
                        if index not in indices:
                            indices.append(index)
        except ValueError as error:
            unsupported_cloth(mesh.m_Name, str(error))
            continue
        transform = game_object_transform(region['renderComponent'].m_GameObject.read())
        # Same response choice as MC2 generic cloth, distinct from MC1 dynamics.
        result.setdefault('cloths', []).append({
            'node': node_index, 'primitive': 0, 'fixed': region['fixed'],
            'radius': output_mapping.radius(transform, .003, target_node=node_index),
            'stiffness': 12., 'damping': .8, 'gravity': [0., 0., 0.], 'colliders': indices})
    return result if result['springs'] or result.get('cloths') else None


def collider_geometry(pointer, mapping):
    """Match the common MC1 collider geometry/segmented taper policy."""
    if not pointer:
        return []
    c = pointer.read()
    if not renderer_is_active(c):
        return []
    transform = game_object_transform(c.m_GameObject.read())
    node = mapping.node_index(transform)
    name = c.m_Script.read().m_ClassName
    vec = lambda v: [float(getattr(v, axis)) for axis in 'xyz']
    if name == 'MagicaSphereCollider':
        return [{'shape': 'sphere', 'node': node, 'offset': mapping.point(transform, vec(c.center)),
                 'radius': mapping.radius(transform, float(c.radius))}]
    if name != 'MagicaCapsuleCollider':
        raise ValueError(f'unsupported Yohane mesh-cloth collider {name}')
    start, end, _ = capsule_endpoints(c, magica2=False)
    r0, r1 = float(c.startRadius), float(c.endRadius)
    pieces = min(32, max(1, math.ceil(mapping.radius(transform, abs(r1-r0))/.005)))
    result = []
    for i in range(pieces):
        a, b = i/pieces, (i+1)/pieces
        p0 = [s + (e-s)*a for s,e in zip(start,end)]
        p1 = [s + (e-s)*b for s,e in zip(start,end)]
        result.append({'shape':'capsule', 'node':node, 'offset':mapping.point(transform,p0),
                       'radius':mapping.radius(transform,max(r0+(r1-r0)*a,r0+(r1-r0)*b)),
                       'tail':{'node':node,'offset':mapping.point(transform,p1)}})
    return result


def source_mesh_cloths(environment, exported):
    """Report the selected prefab's attached MC1 mesh cloth declarations."""
    result = []
    for obj in environment.objects:
        if obj.type.name != 'MonoBehaviour':
            continue
        component = obj.read()
        if not component.m_Script:
            continue
        script = component.m_Script.read()
        if script.m_ClassName != 'MagicaMeshCloth' or not renderer_is_active(component):
            continue
        transform = game_object_transform(component.m_GameObject.read())
        if object_id(transform) not in exported.node_mapping.source_nodes:
            continue
        result.append({'object': component.m_GameObject.read().m_Name,
                       'source': object_id(component),
                       'clothData': bool(component.clothData),
                       'virtualDeformer': bool(component.virtualDeformer)})
    return result


def decode_child_weights(child_data, proxy_vertex_count):
    """Decode saved render-to-proxy weights without spatial resampling.

    MeshWorker.CollectionVertex at RVA 0x310A6E4 reads vertexInfo and calls
    Unpack4_28Hi/Low (0x3547584/8C): count=pack>>28, offset=pack&0x0fffffff.
    RVA 0x310A768 indexes 44-byte VertexWeight entries, parent at +0x24,
    weight at +0x28; the following loop evaluates each saved influence.
    """
    info = child_data['vertexInfoList']
    weights = child_data['vertexWeightList']
    result = []
    for pack in info:
        count, offset = int(pack) >> 28, int(pack) & 0x0fffffff
        if offset + count > len(weights):
            raise ValueError('MC1 child vertex weight span exceeds saved array')
        influences = []
        for entry in weights[offset:offset + count]:
            parent = int(entry['parentIndex'])
            if not 0 <= parent < proxy_vertex_count:
                raise ValueError('MC1 child vertex refers to missing proxy vertex')
            # Preserve source data, including zero weights and its local frame.
            influences.append(dict(entry))
        result.append(influences)
    return result


def saved_render_pairs(mesh_data, renderers):
    """Follow VirtualMeshDeformer.OnInit's saved child/render array ordering.

    RVA 0x27F19B8..19D4 selects renderDeformerList[i] for each MeshData
    child; 0x27F1D58..1D68 selects childDataList[i] in the registration loop.
    Serialized child/render data hashes are not a pairing condition.
    """
    children = mesh_data['childDataList']
    if len(renderers) < len(children):
        raise ValueError('saved child list has no corresponding render deformer at the same index')
    return [(renderers[index], child) for index, child in enumerate(children)]


def mesh_cloth_regions(environment, exported):
    """Expose verified MC1 source regions for generic renderer-vertex cloth.

    Fixed/Extend particles carry the same fixed flag in ClothSetup.b__0 at
    0x27E15C0..1620. SetDeformerUseVertex at 0x27E70F8 passes !IsMoveVertex.
    Render vertices with zero contribution from moving proxy particles cannot
    move under the saved weighted mapping. This is a generic direct-vertex
    adaptation boundary, not a recreation of the proxy simulation.
    """
    regions = []
    for obj in environment.objects:
        if obj.type.name != 'MonoBehaviour':
            continue
        c = obj.read()
        if (not c.m_Script or c.m_Script.read().m_ClassName != 'MagicaMeshCloth'
                or not renderer_is_active(c)):
            continue
        t = game_object_transform(c.m_GameObject.read())
        if object_id(t) not in exported.node_mapping.source_nodes:
            continue
        virtual = c.virtualDeformer.read().deformer
        mesh = virtual.meshData.read_typetree()
        cloth = c.clothData.read_typetree()
        selections = dict(zip(map(int, cloth['useVertexList']), map(int, cloth['selectionData'])))
        try:
            pairs = saved_render_pairs(mesh, virtual.renderDeformerList)
        except ValueError as error:
            unsupported_cloth(c.m_GameObject.read().m_Name, str(error))
            continue
        for renderer_pointer, child in pairs:
            render = renderer_pointer.read().deformer
            weights = decode_child_weights(child, mesh['vertexCount'])
            moving_weights = [sum(float(w['weight']) for w in row
                                  if selections.get(int(w['parentIndex']), 0) == 1)
                              for row in weights]
            regions.append({'component': c, 'renderComponent': renderer_pointer.read(),
                            'mesh': render.sharedMesh.read(),
                            'fixed': [i for i, value in enumerate(moving_weights) if value == 0],
                            'movingWeights': moving_weights, 'influences': weights,
                            'proxySelections': selections, 'proxyMesh': mesh})
    return regions
