import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { discoverModels, writePreview, syncPreviews } from '../tools/generate-model-previews.mjs';

const preview = 'data:image/webp;base64,UklGRg==';
test('discover integrated components and sync only preview by name', async () => {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), 'model-previews-'));
  try {
    const output = path.join(root, 'output'), game = path.join(root, 'game');
    const source = path.join(output, 'source/config.json');
    const target = path.join(game, '自定义目录/config.json');
    await fs.mkdir(path.dirname(source), { recursive: true });
    await fs.mkdir(path.dirname(target), { recursive: true });
    const model = { type: 'model', name: 'Ruby', role: 'integrated', description: '説明', model: 'ruby.glb' };
    const sourceConfig = { components: [model, { type: 'motion', name: 'Idle' }] };
    const targetConfig = { components: [{ ...model, description: '用户说明', model: 'custom.glb', behaviors: [{ name: 'custom' }] }] };
    await fs.writeFile(source, JSON.stringify(sourceConfig));
    await fs.writeFile(target, JSON.stringify(targetConfig));
    await fs.writeFile(path.join(output, 'config.json'), JSON.stringify(sourceConfig));
    assert.equal((await discoverModels(output)).length, 1);
    await writePreview(source, 0, preview);
    assert.equal(await syncPreviews(output, game), 1);
    assert.deepEqual(JSON.parse(await fs.readFile(target, 'utf8')), {
      components: [{ ...targetConfig.components[0], preview }],
    });
    assert.deepEqual(JSON.parse(await fs.readFile(source, 'utf8')).components[1], sourceConfig.components[1]);
    await assert.rejects(writePreview(source, 0, 'data:image/png;base64,AAAA'), /WebP/);
  } finally { await fs.rm(root, { recursive: true, force: true }); }
});

test('duplicate source identities cannot silently select a thumbnail', async () => {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), 'model-previews-'));
  try {
    const output = path.join(root, 'output'), game = path.join(root, 'game');
    await fs.mkdir(game);
    for (const directory of ['one', 'two']) {
      await fs.mkdir(path.join(output, directory), { recursive: true });
      await fs.writeFile(path.join(output, directory, 'config.json'), JSON.stringify({
        components: [{ type: 'model', role: 'integrated', name: 'Same', preview }],
      }));
    }
    await assert.rejects(syncPreviews(output, game), /Duplicate model name/);
  } finally { await fs.rm(root, { recursive: true, force: true }); }
});
