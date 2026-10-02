"""Source cloth geometry adapted to the generic model physics contract.

This is not a port of SwingBone, SpringBone or Magica's solver. Geometry and explicit
collision associations come from their components; response coefficients are
deliberately conservative defaults for our different, generic solver.
"""

from __future__ import annotations

import math
from dataclasses import replace
from typing import Any

from UnityPy.helpers.MeshHelper import MeshHandler

from .unity import component_pointer, game_object_transform, object_id
from .normalized_model import (
    _mat4_inverse, _mat4_mul, _mat4_transform_point, _trs_to_mat, renderer_node_name,
)


def _read(value: Any) -> Any:
    return value.read() if hasattr(value, "read") else value


def _vector(value: Any) -> list[float]:
    return [float(getattr(value, axis)) for axis in "xyz"]


def _class(component: Any) -> str:
    return str(component.m_Script.read().m_ClassName)


def _transform(component: Any) -> Any:
    return game_object_transform(component.m_GameObject.read())


def spring_bone_tail(component: Any, mapping: Any) -> list[float]:
    """Unity.Animations.SpringBones.ComputeChildPosition, Hasu 5.1.0 RVA 0x4E1A818.

    Pivot children are excluded. Multiple children define a mean world direction
    with their mean distance, not the longest child or the mean local position.
    Only geometry is retained; the generic solver does not port spring forces.
    """
    transform = _transform(component)
    node = mapping.node_index(transform)
    children = []
    for pointer in transform.m_Children:
        child = _read(pointer)
        pivot = False
        for entry in child.m_GameObject.read().m_Component:
            item = component_pointer(entry)
            if item and item.type.name == 'MonoBehaviour' and _class(_read(item)) == 'SpringBonePivot':
                pivot = True
                break
        if not pivot:
            children.append(child)
    if len(children) == 1:
        return mapping.point(children[0], [0., 0., 0.], target_node=node)
    if len(children) > 1 and component.explicitlyChild:
        return mapping.point(_read(component.explicitlyChild), [0., 0., 0.], target_node=node)
    matrix = mapping.canonical_world[node]
    origin = _mat4_transform_point(matrix, [0., 0., 0.])
    if children:
        endpoints = [_mat4_transform_point(matrix, mapping.point(child, [0., 0., 0.], target_node=node))
                     for child in children]
        vectors = [[point[i] - origin[i] for i in range(3)] for point in endpoints]
        direction = [sum(v[i] for v in vectors) / len(vectors) for i in range(3)]
        distance = sum(math.sqrt(sum(x*x for x in v)) for v in vectors) / len(vectors)
    else:
        # Source fallback: world position - transform.right * 0.1.
        end = _mat4_transform_point(matrix, mapping.direction(transform, [-1., 0., 0.]))
        direction = [end[i] - origin[i] for i in range(3)]
        distance = .1
    length = math.sqrt(sum(x*x for x in direction))
    # Unity Vector3.Normalize returns zero at/below 1e-5, measured on the
    # average direction, not the unscaled sum (RVA 0x4E1AAD4).
    endpoint = [origin[i] + (direction[i] * distance / length if length > 1e-5 else 0.) for i in range(3)]
    return list(_mat4_transform_point(_mat4_inverse(matrix), endpoint))


def capsule_endpoints(component: Any, *, magica2: bool) -> tuple[list[float], list[float], float]:
    """Decode Magica geometry, not its dynamics.

    MC1 Length is half the full external length (vendor's 2020-11-15 answer).
    MC2 GetSize/ColliderManager specify full length and optionally start pivot.
    Taper is conservatively enclosed by a constant-radius capsule; this can
    leave a larger gap at its thinner end, but never shrinks the source body.
    """
    center = _vector(component.center)
    if magica2:
        start_radius = float(component.size.x)
        end_radius = float(component.size.y if component.radiusSeparation else component.size.x)
        length = float(component.size.z)
        centered = bool(component.alignedOnCenter)
        start_length = max((length * .5 if centered else 0.) - start_radius, 0.)
        end_length = max((length * .5 if centered else length - start_radius) - end_radius, 0.)
        axis = int(component.direction)
        sign = -1. if component.reverseDirection else 1.
    else:
        start_radius, end_radius = float(component.startRadius), float(component.endRadius)
        start_length = max(float(component.length) - start_radius, 0.)
        end_length = max(float(component.length) - end_radius, 0.)
        axis, sign = int(component.axis), 1.
    if axis not in (0, 1, 2):
        raise ValueError(f"invalid capsule axis {axis}")
    start, end = list(center), list(center)
    start[axis] += sign * start_length
    end[axis] -= sign * end_length
    return start, end, max(start_radius, end_radius)


def magica1_radius(parameter: Any, depth: float) -> float:
    """BezierParam.Evaluate, verified in BG native ELF at RVA 0x58CD70C."""
    t = min(1., max(0., float(depth)))
    start = float(parameter.startValue)
    end = float(parameter.endValue) if parameter.useEndValue else start
    curve = float(parameter.curveValue)
    if parameter.useEndValue and parameter.useCurveValue and curve != 0.:
        control = end + (start - end) * (curve * .5 + .5)
        return (1. - t) ** 2 * start + 2. * (1. - t) * t * control + t * t * end
    return start + (end - start) * t


def animation_curve_value(curve: Any, time: float) -> float:
    """Evaluate unweighted Unity keyframes as cubic Hermite segments.

    Current Hasunosora radius curves all have weightedMode=0. Do not silently
    approximate weighted curves if another source supplies one later.
    """
    keys = curve.m_Curve
    if not keys:
        raise ValueError("physics radius AnimationCurve has no keys")
    if any(int(key.weightedMode) for key in keys):
        raise ValueError("weighted physics radius curves require Unity sampling")
    if time <= keys[0].time:
        return float(keys[0].value)
    if time >= keys[-1].time:
        return float(keys[-1].value)
    for left, right in zip(keys, keys[1:]):
        if time <= right.time:
            duration = float(right.time - left.time)
            if duration <= 0.:
                raise ValueError("physics radius curve times must strictly increase")
            if not math.isfinite(left.outSlope) or not math.isfinite(right.inSlope):
                return float(left.value)
            t = (time - left.time) / duration
            return ((2*t**3 - 3*t*t + 1) * left.value
                    + (t**3 - 2*t*t + t) * duration * left.outSlope
                    + (-2*t**3 + 3*t*t) * right.value
                    + (t**3 - t*t) * duration * right.inSlope)
    raise AssertionError("curve segment missing")


def magica2_radius(parameter: Any, depth: float) -> float:
    """CurveSerializeData's 16 samples followed by DataUtility.EvaluateCurve."""
    if not parameter.useCurve:
        return float(parameter.value)
    scaled = min(1., max(0., depth)) * 15
    index = min(14, int(scaled))
    t = scaled - index
    a = animation_curve_value(parameter.curve, index / 15.)
    b = animation_curve_value(parameter.curve, (index + 1) / 15.)
    return float(parameter.value) * (a + (b - a) * t)


def _magica1_particles(component: Any) -> dict[tuple[int, int], tuple[float, bool, bool]]:
    data = component.clothData.read()
    fields = (data.useVertexList, data.vertexDepthList, data.selectionData)
    if len({len(field) for field in fields}) != 1:
        raise ValueError("Magica1 particle/depth/selection arrays disagree")
    return {object_id(component.useTransformList[int(vertex)].read()):
            (magica1_radius(component.clothParams.radius, float(depth)), int(selection) == 1, True)
            for vertex, depth, selection in zip(*fields)}


def _magica2_particles(component: Any, mapping: Any) -> dict[tuple[int, int], tuple[float, bool, bool]]:
    """Resolve saved spatial selection and metric depth, not hierarchy level.

    Magica2 VirtualMeshProxy.ApplySelectionAttribute maps by nearest position.
    BaseLine_CalcMaxBaseLineLengthJob divides distance to the nearest fixed
    ancestor by the maximum distance across the whole cloth, not each chain.
    """
    selection = component.serializeData2.selectionData
    positions = [[-p.x, p.y, p.z] for p in selection.positions]
    attributes = [int(a.Value) for a in selection.attributes]
    if not positions or len(positions) != len(attributes):
        raise ValueError("Magica2 bone cloth requires valid spatial selection data")
    transforms, parents = {}, {}
    def visit(pointer: Any, parent: tuple[int, int] | None = None) -> None:
        transform = pointer.read()
        key = object_id(transform)
        if key in transforms:
            return
        transforms[key], parents[key] = transform, parent
        for child in transform.m_Children:
            visit(child, key)
    for root in component.serializeData.rootBones:
        if root:
            visit(root)
    cloth = _transform(component)
    inverse = _mat4_inverse(mapping.source_world[mapping.source_nodes[object_id(cloth)]])
    local = {key: _mat4_transform_point(_mat4_mul(inverse, mapping.source_world[mapping.source_nodes[key]]),
                                      [0., 0., 0.]) for key in transforms}
    edges = [math.dist(local[key], local[parent]) for key, parent in parents.items() if parent is not None]
    # MinimumGridSize is 0.00001 in Magica2 Define; the spatial search itself is
    # equivalent to the grid accelerator's nearest match within this radius.
    search_radius = max(sum(edges) / len(edges) if edges else 0., float(selection.maxConnectionDistance), .00001)
    flags = {}
    for key, point in local.items():
        nearest = min(range(len(positions)), key=lambda i: math.dist(point, positions[i]))
        flags[key] = attributes[nearest] if math.dist(point, positions[nearest]) <= search_radius else 0
    distances = {}
    for key in transforms:
        distance, child = 0., key
        if flags[key] & 2:
            parent = parents[child]
            while parent is not None:
                distance += math.dist(local[child], local[parent])
                if not flags[parent] & 2:
                    break
                child, parent = parent, parents[parent]
        distances[key] = distance
    maximum = max(distances.values(), default=0.)
    return {key: (magica2_radius(component.serializeData.radius, distance / maximum if maximum else 0.),
                  bool(flags[key] & 2), not bool(flags[key] & 16)) for key, distance in distances.items()}


def _resample_mesh_fixed(vertices: Any, mesh_to_cloth: list[float], selection: Any) -> list[int]:
    """Resample source proxy paint onto the original renderer's vertex order.

    Saved Magica selection positions are reduced proxy points in cloth-local
    space, not Mesh vertex indices. Nearest paint is our new solver's mapping;
    it is not claimed equivalent to Magica's render-to-proxy interpolation.
    Both input vertices and this matrix use the reflected glTF coordinate frame.
    """
    positions = [[-float(p.x), float(p.y), float(p.z)] for p in selection.positions]
    attributes = [int(a.Value) for a in selection.attributes]
    if not positions or len(positions) != len(attributes):
        raise ValueError("MeshCloth requires matching source paint positions and attributes")
    if any(value not in (0, 1, 2, 8, 9, 10) for value in attributes):
        raise ValueError("MeshCloth paint has an unsupported selection attribute")
    if not all(math.isfinite(value) for point in positions for value in point):
        raise ValueError("MeshCloth paint positions must be finite")
    maximum = float(selection.maxConnectionDistance)
    if not math.isfinite(maximum) or maximum <= 0:
        raise ValueError("MeshCloth paint requires a positive connection distance")
    fixed = []
    for index, vertex in enumerate(vertices):
        point = _mat4_transform_point(mesh_to_cloth, [-float(vertex[0]), float(vertex[1]), float(vertex[2])])
        if not all(math.isfinite(value) for value in point):
            raise ValueError("MeshCloth vertices must be finite")
        nearest = min(range(len(positions)), key=lambda i: math.dist(point, positions[i]))
        if math.dist(point, positions[nearest]) > maximum + 1e-6:
            raise ValueError(f"MeshCloth vertex {index} is outside saved paint coverage")
        # The moving flag is bit 2, also used by the BoneCloth extractor.
        # Saved source paint has 0/1/2 and 8/9/10; the extra bit in 8/9/10
        # does not change whether the vertex participates in our solver.
        # Unselected vertices stay on their skinned pose.
        if not attributes[nearest] & 2:
            fixed.append(index)
    if not fixed or len(fixed) == len(vertices):
        raise ValueError("MeshCloth requires both fixed and moving vertices")
    return fixed


def _mesh_cloth_entries(component: Any, exported: Any, indices: list[int]) -> list[dict[str, Any]]:
    mapping = exported.node_mapping
    document = exported.builder.document
    cloth_transform = _transform(component)
    cloth_world = mapping.source_world[mapping.source_nodes[object_id(cloth_transform)]]
    entries = []
    for pointer in component.serializeData.sourceRenderers:
        renderer = pointer.read()
        mesh = renderer.m_Mesh.read()
        decoded = MeshHandler(mesh)
        decoded.process()
        transform = _transform(renderer)
        source_world = mapping.source_world[mapping.source_nodes[object_id(transform)]]
        fixed = _resample_mesh_fixed(decoded.m_Vertices,
                                    _mat4_mul(_mat4_inverse(cloth_world), source_world),
                                    component.serializeData2.selectionData)
        # The normalized exporter retains Mesh vertex order and shared POSITION
        # across submeshes. Its renderer node is separate from its source GO.
        candidates = [(i, node) for i, node in enumerate(document["nodes"])
                      if node.get("name") == renderer_node_name(mesh.m_Name)
                      and "mesh" in node
                      and document["meshes"][node["mesh"]].get("name") == mesh.m_Name]
        if len(candidates) != 1:
            raise ValueError(f"MeshCloth renderer {mesh.m_Name!r} needs one unambiguous exported mesh node")
        node_index, node = candidates[0]
        gltf_mesh = document["meshes"][node["mesh"]]
        if len(gltf_mesh["primitives"]) != 1:
            raise ValueError(f"MeshCloth renderer {mesh.m_Name!r} requires a single triangle primitive")
        primitive = gltf_mesh["primitives"][0]
        if primitive.get("mode", 4) != 4:
            raise ValueError("MeshCloth requires triangle geometry")
        accessor = document["accessors"][primitive["attributes"]["POSITION"]]
        if accessor["count"] != len(decoded.m_Vertices):
            raise ValueError("MeshCloth source/exported vertex counts disagree")
        # A 3 mm collision margin is a new cloth-solver parameter, not Magica's
        # 12-40 mm sparse proxy-particle radius. Skinned renderer nodes are scene
        # roots: the skin/IBMs restore the attachment transform, so their final
        # local space is NOT the source Transform's canonical local frame.
        # Include appended renderer nodes in the existing mapping to explicitly
        # target that actual output frame (including non-unit attachment scale).
        parents = {child: parent for parent, item in enumerate(document["nodes"])
                   for child in item.get("children", [])}
        def world(index: int) -> list[float]:
            if index < len(mapping.canonical_world):
                return mapping.canonical_world[index]
            item = document["nodes"][index]
            local = item.get("matrix") or _trs_to_mat(item.get("translation", [0., 0., 0.]),
                        item.get("rotation", [0., 0., 0., 1.]), item.get("scale", [1., 1., 1.]))
            return _mat4_mul(world(parents[index]), local) if index in parents else local
        output_mapping = replace(mapping, canonical_world=mapping.canonical_world + [
            world(i) for i in range(len(mapping.canonical_world), len(document["nodes"]))])
        entries.append({"node": node_index, "primitive": 0, "fixed": fixed,
                        "radius": output_mapping.radius(transform, .003, target_node=node_index),
                        "stiffness": 12., "damping": .8, "gravity": [0., 0., 0.],
                        "colliders": indices})
    if not entries:
        raise ValueError("MeshCloth has no source renderers")
    return entries


def _merge_mesh_cloth_regions(cloths: list[dict[str, Any]], document: dict[str, Any]) -> list[dict[str, Any]]:
    """Combine source components painting disjoint regions of one render mesh."""
    groups: dict[tuple[int, int], list[dict[str, Any]]] = {}
    for cloth in cloths:
        groups.setdefault((cloth["node"], cloth["primitive"]), []).append(cloth)
    merged = []
    for (node_index, primitive_index), regions in groups.items():
        if len(regions) == 1:
            merged.append(regions[0])
            continue
        mesh_index = document["nodes"][node_index]["mesh"]
        primitive = document["meshes"][mesh_index]["primitives"][primitive_index]
        count = document["accessors"][primitive["attributes"]["POSITION"]]["count"]
        all_vertices = set(range(count))
        moving_seen: set[int] = set()
        for region in regions:
            if any(region[field] != regions[0][field]
                   for field in ("radius", "stiffness", "damping", "gravity")):
                raise ValueError(f"MeshCloth regions on {node_index}/{primitive_index} have different response parameters")
            fixed = set(region["fixed"])
            if not fixed <= all_vertices:
                raise ValueError(f"MeshCloth region on {node_index}/{primitive_index} has an out-of-range vertex")
            moving = all_vertices - fixed
            if moving_seen & moving:
                raise ValueError(f"MeshCloth regions on {node_index}/{primitive_index} overlap")
            moving_seen.update(moving)
        # The source components own separate moving areas of the same Unity
        # renderer. The generic solver owns one record per glTF primitive.
        # Preserve every moving vertex and every declared collision source.
        combined = dict(regions[0])
        combined["fixed"] = sorted(all_vertices - moving_seen)
        combined["colliders"] = list(dict.fromkeys(
            collider for region in regions for collider in region["colliders"]
        ))
        merged.append(combined)
    return merged


def extract_model_physics(environment: Any, exported: Any) -> dict[str, Any] | None:
    """Extract declared bone and mesh cloth with shared collision geometry.

    Nodes refer to this component's GLB, never names shared across model parts.
    All source coordinates cross the common normalized-model mapping exactly
    once, including collision centers attached to canonical Humanoid bones.
    """
    mapping = exported.node_mapping
    core = set(exported.standard_bones.values())
    colliders: list[dict[str, Any]] = []
    collider_indices: dict[tuple[int, int], list[int]] = {}
    springs: dict[int, dict[str, Any]] = {}
    cloths: list[dict[str, Any]] = []
    components = []
    ground_managers = []
    for reader in environment.objects:
        if reader.type.name != "MonoBehaviour":
            continue
        component = reader.read()
        if not component.m_Script:
            continue
        name = _class(component)
        if (name == 'SpringManager' and component.m_Enabled and component.collideWithGround
                and object_id(_transform(component)) in mapping.source_nodes):
            ground_managers.append(component)
        if name in {"SwingBone", "SpringBone", "MagicaBoneCloth", "MagicaCloth"} and component.m_Enabled:
            # An AB can contain multiple prefabs. Only the selected prefab's
            # attached components belong to this exported model; references
            # inside those components still go through strict node mapping.
            if object_id(_transform(component)) not in mapping.source_nodes:
                continue
            components.append((name, component))

    ground_by_bone: dict[tuple[int, int], list[int]] = {}
    for manager in ground_managers:
        transform = _transform(manager)
        root = transform
        while root.m_Father:
            parent = _read(root.m_Father)
            if object_id(parent) not in mapping.source_nodes:
                break
            root = parent
        # GroundHeight is world Y, not a local offset on the SpringManager.
        # Freeze its source placement in the model root frame so a packaged
        # portrait can be moved/scaled as a whole without rotating its floor
        # along with any animated auxiliary or Humanoid bone.
        world = mapping.source_world[mapping.source_nodes[object_id(root)]]
        point = _mat4_transform_point(_mat4_inverse(world), [0., float(manager.groundHeight), 0.])
        local_normal = [world[1], world[5], world[9]]
        entry = {'shape': 'plane', 'node': mapping.node_index(root),
                 'offset': mapping.point(root, [-point[0], point[1], point[2]]),
                 'normal': mapping.normal(root, [-local_normal[0], local_normal[1], local_normal[2]])}
        index = len(colliders)
        colliders.append(entry)
        def register_ground(node: Any) -> None:
            ground_by_bone.setdefault(object_id(node), []).append(index)
            for child in node.m_Children:
                register_ground(_read(child))
        register_ground(transform)

    def collider_index(pointer: Any) -> list[int]:
        if not pointer:
            return []
        component = _read(pointer)
        if not component.m_Enabled:
            return []
        key = object_id(component)
        if key in collider_indices:
            return collider_indices[key]
        transform = _transform(component)
        node = mapping.node_index(transform)
        name = _class(component)
        if name in {'SpringSphereCollider', 'SpringCapsuleCollider', 'SpringPanelCollider'}:
            # The original collision methods skip a disabled linked renderer.
            if component.linkedRenderer and not _read(component.linkedRenderer).m_Enabled:
                return []
            if name == 'SpringPanelCollider':
                # Original panel is centered on local XY, front = +Z.
                # Reverse one half-edge after mapping's handedness reflection
                # so their cross product still points to the permitted side.
                axes = [mapping.direction(transform, [float(component.width) * .5, 0., 0.]),
                        mapping.direction(transform, [0., float(component.height) * .5, 0.])]
                normal = mapping.normal(transform, [0., 0., 1.])
                a, b = axes
                cross = [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]
                if sum(x*y for x, y in zip(cross, normal)) < 0.:
                    axes[0] = [-x for x in a]
                entry = {'shape': 'panel', 'node': node,
                         'offset': mapping.point(transform, [0., 0., 0.]), 'halfAxes': axes}
            else:
                if float(component.radius) <= .0001:
                    return []
                entry = {'shape': 'sphere', 'node': node,
                         'offset': mapping.point(transform, [0., 0., 0.]),
                         'radius': mapping.radius(transform, float(component.radius))}
                if name == 'SpringCapsuleCollider':
                    # CheckForCollisionAndReact RVA 0x4E0D230 uses the local Y
                    # segment [0,height]; height is NOT the total outer length.
                    entry.update(shape='capsule', tail={'node': node,
                                 'offset': mapping.point(transform, [0., float(component.height), 0.])})
        elif name == "SwingCollider":
            entry = {"shape": "sphere", "node": node,
                     "offset": mapping.point(transform, _vector(component.offset)),
                     "radius": mapping.radius(transform, float(component.radius))}
            if component.sibling:
                sibling = component.sibling.read()
                other = _transform(sibling)
                # Native GetRadius interpolates the two radii. The first
                # generic implementation uses their conservative envelope.
                radius_other = mapping.radius(other, float(sibling.radius), target_node=node)
                entry.update(shape="capsule", radius=max(entry["radius"], radius_other),
                             tail={"node": mapping.node_index(other),
                                   "offset": mapping.point(other, _vector(sibling.offset))})
        elif name == "MagicaSphereCollider":
            radius = float(component.radius if hasattr(component, "radius") else component.size.x)
            entry = {"shape": "sphere", "node": node,
                     "offset": mapping.point(transform, _vector(component.center)),
                     "radius": mapping.radius(transform, radius)}
        elif name == "MagicaCapsuleCollider":
            is_magica2 = hasattr(component, "size")
            start, end, _ = capsule_endpoints(component, magica2=is_magica2)
            r0 = float(component.size.x if is_magica2 else component.startRadius)
            r1 = float((component.size.y if component.radiusSeparation else component.size.x)
                       if is_magica2 else component.endRadius)
            # A tapered collider is the sweep of linearly varying spheres.
            # Piecewise constant capsule envelopes reduce over-inflation to
            # <= 5 mm in normalized node coordinates (up to 32 pieces; larger
            # exceptional radii have a bound abs(r1-r0)/32 instead).
            pieces = min(32, max(1, math.ceil(mapping.radius(transform, abs(r1-r0)) / .005)))
            result = []
            for i in range(pieces):
                a, b = i / pieces, (i+1) / pieces
                p0 = [s + (e-s)*a for s, e in zip(start, end)]
                p1 = [s + (e-s)*b for s, e in zip(start, end)]
                radius = max(r0 + (r1-r0)*a, r0 + (r1-r0)*b)
                result.append(len(colliders))
                colliders.append({"shape": "capsule", "node": node,
                                  "offset": mapping.point(transform, p0),
                                  "radius": mapping.radius(transform, radius),
                                  "tail": {"node": node, "offset": mapping.point(transform, p1)}})
            collider_indices[key] = result
            return result
        elif name == "MagicaPlaneCollider":
            normal = mapping.normal(transform, [0., 1., 0.])
            length = math.sqrt(sum(value * value for value in normal))
            if length < 1e-9:
                raise ValueError("physics plane has a degenerate normal")
            entry = {"shape": "plane", "node": node,
                     "offset": mapping.point(transform, _vector(component.center)),
                     "normal": [value / length for value in normal]}
        else:
            raise ValueError(f"unsupported source physics collider {name}")
        index = len(colliders)
        colliders.append(entry)
        collider_indices[key] = [index]
        return [index]

    def references(pointers: Any) -> list[int]:
        return list(dict.fromkeys(index for pointer in pointers for index in collider_index(pointer)))

    def spring(transform: Any, child: Any, radius: float, indices: list[int], radius_basis: Any = None,
               *, tail: list[float] | None = None) -> None:
        node = mapping.node_index(transform)
        if node in core:
            # Secondary physics never changes Unity-baked Humanoid animation.
            return
        if tail is None:
            tail = mapping.point(child, [0., 0., 0.], target_node=node)
        if sum(value * value for value in tail) < 1e-12:
            return
        entry = {"node": node, "tail": tail,
                 "radius": mapping.radius(radius_basis if radius_basis is not None else transform, radius,
                                          target_node=node),
                 # Source force, friction and drag have incompatible meanings.
                 # Keep pose restoration strong and inertia heavily damped for
                 # moving portraits; these are new response parameters, not
                 # claimed equivalent source coefficients. No extra gravity is
                 # imposed on artist-authored rest shapes in this minimum pass.
                 "stiffness": 1.5, "damping": .8,
                 "gravity": [0., 0., 0.], "colliders": indices}
        previous = springs.get(node)
        if previous is not None:
            if previous["tail"] != tail:
                raise ValueError(f"multiple physics tails drive GLB node {node}")
            previous["colliders"] = list(dict.fromkeys(previous["colliders"] + indices))
            previous["radius"] = max(previous["radius"], entry["radius"])
        else:
            springs[node] = entry

    def chain(pointer: Any, particles: dict, indices: list[int], seen: set[tuple[int, int]], radius_basis: Any) -> None:
        transform = _read(pointer)
        key = object_id(transform)
        if key in seen:
            return
        seen.add(key)
        children = [child.read() for child in transform.m_Children]
        # Branches are visited independently. A single rotation cannot satisfy
        # different branch tips; choose the longest actual outgoing bone as
        # the representative direction rather than inventing an endpoint.
        node = mapping.node_index(transform)
        moving_children = [child for child in children if object_id(child) in particles
                           and particles[object_id(child)][1]]
        if moving_children:
            child = max(moving_children, key=lambda item: sum(value * value for value in
                        mapping.point(item, [0., 0., 0.], target_node=node)))
            radius, _, collision = particles[object_id(child)]
            spring(transform, child, radius, indices if collision else [], radius_basis)
        for child in children:
            chain(child, particles, indices, seen, radius_basis)

    for name, component in components:
        if name == 'SpringBone':
            pointers = [*component.sphereColliders, *component.capsuleColliders, *component.panelColliders]
            indices = ground_by_bone.get(object_id(_transform(component)), []) + references(pointers)
            # Source takes the magnitude of TransformDirection(radius,0,0).
            # All current SpringBone source frames have unit world scale.
            spring(_transform(component), None, abs(float(component.radius)), indices,
                   tail=spring_bone_tail(component, mapping))
        elif name == "SwingBone":
            if component.child:
                spring(_transform(component), component.child.read(), float(component.radius),
                       references(component.colliders))
        elif name == "MagicaBoneCloth":
            # Original MC1 VerifyData (BG RVA 0x587E474) rejects null clothData
            # or meshData with ClothDataNull/MeshDataNull; CoreComponent.Init
            # (0x5864064) then sets InitError without creating physics. Root
            # bones alone are not a built cloth. Non-null broken references
            # must still fail, rather than silently becoming static geometry.
            if not component.clothData or not component.meshData:
                continue
            component.meshData.read()
            params = component.clothParams
            indices = references(component.teamData.colliderList) if params.useCollision else []
            # mergeAvatarCollider is a runtime avatar registration mechanism,
            # not permission to associate every collider in an AB. Explicit
            # lists remain authoritative for this self-contained model part.
            particles = _magica1_particles(component)
            seen: set[tuple[int, int]] = set()
            for root in component.clothTarget.rootList:
                if root:
                    chain(root, particles, indices, seen, _transform(component))
        else:
            data = component.serializeData
            if int(data.clothType) == 0:
                indices = references(data.colliderCollisionConstraint.colliderList)
                cloths.extend(_mesh_cloth_entries(component, exported, indices))
                continue
            if int(data.clothType) != 1:
                continue
            indices = references(data.colliderCollisionConstraint.colliderList)
            particles = _magica2_particles(component, mapping)
            seen = set()
            for root in data.rootBones:
                if root:
                    chain(root, particles, indices, seen, _transform(component))
    if cloths:
        cloths = _merge_mesh_cloth_regions(cloths, exported.builder.document)
    if not springs and not cloths:
        return None
    result = {"colliders": colliders, "springs": list(springs.values())}
    spring_indices = {node: index for index, node in enumerate(springs)}
    collision_edges = []
    seen_edges = set()
    for name, component in components:
        if name != "SwingBone" or not getattr(component, "sibling", None):
            continue
        start = mapping.node_index(_transform(component))
        end = mapping.node_index(_transform(component.sibling.read()))
        if start not in spring_indices or end not in spring_indices:
            continue
        pair = (spring_indices[start], spring_indices[end])
        if pair[0] == pair[1]:
            continue
        indices = references(component.colliders)
        key = (tuple(sorted(pair)), tuple(sorted(indices)))
        if key not in seen_edges:
            seen_edges.add(key)
            collision_edges.append({"springs": list(pair), "colliders": indices})
    if collision_edges:
        result["collisionEdges"] = collision_edges
    if cloths:
        result["cloths"] = cloths
    return result
