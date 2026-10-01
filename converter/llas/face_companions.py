"""Source bindings and Unity samples for ordinary-face non-Morph properties.

This module extracts data, not Unity's mixer. Runtime coefficients are supplied
by the standard expression query; game-specific mixing lives in LLAS.Face.
"""
from collections import Counter
import math
from pathlib import Path
import struct
import zlib

import UnityPy

from converter.common.animation import packed_clip_values


def streamed_polynomials(packed):
    """Preserve the source streamed key's cubic coefficients, not just values."""
    data = packed.m_StreamedClip.data
    raw = struct.pack(f'<{len(data)}I', *data)
    curves, offset = {}, 0
    while offset < len(raw):
        time, count = struct.unpack_from('<fi', raw, offset)
        offset += 8
        if count < 0 or offset + count * 20 > len(raw):
            raise ValueError('Malformed LLAS streamed curve')
        for _ in range(count):
            index, a, b, c, value = struct.unpack_from('<i4f', raw, offset)
            offset += 20
            if math.isfinite(time):
                curves.setdefault(index, {})[max(0.0, time)] = [a, b, c, value]
    return {index: [[time, *value] for time, value in sorted(keys.items())]
            for index, keys in curves.items()}


def source_companions(face, sources):
    paths = {}

    def visit(node, path):
        hashed = zlib.crc32(path.encode('utf-8')) & 0xffffffff
        if hashed in paths and paths[hashed] != path:
            raise ValueError('LLAS face animation path hash collision')
        paths[hashed] = path
        for pointer in node.m_Children:
            child = pointer.read()
            name = child.m_GameObject.read().m_Name
            visit(child, f'{path}/{name}' if path else name)

    visit(face.face_root, '')
    environments = {path: UnityPy.load(path.read_bytes()) for path in {s['source'] for s in sources}}
    result = []
    for source in sources:
        readers = [r for r in environments[source['source']].objects
                   if r.type.name == 'AnimationClip' and r.path_id == source['path_id']]
        if len(readers) != 1:
            raise ValueError(f'Ambiguous face clip: {source["name"]}')
        reader = readers[0]
        clip = reader.read()
        constants, curves = packed_clip_values(clip)
        packed = clip.m_MuscleClip.m_Clip.data
        variable_count = packed.m_StreamedClip.curveCount + packed.m_DenseClip.m_CurveCount
        polynomials = streamed_polynomials(packed)
        duration = float(clip.m_MuscleClip.m_StopTime - clip.m_MuscleClip.m_StartTime)
        offset, entries = 0, []
        for binding in reader.read_typetree()['m_ClipBindingConstant']['genericBindings']:
            first_index = offset
            kind, attribute = binding['typeID'], binding['attribute']
            width = {1: 3, 2: 4, 3: 3, 4: 3}.get(attribute, 1) if kind == 4 else 1
            values = []
            for index in range(offset, offset + width):
                values.append(curves.get(index, []) if index < variable_count else [(0, constants[index-variable_count])])
            offset += width
            if kind == 137 and attribute != 3305885265:
                continue  # Morphs are already owned by the standard expression system.
            path = paths.get(binding['path'])
            if not path or binding['isPPtrCurve']:
                raise ValueError(f'Unresolved ordinary face companion binding: {source["name"]}: {binding}')
            if kind == 4 and attribute in (1, 2, 3, 4):
                if any(not samples or any(not math.isfinite(value) or abs(value-samples[0][1]) > 1e-7
                                          for _, value in samples) for samples in values):
                    raise ValueError(f'Nonconstant face TRS requires native curve baking: {source["name"]}/{path}')
                if any(any(key[1:4]) for index in range(first_index, first_index+width)
                       for key in polynomials.get(index, [])):
                    raise ValueError(f'Nonconstant face TRS polynomial: {source["name"]}/{path}')
                property_name = {1: 'position', 2: 'quaternion', 3: 'scale', 4: 'quaternion'}[attribute]
                entry = dict(path=path, property=property_name)
                if property_name in ('position', 'scale'):
                    # A standalone Unity clip can fold tiny translations into
                    # its default, unlike the complete source mixer. Preserve
                    # constant source vectors; rotations still come from Unity.
                    entry['value'] = [samples[0][1] for samples in values]
                entries.append(entry)
            elif kind in (25, 137) and attribute == 3305885265:
                if duration <= 0 or not values[0] or any(value not in (0, 1) for _, value in values[0]):
                    raise ValueError(f'Unsupported face visibility values: {source["name"]}/{path}')
                if first_index >= variable_count:
                    curve = [[0, 0, 0, 0, constants[first_index-variable_count]]]
                elif first_index in polynomials:
                    curve = [key for key in polynomials[first_index] if key[0] <= duration]
                else:
                    raise ValueError(f'Dense visibility curve requires native recovery: {source["name"]}/{path}')
                entries.append(dict(path=path, property='visible', length=duration, curve=curve))
            else:
                raise ValueError(f'Unsupported face companion binding: {source["name"]}: {binding}')
        if len({(e['path'], e['property']) for e in entries}) != len(entries):
            raise ValueError(f'Duplicate face companion property: {source["name"]}')
        result.append(dict(source, companions=entries))
    return result


def assemble_companions(sources, report):
    defaults = {node['path']: node for node in report['defaults']}
    bindings = {}
    field = {'position': 'position', 'quaternion': 'rotation', 'scale': 'scale'}

    def vector(node, property_name):
        value = node[field[property_name]]
        return [value[k] for k in ('xyzw' if property_name == 'quaternion' else 'xyz')]

    for source in sources:
        matches = [clip for clip in report['clips'] if clip['name'] == source['clip_name']
                   and Path(clip['bundle']).resolve() == Path(source['bundle']).resolve()]
        if len(matches) != 1:
            raise ValueError(f'Missing native companion clip: {source["name"]}')
        poses = matches[0]['poses']
        snapshots = [{node['path']: node for node in pose['nodes']} for pose in poses]
        for entry in source['companions']:
            path, prop = entry['path'], entry['property']
            if path not in defaults or not snapshots or any(path not in s for s in snapshots):
                raise ValueError(f'Missing native companion node: {path}')
            default = defaults[path]['enabled'] if prop == 'visible' else vector(defaults[path], prop)
            binding = bindings.setdefault((path, prop), dict(path=path, property=prop, default=default, poses=[]))
            if prop == 'visible':
                binding['poses'].append(dict(name=source['name'], length=entry['length'], curve=entry['curve']))
            else:
                native = [vector(snapshot[path], prop) for snapshot in snapshots]
                if any(max(abs(a-b) for a, b in zip(value, native[-1])) > 1e-6 for value in native):
                    raise ValueError(f'Native face transform is not constant: {source["name"]}/{path}/{prop}')
                value = entry['value'] if prop in ('position', 'scale') else native[-1]
                binding['poses'].append(dict(name=source['name'], value=value))
    # Unity folds properties whose whole graph agrees with the default. Keeping
    # these as weighted writes would incorrectly scale e.g. [1,1,1] at sum > 1.
    return {'bindings': [binding for binding in bindings.values()
                         if binding['property'] == 'visible' or
                         any(pose['value'] != binding['default'] for pose in binding['poses'])]}


def build_face_behavior(document, sampled, morph_poses):
    nodes = document['nodes']
    counts = Counter(node.get('name') for node in nodes)
    names = {p['name'] for p in morph_poses}
    bindings = []
    for binding in sampled['bindings']:
        name = binding['path'].rsplit('/', 1)[-1]
        if counts[name] != 1:
            raise ValueError(f'LLAS companion target must resolve uniquely: {name}')
        node = next(n for n in nodes if n.get('name') == name)
        prop = binding['property']
        if prop == 'visible' and 'mesh' not in node:
            raise ValueError(f'LLAS companion renderer was not exported: {name}')

        def reflect(value):
            if prop == 'position':
                return [-value[0], value[1], value[2]]
            if prop == 'quaternion':
                return [value[0], -value[1], -value[2], value[3]]
            return value

        poses = []
        for pose in binding['poses']:
            if pose['name'] not in names:
                raise ValueError(f'LLAS companion has no Morph recipe: {pose["name"]}')
            poses.append(dict(name=pose['name'], **({'length': pose['length'], 'curve': pose['curve']} if prop == 'visible'
                                                   else {'value': reflect(pose['value'])})))
        bindings.append(dict(node=name, property=prop, default=reflect(binding['default']), poses=poses))
    return {'name': 'LLAS.Face', 'required': True, 'parameters': {'bindings': bindings}}
