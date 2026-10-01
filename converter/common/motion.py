from __future__ import annotations

from pathlib import Path
from typing import Any

import UnityPy


def motion_clip_ids(data: dict[str, Any]) -> dict[str, str]:
    """Assign stable ids to every clip referenced by a baked motion file."""
    result: dict[str, str] = {}
    groups = (
        ("clips", "clip"),
        ("auxiliaryClips", "auxiliary"),
        ("leftHandPoses", "leftPose"),
        ("rightHandPoses", "rightPose"),
    )
    for field, prefix in groups:
        for index, clip in enumerate(data.get(field, [])):
            clip_id = str(clip.get("name", "")) or f"{prefix}{index}"
            if clip_id in result:
                raise ValueError(f"Duplicate motion clip name: {clip_id}")
            clip["id"] = clip_id
            result[clip_id] = clip_id
    return result


def controller_program(bundle_path: Path, data: dict[str, Any]) -> dict[str, Any] | None:
    """Compile a Unity AnimatorController into an engine-neutral state graph."""
    environment = UnityPy.load(str(bundle_path))
    objects = {obj.path_id: obj for obj in environment.objects}
    controllers = [obj for obj in environment.objects if obj.type.name == "AnimatorController"]
    if not controllers:
        return None
    controller = controllers[0].read_typetree()
    compiled = controller["m_Controller"]
    strings = dict(controller.get("m_TOS", []))
    source_clip_names: list[str] = []
    for pointer in controller.get("m_AnimationClips", []):
        target = objects.get(pointer.get("m_PathID", 0))
        source_clip_names.append(target.read_typetree().get("m_Name", "") if target else "")
    clip_ids = motion_clip_ids(data)

    value_entries = compiled.get("m_Values", {}).get("data", {}).get("m_ValueArray", [])
    defaults = compiled.get("m_DefaultValues", {}).get("data", {})
    bool_defaults = defaults.get("m_BoolValues", [])
    parameters: list[dict[str, Any]] = []
    parameter_by_hash: dict[int, str] = {}
    for entry in value_entries:
        if entry.get("m_Type") != 9:
            continue
        parameter_id = strings.get(int(entry["m_ID"])) or f"parameter{len(parameters)}"
        value_index = int(entry.get("m_Index", 0))
        default = bool(bool_defaults[value_index]) if value_index < len(bool_defaults) else False
        parameters.append({"id": parameter_id, "type": "bool", "default": default})
        parameter_by_hash[int(entry["m_ID"])] = parameter_id

    layers = compiled.get("m_LayerArray", [])
    machines = compiled.get("m_StateMachineArray", [])
    if not layers or not machines:
        return None

    def build_states(machine: dict[str, Any]) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        raw_states = machine.get("m_StateConstantArray", [])
        state_ids = [
            strings.get(int(wrapped["data"].get("m_NameID", 0))) or f"state{index}"
            for index, wrapped in enumerate(raw_states)
        ]
        if len(set(state_ids)) != len(state_ids):
            raise ValueError(f"{bundle_path.name}: duplicate state names are not supported")
        for state_index, wrapped_state in enumerate(raw_states):
            state = wrapped_state["data"]
            trees = state.get("m_BlendTreeConstantArray", [])
            nodes = trees[0]["data"].get("m_NodeArray", []) if trees else []
            if len(nodes) != 1:
                raise ValueError(f"{bundle_path.name}: only single-clip states are currently supported")
            clip_index = int(nodes[0]["data"]["m_ClipID"])
            clip_id = clip_ids.get(source_clip_names[clip_index])
            if clip_id is None:
                continue
            transitions: list[dict[str, Any]] = []
            for wrapped_transition in state.get("m_TransitionConstantArray", []):
                transition = wrapped_transition["data"]
                conditions: list[dict[str, Any]] = []
                for wrapped_condition in transition.get("m_ConditionConstantArray", []):
                    condition = wrapped_condition["data"]
                    parameter = parameter_by_hash.get(int(condition["m_EventID"]))
                    mode = int(condition["m_ConditionMode"])
                    if parameter is None or mode not in {1, 2}:
                        raise ValueError(f"{bundle_path.name}: unsupported Animator condition")
                    conditions.append({
                        "parameter": parameter,
                        "operator": "isTrue" if mode == 1 else "isFalse",
                    })
                transitions.append({
                    "to": state_ids[int(transition["m_DestinationState"])],
                    "exitTime": float(transition["m_ExitTime"]) if transition.get("m_HasExitTime") else None,
                    "duration": float(transition.get("m_TransitionDuration", 0.0)),
                    "offset": float(transition.get("m_TransitionOffset", 0.0)),
                    "conditions": conditions,
                })
            result.append({
                "id": state_ids[state_index],
                "clip": clip_id,
                "speed": float(state.get("m_Speed", 1.0)),
                "loop": bool(state.get("m_Loop", False)),
                "transitions": transitions,
            })
        resolved_ids = {state["id"] for state in result}
        for state in result:
            state["transitions"] = [t for t in state["transitions"] if t["to"] in resolved_ids]
        return result

    base_layer = layers[0]["data"]
    machine = machines[int(base_layer["m_StateMachineIndex"])]["data"]
    states = build_states(machine)
    if not states:
        return None

    stop_commands: list[dict[str, Any]] = []
    for state in states:
        for transition in state["transitions"]:
            if transition["exitTime"] is None and len(transition["conditions"]) == 1:
                condition = transition["conditions"][0]
                if condition["operator"] == "isTrue":
                    stop_commands = [{"parameter": condition["parameter"], "value": True}]
                    break
        if stop_commands:
            break

    pose_slots = []
    for slot_id, field in (("leftHand", "leftHandPoses"), ("rightHand", "rightHandPoses")):
        options = [{"id": clip["name"], "clip": clip["id"]} for clip in data.get(field, [])]
        if options:
            pose_slots.append({"id": slot_id, "default": options[0]["id"], "options": options})

    base_layer_id = strings.get(int(base_layer.get("m_Binding", 0))) or "Base Layer"
    base_initial_index = int(machine.get("m_DefaultState", 0))
    program_layers = [{
        "id": base_layer_id,
        "blend": "override",
        "weight": 1.0,
        "initialState": states[base_initial_index]["id"],
        "states": states,
    }]
    for layer_index, wrapped_layer in enumerate(layers[1:], 1):
        layer = wrapped_layer["data"]
        weight = float(layer.get("m_DefaultWeight", 0.0))
        blend_mode = int(layer.get("(int&)m_LayerBlendingMode", 0))
        if weight <= 0 or blend_mode != 1:
            continue
        layer_machine = machines[int(layer["m_StateMachineIndex"])]["data"]
        layer_states = build_states(layer_machine)
        if not layer_states:
            continue
        layer_id = strings.get(int(layer.get("m_Binding", 0))) or f"Layer {layer_index}"
        initial_index = int(layer_machine.get("m_DefaultState", 0))
        program_layers.append({
            "id": layer_id,
            "blend": "additive",
            "weight": weight,
            "initialState": layer_states[initial_index]["id"],
            "states": layer_states,
        })

    return {
        "parameters": parameters,
        "commands": {"stop": stop_commands},
        "baseLayer": base_layer_id,
        "layers": program_layers,
        "poseSlots": pose_slots,
    }
