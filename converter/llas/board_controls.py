"""LLAS-only zero-delta Morph signal adapter for the native board selector."""
from copy import deepcopy
import struct

SIGNAL_NODE = 'LLAS Board Signals'


def append_board_controls(builder, sampled):
    document = builder.document
    nodes = document['nodes']
    if any(node.get('name') == SIGNAL_NODE for node in nodes):
        raise ValueError('Duplicate LLAS board signal node')
    domains = sampled['domains']
    if [d['name'] for d in domains] != ['eye', 'mouth']:
        raise ValueError('Board samples require ordered eye and mouth domains')
    names = [e['name'] for d in domains for e in d['entries']]
    if len(set(names)) != len(names) or not names:
        raise ValueError('Board signal names must be unique and nonempty')
    for domain in domains:
        targets = set(domain['defaults'])
        if not targets:
            raise ValueError('Board samples have no visibility targets')
        for name in targets:
            matches = [node for node in nodes if node.get('name') == name and 'mesh' in node]
            if len(matches) != 1:
                raise ValueError(f'Board renderer not uniquely exported: {name}')
        for entry in domain['entries']:
            if set(entry['visibility']) != targets:
                raise ValueError('Incomplete board visibility snapshot')
    # One tiny hidden primitive avoids adding dozens of Morph slots to the face.
    position = builder.add_accessor([(0, 0, 0), (.001, 0, 0), (0, .001, 0)], 'VEC3', 5126,
                                    target=34962, minimum=[0, 0, 0], maximum=[.001, .001, 0])
    zero = builder.add_accessor([(0, 0, 0)] * 3, 'VEC3', 5126, target=34962,
                               minimum=[0, 0, 0], maximum=[0, 0, 0])
    mesh = len(document['meshes'])
    document['meshes'].append({'name': SIGNAL_NODE,
        'primitives': [{'attributes': {'POSITION': position}, 'targets': [{'POSITION': zero} for _ in names]}],
        'weights': [0] * len(names), 'extras': {'targetNames': names}})
    node = len(nodes)
    nodes.append({'name': SIGNAL_NODE, 'mesh': mesh})
    heads = [i for i, item in enumerate(nodes) if item.get('name') == 'Head']
    if len(heads) != 1:
        raise ValueError('Board signal carrier needs the normalized Head node')
    nodes[heads[0]].setdefault('children', []).append(node)
    recipes = [{'name': name, 'targets': {SIGNAL_NODE: {name: 1}}} for name in names]
    available = {d['name']: [e['name'].split('/', 1)[1] for e in d['entries']] for d in domains}

    def replacement(base, target):
        return {target: 1} if base == target else {base: 0, target: 1}

    groups = []
    for domain, labels in available.items():
        neutral = 'Open' if domain == 'eye' else 'N'
        if neutral not in labels or ('Close' if domain == 'eye' else 'A') not in labels \
                or (domain == 'mouth' and 'Smile' not in labels):
            raise ValueError(f'Board {domain} lacks neutral/control entry')
        states = []
        for label in [neutral, *(label for label in labels if label != neutral)]:
            base, controls = f'{domain}/{label}', {}
            if domain == 'eye':
                if label not in {'Close', 'CloseSmile', 'Missing', 'Tightly'}:
                    target = 'eye/CloseSmile' if label in {'WinkL', 'WinkR'} else 'eye/Close'
                    if target not in names:
                        raise ValueError(f'Board blink endpoint absent: {target}')
                    controls['blink'] = replacement(base, target)
            states.append({'name': label, 'poses': {base: 1}, **({'controls': controls} if controls else {})})
        groups.append({'name': domain, 'type': domain, 'states': states})
    parameters = {'inputNode': SIGNAL_NODE, 'minRateToActive': struct.unpack('<f', bytes.fromhex('5c8f023f'))[0],
        'domains': [{'name': d['name'], 'defaults': deepcopy(d['defaults']),
                     'entries': [{'morph': e['name'], 'visibility': deepcopy(e['visibility'])}
                                 for e in d['entries']]} for d in domains]}
    return {'morphPoses': recipes, 'expressionGroups': groups,
            'defaultExpression': {'eye': 'Open', 'closed': 'Smile', 'open': 'A'}, 'behaviors': [
                {'name': 'LLAS.BoardFace', 'required': True, 'parameters': parameters}]}
