"""Publish source story entry transitions and loop states as complete actions."""
from __future__ import annotations

import copy


LABELS = {'angry': '生气', 'cheer': '欢呼', 'doubt': '疑惑', 'happy': '高兴',
          'idle': '剧情待机', 'run': '跑步', 'smile': '微笑', 'surprise': '惊讶',
          'think': '思考', 'verysurprise': '大吃一惊', 'walk': '走路',
          'panic': '慌张', 'sad': '难过', 'punsuka': '气鼓鼓'}


def default_action(controller) -> tuple[str, str]:
    """Resolve the original Base Layer initial state and its clip, not a guessed name."""
    tree = controller.read_typetree()
    strings = dict(tree['m_TOS'])
    data = tree['m_Controller']
    layers = [item['data'] for item in data['m_LayerArray']
              if strings[item['data']['m_Binding']] == 'Base Layer']
    if len(layers) != 1:
        raise ValueError(f'{controller.peek_name()}: expected one Base Layer')
    machine = data['m_StateMachineArray'][layers[0]['m_StateMachineIndex']]['data']
    state = machine['m_StateConstantArray'][machine['m_DefaultState']]['data']
    nodes = state['m_BlendTreeConstantArray'][0]['data']['m_NodeArray']
    if len(nodes) != 1 or nodes[0]['data']['m_ChildIndices']:
        raise ValueError(f'{controller.peek_name()}: unsupported default-state blend tree')
    clips = controller.read().m_AnimationClips
    pose_clip = clips[nodes[0]['data']['m_ClipID']].read().m_Name
    seen = set()
    while state['m_TransitionConstantArray']:
        transitions = state['m_TransitionConstantArray']
        if len(transitions) != 1 or state['m_NameID'] in seen:
            raise ValueError(f'{controller.peek_name()}: ambiguous default action entry')
        seen.add(state['m_NameID'])
        transition = transitions[0]['data']
        if transition['m_ConditionConstantArray']:
            raise ValueError(f'{controller.peek_name()}: conditional default action entry')
        state = machine['m_StateConstantArray'][transition['m_DestinationState']]['data']
    nodes = state['m_BlendTreeConstantArray'][0]['data']['m_NodeArray']
    if len(nodes) != 1 or nodes[0]['data']['m_ChildIndices']:
        raise ValueError(f'{controller.peek_name()}: unsupported default-state blend tree')
    return clips[nodes[0]['data']['m_ClipID']].read().m_Name, pose_clip


def export_motions(controller, baked: dict, description: str = '') -> dict[str, dict]:
    tree = controller.read_typetree()
    strings = dict(tree['m_TOS'])
    source_controller = tree['m_Controller']
    base_layers = [layer['data'] for layer in source_controller['m_LayerArray']
                   if strings[layer['data']['m_Binding']] == 'Base Layer']
    if len(base_layers) != 1:
        raise ValueError(f'{controller.peek_name()}: expected one Base Layer')
    machine = source_controller['m_StateMachineArray'][base_layers[0]['m_StateMachineIndex']]['data']
    source_states = [item['data'] for item in machine['m_StateConstantArray']]
    clip_names = [pointer.read().m_Name for pointer in controller.read().m_AnimationClips]
    if baked.get('schemaVersion') != 8:
        raise ValueError('Yohane body bake must use the current baked motion schema')
    clips = {}
    for original in baked.get('clips', []):
        clip = copy.deepcopy(original)
        name = clip['name']
        if name in clips:
            raise ValueError(f'Duplicate baked clip {name}')
        clip['id'] = name
        for track in clip['tracks']:
            if not track.get('translation'):
                track.pop('translation', None)
        clips[name] = clip
    states = []
    for source in source_states:
        trees = source['m_BlendTreeConstantArray']
        if not trees:
            # Original controllers include terminal empty editor states. They
            # remain in the source index space but contain no animation asset.
            states.append(None)
            continue
        nodes = trees[0]['data']['m_NodeArray'] if len(trees) == 1 else []
        if (len(nodes) != 1 or nodes[0]['data']['m_ChildIndices']
                or source['m_Mirror'] or source['m_CycleOffset']):
            raise ValueError(f'{controller.peek_name()}: unsupported Base Layer blend tree/mirror/cycle offset')
        name = clip_names[nodes[0]['data']['m_ClipID']]
        if name not in clips:
            raise ValueError(f'{controller.peek_name()}: missing baked body clip {name}')
        states.append({'id': strings[source['m_NameID']], 'clip': name,
                       'speed': source['m_Speed'], 'loop': source['m_Loop'], 'transitions': []})
    incoming = {}
    for index, source in enumerate(source_states):
        if states[index] is None:
            if source['m_TransitionConstantArray']:
                raise ValueError(f'{controller.peek_name()}: unsupported animated transition from an empty state')
            continue
        for wrapped in source['m_TransitionConstantArray']:
            transition = wrapped['data']
            if (transition['m_ConditionConstantArray'] or not transition['m_HasExitTime']
                    or not transition['m_HasFixedDuration']):
                raise ValueError(f'{controller.peek_name()}: unsupported conditional/timed Base Layer transition')
            target = transition['m_DestinationState']
            if not 0 <= target < len(states) or states[target] is None:
                raise ValueError(f'{controller.peek_name()}: transition destination is not a body state')
            states[index]['transitions'].append({'to': states[target]['id'],
                'exitTime': transition['m_ExitTime'], 'duration': transition['m_TransitionDuration'],
                'offset': transition['m_TransitionOffset'], 'conditions': []})
            incoming.setdefault(target, []).append(index)
    actions = {}
    for index, state in enumerate(states):
        if state is None:
            continue
        if state['transitions']:
            continue
        indices = [index]
        cursor = index
        while cursor in incoming:
            predecessors = incoming[cursor]
            if len(predecessors) != 1 or predecessors[0] in indices:
                raise ValueError(f'{controller.peek_name()}/{state["id"]}: ambiguous action entry')
            cursor = predecessors[0]
            if states[cursor]['loop'] or len(states[cursor]['transitions']) != 1:
                raise ValueError(f'{controller.peek_name()}: unsupported looping/branching action entry')
            indices.insert(0, cursor)
        selected = [states[i] for i in indices]
        name = state['clip']
        if name in actions:
            raise ValueError(f'{controller.peek_name()}: multiple actions use clip {name}')
        label = LABELS.get(name.split('_')[1] if '_' in name else name, '')
        actions[name] = {'type': 'motion', 'name': name,
            'description': ' '.join(part for part in (description, label) if part),
            'clips': [clips[s['clip']] for s in selected],
            'auxiliaryClips': [], 'leftHandPoses': [], 'rightHandPoses': [],
            'program': {'parameters': [], 'commands': {}, 'baseLayer': 'base', 'poseSlots': [],
                'layers': [{'id': 'base', 'blend': 'override', 'weight': 1,
                            'initialState': selected[0]['id'], 'states': selected}]}}
    if not actions:
        raise ValueError(f'{controller.peek_name()}: no supported terminal story actions')
    return actions
