import assert from 'node:assert/strict';
import test from 'node:test';
import { chromium } from 'playwright';
import { createServer } from 'vite';

test('preview canvas follows its viewport when the window grows and shrinks', { timeout: 30_000 }, async (t) => {
  const vite = await createServer({ logLevel: 'silent', server: { host: '127.0.0.1', port: 0 } });
  await vite.listen();
  const browser = await chromium.launch({ headless: true });
  t.after(async () => { await browser.close(); await vite.close(); });
  const page = await browser.newPage({ viewport: { width: 1024, height: 800 } });
  const origin = `http://127.0.0.1:${vite.httpServer.address().port}`;
  await page.route('**/packages/runtime/**', (route) => route.fulfill({ json: { components: [] } }));
  await page.route('**/packages/parameter-input/config.json', (route) => route.fulfill({ json: { components: [] } }));
  await page.route(`${origin}/packages/config.json`, (route) => route.fulfill({
    contentType: 'application/json', body: '{"components":[]}',
  }));
  await page.route(`${origin}/src/main.js*`, async (route) => {
    const response = await route.fetch();
    await route.fulfill({ response, body: `${await response.text()}\nwindow.__previewAspect = () => camera.aspect;` });
  });
  await page.goto(origin);
  await page.waitForFunction(() => window.__previewAspect);
  for (const [width, height] of [[1920, 1080], [1024, 800]]) {
    await page.setViewportSize({ width, height });
    const snapshot = await page.waitForFunction(({ width, height }) => {
      if (innerWidth !== width || innerHeight !== height) return false;
      const viewport = document.querySelector('#viewport');
      const canvas = viewport.querySelector('canvas');
      const rect = canvas.getBoundingClientRect();
      const cameraAspect = window.__previewAspect();
      if (canvas.width !== viewport.clientWidth || canvas.height !== viewport.clientHeight
        || Math.abs(rect.width - viewport.clientWidth) > 1
        || Math.abs(rect.height - viewport.clientHeight) > 1
        || Math.abs(cameraAspect - viewport.clientWidth / viewport.clientHeight) >= 1e-6) return false;
      return { viewport: [viewport.clientWidth, viewport.clientHeight],
        canvas: [rect.width, rect.height], buffer: [canvas.width, canvas.height], cameraAspect };
    }, { width, height });
    const result = await snapshot.jsonValue();
    await snapshot.dispose();
    assert.ok(Math.abs(result.canvas[0] - result.viewport[0]) <= 1, JSON.stringify(result));
    assert.ok(Math.abs(result.canvas[1] - result.viewport[1]) <= 1, JSON.stringify(result));
    assert.ok(Math.abs(result.cameraAspect - result.viewport[0] / result.viewport[1]) < 1e-6,
      JSON.stringify(result));
  }
});
