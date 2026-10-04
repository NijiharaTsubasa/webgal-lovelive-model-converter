// Offline verification of every indexed motion payload, with no game dispatch.
import fs from "node:fs/promises";
import path from "node:path";
import crypto from "node:crypto";
import { pathToFileURL } from "node:url";
import * as THREE from "three";
import { validateMotionPayload } from "webgal-lovelive-gltf-renderer/motion-manifest.js";
import { MotionPlayer } from "webgal-lovelive-gltf-renderer/motion-player.js";
import { HUMANOID_BONE_NAMES } from "webgal-lovelive-gltf-renderer/skeleton-composer.js";
import { decodeMotionBinary } from "webgal-lovelive-gltf-renderer/motion-binary.js";

export async function readMotionFile(file, bytes = null) {
  bytes ??= await fs.readFile(file);
  return file.endsWith('.motionbin')
    ? decodeMotionBinary(bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength))
    : JSON.parse(bytes.toString('utf8'));
}

const COLLECTIONS = ["clips", "auxiliaryClips", "leftHandPoses", "rightHandPoses"];
function require(value, message) { if (!value) throw new Error(message); }
function id(value, label) { require(typeof value === "string" && value.trim(), `${label} must be a nonempty string`); }
function finite(value, label) { require(Number.isFinite(value), `${label} must be finite`); }
function unique(items, label) {
  require(Array.isArray(items), `${label} must be an array`);
  const map = new Map();
  for (const item of items) { id(item.id, label); require(!map.has(item.id), `Duplicate ${label} ${item.id}`); map.set(item.id, item); }
  return map;
}
function child(root, relative) {
  id(relative, "relative path");
  const result = path.resolve(root, relative.replaceAll('\\', '/')), rel = path.relative(path.resolve(root), result);
  require(rel && rel !== '..' && !rel.startsWith('..' + path.sep) && !path.isAbsolute(rel), `Path escapes package: ${relative}`);
  return result;
}
function channel(values, count, label) {
  require((Array.isArray(values) || ArrayBuffer.isView(values) && !(values instanceof DataView))
    && values.length === count, `${label}: expected ${count} values, got ${values?.length}`);
  require(values.every(Number.isFinite), `${label} contains nonfinite values`);
}
function rotations(values, frames, label, stats) {
  channel(values, frames * 4, label);
  for (let i = 0; i < frames; i += 1) {
    const offset = i * 4, q = values.slice(offset, offset + 4), error = Math.abs(Math.hypot(...q) - 1);
    stats.maxQuaternionNormError = Math.max(stats.maxQuaternionNormError, error);
    require(error < 1e-5, `${label} frame ${i} quaternion norm error ${error}`);
    if (i) require(q.reduce((sum, v, c) => sum + v * values[offset - 4 + c], 0) >= -1e-6,
      `${label} frame ${i} quaternion hemisphere discontinuity`);
  }
}
function finger(name, side = "(?:Left|Right)") {
  return new RegExp(`^${side}(?:Thumb|Index|Middle|Ring|Little)(?:Proximal|Intermediate|Distal)$`).test(name);
}
function valueForParameter(parameter, value) {
  return parameter?.type === "float" ? Number.isFinite(value)
    : parameter?.type === "int" ? Number.isInteger(value)
      : ["bool", "trigger"].includes(parameter?.type) && typeof value === "boolean";
}

export function validateData(payload, label = "motion") {
  validateMotionPayload(payload, label);
  const clips = new Map(), poseClips = new Set();
  const stats = { clips: 0, tracks: 0, groupTracks: 0, frames: 0, float32FrameBoundaries: 0, maxQuaternionNormError: 0 };
  for (const collection of COLLECTIONS) for (const clip of payload[collection]) {
    id(clip.id, "Clip.id"); require(!clips.has(clip.id), `Duplicate Clip.id ${clip.id}`); clips.set(clip.id, clip);
    id(clip.name, `${clip.id}.name`);
    finite(clip.duration, "duration"); finite(clip.sampleRate, "sampleRate");
    require(clip.duration >= 0 && clip.sampleRate > 0, `${clip.id} invalid duration/sampleRate`);
    // MotionBaker uses float32 clip.length * sampleRate before Mathf.CeilToInt.
    // Reproducing that arithmetic prevents JSON's double parsing adding a frame.
    const expected = Math.max(2, Math.ceil(clip.duration * clip.sampleRate) + 1);
    const unityExpected = Math.max(2, Math.ceil(Math.fround(Math.fround(clip.duration) * Math.fround(clip.sampleRate))) + 1);
    require(Number.isInteger(clip.frames) && [expected, unityExpected].includes(clip.frames), `${clip.id} expected ${expected} frames (Unity float32: ${unityExpected}), found ${clip.frames}`);
    if (expected !== unityExpected && clip.frames === unityExpected) stats.float32FrameBoundaries += 1;
    require(Array.isArray(clip.tracks), `${clip.id} tracks must be an array`);
    const bones = new Set();
    const side = collection === "leftHandPoses" ? "Left" : collection === "rightHandPoses" ? "Right" : null;
    if (side) poseClips.add(clip.id);
    for (const track of clip.tracks) {
      require(HUMANOID_BONE_NAMES.has(track.bone) && !bones.has(track.bone), `${clip.id} invalid/repeated bone ${track.bone}`);
      bones.add(track.bone);
      rotations(track.rotation, clip.frames, `${clip.id}/${track.bone}`, stats);
      if (track.translation !== undefined) {
        require(track.bone === "Hips", `${clip.id}/${track.bone}: translation belongs only to Hips`);
        channel(track.translation, clip.frames * 3, `${clip.id}/Hips translation`);
      }
      if (side) require(finger(track.bone, side) && track.translation === undefined, `${collection} contains non-${side}-finger motion`);
      stats.tracks += 1;
    }
    require(clip.groupTracks === undefined || Array.isArray(clip.groupTracks), `${clip.id} invalid groupTracks`);
    const groupTargets = new Set();
    for (const track of clip.groupTracks ?? []) {
      id(track.node, "groupTrack.node"); id(track.property, "groupTrack.property");
      const target = `${track.node}\0${track.property}`;
      require(!groupTargets.has(target), `${clip.id} duplicate group track ${target}`); groupTargets.add(target);
      require(["morph", "transform", "visibility"].includes(track.kind), `${clip.id} unknown group track kind`);
      if (track.kind === "transform") {
        require(track.property === "localTRS", "Transform group track must use localTRS");
        rotations(track.rotation, clip.frames, `${clip.id}/${track.node} group rotation`, stats);
        for (const key of ["translation", "scale"]) if (track[key] !== undefined && track[key]?.length !== 0) channel(track[key], clip.frames * 3, `${clip.id}/${track.node} ${key}`);
      } else {
        channel(track.values, clip.frames, `${clip.id}/${track.node}/${track.property}`);
        if (track.kind === "visibility") require(track.property === "visible", "Visibility group track must use visible");
      }
      stats.groupTracks += 1;
    }
    stats.clips += 1; stats.frames += clip.frames;
  }
  require(clips.size, "Motion has no clips");
  const program = payload.program, parameters = unique(program.parameters, "parameter"), layers = unique(program.layers, "layer");
  for (const parameter of parameters.values()) require(valueForParameter(parameter, parameter.default)
    && (parameter.type !== "trigger" || parameter.default === false), `Invalid parameter ${parameter.id}`);
  require(program.commands && typeof program.commands === "object" && !Array.isArray(program.commands), "commands must be an object");
  for (const [command, assignments] of Object.entries(program.commands)) {
    id(command, "command"); require(Array.isArray(assignments), "command assignments must be an array");
    for (const assignment of assignments) require(valueForParameter(parameters.get(assignment.parameter), assignment.value), `Invalid command parameter ${assignment.parameter}`);
  }
  require(layers.has(program.baseLayer), "Missing baseLayer reference");
  for (const layer of layers.values()) {
    finite(layer.weight, "layer weight"); require(layer.weight >= 0 && layer.weight <= 1, "Layer weight outside [0,1]");
    require(layer.id === program.baseLayer ? layer.blend === "override" && layer.weight === 1 : layer.blend === "additive", "Invalid base/additive layer contract");
    const states = unique(layer.states, "state"); require(states.has(layer.initialState), `Missing initialState ${layer.initialState}`);
    for (const state of states.values()) {
      require(clips.has(state.clip), `Missing state clip ${state.clip}`); finite(state.speed, "state speed");
      require(typeof state.loop === "boolean" && Array.isArray(state.transitions), `Invalid state ${state.id}`);
      for (const transition of state.transitions) {
        require(states.has(transition.to), `Missing transition destination ${transition.to}`);
        if (transition.exitTime !== null) finite(transition.exitTime, "exitTime");
        finite(transition.duration, "transition duration"); require(transition.duration >= 0, "Negative transition duration");
        finite(transition.offset, "transition offset"); require(Array.isArray(transition.conditions), "conditions must be an array");
        for (const condition of transition.conditions) {
          const parameter = parameters.get(condition.parameter); require(parameter, `Missing condition parameter ${condition.parameter}`);
          const operators = { bool: ["isTrue", "isFalse"], trigger: ["isTrue", "isFalse"], float: ["greater", "less"], int: ["greater", "less", "equals", "notEquals"] };
          require(operators[parameter.type].includes(condition.operator), `Invalid operator ${condition.operator} for ${parameter.type}`);
          if (["bool", "trigger"].includes(parameter.type)) require(condition.value === undefined, "Boolean condition carries value");
          else require(valueForParameter(parameter, condition.value), "Invalid numeric condition value");
        }
      }
    }
  }
  const slots = unique(program.poseSlots, "poseSlot"), assignedBones = new Map();
  for (const slot of slots.values()) {
    const options = unique(slot.options, "poseOption"); require(options.has(slot.default), `Missing pose default ${slot.default}`);
    const slotBones = new Set();
    for (const option of options.values()) {
      require(poseClips.has(option.clip), `Pose option does not reference a hand-pose clip: ${option.clip}`);
      for (const track of clips.get(option.clip).tracks) slotBones.add(track.bone);
    }
    for (const bone of slotBones) { require(!assignedBones.has(bone), `Pose slots overlap on ${bone}`); assignedBones.set(bone, slot.id); }
  }
  return stats;
}

export function probeSharedPayload(payload) {
  const makeRig = (variant, motion = payload) => {
    const root = new THREE.Group(), bones = new Map(), references = new Map(), positions = new Map();
    root.name = `VerificationRig${variant}`; root.rotation.y = variant ? 0.6 : -0.3;
    let index = 0;
    for (const name of HUMANOID_BONE_NAMES) {
      const bone = new THREE.Bone(); bone.name = name;
      bone.position.set(index * 0.01, name === "Hips" ? 0.9 + variant * 0.3 : 0.2 + variant * 0.4, 0);
      if (name !== "Hips") bone.quaternion.setFromEuler(new THREE.Euler(0.2 + variant * 0.3, index * 0.01, -0.4 + variant * 0.2));
      root.add(bone); bones.set(name, bone); references.set(name, bone.quaternion.clone()); positions.set(name, bone.position.clone()); index += 1;
    }
    const scale = variant ? 1.3 : 0.8;
    return { root, bones, references, positions, scale, player: new MotionPlayer(root, scale, motion) };
  };
  const left = makeRig(0), right = makeRig(1); let maxSharedDeltaError = 0, maxSharedHipsError = 0;
  const disposeRig = rig => {
    rig.player.dispose();
    for (const [name, bone] of rig.bones) {
      require(bone.position.distanceTo(rig.positions.get(name)) < 1e-10
        && bone.quaternion.angleTo(rig.references.get(name)) < 1e-6, `Dispose did not restore bone ${name}`);
    }
  };
  try {
    for (const dt of [0, 0.13, 0.43]) {
      left.player.update(dt); right.player.update(dt);
      for (const name of HUMANOID_BONE_NAMES) {
        const delta = rig => rig.references.get(name).clone().invert().multiply(rig.bones.get(name).quaternion);
        const error = delta(left).angleTo(delta(right)); maxSharedDeltaError = Math.max(maxSharedDeltaError, error);
        require(error < 1e-6, `One payload produced different local deltas on two rigs: ${name}`);
      }
      const hips = rig => rig.bones.get("Hips").position.clone().sub(rig.positions.get("Hips")).divideScalar(rig.scale);
      const error = hips(left).distanceTo(hips(right)); maxSharedHipsError = Math.max(maxSharedHipsError, error);
      require(error < 1e-6, "One payload produced inconsistent normalized Hips displacement");
    }
  } finally { disposeRig(left); disposeRig(right); }
  // This independent oracle deliberately does not call MotionPlayer sampling helpers.
  // Production samples discrete floor(time * sampleRate) frames, not interpolated frames.
  let exactClipChecks = 0, changingTracks = 0, maxExpectedRotationError = 0, maxExpectedTranslationError = 0;
  for (const clip of COLLECTIONS.flatMap(key => payload[key] ?? [])) {
    const isolated = isolatedClipPayload(clip), times = clipSampleTimes(clip);
    const rigs = [makeRig(0, isolated), makeRig(1, isolated)];
    try {
      for (const rig of rigs) {
        let previousTime = 0;
        const firstActual = new Map(), firstExpected = new Map(), changed = new Set();
        for (const time of times) {
          rig.player.update(time - previousTime); previousTime = time;
          const frame = Math.min(clip.frames - 1, Math.floor(Math.min(time, clip.duration) * clip.sampleRate));
          for (const track of clip.tracks) {
            const bone = rig.bones.get(track.bone);
            require(bone, `${clip.id}: missing target bone ${track.bone}`);
            if (track.rotation?.length) {
              const delta = new THREE.Quaternion().fromArray(track.rotation, frame * 4).normalize();
              const expected = rig.references.get(track.bone).clone().multiply(delta).normalize();
              const actual = bone.quaternion.clone().normalize(), error = actual.angleTo(expected);
              maxExpectedRotationError = Math.max(maxExpectedRotationError, error);
              require(error < 1e-6, `${clip.id}/${track.bone}: actual rotation differs from reference * payload frame (${error})`);
              if (!firstActual.has(track.bone)) { firstActual.set(track.bone, actual); firstExpected.set(track.bone, expected); }
              if (expected.angleTo(firstExpected.get(track.bone)) > 1e-4) {
                require(actual.angleTo(firstActual.get(track.bone)) > 5e-5, `${clip.id}/${track.bone}: changing payload produced a stationary bone`);
                changed.add(track.bone);
              }
            }
            if (track.translation?.length) {
              const expected = new THREE.Vector3().fromArray(track.translation, frame * 3).multiplyScalar(rig.scale).add(rig.positions.get(track.bone));
              const error = bone.position.distanceTo(expected);
              maxExpectedTranslationError = Math.max(maxExpectedTranslationError, error);
              require(error < 1e-6, `${clip.id}/${track.bone}: actual translation differs from scaled payload frame (${error})`);
            }
          }
        }
        changingTracks += changed.size;
      }
    } finally { for (const rig of rigs) disposeRig(rig); }
    exactClipChecks += 1;
  }
  return { sharedPayloadRigCount: 2, maxSharedDeltaError, maxSharedHipsError,
    exactClipChecks, changingTracks, maxExpectedRotationError, maxExpectedTranslationError };
}

export function isolatedClipPayload(clip) {
  return { clips: [clip], auxiliaryClips: [], leftHandPoses: [], rightHandPoses: [], program: {
    parameters: [], commands: {}, baseLayer: "probe", poseSlots: [], layers: [{ id: "probe", blend: "override", weight: 1,
      initialState: "play", states: [{ id: "play", clip: clip.id, speed: 1, loop: false, transitions: [] }] }],
  } };
}

export function clipSampleTimes(clip) {
  const last = Math.min(clip.frames - 1, Math.floor(clip.duration * clip.sampleRate));
  const frames = new Set([0, Math.floor(last / 2), last]);
  // Include each track's most different reachable frame, so short gestures cannot
  // accidentally fall between the three coarse sample times.
  for (const track of clip.tracks) {
    for (const [key, width] of [["rotation", 4], ["translation", 3]]) {
      if (!track[key]?.length) continue;
      let bestFrame = 0, bestDifference = 0;
      for (let frame = 1; frame <= last; frame += 1) {
        let difference = 0;
        for (let c = 0; c < width; c += 1) difference += (track[key][frame * width + c] - track[key][c]) ** 2;
        if (difference > bestDifference) { bestDifference = difference; bestFrame = frame; }
      }
      if (bestDifference > 1e-10) frames.add(bestFrame);
    }
  }
  return [...frames].sort((a, b) => a - b).map(frame => frame === 0 ? 0 : Math.min(clip.duration, (frame + 0.25) / clip.sampleRate));
}

export function validateMotionResource(payload, label = "motion") {
  require(payload?.type === "motion", `${label}: type must be motion`);
  id(payload.name, `${label}.name`);
  if (payload.description !== undefined) require(typeof payload.description === "string", `${label}.description must be a string`);
  if (payload.motionGroup !== undefined) id(payload.motionGroup, `${label}.motionGroup`);
  return payload;
}

export async function motionFiles(root) {
  const indexFile = path.join(root, 'index.json');
  try {
    const index = JSON.parse(await fs.readFile(indexFile, 'utf8'));
    const motions = index.motions ?? [];
    require(Array.isArray(motions) && new Set(motions).size === motions.length, 'Invalid index motions');
    return motions.map(file => child(root, file));
  } catch (error) {
    if (error.code !== 'ENOENT' || error.path !== indexFile) throw error;
  }
  const files = [];
  async function scan(directory) {
    for (const entry of await fs.readdir(directory, { withFileTypes: true })) {
      const file = path.join(directory, entry.name);
      if (entry.isDirectory()) await scan(file);
      else if (entry.isFile() && entry.name.endsWith('.motionbin')) files.push(file);
      else if (entry.isFile() && entry.name.endsWith('.json') && entry.name !== 'config.json') {
        // JSON files in a resource tree may describe other resource types.
        if (JSON.parse(await fs.readFile(file, 'utf8'))?.type === 'motion') files.push(file);
      }
    }
  }
  await scan(root);
  return files.sort();
}

export async function auditMotions(directory, { expectedGroups = null, expectedClips = null, progress = () => {} } = {}) {
  if (expectedGroups !== null) require(expectedGroups && !Array.isArray(expectedGroups)
    && typeof expectedGroups === 'object' && Object.values(expectedGroups).every(n => Number.isInteger(n) && n >= 0), 'expected-groups must be a JSON object of nonnegative counts');
  if (expectedClips !== null) require(Number.isInteger(expectedClips) && expectedClips >= 0, 'expected-clips must be nonnegative');
  const root = path.resolve(directory);
  const work = await motionFiles(root), payloadPaths = new Set(work);
  const inventory = {};
  const results = [], groups = {}, started = Date.now();
  for (const file of work) {
    const result = { file: path.relative(root, file).replaceAll("\\", "/") };
    try {
      const bytes = await fs.readFile(file), payload = await readMotionFile(file, bytes);
      validateMotionResource(payload, file);
      result.name = payload.name; result.motionGroup = payload.motionGroup ?? null;
      const group = payload.motionGroup ?? "<common>";
      groups[group] = (groups[group] ?? 0) + 1;
      Object.assign(result, validateData(payload, file), probeSharedPayload(payload), {
        sha256: crypto.createHash("sha256").update(bytes).digest("hex"), error: null,
        payloadFields: Object.keys(payload).sort(),
      });
    } catch (error) { result.error = error.message; }
    results.push(result);
    if (results.length % 25 === 0 || results.length === work.length) progress(`Validated ${results.length}/${work.length}; failures ${results.filter(r => r.error).length}`);
  }
  Object.assign(inventory, groups);
  if (expectedGroups !== null) requireExactCounts(inventory, expectedGroups, "Motion groups");
  const failed = results.filter(r => r.error);
  const clipCount = results.reduce((sum, result) => sum + (result.clips ?? 0), 0);
  const coverageErrors = expectedClips === null || clipCount === expectedClips ? [] : [`Expected ${expectedClips} clips, found ${clipCount}`];
  const report = { root, motions: work.length, uniquePayloadFiles: payloadPaths.size, groups, passed: results.length - failed.length, failed: failed.length,
    expectedGroups, expectedClips, clipCount, coverageErrors,
    elapsedSeconds: (Date.now() - started) / 1000,
    checks: ["Self-contained motion metadata and validateMotionPayload", "Global clip IDs and Program/pose references", "Sampling frame count (including Unity float32 boundaries); array lengths/finite/unit quaternions/continuous hemisphere", "Humanoid translation only Hips; corresponding finger-only pose collections", "Group track shapes", "Exact same payload object drives two different reference frames, bone offsets and human scales without model-specific variants", "Every original clip independently sampled on both rigs: actual rotation = reference * payload quaternion, scaled Hips translation, changing source tracks actually change", "Disposing playback restores synthetic-rig bone transforms"],
    limits: ["Synthetic-rig playback proves shared-data runtime behavior; it does not replace Unity-to-target pose/visual acceptance", "Group tracks receive structural/numeric validation only; these rigs do not contain model-specific targets", "Shared-rig probe samples the program at accumulated times 0, 0.13, 0.56 seconds; all clips receive structural/numeric verification"], results };
  return report;
}

async function main() {
  const options = { root: 'output_packages', report: '.tmp/all-motion-validation.json', 'expected-groups': null, 'expected-clips': null };
  for (let i = 2; i < process.argv.length; i += 2) {
    const key = process.argv[i].slice(2);
    require(process.argv[i].startsWith('--') && Object.hasOwn(options, key) && process.argv[i + 1], `Invalid argument ${process.argv[i]}`);
    options[key] = process.argv[i + 1];
  }
  const report = await auditMotions(options.root, {
    expectedGroups: options['expected-groups'] === null ? null : JSON.parse(options['expected-groups']),
    expectedClips: options['expected-clips'] === null ? null : Number(options['expected-clips']),
    progress: console.log,
  });
  await fs.mkdir(path.dirname(path.resolve(options.report)), { recursive: true });
  await fs.writeFile(options.report, JSON.stringify(report, null, 2) + "\n", "utf8");
  console.log(JSON.stringify({ motions: report.motions, groups: report.groups, clipCount: report.clipCount, coverageErrors: report.coverageErrors, passed: report.passed, failed: report.failed, elapsedSeconds: report.elapsedSeconds, report: options.report }));
  if (report.coverageErrors.length) console.error(report.coverageErrors.join('\n'));
  if (report.failed || report.coverageErrors.length) process.exitCode = 1;
}

export function requireExactCounts(actual, expected, label) {
  require(Object.keys(actual).length === Object.keys(expected).length
    && Object.entries(expected).every(([key, count]) => actual[key] === count),
  `${label}: expected ${JSON.stringify(expected)}, found ${JSON.stringify(actual)}`);
}

if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href) main().catch(error => { console.error(error); process.exitCode = 1; });
