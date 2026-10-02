import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { exportGarupaLive2d } from '../tools/export-garupa-live2d.mjs';

test('exports a self-contained parameter package with original bytes, names and fades', async t => {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), 'garupa-export-'));
  t.after(() => fs.rm(root, { recursive: true, force: true }));
  const input = path.join(root, '.mtn_exp'), output = path.join(root, 'output');
  await fs.mkdir(path.join(input, 'motions'), { recursive: true });
  await fs.mkdir(path.join(input, 'expressions'), { recursive: true });
  const motion = Buffer.from('# fps=30\nPARAM_ANGLE_X=0,1\n');
  const expression = Buffer.from('{"params":[]}');
  await fs.writeFile(path.join(input, 'motions', '中文.mtn'), motion);
  await fs.writeFile(path.join(input, 'expressions', 'smile.exp.json'), expression);
  await fs.writeFile(path.join(input, 'unused.moc'), 'unused');
  await fs.writeFile(path.join(input, 'model.json'), JSON.stringify({
    motions: { 'anon/test': [{ file: '../.mtn_exp/motions/中文.mtn', fade_in: 200 }] },
    expressions: [{ name: 'anon/smile', file: 'expressions/smile.exp.json' }],
  }));
  const config = await exportGarupaLive2d(input, output);
  assert.equal(config.components[0].name, 'anon/test');
  assert.equal(config.components[0].fade_in, 200);
  assert.equal(config.components[0].src, 'anon/test.mtn');
  assert.equal(config.components[1].src, 'anon/smile.exp.json');
  assert.deepEqual(JSON.parse(await fs.readFile(path.join(output, 'config.json'), 'utf8')), config);
  for (const component of config.components) {
    const relative = component.src.split('/').map(decodeURIComponent).join(path.sep);
    assert.deepEqual(await fs.readFile(path.join(output, relative)), component.type === 'garupa-motion' ? motion : expression);
  }
  await assert.rejects(fs.stat(path.join(output, 'unused.moc')), { code: 'ENOENT' });
  await exportGarupaLive2d(input, output);
  await assert.rejects(exportGarupaLive2d(input, input), /互相包含/);
  await assert.rejects(exportGarupaLive2d(path.join(root, 'missing'), output), /没有声明/);
});

test('exports custom resources by their declared nested names and refuses path escapes', async t => {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), 'garupa-export-names-'));
  t.after(() => fs.rm(root, { recursive: true, force: true }));
  const input = path.join(root, 'input'), output = path.join(root, 'output');
  await fs.mkdir(input);
  await fs.writeFile(path.join(input, 'source.mtn'), '# fps=30\n');
  const model = { motions: {
    'custom/中文 名/gesture': [{ file: 'source.mtn' }],
    'anon/group': [{ file: 'source.mtn' }, { file: 'source.mtn' }],
  } };
  await fs.writeFile(path.join(input, 'model.json'), JSON.stringify(model));
  const config = await exportGarupaLive2d(input, output);
  assert.deepEqual(config.components.map(c => c.name), ['custom/中文 名/gesture', 'anon/group/1', 'anon/group/2']);
  assert.equal(config.components[0].src, 'custom/%E4%B8%AD%E6%96%87%20%E5%90%8D/gesture.mtn');
  for (const file of ['custom/中文 名/gesture.mtn', 'anon/group/1.mtn', 'anon/group/2.mtn']) {
    assert.equal(await fs.readFile(path.join(output, file), 'utf8'), '# fps=30\n');
  }
  model.motions = { '../escape': [{ file: 'source.mtn' }] };
  await fs.writeFile(path.join(input, 'model.json'), JSON.stringify(model));
  await assert.rejects(exportGarupaLive2d(input, output), /包内路径/);
  assert.deepEqual(JSON.parse(await fs.readFile(path.join(output, 'config.json'), 'utf8')), config);
});
