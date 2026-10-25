import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import test from 'node:test';
import { chromium } from 'playwright';
import { createServer } from 'vite';
import previewConfig from '../vite.config.js';

test('preview serves the real cloth WASM when the renderer is installed as a dependency', { timeout: 30_000 }, async t => {
  const temporary = path.resolve('.tmp');
  await fs.mkdir(temporary, { recursive: true });
  const directory = await fs.mkdtemp(path.join(temporary, 'cloth-wasm-test-'));
  t.after(() => fs.rm(directory, { recursive: true, force: true }));
  await fs.writeFile(path.join(directory, 'index.html'), '<script type="module" src="./probe.js"></script>');
  await fs.writeFile(path.join(directory, 'probe.js'), `
    import * as THREE from 'three';
    import { createJoltClothSolver } from 'webgal-lovelive-gltf-renderer/jolt-cloth-solver.js';
    console.info('[cloth-probe] module imports complete');
    try {
      console.info('[cloth-probe] creating solver');
      const solver = await createJoltClothSolver({
        positions: [new THREE.Vector3(0, 0, 0), new THREE.Vector3(1, 0, 0), new THREE.Vector3(0, 1, 0)],
        indices: [0, 1, 2], fixed: new Set([0]), radius: 0.01, damping: 0.1, colliders: [],
      });
      solver.destroy();
      console.info('[cloth-probe] solver created and destroyed');
      window.clothProbe = { passed: true };
    } catch (error) { console.error('[cloth-probe]', error.stack ?? error.message); window.clothProbe = { error: error.message }; }
  `);
  const server = await createServer({ ...previewConfig, configFile: false, root: directory, logLevel: 'silent',
    server: { ...previewConfig.server, host: '127.0.0.1', port: 0 } });
  t.after(() => server.close());
  await server.listen();
  const browser = await chromium.launch({ headless: true });
  t.after(() => browser.close());
  const page = await browser.newPage();
  const requests = [];
  page.on('console', message => console.info('[cloth-browser-console]', message.type(), message.text()));
  page.on('pageerror', error => console.error('[cloth-browser-pageerror]', error.stack ?? error.message));
  page.on('requestfailed', request => console.error('[cloth-browser-requestfailed]', request.url(), request.failure()));
  page.on('response', response => {
    if (!response.ok()) console.error('[cloth-browser-response]', response.status(), response.url());
    if (response.url().split('?')[0].endsWith('.wasm')) requests.push({ url: response.url(),
      status: response.status(), type: response.headers()['content-type'] });
    if (response.url().split('?')[0].endsWith('.wasm')) console.info('[cloth-browser-wasm]', requests.at(-1));
  });
  await page.goto(`http://127.0.0.1:${server.httpServer.address().port}`);
  await page.waitForFunction(() => window.clothProbe);
  assert.deepEqual(await page.evaluate(() => window.clothProbe), { passed: true }, JSON.stringify(requests));
  assert.ok(requests.length, 'The solver must actually fetch its WASM');
  assert.ok(requests.every(request => request.status === 200 && !request.type?.includes('text/html')), JSON.stringify(requests));
});
