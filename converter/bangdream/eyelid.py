"""Bind the separately authored eye-crease strips to their GLB vertices."""
from __future__ import annotations

import re

import numpy as np

from ..common.unity import object_id


def _accessor(builder, index):
    accessor = builder.document["accessors"][index]
    view = builder.document["bufferViews"][accessor["bufferView"]]
    dtype = np.dtype({5121: "u1", 5123: "<u2", 5125: "<u4", 5126: "<f4"}[accessor["componentType"]])
    width = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}[accessor["type"]]
    return np.ndarray((accessor["count"], width), dtype=dtype, buffer=builder.binary,
                      offset=view.get("byteOffset", 0) + accessor.get("byteOffset", 0),
                      strides=(view.get("byteStride", width * dtype.itemsize), dtype.itemsize))


def _components(triangles):
    parent = {int(i): int(i) for i in triangles.flat}

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for triangle in triangles:
        root = find(int(triangle[0]))
        for i in triangle[1:]:
            parent[find(int(i))] = root
    groups = {}
    for i in parent:
        groups.setdefault(find(i), []).append(i)
    return list(groups.values())


def identify_eyelid_vertices(positions, uv, triangles, image, eye_midline):
    """Find crease backing plates and their matching ink in a face primitive.

    The source face atlas uses rosy backing plates both for the upper crease
    and for the eyelid rim immediately above the lashes. The uppermost plate
    belongs to the crease. Its coincident-position components contain the ink
    and any separately indexed plate pieces. The lower rim stays with the eye.
    """
    pixels = np.asarray(image.convert("RGB"), dtype=np.int16)
    height, width = pixels.shape[:2]
    groups = _components(triangles)
    result = {}
    for side, sign in (("left", 1), ("right", -1)):
        candidates, plates = {}, []
        for group, indices in enumerate(groups):
            points = positions[indices]
            if not np.all(points[:, 0] * sign > 0) or points[:, 1].mean() < eye_midline:
                continue
            members = triangles[np.isin(triangles[:, 0], indices)]
            # Interior samples avoid atlas-island boundary filtering artifacts.
            samples = uv[members].mean(axis=1) % 1
            color = pixels[(samples[:, 1] * height).astype(int),
                           (samples[:, 0] * width).astype(int)]
            candidates[group] = indices
            rosy = ((color[:, 0] > 180) & (color[:, 0] - color[:, 1] > 20)
                    & (np.abs(color[:, 1] - color[:, 2]) < 20))
            if rosy.mean() > .5:
                plates.append(group)
        if not plates:
            continue
        upper = max(plates, key=lambda group: positions[candidates[group], 1].max())
        selected = {upper}
        points = {tuple(point) for point in positions[candidates[upper]]}
        pending = set(candidates).difference(selected)
        while pending:
            adjacent = {group for group in pending
                        if any(tuple(point) in points for point in positions[candidates[group]])}
            if not adjacent:
                break
            selected.update(adjacent)
            pending.difference_update(adjacent)
            points.update(tuple(point) for group in adjacent for point in positions[candidates[group]])
        result[side] = sorted(index for group in selected for index in candidates[group])
    return result


def attach_eyelid_bindings(exported, renderer_bindings, *, role):
    if role != "head":
        return
    builder = exported.builder
    document = builder.document
    eyes = [_accessor(builder, primitive["attributes"]["POSITION"])
            for mesh in document["meshes"] if re.match(r"eye(?:[LR])?_", mesh.get("name", ""), re.I)
            for primitive in mesh["primitives"]]
    if not eyes:
        return
    eye_y = np.concatenate(eyes)[:, 1]
    eye_midline = float((eye_y.min() + eye_y.max()) * .5)
    for renderer, mesh_node in renderer_bindings:
        mesh = document["meshes"][document["nodes"][mesh_node]["mesh"]]
        if not re.search(r"face_NoOutline", mesh.get("name", ""), re.I):
            continue
        for primitive in mesh["primitives"]:
            if "TEXCOORD_0" not in primitive["attributes"]:
                continue
            material = next((pointer.deref_parse_as_object() for pointer in renderer.m_Materials
                             if pointer and builder.materials.get(object_id(pointer.deref_parse_as_object()))
                             == primitive.get("material")), None)
            if material is None:
                continue
            environment = next((value for key, value in material.m_SavedProperties.m_TexEnvs
                                if str(getattr(key, "name", key)) == "_MainTex"), None)
            if environment is None or not environment.m_Texture:
                continue
            image = environment.m_Texture.deref_parse_as_object().image
            binding = identify_eyelid_vertices(
                _accessor(builder, primitive["attributes"]["POSITION"]),
                _accessor(builder, primitive["attributes"]["TEXCOORD_0"]),
                _accessor(builder, primitive["indices"]).reshape(-1, 3), image, eye_midline)
            if binding:
                primitive.setdefault("extras", {})["garupaEyelid"] = binding
