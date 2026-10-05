import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import net from "node:net";
import path from "node:path";
import test from "node:test";

import { chromium } from "playwright";

async function freePort() {
  const server = net.createServer();
  await new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", resolve);
  });
  const { port } = server.address();
  await new Promise((resolve, reject) => server.close((error) => error ? reject(error) : resolve()));
  return port;
}

async function waitForServer(url, child) {
  for (let attempt = 0; attempt < 200; attempt += 1) {
    if (child.exitCode !== null) throw new Error(`Vite exited with ${child.exitCode}`);
    try {
      const response = await fetch(url);
      if (response.ok) return;
    } catch {}
    await new Promise((resolve) => setTimeout(resolve, 50));
  }
  throw new Error(`Vite did not start at ${url}`);
}

test("Chrome loads one preview catalog, fetches only selected manifests, and survives rapid input", { timeout: 120_000 }, async (t) => {
  const port = await freePort();
  const server = spawn(process.execPath, [path.resolve("node_modules/vite/bin/vite.js"), "--host", "127.0.0.1", "--port", String(port)], {
    cwd: process.cwd(),
    stdio: "ignore",
    windowsHide: true,
  });
  t.after(() => { if (server.exitCode === null) server.kill(); });
  const baseUrl = `http://127.0.0.1:${port}`;
  await waitForServer(baseUrl, server);

  const browser = await chromium.launch({ headless: true });
  t.after(() => browser.close());
  const page = await browser.newPage();
  await page.addInitScript(() => {
    const originalFetch = window.fetch;
    window.manifestRequests = { active: 0, peak: 0, total: 0 };
    window.runtimeManifestRequests = [];
    window.fetch = function (...args) {
      const url = new URL(typeof args[0] === "string" ? args[0] : args[0].url, location.href);
      if (url.pathname.startsWith('/packages/runtime/') && url.pathname.endsWith('/config.json')) {
        window.runtimeManifestRequests.push(url.pathname);
        return originalFetch.apply(this, args);
      }
      if (!url.pathname.startsWith("/packages/") || !url.pathname.endsWith("/config.json")) {
        return originalFetch.apply(this, args);
      }
      const counters = window.manifestRequests;
      counters.total += 1;
      counters.active += 1;
      counters.peak = Math.max(counters.peak, counters.active);
      return originalFetch.apply(this, args).finally(() => { counters.active -= 1; });
    };
  });
  const failures = [];
  page.on("pageerror", (error) => failures.push(error.message));
  page.on("console", (message) => {
    if (message.type() === "error") failures.push(message.text());
  });

  await page.goto(baseUrl);
  await page.waitForFunction(() => {
    const text = document.querySelector("#status")?.textContent || "";
    return text && !text.startsWith("正在");
  }, null, { timeout: 90_000 });
  assert.ok(!(await page.locator("#status").textContent()).startsWith("加载失败"), failures.join("\n"));
  const requests = await page.evaluate(() => window.manifestRequests);
  assert.ok(requests.total >= 2 && requests.total <= 4,
    `Initial page requested ${requests.total} manifests instead of the catalog, parameter input and at most two selected model configs`);
  assert.ok(requests.peak <= 2, `Manifest request fan-out was ${requests.peak}`);
  assert.deepEqual(await page.evaluate(() => window.runtimeManifestRequests),
    ['hasunosora_runtime', 'garupa_runtime', 'llas_runtime'].map(name => `/packages/runtime/${name}/config.json`));
  const catalog = await (await fetch(`${baseUrl}/packages/config.json`)).json();
  const models = catalog.components.filter(component => component.type === 'model');
  const composed = models.some(head => head.role === 'head'
    && models.some(body => body.role === 'body' && body.group === head.group));
  const integrated = models.some(component => component.role === 'integrated');
  assert.ok(composed || integrated, 'Integration validation requires at least one loadable model');
  const mode = composed ? 'composed' : 'integrated';
  await page.selectOption('#package-mode', mode);
  for (let index = 1; index <= 5; index += 1) {
    if (composed) {
      await page.selectOption('#head', { index: index % await page.locator('#head option').count() });
      const bodies = await page.locator('#body option').count();
      assert.ok(bodies, 'Selected head has no matching body');
      await page.selectOption('#body', { index: (5 - index) % bodies });
    } else {
      await page.selectOption('#character', { index: index % await page.locator('#character option').count() });
    }
    await page.locator("#parameterized-rendering-toggle").click();
    // Capabilities can change while a model loads; check and dispatch atomically.
    // Static faces legitimately disable these controls.
    await page.evaluate(({ eye, mouth }) => {
      for (const [id, value] of [["eye-open", eye], ["mouth-open", mouth]]) {
        const input = document.getElementById(id);
        if (!input.disabled) {
          input.value = String(value);
          input.dispatchEvent(new Event("input", { bubbles: true }));
        }
      }
    }, { eye: index / 5, mouth: (5 - index) / 5 });
  }
  if (await page.locator('#motion option').count() > 1) await page.selectOption('#motion', { index: 1 });
  if (integrated) await page.selectOption('#package-mode', 'integrated');
  await page.selectOption('#package-mode', mode);

  const selectedName = async (selector) => {
    const key = await page.locator(selector).inputValue();
    const selected = models.find(component =>
      `${component.sourceConfig}#model:${component.name}:${component.role}` === key);
    assert.ok(selected, `Selected model ${key} is missing from the catalog`);
    return selected.name;
  };
  const expectedHead = await selectedName(composed ? '#head' : '#character');
  const expectedBody = composed ? await selectedName('#body') : '';
  await page.waitForFunction(({ head, body }) => {
    const text = document.querySelector("#status")?.textContent || "";
    return text.includes(head) && text.includes(body) && !text.startsWith("正在");
  }, { head: expectedHead, body: expectedBody }, { timeout: 90_000 });

  assert.deepEqual(failures, []);
});
