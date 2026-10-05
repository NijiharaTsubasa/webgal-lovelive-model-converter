import assert from 'node:assert/strict';
import test from 'node:test';
import path from 'node:path';
import { createRequire } from 'node:module';
import { chromium } from 'playwright';
import { createServer } from 'vite';

function fixtureGlb() {
  const json = Buffer.from(JSON.stringify({
    asset: { version: '2.0' }, scene: 0, scenes: [{ nodes: [0] }],
    nodes: [{ name: 'Root' }],
  }), 'utf8');
  const length = Math.ceil(json.length / 4) * 4;
  const bytes = Buffer.alloc(20 + length, 0x20);
  bytes.write('glTF', 0, 'ascii');
  bytes.writeUInt32LE(2, 4);
  bytes.writeUInt32LE(bytes.length, 8);
  bytes.writeUInt32LE(length, 12);
  bytes.writeUInt32LE(0x4e4f534a, 16);
  json.copy(bytes, 20);
  return bytes;
}

function model(name, eyeNames, mouthNames, selection) {
  return {
    type: 'model', name, role: 'integrated', model: 'model.glb', humanoidScale: 1,
    morphPoses: [],
    expressionGroups: [
      { name: 'eyes', type: 'eye', states: eyeNames.map(name => ({ name, poses: {}, controls: { blink: {} } })) },
      { name: 'lips', type: 'mouth', states: mouthNames.map(name => ({ name, poses: {} })) },
    ],
    defaultExpression: selection,
  };
}

test('native expression cascade commits on its last step and preserves compatible model state', { timeout: 60_000 }, async t => {
  const models = [
    model('First', ['Open', 'Sad'], ['Closed', 'A', 'Smile'], { eye: 'Open', closed: 'Closed', open: 'A' }),
    model('Second', ['Open', 'Sad'], ['Closed', 'A', 'Smile'], { eye: 'Open', closed: 'Closed', open: 'A' }),
    model('Third', ['DifferentEye'], ['DifferentClosed', 'DifferentOpen'],
      { eye: 'DifferentEye', closed: 'DifferentClosed', open: 'DifferentOpen' }),
  ];
  const rendererSource = path.dirname(createRequire(import.meta.url).resolve('webgal-lovelive-gltf-renderer'));
  const vite = await createServer({ logLevel: 'silent',
    resolve: { alias: { 'webgal-lovelive-gltf-renderer': rendererSource } },
    server: { host: '127.0.0.1', port: 0 } });
  await vite.listen();
  t.after(() => vite.close());
  const browser = await chromium.launch({ headless: true });
  t.after(() => browser.close());
  const page = await browser.newPage();
  page.setDefaultTimeout(10_000);
  const failures = [];
  page.on('pageerror', error => failures.push(error.message));
  page.on('console', message => { if (message.type() === 'error') failures.push(message.text()); });
  await page.route('**/src/main.js', async route => {
    const response = await route.fetch();
    const body = await response.text();
    await route.fulfill({ response, body: `${body}\n
      const calls = [];
      const originalSetExpression = character.setExpression.bind(character);
      character.setExpression = (...args) => { calls.push(args[0]); return originalSetExpression(...args); };
      window.__nativeExpressionProbe = () => ({
        selection: character.faceCapabilities?.selections,
        blink: character.face?.blink, speech: character.face?.speech, calls: [...calls],
      });` });
  });
  await page.route('**/packages/**', route => {
    const pathname = new URL(route.request().url()).pathname;
    if (pathname === '/packages/config.json') return route.fulfill({ json: {
      components: models.map(component => ({ ...component, sourceConfig: `fixture/${component.name}/config.json` })),
    } });
    if (pathname === '/packages/parameter-input/config.json' || pathname.startsWith('/packages/runtime/')) {
      return route.fulfill({ json: { components: [] } });
    }
    const name = pathname.split('/')[3];
    const component = models.find(component => component.name === name);
    if (component && pathname.endsWith('/config.json')) return route.fulfill({ json: { components: [component] } });
    if (component && pathname.endsWith('/model.glb')) return route.fulfill({ contentType: 'model/gltf-binary', body: fixtureGlb() });
    return route.abort();
  });
  await page.goto(vite.resolvedUrls.local[0], { waitUntil: 'commit', timeout: 30_000 });
  await page.waitForFunction(() => window.__nativeExpressionProbe?.().selection?.eye === 'Open').catch(async error => {
    throw new Error(`${error.message}; status=${await page.locator('#status').textContent()}; errors=${JSON.stringify(failures)}`);
  });
  const selects = page.locator('#expression-groups select');
  assert.equal(await selects.count(), 3);
  assert.deepEqual(await page.locator('#expression-groups label').evaluateAll(labels => labels.map(label => label.firstChild.textContent)),
    ['3D眼型', '3D闭口', '3D张口']);
  assert.deepEqual(await selects.evaluateAll(items => items.map(item => item.value)), ['Open', 'Closed', 'A']);
  const initial = await page.evaluate(() => window.__nativeExpressionProbe());
  await selects.nth(0).selectOption('Sad');
  await selects.nth(1).selectOption('Smile');
  let state = await page.evaluate(() => window.__nativeExpressionProbe());
  assert.deepEqual(state.selection, initial.selection);
  assert.equal(state.calls.length, initial.calls.length, 'the first two cascade steps only edit the pending selection');
  // Confirming the current last option must also commit pending earlier steps.
  await selects.nth(2).dispatchEvent('click', { detail: 0 });
  state = await page.evaluate(() => window.__nativeExpressionProbe());
  assert.deepEqual(state.selection, { eye: 'Sad', closed: 'Smile', open: 'A' });
  assert.equal(state.calls.length, initial.calls.length + 1);
  await selects.nth(2).selectOption('Smile');
  assert.deepEqual((await page.evaluate(() => window.__nativeExpressionProbe())).selection,
    { eye: 'Sad', closed: 'Smile', open: 'Smile' });
  await page.locator('#eye-open').evaluate(input => { input.value = '0.34'; input.dispatchEvent(new Event('input')); });
  await page.locator('#mouth-open').evaluate(input => { input.value = '0.67'; input.dispatchEvent(new Event('input')); });
  await page.selectOption('#character', 'fixture/Second/config.json#model:Second:integrated');
  await page.waitForFunction(() => document.querySelector('#status').textContent === 'Second');
  state = await page.evaluate(() => window.__nativeExpressionProbe());
  assert.deepEqual(state.selection, { eye: 'Sad', closed: 'Smile', open: 'Smile' });
  assert.ok(Math.abs(state.blink - 0.66) < 1e-8);
  assert.equal(state.speech, 0.67);
  assert.deepEqual(await selects.evaluateAll(items => items.map(item => item.value)), ['Sad', 'Smile', 'Smile']);
  await page.selectOption('#character', 'fixture/Third/config.json#model:Third:integrated');
  await page.waitForFunction(() => document.querySelector('#status').textContent === 'Third');
  state = await page.evaluate(() => window.__nativeExpressionProbe());
  assert.deepEqual(state.selection, models[2].defaultExpression);
  assert.ok(Math.abs(state.blink - 0.66) < 1e-8);
  assert.equal(state.speech, 0.67);
  assert.equal(await page.locator('#eye-open').inputValue(), '0.34');
  assert.equal(await page.locator('#mouth-open').inputValue(), '0.67');
  assert.deepEqual(failures, []);
});
