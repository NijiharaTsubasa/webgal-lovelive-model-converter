import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import test from 'node:test';
import { chromium } from 'playwright';
import { createServer } from 'vite';
import previewConfig from '../vite.config.js';

test('preview runs the renderer mesh cloth when the renderer is installed as a dependency', { timeout: 30_000 }, async t => {
  const temporary = path.resolve('.tmp');
  await fs.mkdir(temporary, { recursive: true });
  const directory = await fs.mkdtemp(path.join(temporary, 'mesh-cloth-test-'));
  t.after(() => fs.rm(directory, { recursive: true, force: true }));
  await fs.writeFile(path.join(directory, 'index.html'), '<script type="module" src="./probe.js"></script>');
  await fs.writeFile(path.join(directory, 'probe.js'), `
    import * as THREE from 'three';
    import { createMeshCloth } from 'webgal-lovelive-gltf-renderer/mesh-cloth.js';
    try {
      const root = new THREE.Group();
      const geometry = new THREE.PlaneGeometry(1, 1, 8, 8);
      const count = geometry.getAttribute('position').count;
      const weights = new Float32Array(count * 4);
      for (let i = 0; i < count; i++) weights[i * 4] = 1;
      geometry.setAttribute('skinIndex', new THREE.BufferAttribute(new Uint16Array(count * 4), 4));
      geometry.setAttribute('skinWeight', new THREE.BufferAttribute(weights, 4));
      const mesh = new THREE.SkinnedMesh(geometry, new THREE.MeshBasicMaterial());
      const bone = new THREE.Bone(); root.add(bone, mesh); mesh.bind(new THREE.Skeleton([bone]));
      // A body-side collider behind the sheet (its normal faces +Z).
      const collider = new THREE.Object3D(); collider.position.set(0, -.2, -.05); root.add(collider);
      const fixed = [...Array(9).keys()];
      const physics = { springs: [], colliders: [{ shape: 'sphere', node: 1, offset: [0, 0, 0], radius: .15 }],
        cloths: [{ node: 0, primitive: 0, fixed, radius: .003, stiffness: 12, damping: .8, gravity: [0, 0, 0], colliders: [0] }] };
      root.updateMatrixWorld(true);
      const cloth = await createMeshCloth(root, [{ physics, resolve: i => [mesh, collider][i] }]);
      for (let i = 0; i < 30; i++) { cloth.beforeAnimation(); root.updateMatrixWorld(true); cloth.update(1 / 60); }
      const moved = geometry.getAttribute('position').getZ(6 * 9 + 4); // (0, -0.25), inside the sphere at rest
      cloth.destroy();
      window.clothProbe = { passed: moved > .05 };
    } catch (error) { console.error('[cloth-probe]', error.stack ?? error.message); window.clothProbe = { error: error.message }; }
  `);
  const server = await createServer({ ...previewConfig, configFile: false, root: directory, logLevel: 'silent',
    server: { ...previewConfig.server, host: '127.0.0.1', port: 0 } });
  t.after(() => server.close());
  await server.listen();
  const browser = await chromium.launch({ headless: true });
  t.after(() => browser.close());
  const page = await browser.newPage();
  page.on('pageerror', error => console.error('[cloth-browser-pageerror]', error.stack ?? error.message));
  await page.goto(`http://127.0.0.1:${server.httpServer.address().port}`);
  await page.waitForFunction(() => window.clothProbe);
  assert.deepEqual(await page.evaluate(() => window.clothProbe), { passed: true });
});
