import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { auditResourcePackages, validatePhysicsReferences, validateMaterialReferences } from "../tools/validate-resource-packages.mjs";

const settings = { radius: 0.01, stiffness: 1, damping: 0.5, gravity: [0, 0, 0], colliders: [0] };
function fixture() {
  return {
    document: {
      nodes: [{ name: "Skirt", mesh: 0, skin: 0 }, { name: "Hips" }, { name: "SkirtBone" }],
      meshes: [{ primitives: [{ attributes: { POSITION: 0, JOINTS_0: 1, WEIGHTS_0: 2 }, indices: 3 }] }],
      skins: [{ joints: [1, 2] }],
      accessors: [{ type: "VEC3", count: 4 }, {}, {}, { type: "SCALAR", count: 3, componentType: 5123, bufferView: 0 }],
      bufferViews: [{ buffer: 0, byteLength: 6 }],
    },
    buffers: [Buffer.from([0, 0, 1, 0, 2, 0])],
    physics: {
      colliders: [{ shape: "capsule", node: 1, offset: [0, 0, 0], radius: 0.1, tail: { node: 2, offset: [0, 1, 0] } }],
      springs: [{ ...settings, node: 2, tail: [0, 1, 0] }],
      cloths: [{ ...settings, node: 0, primitive: 0, fixed: [0] }],
    },
  };
}
const validate = ({ document, buffers, physics }) => validatePhysicsReferences(document, buffers, physics);

test("physics references accept valid indexed and nonindexed skinned cloth", () => {
  const value = fixture(); validate(value);
  delete value.document.meshes[0].primitives[0].indices;
  value.document.accessors[0].count = 3; validate(value);
});

test("physics references reject missing collider endpoints, core springs and invalid primitives", () => {
  let value = fixture(); value.physics.colliders[0].tail.node = 99;
  assert.throws(() => validate(value), /node 99/);
  value = fixture(); value.physics.springs[0].node = 1;
  assert.throws(() => validate(value), /核心骨/);
  value = fixture(); value.physics.cloths[0].primitive = 1;
  assert.throws(() => validate(value), /primitive/);
  value = fixture(); value.document.skins[0].joints.push(99);
  assert.throws(() => validate(value), /node 99/);
});

test("cloth fixed vertices must be in range and used by the primitive", () => {
  const value = fixture(); value.physics.cloths[0].fixed = [4];
  assert.throws(() => validate(value), /超出 POSITION/);
  value.physics.cloths[0].fixed = [3];
  assert.throws(() => validate(value), /未被 primitive 使用/);
  value.physics.cloths[0].fixed = [0]; value.buffers[0].writeUInt16LE(4, 4);
  assert.throws(() => validate(value), /三角形顶点越界/);
});

test("cloth index accessors support sparse updates", () => {
  const value = fixture();
  value.document.bufferViews.push({ buffer: 1, byteLength: 1 }, { buffer: 2, byteLength: 2 });
  value.buffers.push(Buffer.from([2]), Buffer.from([3, 0]));
  value.document.accessors[3].sparse = {
    count: 1, indices: { bufferView: 1, componentType: 5121 }, values: { bufferView: 2 },
  };
  value.physics.cloths[0].fixed = [3]; validate(value);
});

const shader = {
  name: "test", passes: [{ id: "Forward", sections: {} }],
  samplers: [{ name: "Main", type: "sampler2D", missing: { behavior: "error" } }],
};
test("cross-package material audit resolves passes, required samplers and texture color space", () => {
  const shaders = new Map([["test", shader]]);
  const document = { textures: [{ extras: { colorSpace: "srgb" } }], materials: [
    {}, { extras: { shader: "test", passes: [{ id: "Forward" }], textures: { Main: 0 } } },
  ] };
  validateMaterialReferences(document, shaders);
  document.materials[1].extras.passes[0].id = "Missing";
  assert.throws(() => validateMaterialReferences(document, shaders), /unknown Shader pass/);
  document.materials[1].extras.passes[0].id = "Forward";
  delete document.materials[1].extras.textures.Main;
  assert.throws(() => validateMaterialReferences(document, shaders), /缺少 sampler/);
  document.materials[1].extras.textures.Main = 2;
  assert.throws(() => validateMaterialReferences(document, shaders), /texture 2/);
  document.materials[1].extras.textures.Main = 0; delete document.textures[0].extras.colorSpace;
  assert.throws(() => validateMaterialReferences(document, shaders), /colorSpace/);
});

async function packageFixture(t, components, indexed = ["deps/config.json"]) {
  const directory = await fs.mkdtemp(path.join(os.tmpdir(), "resource-audit-"));
  t.after(() => fs.rm(directory, { recursive: true, force: true }));
  await fs.mkdir(path.join(directory, "deps"));
  await fs.writeFile(path.join(directory, "index.json"), JSON.stringify({ configs: indexed }));
  await fs.writeFile(path.join(directory, "deps/config.json"), JSON.stringify({ components }));
  return directory;
}

test("package audit validates real dependency files without interpreting private Behavior parameters", async (t) => {
  const directory = await packageFixture(t, [{ type: "behavior", namespace: "test", name: "face", script: "face.js" }]);
  await fs.writeFile(path.join(directory, "deps/face.js"), "export function createBehavior() {}\n");
  assert.equal((await auditResourcePackages(directory, { runtime: false })).passed, true);
  await fs.unlink(path.join(directory, "deps/face.js"));
  const report = await auditResourcePackages(directory, { runtime: false });
  assert.equal(report.passed, false); assert.match(report.errors[0].message, /face.js/);
});

test("package audit detects index/disk mismatches", async (t) => {
  const directory = await packageFixture(t, [{ type: "typo", name: "bad" }], ["absent/config.json"]);
  const report = await auditResourcePackages(directory, { runtime: false });
  assert.equal(report.passed, false);
  assert.ok(report.errors.some((e) => /不存在的 config/.test(e.message)));
  assert.ok(report.errors.some((e) => /未被索引/.test(e.message)));
});

test("package audit skips unknown resource types while validating known entries", async (t) => {
  const directory = await packageFixture(t, [
    { type: 'future-resource', name: 'extension' },
    { type: 'garupa-future-resource', name: 'another-extension' },
    { type: 'behavior', namespace: 'test', name: 'face', script: 'face.js' },
  ]);
  await fs.writeFile(path.join(directory, 'deps/face.js'), '');
  const report = await auditResourcePackages(directory, { runtime: false });
  assert.equal(report.passed, true, JSON.stringify(report.errors));
  assert.equal(report.counts.behavior, 1);
  await fs.unlink(path.join(directory, 'deps/face.js'));
  assert.equal((await auditResourcePackages(directory, { runtime: false })).passed, false);
});

test("shader audit checks section and resource file references", async (t) => {
  const directory = await packageFixture(t, [{ ...shader, type: "shader", src: "test.glsl", passes: [
    { id: "Forward", sections: { fragmentBody: "BODY" } },
  ] }]);
  await fs.writeFile(path.join(directory, "deps/test.glsl"), "// @section BODY\nvec4 color;\n// @end\n");
  assert.equal((await auditResourcePackages(directory, { runtime: false })).passed, true);
  await fs.writeFile(path.join(directory, "deps/test.glsl"), "// empty\n");
  assert.match((await auditResourcePackages(directory, { runtime: false })).errors[0].message, /section BODY/);
});

test("root preview catalogue is not audited as another package", async (t) => {
  const directory = await packageFixture(t, [{ type: "behavior", namespace: "test", name: "face", script: "face.js" }]);
  await fs.writeFile(path.join(directory, "deps/face.js"), "");
  await fs.writeFile(path.join(directory, "config.json"), JSON.stringify({ components: [
    { type: "behavior", namespace: "test", name: "face", script: "deps/face.js", configPath: "deps/config.json" },
  ] }));
  const report = await auditResourcePackages(directory, { runtime: false });
  assert.equal(report.passed, true, JSON.stringify(report.errors));
  assert.equal(report.counts.configs, 1);
});

test("single package and recursive directories do not require a preview index", async (t) => {
  const directory = await packageFixture(t, [{ type: "behavior", namespace: "test", name: "face", script: "face.js" }]);
  await fs.writeFile(path.join(directory, "deps/face.js"), "");
  await fs.unlink(path.join(directory, "index.json"));
  for (const root of [directory, path.join(directory, "deps")]) {
    const report = await auditResourcePackages(root, { runtime: false });
    assert.equal(report.passed, true, JSON.stringify(report.errors));
  }
});

function glb(document) {
  const text = Buffer.from(JSON.stringify(document));
  const size = Math.ceil(text.length / 4) * 4;
  const bytes = Buffer.alloc(20 + size, 0x20);
  bytes.write("glTF"); bytes.writeUInt32LE(2, 4); bytes.writeUInt32LE(bytes.length, 8);
  bytes.writeUInt32LE(size, 12); bytes.writeUInt32LE(0x4e4f534a, 16); text.copy(bytes, 20);
  return bytes;
}

test("model audit permits unreferenced morph names and validates pose references when present", async (t) => {
  const component = { type: "model", name: "head", role: "integrated", model: "head.glb",
    humanoidScale: 1, morphPoses: [], expressionGroups: [], expressions: [] };
  const directory = await packageFixture(t, [component]);
  await fs.writeFile(path.join(directory, "deps/head.glb"), glb({ asset: { version: "2.0" },
    nodes: [{ mesh: 0 }, { name: "duplicate", mesh: 0 }, { name: "duplicate", mesh: 0 },
      { name: "Face", mesh: 1 }],
    meshes: [{ extras: { targetNames: ["unused", "unused", ""] } },
      { extras: { targetNames: ["mouth_a"] } }],
  }));
  let report = await auditResourcePackages(directory, { runtime: false });
  assert.equal(report.passed, true, JSON.stringify(report.errors));
  component.morphPoses = [{ name: "active", targets: { Face: { mouth_a: 1 } } }];
  await fs.writeFile(path.join(directory, "deps/config.json"), JSON.stringify({ components: [component] }));
  report = await auditResourcePackages(directory, { runtime: false });
  assert.equal(report.passed, true, JSON.stringify(report.errors));
  component.morphPoses[0].targets = { duplicate: { unused: 1 } };
  await fs.writeFile(path.join(directory, "deps/config.json"), JSON.stringify({ components: [component] }));
  report = await auditResourcePackages(directory, { runtime: false });
  assert.equal(report.passed, false);
  assert.ok(report.errors.some(error => /repeats morph node name duplicate/.test(error.message)));
});

test("independent runtime resolves Shader and required Behavior without output index entries", async (t) => {
  const directory = await packageFixture(t, [{ type: "model", name: "body", role: "body", group: "test",
    humanoidScale: 1, model: "body.glb", behaviors: [{ name: "test.face", required: true, parameters: {} }] }]);
  await fs.writeFile(path.join(directory, "deps/body.glb"), glb({ asset: { version: "2.0" },
    materials: [{ extras: { shader: "runtimeShader", passes: [{ id: "Forward" }] } }] }));
  const runtime = await fs.mkdtemp(path.join(os.tmpdir(), "runtime-audit-"));
  t.after(() => fs.rm(runtime, { recursive: true, force: true }));
  await fs.writeFile(path.join(runtime, "config.json"), JSON.stringify({ components: [
    { type: "shader", name: "runtimeShader", src: "shader.glsl", samplers: [],
      passes: [{ id: "Forward", sections: { fragmentBody: "BODY" } }] },
    { type: "behavior", namespace: "test", name: "face", script: "face.js" },
  ] }));
  await fs.writeFile(path.join(runtime, "shader.glsl"), "// @section BODY\nvec4 color;\n// @end\n");
  await fs.writeFile(path.join(runtime, "face.js"), "");
  const report = await auditResourcePackages(directory, { runtime });
  assert.equal(report.passed, true, JSON.stringify(report.errors));
  assert.ok(!(await auditResourcePackages(directory, { runtime: false })).passed);
  await fs.writeFile(path.join(directory, "deps/body.glb"), glb({ asset: { version: "2.0" } }));
  const missing = await auditResourcePackages(directory, { runtime: false });
  assert.ok(missing.errors.some(error => /required Behavior/.test(error.message)));
});

test("parameter motions, expressions and adapters validate their package files", async (t) => {
  const directory = await packageFixture(t, [
    { type: "garupa-motion", name: "anon/angry", src: "angry.mtn" },
    { type: "garupa-expression", name: "anon/angry", src: "angry.exp.json" },
    { type: "garupa-expression-adapter", name: "face", motionGroup: "llas", script: "face.js" },
  ]);
  for (const name of ["angry.mtn", "angry.exp.json", "face.js"]) await fs.writeFile(path.join(directory, "deps", name), "");
  assert.equal((await auditResourcePackages(directory, { runtime: false })).passed, true);
  await fs.unlink(path.join(directory, "deps/face.js"));
  assert.ok((await auditResourcePackages(directory, { runtime: false })).errors.some(error => /face.js/.test(error.message)));
});

test("binary motion packages are decoded before payload validation", async (t) => {
  const directory = await packageFixture(t, [{ type: "motion", name: "idle", src: "idle.motionbin" }]);
  const payload = { clips: [{ id: "idle", name: "idle", duration: 0, sampleRate: 30, frames: 2,
    tracks: [{ bone: "Hips", rotation: { type: "f32", offset: 0, length: 8 } }] }],
    auxiliaryClips: [], leftHandPoses: [], rightHandPoses: [],
    program: { parameters: [], commands: {}, baseLayer: "base", layers: [{ id: "base", weight: 1, blend: "override", initialState: "idle",
      states: [{ id: "idle", clip: "idle", speed: 1, loop: true, transitions: [] }] }], poseSlots: [] } };
  const header = Buffer.from(JSON.stringify(payload));
  const dataStart = Math.ceil((12 + header.length) / 8) * 8;
  const bytes = Buffer.alloc(dataStart + 32);
  bytes.write("MOTION\0\0"); bytes.writeUInt32LE(header.length, 8); header.copy(bytes, 12);
  bytes.writeFloatLE(1, dataStart + 12); bytes.writeFloatLE(1, dataStart + 28);
  await fs.writeFile(path.join(directory, "deps/idle.motionbin"), bytes);
  const report = await auditResourcePackages(directory, { runtime: false });
  assert.equal(report.passed, true, JSON.stringify(report.errors));
});
