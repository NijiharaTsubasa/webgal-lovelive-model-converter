import assert from 'node:assert/strict';
import test from 'node:test';
import { chromium } from 'playwright';
import { createServer } from 'vite';

test('native select replays the selected item without loading a changed item twice', { timeout: 30_000 }, async (t) => {
  const vite = await createServer({ logLevel: 'silent', server: { host: '127.0.0.1', port: 0 } });
  await vite.listen();
  const browser = await chromium.launch({ headless: true });
  t.after(async () => { await browser.close(); await vite.close(); });
  const page = await browser.newPage();
  const origin = `http://127.0.0.1:${vite.httpServer.address().port}`;
  await page.route(`${origin}/`, (route) => route.fulfill({ contentType: 'text/html', body: `
    <select id="motion"><option value="first">First</option><option value="second">Second</option></select>
    <script type="module">
      import { onSelectIncludingRepeat } from '/src/replayable-select.js';
      window.played = [];
      onSelectIncludingRepeat(document.querySelector('#motion'), value => window.played.push(value));
    </script>
  ` }));
  await page.goto(origin);
  await page.waitForFunction(() => Array.isArray(window.played));

  await page.locator('#motion').click();
  await page.keyboard.press('Enter');
  assert.deepEqual(await page.evaluate(() => window.played), ['first']);

  await page.locator('#motion').click();
  await page.keyboard.press('ArrowDown');
  await page.keyboard.press('Enter');
  assert.deepEqual(await page.evaluate(() => window.played), ['first', 'second']);

  await page.locator('#motion').click();
  await page.keyboard.press('Enter');
  assert.deepEqual(await page.evaluate(() => window.played), ['first', 'second', 'second']);
});
