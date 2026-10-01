import assert from "node:assert/strict";
import test from "node:test";

import {
  buildMorphNodeIndex,
  validateTargetMap,
} from "../tools/glb-reference-validation.mjs";

function document(nodeNames = ["face Renderer"], targetNames = ["mouth_a"]) {
  return {
    meshes: [{ extras: { targetNames } }],
    nodes: nodeNames.map((name) => ({ name, mesh: 0 })),
  };
}

test("GLB references resolve one original node and one morph target", () => {
  const index = buildMorphNodeIndex(document(), "head");
  assert.deepEqual(
    validateTargetMap({ "face Renderer": { mouth_a: 0.5 } }, index, "Neutral"),
    ["face Renderer\nmouth_a"],
  );
});

test("GLB references allow unreferenced unnamed and duplicate morph nodes and targets", () => {
  const value = document();
  value.meshes.push({ extras: { targetNames: ["unused", "unused", ""] } });
  value.nodes.push({ mesh: 1 }, { name: "unused", mesh: 1 }, { name: "unused", mesh: 1 });
  const index = buildMorphNodeIndex(value, "head");
  assert.deepEqual(validateTargetMap({}, index, "empty"), []);
  assert.deepEqual(validateTargetMap({ "face Renderer": { mouth_a: 1 } }, index, "active"),
    ["face Renderer\nmouth_a"]);
});

test("GLB references only require uniqueness for the morph names used by a pose", () => {
  const index = buildMorphNodeIndex(document(["face"], ["mouth_a", "unused", "unused", ""]));
  assert.deepEqual(validateTargetMap({ face: { mouth_a: 1 } }, index, "active"), ["face\nmouth_a"]);
  assert.throws(() => validateTargetMap({ face: { unused: 1 } }, index, "active"),
    /repeats morph target name unused/);
});

test("GLB reference validation rejects missing and ambiguous targets", () => {
  const duplicate = document();
  duplicate.nodes.push({ name: 'face Renderer' });
  assert.throws(() => validateTargetMap({ "face Renderer": { mouth_a: 1 } },
    buildMorphNodeIndex(duplicate), "active"), /repeats morph node/);
  assert.throws(
    () => validateTargetMap({ face: { mouth_a: 1 } },
      buildMorphNodeIndex(document(["face", "face"]), "head"), "active"),
    /repeats morph node name face/,
  );
  assert.throws(
    () => validateTargetMap({ face: { mouth_a: 1 } },
      buildMorphNodeIndex(document(["face"], ["mouth_a", "mouth_a"]), "head"), "active"),
    /repeats morph target name mouth_a/,
  );
  const index = buildMorphNodeIndex(document(), "head");
  assert.throws(() => validateTargetMap({ missing: { mouth_a: 0 } }, index, "Neutral"), /missing morph node/);
  assert.throws(() => validateTargetMap({ "face Renderer": { missing: 0 } }, index, "Neutral"), /missing morph/);
  assert.throws(() => validateTargetMap({ "": { mouth_a: 0 } }, index, "Neutral"), /empty morph node/);
  assert.throws(() => validateTargetMap({ "face Renderer": { "": 0 } }, index, "Neutral"), /empty morph target/);
  assert.throws(() => validateTargetMap({ plain: { mouth_a: 1 } },
    buildMorphNodeIndex({ nodes: [{ name: "plain" }] }), "active"), /missing morph node/);
});

test("Morph pose weights allow finite extrapolation without clamping", () => {
  const index = buildMorphNodeIndex(document());
  for (const value of [-0.5, 1.5]) {
    assert.equal(validateTargetMap({ 'face Renderer': { mouth_a: value } }, index, 'raw').length, 1);
  }
  for (const value of [NaN, Infinity, '1']) {
    assert.throws(() => validateTargetMap({ 'face Renderer': { mouth_a: value } }, index, 'raw'), /invalid weight/);
  }
});
