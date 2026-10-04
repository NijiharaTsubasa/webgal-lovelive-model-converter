import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { exportGarupaLive2d } from '../tools/export-garupa-live2d.mjs';

test('exports parameter files with original bytes and declared names', async t => {
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
  assert.equal(await exportGarupaLive2d(input, output), 2);
  assert.deepEqual(await fs.readFile(path.join(output, 'anon/test.mtn')), motion);
  assert.deepEqual(await fs.readFile(path.join(output, 'anon/smile.exp.json')), expression);
  await assert.rejects(fs.stat(path.join(output, 'config.json')), { code: 'ENOENT' });
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
  assert.equal(await exportGarupaLive2d(input, output), 3);
  for (const file of ['custom/中文 名/gesture.mtn', 'anon/group/1.mtn', 'anon/group/2.mtn']) {
    assert.equal(await fs.readFile(path.join(output, file), 'utf8'), '# fps=30\n');
  }
  model.motions = { '../escape': [{ file: 'source.mtn' }] };
  await fs.writeFile(path.join(input, 'model.json'), JSON.stringify(model));
  await assert.rejects(exportGarupaLive2d(input, output), /包内路径/);
  await assert.rejects(fs.stat(path.join(output, 'config.json')), { code: 'ENOENT' });
});
