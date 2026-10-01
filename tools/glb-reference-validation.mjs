export function buildMorphNodeIndex(document) {
  const meshes = document.meshes ?? [];
  const morphsByMesh = meshes.map((mesh) => {
    const targetNames = mesh.extras?.targetNames ?? [];
    const morphs = new Map();
    for (const morphName of targetNames) {
      morphs.set(morphName, (morphs.get(morphName) ?? 0) + 1);
    }
    return morphs;
  });

  const nodeMorphs = new Map();
  for (const node of document.nodes ?? []) {
    if (!nodeMorphs.has(node.name)) nodeMorphs.set(node.name, []);
    nodeMorphs.get(node.name).push(Number.isInteger(node.mesh) ? morphsByMesh[node.mesh] : undefined);
  }
  return nodeMorphs;
}

export function validateTargetMap(targets, nodeMorphs, label) {
  const keys = [];
  for (const [nodeName, morphs] of Object.entries(targets ?? {})) {
    if (!nodeName.trim()) throw new Error(`${label} targets an empty morph node name`);
    const matches = nodeMorphs.get(nodeName);
    if (!matches?.length) throw new Error(`${label} targets missing morph node ${nodeName}`);
    if (matches.length !== 1) throw new Error(`${label} repeats morph node name ${nodeName}`);
    const available = matches[0];
    if (!available?.size) throw new Error(`${label} targets missing morph node ${nodeName}`);
    for (const [morphName, weight] of Object.entries(morphs ?? {})) {
      if (!morphName.trim()) throw new Error(`${label} targets an empty morph target name`);
      if (!available.has(morphName)) {
        throw new Error(`${label} targets missing morph ${nodeName}/${morphName}`);
      }
      if (available.get(morphName) !== 1) {
        throw new Error(`${label} repeats morph target name ${morphName} on ${nodeName}`);
      }
      if (!Number.isFinite(weight)) {
        throw new Error(`${label} has invalid weight ${nodeName}/${morphName}=${weight}`);
      }
      keys.push(`${nodeName}\n${morphName}`);
    }
  }
  return keys.sort();
}
