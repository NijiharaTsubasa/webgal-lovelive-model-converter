"""Game-agnostic building blocks for converting Unity AssetBundles into
standardized character packages.

Submodules:
    unity   — UnityPy primitives: pointer/object identity, transforms,
              AssetBundle metadata, the external-clip resolver used by every
              AnimatorController reader, plus coordinate-axis conversions.
    shader  — material property fingerprint -> shader-kind identifier and the
              "is this an eye shader?" predicate used to decide whether a
              hidden renderer should still be emitted.
    glb     — GlbBuilder (low-level glTF document + binary chunk writer),
              morph extraction, and renderer compatibility helpers used by
              the Unity-normalized model exporter.
    animation — packed AnimationClip -> keyframes (streamed + dense + constant).
    normalized_model — canonical skeleton validation, skin rebasing and
              normalized Unity -> glTF export with a narrow game-adapter seam.

Anything game-specific (which bundles are characters, how character names
are extracted, how the game's expression controller is interpreted) stays
in the game-specific converter scripts that import from this package.
"""

from .animation import packed_clip_values
from .glb import (
    GlbBuilder,
    mesh_morphs,
    trim_unused_trailing_renderer_bones,
)
from .normalized_model import (
    NormalizedExport,
    NormalizedModelAdapter,
    export_normalized_model,
)
from .shader import renderer_uses_eye_shader, shader_kind
from .unity import (
    COMPONENT_FLOAT,
    COMPONENT_UNSIGNED_BYTE,
    COMPONENT_UNSIGNED_INT,
    COMPONENT_UNSIGNED_SHORT,
    bundle_metadata,
    component_pointer,
    controller_clip_objects,
    crc,
    dependency_closure,
    game_object_transform,
    logical_name,
    matrix,
    object_id,
    pointer_id,
    rotation,
    safe_name,
    vec3,
)

__all__ = [
    "COMPONENT_FLOAT",
    "COMPONENT_UNSIGNED_BYTE",
    "COMPONENT_UNSIGNED_INT",
    "COMPONENT_UNSIGNED_SHORT",
    "GlbBuilder",
    "NormalizedExport",
    "NormalizedModelAdapter",
    "bundle_metadata",
    "component_pointer",
    "controller_clip_objects",
    "crc",
    "dependency_closure",
    "game_object_transform",
    "logical_name",
    "matrix",
    "mesh_morphs",
    "object_id",
    "packed_clip_values",
    "pointer_id",
    "renderer_uses_eye_shader",
    "rotation",
    "safe_name",
    "shader_kind",
    "trim_unused_trailing_renderer_bones",
    "export_normalized_model",
    "vec3",
]
