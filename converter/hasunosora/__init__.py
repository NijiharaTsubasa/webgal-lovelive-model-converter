"""Hasu-no-Sora (蓮ノ空) AssetBundle -> standardized character package.

This is the per-game converter. It walks the Hasu input directory, finds
character body bundles, exports each one through the generic Unity -> glTF
pipeline in :mod:`converter.common`, and (for characters that ship an
expression_controller) additionally exports a per-character expression
package (named Morph recipes, independent face/mouth groups and presets).

Anything generic (GLB writer, packed-clip decoder and normalized-model
exporter) lives in :mod:`converter.common`. What stays here is the Hasu-specific
glue:
    - how to recognise a character bundle in a sea of Hasu CABs,
    - how to extract the character's Unity skeleton name,
    - how to detect that a character ships an expression controller,
    - how to walk the controller's face/mouth blend trees and produce the
      {name, face, blink, mouth[]} records consumed by build_expression_package.

The motion controller compiler also stays here because its bundle naming,
parameters and layer layout are Hasu source conventions rather than a common
Unity contract.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import UnityPy

from ..common.component_order import order_model_component
from ..common.idle_pose import sample_baked_pose
from ..common.physics import extract_model_physics
from ..common import (
    bundle_metadata,
    component_pointer,
    controller_clip_objects,
    dependency_closure,
    game_object_transform,
    logical_name,
    object_id,
    packed_clip_values,
    safe_name,
)
from ..common.normalized_model import (
    FaceBonesCopierAdapter,
    NormalizedExport,
    export_normalized_model,
)
from .motion import collect_baked_motions, write_motion_index
from .materials import adapt_material
from .source import discover_inputs
from .identity import SUPPLEMENTAL_COSTUMES, load_costume_motion_groups
from .sub_bone import extract_sub_bone_behavior
from ..common.cli import configure_output


@dataclass
class ExportedExpression:
    """One named expression discovered from the controller.

    `face` is the full-face pose; `blink` is the same expression while the
    eye-blink parameter is active (used to derive this expression's blink
    endpoint); `mouth` is either one fixed clip or the six lip-shape clips
    [close, a, i, u, e, o]."""

    name: str
    face: Any
    blink: Any | None
    mouth: list[Any]


def character_identity(root: Any) -> str:
    """Return the Unity skeleton name from the character's body node."""
    stack = [game_object_transform(root)]
    body_name = None
    while stack:
        transform = stack.pop()
        name = transform.m_GameObject.deref_parse_as_object().m_Name
        if re.fullmatch(r"SCSch\d+[A-Za-z]+(?:_fb)?", name):
            body_name = name.removesuffix("_fb")
        stack.extend(pointer.deref_parse_as_object() for pointer in transform.m_Children if pointer)
    if body_name is None:
        raise ValueError("Hasu character bundle has no SCSch body object")
    return safe_name(body_name)


def has_expression_controller(dependencies: list[str]) -> bool:
    return any("expression_controller.controller" in name.lower() for name in dependencies)


class HasunosoraModelAdapter(FaceBonesCopierAdapter):
    """Ignore only unbound renderers excluded by the source mesh registry."""

    adapt_material = staticmethod(adapt_material)

    def copied_bone_keys(self, redirects: dict[tuple[int, int], int]) -> frozenset[tuple[int, int]]:
        # APK 5.1.0 FaceBonesCopier.LateUpdate (RVA 0x4F4B130): spine03
        # copies world position/rotation; neck, head and eyes copy local rotation.
        # The serialized face rig may start at origin, so its helpers must
        # follow the copied body bones instead of keeping that original offset.
        return frozenset(redirects)

    def local_rotation_copy_keys(
        self, redirects: dict[tuple[int, int], int], standard_bones: dict[str, int],
    ) -> frozenset[tuple[int, int]]:
        # LateUpdate calls get/set_localRotation for neck, head and both eyes;
        # only spine03 calls get/set_position and get/set_rotation.
        return frozenset(key for key, node in redirects.items()
                         if node != standard_bones.get("UpperChest"))

    SHADERS = {
        "MELPOT/Toon/UberToonShader": "melpot-toon",
        "MELPOT/Toon/UberToonShader(HLSLMacros)": "melpot-toon-hlslmacros",
        "MELPOT/Toon/UberToonShader_Eye": "melpot-toon-eye",
        "Character/ToonShader_CharacterEye": "character-eye",
        "Character/ToonShader_CharacterHighlight": "character-highlight",
        "Character/Highlight_Distortion": "highlight-distortion",
        "Universal Render Pipeline/Lit": "urp-lit",
    }

    @classmethod
    def classify_shader(cls, material: Any) -> str:
        shader_pointer = getattr(material, "m_Shader", None)
        if not shader_pointer:
            raise ValueError(f"{material.m_Name}: source Shader pointer is missing")
        shader = shader_pointer.deref_parse_as_object()
        source_name = shader.m_ParsedForm.m_Name
        try:
            return cls.SHADERS[source_name]
        except KeyError as exc:
            raise ValueError(f"{material.m_Name}: unsupported source Shader {source_name!r}") from exc

    def __init__(self, environment: Any, root: Any) -> None:
        super().__init__(environment)
        self.registered_renderers: set[tuple[int, int]] = set()
        stack = [game_object_transform(root)]
        while stack:
            transform = stack.pop()
            game_object = transform.m_GameObject.deref_parse_as_object()
            for entry in game_object.m_Component:
                pointer = component_pointer(entry)
                if not pointer or pointer.type.name != "MonoBehaviour":
                    continue
                component = pointer.deref_parse_as_object()
                script = component.m_Script.deref_parse_as_object() if component.m_Script else None
                if not script or getattr(script, "m_ClassName", None) != "CharacterMeshReference":
                    continue
                for category in component.categorizedMeshRenderers:
                    for renderer_pointer in category.meshRenderers:
                        if renderer_pointer:
                            self.registered_renderers.add(object_id(renderer_pointer.deref_parse_as_object()))
            stack.extend(child.deref_parse_as_object() for child in transform.m_Children if child)

    def should_export_renderer(self, renderer: Any) -> bool:
        if not any(not bone for bone in getattr(renderer, "m_Bones", [])):
            return True
        return object_id(renderer) in self.registered_renderers


def _expression_controller_data(environment: Any) -> list[ExportedExpression] | None:
    """Parse the character's expression AnimatorController into a flat list of
    ExportedExpression. Returns None if no AnimatorController is present.

    Hasu's controller layout:
        layer 0 = face layer  (root blend tree: face_states, each keyed by
                                expression_<name>. Some states are nested
                                1D sub-trees with an open clip and a -blink
                                clip.)
        layer 1 = mouth layer (root blend tree: mouth_states, each keyed by
                                expression_<name>. A child is either a single
                                static mouth clip or a 6-leaf direct blend
                                tree keyed by lip_<close,a,i,u,e,o>.)
    """
    controllers = [obj for obj in environment.objects if obj.type.name == "AnimatorController"]
    if not controllers:
        return None
    controller_obj = controllers[0]
    tree = controller_obj.read_typetree()
    strings = dict(tree.get("m_TOS", []))
    compiled = tree["m_Controller"]
    clips = controller_clip_objects(controller_obj, tree)

    param_by_hash: dict[int, str] = {}
    for entry in compiled["m_Values"]["data"]["m_ValueArray"]:
        param_by_hash[int(entry["m_ID"])] = strings.get(int(entry["m_ID"])) or ""

    machines = compiled["m_StateMachineArray"]
    layers = compiled["m_LayerArray"]

    def blend_root(layer_index: int) -> Any:
        machine = machines[int(layers[layer_index]["data"]["m_StateMachineIndex"])]["data"]
        return machine["m_StateConstantArray"][0]["data"]["m_BlendTreeConstantArray"][0]["data"]

    face_nodes = [w["data"] for w in blend_root(0)["m_NodeArray"]]
    mouth_nodes = [w["data"] for w in blend_root(1)["m_NodeArray"]]

    def direct_children(root: dict[str, Any], nodes: list[dict[str, Any]]) -> list[tuple[str, dict[str, Any]]]:
        data = root["m_BlendDirectData"]["data"]
        if int(root["m_BlendType"]) != 4 or data["m_NormalizedBlendValues"]:
            raise ValueError("Hasunosora expressions require the verified non-normalizing Direct Blend Tree")
        direct = data["m_ChildBlendEventIDArray"]
        if len(direct) != len(root["m_ChildIndices"]):
            raise ValueError("Hasunosora Direct Blend Tree parameter/child count mismatch")
        return [(param_by_hash.get(int(hash_value), ""), nodes[int(index)])
                for hash_value, index in zip(direct, root["m_ChildIndices"])]

    def clip_at(node: dict[str, Any]) -> Any:
        return clips[int(node["m_ClipID"])]

    expressions: dict[str, ExportedExpression] = {}
    for param, child in direct_children(face_nodes[0], face_nodes):
        if not param.startswith("expression_"):
            continue
        name = param[len("expression_"):]
        face: Any = None
        blink: Any = None
        if int(child["m_ClipID"]) == 4294967295:
            thresholds = child["m_Blend1dData"]["data"]["m_ChildThresholdArray"]
            child_indices = child["m_ChildIndices"]
            if (int(child["m_BlendType"]) != 0
                    or param_by_hash.get(int(child["m_BlendEventID"])) != "blink"
                    or (thresholds, len(child_indices)) not in (([0.0], 1), ([0.0, 1.0], 2))):
                raise ValueError(f"Hasunosora {name!r} uses an unverified blink Blend Tree")
            sub = [face_nodes[int(index)] for index in child_indices]
            face = clip_at(sub[0])
            if len(sub) == 2:
                blink = clip_at(sub[1])
        else:
            face = clip_at(child)
        expressions[name] = ExportedExpression(name, face, blink, [])

    for param, child in direct_children(mouth_nodes[0], mouth_nodes):
        if not param.startswith("expression_"):
            continue
        name = param[len("expression_"):]
        if name not in expressions:
            continue
        if int(child["m_ClipID"]) != 4294967295:
            expressions[name].mouth = [clip_at(child)]
        else:
            mouth_children = dict(direct_children(child, mouth_nodes))
            lip_names = [f"lip_{lip}" for lip in ("close", "a", "i", "u", "e", "o")]
            if set(mouth_children) != set(lip_names):
                raise ValueError(f"Hasunosora {name!r} requires its six named source mouth parameters")
            expressions[name].mouth = [clip_at(mouth_children[lip]) for lip in lip_names]

    return [entry for entry in expressions.values() if entry.face is not None]


def _clip_pose(clip: Any, model: NormalizedExport) -> dict[tuple[int, int, str], float]:
    """Read every morph weight from a single AnimationClip and map it onto
    the (node, target_index, target_name) triples that the exported model
    actually owns. Returns the union of bindings present in the clip —
    missing morphs are silently skipped because the renderer should treat
    absent targets as zero."""
    bindings = clip.m_ClipBindingConstant.genericBindings
    constant, _curves = packed_clip_values(clip)
    packed = clip.m_MuscleClip.m_Clip.data
    base = packed.m_StreamedClip.curveCount + packed.m_DenseClip.m_CurveCount
    pose: dict[tuple[int, int, str], float] = {}
    for index, binding in enumerate(bindings):
        candidates = model.morph_targets.get(int(binding.attribute), [])
        if not candidates:
            continue
        if index < base:
            raise ValueError(
                f"Hasunosora facial clip {clip.m_Name!r} has a dynamic Morph curve; "
                "static expression endpoints cannot represent its time-dependent pose"
            )
        if index - base >= len(constant):
            raise ValueError(f"Hasunosora facial clip {clip.m_Name!r} has no value for Morph binding {index}")
        value = constant[index - base]
        weight = float(value) / 100.0
        if not math.isfinite(weight):
            raise ValueError(f"Hasunosora facial clip {clip.m_Name!r} has a non-finite Morph weight")
        for node, target_index, name in candidates:
            pose[(node, target_index, name)] = weight
    return pose


def _pose_targets(model: NormalizedExport, pose: dict[tuple[int, int, str], float]) -> dict[str, dict[str, float]]:
    """Group a (node, target_index, name) -> weight mapping by the node's
    human-readable glTF name, ready for the config.json `targets` field."""
    targets: dict[str, dict[str, float]] = {}
    for (node, _target_index, name), weight in sorted(pose.items()):
        node_name = str(model.builder.document["nodes"][node].get("name", ""))
        targets.setdefault(node_name, {})[name] = weight
    return targets


def build_expression_package(
    model: NormalizedExport,
    controller_data: list[ExportedExpression],
) -> dict[str, Any]:
    """Export source recipes and independently selectable face/mouth states.

    Blink replaces the source face recipe; each mouth state owns its six
    source recipes. High-level viseme interpolation is a consumer adaptation,
    not a claim about arbitrary source Direct Blend Tree inputs.
    """
    result: dict[str, Any] = {"morphPoses": [], "expressionGroups": [], "expressions": []}
    face_states: list[dict[str, Any]] = []
    mouth_states: list[dict[str, Any]] = []

    def add_pose(name: str, pose: dict[tuple[int, int, str], float]) -> str:
        if any(not math.isfinite(value) for value in pose.values()):
            raise ValueError(f"Hasunosora {name!r} has a non-finite Morph weight")
        if any(existing["name"] == name for existing in result["morphPoses"]):
            raise ValueError(f"Hasunosora repeats Morph recipe {name!r}")
        result["morphPoses"].append({"name": name, "targets": _pose_targets(model, pose)})
        return name

    for entry in controller_data:
        snapshot = _clip_pose(entry.face, model)
        mouth_poses = []
        if entry.mouth:
            if len(entry.mouth) not in (1, 6) or any(clip is None for clip in entry.mouth):
                raise ValueError(f"Hasunosora expression {entry.name!r} has an invalid source mouth clip set")
            mouth_poses = [_clip_pose(clip, model) for clip in entry.mouth]
        mouth_keys = set().union(*mouth_poses)
        # Layer ownership follows source mouth bindings, not Morph names.
        # The previous full-face snapshot used the mouth layer on these keys;
        # remove that duplicated contribution when making groups independent.
        face_pose = add_pose(f"face.{entry.name}", {key: value for key, value in snapshot.items()
                                                  if key not in mouth_keys})
        face_state: dict[str, Any] = {"name": entry.name, "poses": {face_pose: 1}}
        if entry.blink is not None:
            blink_pose = _clip_pose(entry.blink, model)
            blink_pose = {key: value for key, value in blink_pose.items() if key not in mouth_keys}
            if any(abs(snapshot.get(key, 0) - blink_pose.get(key, 0)) > 1e-6
                   for key in (set(snapshot) | set(blink_pose)) - mouth_keys):
                blink_name = add_pose(f"face.{entry.name}.blink", blink_pose)
                face_state["controls"] = {"blink": {face_pose: 0, blink_name: 1}}
        face_states.append(face_state)

        mouth_state: dict[str, Any] = {"name": entry.name, "poses": {}}
        if len(mouth_poses) == 1:
            mouth_pose = add_pose(f"mouth.{entry.name}", mouth_poses[0])
            mouth_state["poses"] = {mouth_pose: 1}
        elif mouth_poses:
            lips = {lip: add_pose(f"mouth.{entry.name}.{lip}", pose)
                    for lip, pose in zip(("close", "a", "i", "u", "e", "o"), mouth_poses)}
            mouth_state["poses"] = {lips["close"]: 1}
            visemes = {lip: {lips["close"]: 0, lips[lip]: 1} for lip in "aiueo"}
            mouth_state["controls"] = {
                "speech": dict(visemes["a"]), "visemes": visemes,
            }
        mouth_states.append(mouth_state)
        result["expressions"].append({"name": entry.name,
                                      "selections": {"face": entry.name, "mouth": entry.name}})
    if face_states:
        result["expressionGroups"] = [{"name": "face", "states": face_states},
                                      {"name": "mouth", "states": mouth_states}]
        result["defaultExpression"] = next((entry["name"] for entry in result["expressions"]
                                             if entry["name"] == "normal"), result["expressions"][0]["name"])
    return result


def convert(
    input_dir: Path, output_dir: Path, baked_dir: Path | None, clean: bool,
    *, model_names: list[str] | None = None, models_only: bool = False,
) -> None:
    """Hasu-specific conversion driver.

    Discovers every 3d_costume_<id>.assetbundle in `input_dir`, treats each
    one as a character bundle, normalises it via Unity-side baking (when
    available), exports to glTF via the generic pipeline, and emits the
    standardized config.json. The hasunosora/motions output is produced by
    collect_baked_motions (which compiles each baked JSON's AnimatorController
    sibling through the common motion pipeline).

    Multi-game layout: characters and motions go into `<output_dir>/hasunosora/`,
    shader and Behavior packages are published separately. The
    top-level `index.json` is owned by convert.py — this function only writes
    the per-game index."""
    index, _, motion_bundles = discover_inputs(input_dir)
    model_bundles = sorted((path for name, path in index.items() if name.startswith("3d")),
                           key=lambda path: path.name)
    if not model_bundles and (models_only or not motion_bundles):
        if model_names:
            raise ValueError(f"Hasunosora requested models not found: {sorted(set(model_names))}")
        print(f"[hasunosora:convert] 输入为空: {input_dir}")
        return
    game_dir = output_dir / "hasunosora"
    if clean and game_dir.exists():
        shutil.rmtree(game_dir)
    game_dir.mkdir(parents=True, exist_ok=True)
    costume_labels = load_costume_labels(input_dir)
    costume_motion_groups = load_costume_motion_groups(input_dir)
    idle_defaults = hasunosora_idle_defaults(input_dir, baked_dir)

    motions = []
    if not models_only:
        motion_output = game_dir / "motions"
        motions = collect_baked_motions(baked_dir, input_dir, motion_output)
        write_motion_index(motion_output, motions)

    packages = []
    requested = set(model_names or [])
    matched = set()
    for model_bundle in model_bundles:
        package_name = model_bundle.stem
        if requested and package_name not in requested:
            continue
        closure = dependency_closure(model_bundle, index)
        environment = UnityPy.load(*map(str, closure))
        bundle_name, dependencies = bundle_metadata(model_bundle)
        containers = dict(environment.container.items())
        root_pointer = containers.get(bundle_name) or containers.get(model_bundle.stem)
        if not root_pointer:
            raise RuntimeError(f"Could not find root container for {model_bundle.name}")
        root = root_pointer.deref_parse_as_object()
        body_name = character_identity(root)
        matched.add(package_name)
        norm_data = _load_normalized(baked_dir, package_name)
        if norm_data is None:
            raise FileNotFoundError(f"Normalized skeleton data not found for {model_bundle.name}")
        source_character = norm_data.get("sourceCharacter")
        if not isinstance(source_character, str) or source_character.casefold() != body_name.casefold():
            raise ValueError(f"Normalized skeleton source does not match {model_bundle.name}: "
                             f"{source_character!r} != {body_name!r}")
        exported = export_normalized_model(
            environment, root_pointer, norm_data,
            adapter=HasunosoraModelAdapter(environment, root),
        )
        physics = extract_model_physics(environment, exported)
        behaviors = extract_sub_bone_behavior(root, exported)

        if has_expression_controller(dependencies):
            controller_data = _expression_controller_data(environment)
            if controller_data:
                expressions = build_expression_package(exported, controller_data)
            else:
                expressions = build_expression_package(exported, [])
        else:
            expressions = build_expression_package(exported, [])
        package_dir = game_dir / package_name
        package_dir.mkdir(parents=True, exist_ok=True)
        exported.builder.write(package_dir / "model.glb")

        model_component = {
            "role": "integrated",
            "model": "model.glb",
            **expressions,
            "humanoidScale": exported.human_scale,
            **idle_defaults,
            **({"physics": physics} if physics else {}),
            **({"behaviors": behaviors} if behaviors else {}),
        }
        config = {
            "components": [order_model_component({
                "type": "model",
                "name": package_name,
                **({"description": costume_labels[package_name]} if package_name in costume_labels else {}),
                "group": "hasunosora",
                **({"motionGroup": costume_motion_groups[package_name]}
                   if package_name in costume_motion_groups else {}),
                **model_component,
            })],
        }
        (package_dir / "config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        packages.append(f"{package_name}/config.json")
        print(f"[character] [normalized] {model_bundle.name} -> {package_name} ({len(expressions['expressions'])} expressions)")

    if requested - matched:
        raise ValueError(f"Hasunosora requested models not found: {sorted(requested - matched)}")
    configs = sorted(
        f"{directory.name}/config.json"
        for directory in game_dir.iterdir()
        if directory.is_dir() and (directory / "config.json").is_file()
    )
    (game_dir / "index.json").write_text(json.dumps({"configs": configs}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[done] {len(packages)} character packages, {len(motions)} baked motion files")


def hasunosora_idle_defaults(input_dir: Path, baked_dir: Path | None) -> dict[str, Any]:
    motion_name = "mot_00_00010"
    baked_file = baked_dir / f"{motion_name}.baked.json" if baked_dir else None
    if not baked_file or not baked_file.is_file() or not (input_dir / f"{motion_name}.assetbundle").is_file():
        return {}
    return {
        "defaultMotion": f"hasunosora/{motion_name}",
        "idlePose": sample_baked_pose(baked_file, "m_00_00010@o", -1),
    }


def load_costume_labels(input_dir: Path) -> dict[str, str]:
    """Read master costume labels and the two supplemental source-bundle labels."""
    source = input_dir / "CostumeModels.yaml"
    if not source.is_file():
        return dict(SUPPLEMENTAL_COSTUMES)
    import yaml

    records = yaml.safe_load(source.read_text(encoding="utf-8"))
    if not isinstance(records, list):
        raise ValueError(f"{source}: expected a list of costume records")
    labels = dict(SUPPLEMENTAL_COSTUMES)
    labels.update({
        f"3d_costume_{record['Id']}": record["Label"]
        for record in records
        if isinstance(record, dict)
        and isinstance(record.get("Id"), int)
        and isinstance(record.get("Label"), str)
        and record["Label"]
    })
    return labels


def _load_normalized(baked_dir: Path | None, package_name: str) -> dict[str, Any] | None:
    """Resolve the Unity-side baked normalized skeleton for a character.

    Returns None when the required file is missing; the caller then stops the
    conversion instead of exporting an approximate raw bind pose."""
    if not baked_dir:
        return None
    candidate = baked_dir / "normalized" / f"{safe_name(package_name)}.skeleton.json"
    if not candidate.exists():
        return None
    return json.loads(candidate.read_text(encoding="utf-8"))


def main() -> None:
    configure_output()
    parser = argparse.ArgumentParser(description="Convert Hasu-no-Sora AssetBundles to standalone character packages.")
    parser.add_argument("--input", type=Path, default=Path("input_hasunosora"))
    parser.add_argument("--output", type=Path, default=Path("output_packages"))
    parser.add_argument("--baked", type=Path, default=Path("baked_motions"), help="Unity-baked generic motion directory.")
    parser.add_argument("--clean", action="store_true", help="Remove the output directory before conversion.")
    parser.add_argument("--model", action="append", help="Convert only this exact 3d_costume bundle name; repeat for multiple models.")
    parser.add_argument("--models-only", action="store_true", help="Skip motion collection and output.")
    args = parser.parse_args()
    convert(args.input.resolve(), args.output.resolve(), args.baked.resolve(), args.clean,
            model_names=args.model, models_only=args.models_only)


if __name__ == "__main__":
    main()
