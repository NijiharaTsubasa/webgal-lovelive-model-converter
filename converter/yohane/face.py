"""Export source story facial Morph recipes from Unity face samples.

This is the model-format adapter, not the game's automatic lip-sync player.
Face Layer recipes contribute once; Eye/Mouth additive channels are increments.
"""
from __future__ import annotations

import json
import math
import zlib
from pathlib import Path

def controller_controls(source) -> dict:
    """Resolve original state callbacks and trigger destinations from the AB."""
    controller_name = source.peek_name()
    tree = source.read_typetree()
    strings = dict(tree['m_TOS'])
    controller = tree['m_Controller']
    layers = {strings[layer['data']['m_Binding']]: (index, controller['m_StateMachineArray'][
        layer['data']['m_StateMachineIndex']]['data'])
        for index, layer in enumerate(controller['m_LayerArray'])}
    # Original controllers use both spellings for this additive mouth layer.
    if 'Mouth_Open Layer' in layers and 'Mouth Open Layer' not in layers:
        layers['Mouth Open Layer'] = layers['Mouth_Open Layer']
    description = tree['m_StateMachineBehaviourVectorDescription']
    pointers = source.read().m_StateMachineBehaviours
    face_layer, face_machine = layers['Face Layer']

    def destination(layer_name, trigger):
        machine = layers[layer_name][1]
        event = zlib.crc32(trigger.encode('utf-8'))
        matches = [transition['data']['m_DestinationState']
                   for transition in machine['m_AnyStateTransitionConstantArray']
                   if any(condition['data']['m_EventID'] == event
                          for condition in transition['data']['m_ConditionConstantArray'])]
        if len(matches) != 1:
            raise ValueError(f'{controller_name}/{layer_name}: ambiguous trigger {trigger!r}')
        state = machine['m_StateConstantArray'][matches[0]]['data']
        return strings[state['m_NameID']]

    result = {}
    for wrapped in face_machine['m_StateConstantArray']:
        state = wrapped['data']
        ranges = [value for key, value in description['m_StateMachineBehaviourRanges']
                  if key['m_LayerIndex'] == face_layer and key['m_StateID'] == state['m_FullPathID']]
        if len(ranges) != 1:
            raise ValueError('Missing original face callback range')
        selected = ranges[0]
        callbacks = {}
        for offset in range(selected['m_StartIndex'], selected['m_StartIndex'] + selected['m_Count']):
            index = description['m_StateMachineBehaviourIndices'][offset]
            behaviour = pointers[index].deref()
            script = behaviour.read().m_Script.deref_parse_as_object()
            callbacks[script.m_ClassName] = behaviour.read_typetree()
        blink_trigger = callbacks['SetTriggerStateMachineBehaviour']['m_fireTriggerName']
        lip = callbacks['LipSyncValidStateMachineBehaviour']
        override = lip['m_overrideLipSyncOnTrigger']
        result[strings[state['m_NameID']]] = {
            'blink': destination('Eye Close Layer', blink_trigger),
            'speech': destination('Mouth Open Layer', override or 'f_mouth_open_add')
                      if lip['m_isValidLipSyncLayer'] else None,
            'blinkTrigger': blink_trigger, 'speechTrigger': override or 'f_mouth_open_add',
        }
    return result


def _weights(sample: dict, allowed: dict | None = None) -> dict[str, dict[str, float]]:
    result = {}
    for mesh in sample['meshes']:
        values = {name: float(weight) / 100.0
                  for name, weight in zip(mesh['targets'], mesh['weights']) if weight != 0
                  and (allowed is None or name in allowed.get(mesh['node'], set()))}
        if values:
            if mesh['node'] in result:
                raise ValueError(f"Ambiguous facial node: {mesh['node']}")
            if any(not math.isfinite(value) for value in values.values()):
                raise ValueError('Non-finite sampled Morph weight')
            result[mesh['node']] = values
    return result


def export_face(sample_path: str | Path, source, gltf_document: dict | None = None) -> dict:
    """Return morphPoses, expressionGroups and defaultExpression for a component.

    Optional glTF JSON validates exact exported node/target references. The caller
    supplies builder.document after model export, before writing config.json.
    """
    data = json.loads(Path(sample_path).read_text(encoding='utf-8'))
    allowed = None
    if gltf_document is not None:
        allowed = {}
        for node in gltf_document['nodes']:
            if 'mesh' in node:
                targets = gltf_document['meshes'][node['mesh']].get('extras', {}).get('targetNames', [])
                allowed.setdefault(node.get('name'), set()).update(targets)
    sampled_channels = {mesh['node']: set(mesh['targets'])
                        for sample in data['poses'] for mesh in sample['meshes']}
    if allowed is not None:
        sampled_channels = {node: targets & allowed.get(node, set())
                            for node, targets in sampled_channels.items()}
    if not any(sampled_channels.values()):
        return {'morphPoses': [], 'expressionGroups': [], 'defaultExpression': {}}
    baseline = [sample for sample in data['poses']
                if sample['eye'] == 'f_normal' and sample['mouth'] == 'f_normal'
                and sample['time'] == 0]
    if not baseline:
        raise ValueError('No original Face Layer baseline samples')
    names = {sample['face'] for sample in baseline}
    if 'f_normal' not in names:
        raise ValueError('No source neutral face')
    # Preserve original controller-neutral recipe, including normal=100 where
    # present. Do not infer a common neutral recipe across costume meshes.
    ordered = sorted(baseline, key=lambda sample: (sample['face'] != 'f_normal', sample['face']))
    poses = []
    faces = []
    controls = controller_controls(source)
    for sample in ordered:
        name = sample['face'].removeprefix('f_')
        recipe = f'face.{name}'
        targets = _weights(sample, allowed)
        if targets:
            poses.append({'name': recipe, 'targets': targets})
        faces.append({'name': name, 'poses': {recipe: 1} if targets else {}})

    isolated = data['isolatedClips']
    def source_increment(clip: str, target: str) -> dict:
        # An actually animated source binding identifies the target node. Never
        # infer it from head/face filename patterns or from an unrelated mesh.
        nodes = {node for sample in isolated if sample['face'] == clip
                 for node, weights in _weights(sample, allowed).items() if target in weights}
        # Unity source Morph endpoint 100 becomes GLB weight 1. Source speech
        # timing/volume curves are not baked into this user-controlled endpoint.
        return {node: {target: 1.0} for node in nodes}

    close_targets = source_increment('f_eye_close', 'eye_close')
    if close_targets:
        poses.append({'name': 'eye.close', 'targets': close_targets})
    mouth_clips = sorted({sample['face'] for sample in isolated
                          if sample['face'].endswith('mouth_open')})
    mouth_clips.sort(key=lambda name: (name != 'f_mouth_open', name))
    for clip in mouth_clips:
        target = clip.removeprefix('f_')
        recipe = f'mouth.{target}'
        targets = source_increment(clip, target)
        if targets:
            poses.append({'name': recipe, 'targets': targets})
    recipes = {pose['name'] for pose in poses}
    for state in faces:
        source = controls['f_' + state['name']]
        endpoints = {}
        if source['blink'] == 'f_eye_close' and close_targets:
            endpoints['blink'] = {'eye.close': 1}
        elif source['blink'] == 'f_eye_close_over' and close_targets:
            # The original over-close clip reaches 120 on this original Morph;
            # this user-controlled endpoint is separate from its timed curve.
            peak = max((weights['eye_close'] for sample in isolated if sample['face'] == source['blink']
                        for weights in _weights(sample, allowed).values() if 'eye_close' in weights), default=None)
            if peak is not None:
                endpoints['blink'] = {'eye.close': peak}
        elif source['blink'] not in ('f_normal', 'f_eye_close', 'f_eye_close_over'):
            raise ValueError(f'Unsupported original eye state {source["blink"]}')
        if source['speech']:
            target = source['speech'].removeprefix('f_')
            recipe = f'mouth.{target}'
            if recipe not in recipes:
                pass
            elif target == 'mouth_open':
                endpoints['speech'] = {recipe: 1}
            else:
                # The paired original deltas undo the emotion's open mouth.
                # Base stores closed mouth; speech withdraws that correction.
                state['poses'][recipe] = 1
                endpoints['speech'] = {recipe: 0}
        if endpoints:
            state['controls'] = endpoints
    result = {'morphPoses': poses,
              'expressionGroups': [{'name': 'face', 'type': 'face', 'states': faces}],
              'defaultExpression': {'face': 'normal'}}
    if gltf_document is not None:
        for pose in poses:
            for node, weights in pose['targets'].items():
                matches = [item for item in gltf_document['nodes'] if item.get('name') == node]
                if len(matches) != 1 or 'mesh' not in matches[0]:
                    raise ValueError(f'Exported facial node not unique: {node}')
                targets = gltf_document['meshes'][matches[0]['mesh']].get('extras', {}).get('targetNames', [])
                for target in weights:
                    if targets.count(target) != 1:
                        raise ValueError(f'Exported facial target not unique: {node}/{target}')
    return result

