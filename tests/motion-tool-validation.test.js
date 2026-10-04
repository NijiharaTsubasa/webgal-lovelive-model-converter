import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { auditMotions, readMotionFile, validateData } from '../tools/validate-all-motions.mjs';

function motion() {
  return { type: 'motion', name: 'original_idle', description: '', clips: [{ id: 'clip', name: 'clip', duration: 1, sampleRate: 1, frames: 2,
    tracks: [{ bone: 'Hips', rotation: [0, 0, 0, 1, 0, 0, 0, 1], translation: [0, 0, 0, 0, 0.1, 0] }] }],
  auxiliaryClips: [], leftHandPoses: [], rightHandPoses: [], program: { parameters: [], commands: {}, poseSlots: [],
    baseLayer: 'base', layers: [{ id: 'base', blend: 'override', weight: 1, initialState: 'play',
      states: [{ id: 'play', clip: 'clip', speed: 1, loop: false, transitions: [] }] }] } };
}

function binary(payload) {
  const header = structuredClone(payload), chunks = [];
  let offset = 0;
  for (const track of header.clips[0].tracks) for (const key of ['rotation', 'translation']) {
    const values = track[key], chunk = Buffer.alloc(values.length * 8);
    values.forEach((value, i) => chunk.writeDoubleLE(value, i * 8));
    track[key] = { type: 'f64', offset, length: values.length };
    chunks.push(chunk); offset += chunk.length;
  }
  const json = Buffer.from(JSON.stringify(header)), start = Math.ceil((12 + json.length) / 8) * 8;
  const prefix = Buffer.alloc(start);
  prefix.write('MOTION\0\0'); prefix.writeUInt32LE(json.length, 8); json.copy(prefix, 12);
  return Buffer.concat([prefix, ...chunks]);
}

async function fixture(t) {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), 'motion-tool-'));
  t.after(() => fs.rm(root, { recursive: true, force: true }));
  return root;
}

test('motion reader validates JSON and binary arrays identically, including malformed binary', async t => {
  const root = await fixture(t), payload = motion();
  await fs.writeFile(path.join(root, 'a.json'), JSON.stringify(payload));
  await fs.writeFile(path.join(root, 'a.motionbin'), binary(payload));
  assert.deepEqual(validateData(await readMotionFile(path.join(root, 'a.json'))),
    validateData(await readMotionFile(path.join(root, 'a.motionbin'))));
  await fs.writeFile(path.join(root, 'bad.motionbin'), 'invalid');
  await assert.rejects(readMotionFile(path.join(root, 'bad.motionbin')), /Invalid binary motion/);
});

test('motion audit scans standalone files and has no fixed corpus counts', async t => {
  const root = await fixture(t);
  await fs.writeFile(path.join(root, 'a.motionbin'), binary(motion()));
  const report = await auditMotions(root);
  assert.equal(report.passed, 1); assert.equal(report.failed, 0);
  assert.equal(report.uniquePayloadFiles, 1); assert.deepEqual(report.coverageErrors, []);
  await assert.rejects(auditMotions(root, { expectedGroups: { '<common>': 3 } }), /expected/);
  assert.equal((await auditMotions(root, { expectedClips: 3 })).coverageErrors.length, 1);
});

test('motion audit uses current index without treating the root preview catalog as a package', async t => {
  const root = await fixture(t);
  await fs.mkdir(path.join(root, 'motion'));
  await fs.writeFile(path.join(root, 'config.json'), JSON.stringify({ components: [{ type: 'motion', name: 'preview-only' }] }));
  await fs.writeFile(path.join(root, 'index.json'), JSON.stringify({ configs: [], motions: ['motion/a.json'] }));
  await fs.writeFile(path.join(root, 'motion/a.json'), JSON.stringify(motion()));
  const report = await auditMotions(root);
  assert.equal(report.failed, 0); assert.equal(report.motions, 1);
});

test('motion audit allows the same motion identity in independent packages', async t => {
  const root = await fixture(t);
  for (const name of ['first', 'second']) {
    const directory = path.join(root, name);
    await fs.mkdir(directory);
    await fs.writeFile(path.join(directory, 'idle.json'), JSON.stringify(motion()));
  }
  const report = await auditMotions(root);
  assert.equal(report.passed, 2);
  assert.equal(report.failed, 0);
  assert.equal(report.uniquePayloadFiles, 2);
});

test('motion audit allows repeated names across files and rejects duplicate index paths', async t => {
  const root = await fixture(t);
  await fs.writeFile(path.join(root, 'first.json'), JSON.stringify(motion()));
  await fs.writeFile(path.join(root, 'second.json'), JSON.stringify(motion()));
  assert.equal((await auditMotions(root)).passed, 2);
  await fs.writeFile(path.join(root, 'index.json'), JSON.stringify({ configs: [], motions: ['first.json', 'first.json'] }));
  await assert.rejects(auditMotions(root), /Invalid index motions/);
});

test('motion audit accepts an empty subset and reports missing self-contained metadata', async t => {
  const root = await fixture(t);
  assert.equal((await auditMotions(root)).motions, 0);
  const payload = motion(); delete payload.name;
  await fs.writeFile(path.join(root, 'bad.motionbin'), binary(payload));
  const report = await auditMotions(root);
  assert.equal(report.failed, 1);
  assert.match(report.results[0].error, /name/);
});

test('motion audit reports malformed tracks and accepts double-precision frame boundaries', () => {
  const payload = motion();
  payload.clips[0].duration = 0.2; payload.clips[0].sampleRate = 10.00000001;
  payload.clips[0].frames = 4;
  payload.clips[0].tracks[0].rotation = [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1];
  payload.clips[0].tracks[0].translation = Array(12).fill(0);
  validateData(payload);
  payload.clips[0].tracks[0].translation[0] = NaN;
  assert.throws(() => validateData(payload), /nonfinite/);
});
