import assert from 'node:assert/strict';
import test from 'node:test';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { createServer } from 'vite';
import { chromium } from 'playwright';
import previewConfig from '../vite.config.js';
import { readParameterInput, previewParameterInput } from '../tools/preview-parameter-input.mjs';

async function fixture(t) {
  const directory = await fs.mkdtemp(path.join(os.tmpdir(), 'parameter-input-'));
  t.after(() => fs.rm(directory, { recursive: true, force: true }));
  const root = path.join(directory, '.mtn_exp');
  await fs.mkdir(path.join(root, 'motions/PARAM_IMPORT__37/anon'), { recursive: true });
  await fs.mkdir(path.join(root, 'expressions/__base__/anon'), { recursive: true });
  const model = { model: '.chara/missing.moc', textures: ['missing.png'], physics: 'missing.json',
    motions: { 'anon/angry01': [{ file: '../.mtn_exp/motions/PARAM_IMPORT__37/anon/angry01.mtn', fade_in: 150, fade_out: 250 }] },
    expressions: [{ name: 'anon/angry01', file: '../.mtn_exp/expressions/__base__/anon/angry01.exp.json' }] };
  await fs.writeFile(path.join(root, 'model.json'), JSON.stringify(model));
  await fs.writeFile(path.join(root, 'motions/PARAM_IMPORT__37/anon/angry01.mtn'), '# fps=30\nPARAM_ANGLE_X=0,1\n');
  await fs.writeFile(path.join(root, 'expressions/__base__/anon/angry01.exp.json'), '{"params":[]}');
  return { directory, root, model };
}

test('parameter input preserves source names and uses default motion fades', async t => {
  const { root } = await fixture(t);
  const manifest = await readParameterInput(root);
  assert.deepEqual(manifest.components, [
    { type: 'garupa-motion', name: 'anon/angry01', src: 'motions/PARAM_IMPORT__37/anon/angry01.mtn', fade_in: 500, fade_out: 500 },
    { type: 'garupa-expression', name: 'anon/angry01', src: 'expressions/__base__/anon/angry01.exp.json' },
  ]);
  assert.deepEqual(await readParameterInput(path.join(root, 'absent')), { components: [] });
  await fs.unlink(path.join(root, 'motions/PARAM_IMPORT__37/anon/angry01.mtn'));
  await assert.rejects(readParameterInput(root), /anon\/angry01.*参数文件不可用/);
});

test('parameter input names each entry in a source motion group and diagnoses invalid manifests', async t => {
  const { root, model } = await fixture(t);
  model.motions['anon/angry01'].push({ ...model.motions['anon/angry01'][0] });
  await fs.writeFile(path.join(root, 'model.json'), JSON.stringify(model));
  assert.deepEqual((await readParameterInput(root)).components.slice(0, 2).map(c => c.name), ['anon/angry01/1', 'anon/angry01/2']);
  model.motions['anon/angry01'][0].file = '../outside.mtn';
  await fs.writeFile(path.join(root, 'model.json'), JSON.stringify(model));
  await assert.rejects(readParameterInput(root), /超出/);
  await fs.unlink(path.join(root, 'model.json'));
  await assert.rejects(readParameterInput(root), /无法读取.*model.json/);
});

test('preview serves source files on demand and discovers changes on refresh without writing configs', async t => {
  const { directory, root } = await fixture(t);
  const server = await createServer({ root: directory, configFile: false, logLevel: 'silent', plugins: [previewParameterInput(root)],
    optimizeDeps: { noDiscovery: true, include: [] }, server: { host: '127.0.0.1', port: 0 } });
  await server.listen(); t.after(() => server.close());
  const base = `http://127.0.0.1:${server.httpServer.address().port}/packages/parameter-input/`;
  let response = await fetch(base + 'config.json');
  assert.equal(response.status, 200); assert.equal(response.headers.get('cache-control'), 'no-store');
  const manifest = await response.json();
  assert.equal(await (await fetch(base + manifest.components[0].src)).text(), '# fps=30\nPARAM_ANGLE_X=0,1\n');
  await fs.writeFile(path.join(root, 'motions/PARAM_IMPORT__37/anon/angry01.mtn'), 'changed');
  assert.equal(await (await fetch(base + manifest.components[0].src)).text(), 'changed');
  assert.equal((await fetch(base + 'model.json')).status, 404);
  assert.equal((await fetch(base + '%2e%2e%2foutside.mtn')).status, 400);
  await fs.unlink(path.join(root, 'model.json'));
  response = await fetch(base + 'config.json');
  assert.equal(response.status, 400); assert.match((await response.json()).error, /model.json/);
  await assert.rejects(fs.stat(path.join(root, 'config.json')), { code: 'ENOENT' });
});

test('main preview lists only input parameter resources', { timeout: 30_000 }, async t => {
  const { root } = await fixture(t);
  const server = await createServer({ ...previewConfig, configFile: false, logLevel: 'silent',
    plugins: [previewParameterInput(root), ...previewConfig.plugins.filter(plugin => plugin.name !== 'preview-parameter-input')],
    server: { ...previewConfig.server, host: '127.0.0.1', port: 0 } });
  await server.listen(); t.after(() => server.close());
  const browser = await chromium.launch({ headless: true }); t.after(() => browser.close());
  const page = await browser.newPage();
  const origin = `http://127.0.0.1:${server.httpServer.address().port}`;
  await page.route(`${origin}/packages/config.json`, route => route.fulfill({ json: { components: [
    { type: 'garupa-motion', name: 'output-only', src: 'old.mtn', sourceConfig: 'old/config.json' },
    { type: 'garupa-expression', name: 'output-only', src: 'old.exp.json', sourceConfig: 'old/config.json' },
  ] } }));
  await page.route('**/packages/runtime/**', route => route.fulfill({ json: { components: [
    { type: 'behavior', namespace: 'Fixture', name: route.request().url().split('/').at(-2), script: 'unused.js' },
  ] } }));
  await page.goto(origin);
  await page.waitForFunction(() => [...document.querySelector('#parameter-expression').options].some(o => o.text.includes('anon/angry01')));
  const expressions = await page.locator('#parameter-expression option').evaluateAll(options => options.filter(o => o.text.includes('anon/angry01')).map(o => o.value));
  assert.equal(expressions.length, 1); assert.ok(expressions[0].startsWith('parameter-input/config.json#'));
  await page.selectOption('#motion-source', 'garupa');
  const motions = await page.locator('#motion option').evaluateAll(options => options.filter(o => o.text.includes('anon/angry01')).map(o => o.value));
  assert.equal(motions.length, 1); assert.ok(motions[0].startsWith('parameter-input/config.json#'));
  assert.equal(await page.locator('#motion option').evaluateAll(options => options.some(o => o.text.includes('output-only'))), false);
  assert.equal(await page.locator('#parameter-expression option').evaluateAll(options => options.some(o => o.text.includes('output-only'))), false);
});
