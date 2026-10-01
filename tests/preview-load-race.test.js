import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import fs from "node:fs";
import net from "node:net";
import path from "node:path";
import test from "node:test";

import { chromium } from "playwright";
import { createServer } from "vite";


function minimalGlb(nodeName) {
  const json = JSON.stringify({
    asset: { version: "2.0" },
    scene: 0,
    scenes: [{ nodes: [0] }],
    nodes: [{ name: nodeName }],
  });
  const padded = json.padEnd(Math.ceil(json.length / 4) * 4, " ");
  const jsonBytes = Buffer.from(padded, "utf8");
  const bytes = Buffer.alloc(20 + jsonBytes.length);
  bytes.write("glTF", 0, "ascii");
  bytes.writeUInt32LE(2, 4);
  bytes.writeUInt32LE(bytes.length, 8);
  bytes.writeUInt32LE(jsonBytes.length, 12);
  bytes.writeUInt32LE(0x4e4f534a, 16);
  jsonBytes.copy(bytes, 20);
  return bytes;
}

function humanoidGlb() {
  const json = JSON.stringify({
    asset: { version: "2.0" }, scene: 0,
    scenes: [{ nodes: [0] }],
    nodes: [
      { name: "Root", children: [1] },
      { name: "Hips", translation: [0, 1, 0] },
    ],
  });
  const padded = json.padEnd(Math.ceil(json.length / 4) * 4, " ");
  const jsonBytes = Buffer.from(padded, "utf8");
  const bytes = Buffer.alloc(20 + jsonBytes.length);
  bytes.write("glTF", 0, "ascii");
  bytes.writeUInt32LE(2, 4);
  bytes.writeUInt32LE(bytes.length, 8);
  bytes.writeUInt32LE(jsonBytes.length, 12);
  bytes.writeUInt32LE(0x4e4f534a, 16);
  jsonBytes.copy(bytes, 20);
  return bytes;
}


function integratedManifest(name) {
  return {
    components: [{
      type: "model",
      name,
      role: "integrated",
      model: "model.glb",
      humanoidScale: 1,
      morphPoses: [],
      expressionGroups: [],
      expressions: [],
    }],
  };
}


function emptyTrackMotion(canStop) {
  return {
    clips: [{ id: "idle", duration: 1, sampleRate: 1, frames: 2, tracks: [] }],
    auxiliaryClips: [], leftHandPoses: [], rightHandPoses: [],
    program: {
      parameters: canStop ? [{ id: "stop", type: "trigger", default: false }] : [],
      commands: canStop ? { stop: [{ parameter: "stop", value: true }] } : {},
      baseLayer: "Base Layer",
      layers: [{
        id: "Base Layer", blend: "override", weight: 1, initialState: "idle",
        states: [{ id: "idle", clip: "idle", speed: 1, loop: true, transitions: [] }],
      }],
      poseSlots: [],
    },
  };
}


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
  for (let attempt = 0; attempt < 100; attempt += 1) {
    if (child.exitCode !== null) throw new Error(`Vite exited with ${child.exitCode}`);
    try {
      const response = await fetch(url);
      if (response.ok) return;
    } catch {}
    await new Promise((resolve) => setTimeout(resolve, 50));
  }
  throw new Error(`Vite did not start at ${url}`);
}

test("preview defaults to model action and can show its separate idle pose", { timeout: 30_000 }, async (t) => {
  const port = await freePort();
  const vite = await createServer({
    logLevel: "silent",
    server: { host: "127.0.0.1", port, strictPort: true },
  });
  await vite.listen();
  t.after(() => vite.close());
  const browser = await chromium.launch({ headless: true });
  t.after(() => browser.close());
  const page = await browser.newPage();
  const failures = [];
  page.on("pageerror", (error) => failures.push(error.message));
  page.on("console", (message) => { if (message.type() === "error") failures.push(message.text()); });
  await page.route("**/src/main.js", async (route) => {
    const response = await route.fetch();
    const body = await response.text();
    await route.fulfill({ response, body: `${body}\nwindow.__defaultProbe = () => ({
      selected: motionSelect.value,
      action: character.motion?.motion?.program?.baseLayer ?? null,
      hipsY: character.root?.getObjectByName('Hips')?.position.y ?? null,
    });\n` });
  });
  await page.route("**/packages/**", (route) => {
    const pathname = new URL(route.request().url()).pathname;
    if (pathname === '/packages/parameter-input/config.json') return route.fulfill({ json: { components: [] } });
    if (pathname.startsWith('/packages/runtime/')) return route.fulfill({ json: { components: [
      { type: 'behavior', namespace: 'Fixture', name: pathname.split('/').at(-2), script: 'unused.js' },
    ] } });
    const pose = { tracks: [
      { bone: "Hips", rotation: [0, 0, 0, 1], translation: [0, 0.25, 0] },
    ] };
    if (pathname === "/packages/config.json") {
      return route.fulfill({ json: { components: [
        ...[
          { ...integratedManifest("ActionModel").components[0], defaultMotion: "IdleName" },
          { ...integratedManifest("FallbackModel").components[0], defaultMotion: "Missing" },
        ].map((component) => ({ ...component, sourceConfig: "fixture/models/config.json" })),
        ...['head', 'body'].map(role => ({ ...integratedManifest(role).components[0],
          role, group: 'Fixture', sourceConfig: 'fixture/parts/config.json' })),
        { type: "motion", name: "IdleName", src: "idle.json", sourceConfig: "fixture/motions/config.json" },
      ] } });
    }
    if (pathname === "/packages/fixture/models/config.json") {
      return route.fulfill({ json: { components: [
        { ...integratedManifest("ActionModel").components[0], defaultMotion: "IdleName", idlePose: pose },
        { ...integratedManifest("FallbackModel").components[0], defaultMotion: "Missing", idlePose: pose },
      ] } });
    }
    if (pathname === "/packages/fixture/models/model.glb") {
      return route.fulfill({ contentType: "model/gltf-binary", body: humanoidGlb() });
    }
    if (pathname === "/packages/fixture/motions/config.json") {
      return route.fulfill({ json: { components: [
        { type: "motion", name: "IdleName", src: "idle.json" },
      ] } });
    }
    if (pathname === "/packages/fixture/motions/idle.json") {
      const motion = emptyTrackMotion(false);
      motion.clips[0].tracks = [{
        bone: "Hips", rotation: [0, 0, 0, 1, 0, 0, 0, 1],
        translation: [0, 0.5, 0, 0, 0.5, 0],
      }];
      return route.fulfill({ json: motion });
    }
    return route.abort();
  });
  await page.goto(`http://127.0.0.1:${port}/`);
  await page.waitForFunction(() => window.__defaultProbe?.().action === "Base Layer");
  assert.equal(await page.locator('#package-mode').inputValue(), 'integrated');
  assert.equal((await page.evaluate(() => window.__defaultProbe())).selected, "__default__");
  assert.ok(Math.abs((await page.evaluate(() => window.__defaultProbe())).hipsY - 1.5) < 1e-5);
  await page.selectOption("#motion", "");
  await page.waitForFunction(() => window.__defaultProbe?.().action === null);
  assert.ok(Math.abs((await page.evaluate(() => window.__defaultProbe())).hipsY - 1.25) < 1e-5);
  await page.selectOption("#motion", "__default__");
  await page.waitForFunction(() => window.__defaultProbe?.().action === "Base Layer");
  await page.selectOption("#character", "fixture/models/config.json#model:FallbackModel:integrated");
  await page.waitForFunction(() => window.__defaultProbe?.().action === null
    && Math.abs(window.__defaultProbe().hipsY - 1.25) < 1e-5);
  assert.deepEqual(failures, []);
});


test("preview keeps the latest model selection when GLB loads finish out of order", { timeout: 20_000 }, async (t) => {
  const port = await freePort();
  const viteEntry = path.resolve("node_modules/vite/bin/vite.js");
  assert.equal(fs.existsSync(viteEntry), true, "Vite dependency is required");
  const server = spawn(process.execPath, [viteEntry, "--host", "127.0.0.1", "--port", String(port)], {
    cwd: process.cwd(),
    stdio: "ignore",
    windowsHide: true,
  });
  t.after(() => {
    if (server.exitCode === null) server.kill();
  });
  const baseUrl = `http://127.0.0.1:${port}`;
  await waitForServer(baseUrl, server);

  const browser = await chromium.launch({ headless: true });
  t.after(() => browser.close());
  const page = await browser.newPage();
  const failures = [];
  page.on("pageerror", (error) => failures.push(error.message));
  page.on("console", (message) => {
    if (message.type() === "error") failures.push(message.text());
  });

  let firstRequested;
  const firstRequest = new Promise((resolve) => { firstRequested = resolve; });
  let motionRequested;
  const motionRequest = new Promise((resolve) => { motionRequested = resolve; });
  await page.route("**/packages/**", async (route) => {
    const pathname = new URL(route.request().url()).pathname;
    if (pathname === '/packages/parameter-input/config.json') return route.fulfill({ json: { components: [] } });
    if (pathname.startsWith('/packages/runtime/')) return route.fulfill({ json: { components: [
      { type: 'behavior', namespace: 'Fixture', name: pathname.split('/').at(-2), script: 'unused.js' },
    ] } });
    if (pathname === "/packages/config.json") {
      return route.fulfill({ json: { components: [
        { ...integratedManifest("First").components[0], sourceConfig: "fixture/first/config.json" },
        { ...integratedManifest("Second").components[0], sourceConfig: "fixture/second/config.json" },
        { type: "motion", name: "DelayedMotion", src: "delayed.baked.json",
          motionGroup: "fixture", sourceConfig: "bangdream/motions/config.json" },
      ] } });
    }
    if (pathname === "/packages/bangdream/motions/config.json") {
      return route.fulfill({ json: { components: [{
        type: "motion",
        name: "DelayedMotion",
        src: "delayed.baked.json",
        motionGroup: "fixture",
      }] } });
    }
    if (pathname === "/packages/fixture/first/config.json") {
      return route.fulfill({ json: integratedManifest("First") });
    }
    if (pathname === "/packages/fixture/second/config.json") {
      return route.fulfill({ json: integratedManifest("Second") });
    }
    if (pathname === "/packages/fixture/first/model.glb") {
      firstRequested();
      await new Promise((resolve) => setTimeout(resolve, 800));
      return route.fulfill({ contentType: "model/gltf-binary", body: minimalGlb("FirstRoot") });
    }
    if (pathname === "/packages/fixture/second/model.glb") {
      return route.fulfill({ contentType: "model/gltf-binary", body: minimalGlb("SecondRoot") });
    }
    if (pathname === "/packages/bangdream/motions/delayed.baked.json") {
      motionRequested();
      await new Promise((resolve) => setTimeout(resolve, 500));
      return route.fulfill({ json: {
        clips: [], auxiliaryClips: [], leftHandPoses: [], rightHandPoses: [],
        program: { parameters: [], commands: {}, baseLayer: "Base Layer", layers: [] },
      } });
    }
    return route.abort();
  });

  await page.goto(baseUrl);
  await firstRequest;
  await page.locator("#parameterized-rendering-toggle").click();
  await page.selectOption("#character", "fixture/second/config.json#model:Second:integrated");
  await page.waitForFunction(() => document.querySelector("#status")?.textContent === "Second");
  await page.waitForTimeout(1_000);

  assert.equal(await page.locator("#status").textContent(), "Second");
  assert.deepEqual(failures, []);

  await page.selectOption("#motion", "bangdream/motions/config.json#motion:fixture:DelayedMotion");
  await motionRequest;
  await page.selectOption("#package-mode", "composed");
  await page.waitForFunction(() => document.querySelector("#status")?.textContent === "当前输出目录没有 head 组件");
  await page.waitForTimeout(700);

  assert.equal(await page.locator("#status").textContent(), "当前输出目录没有 head 组件");
  assert.deepEqual(failures, []);
});


test("first load of another motion keeps the current pose until its payload is ready", { timeout: 30_000 }, async (t) => {
  const port = await freePort();
  const vite = await createServer({
    logLevel: "silent",
    server: { host: "127.0.0.1", port, strictPort: true },
  });
  await vite.listen();
  t.after(() => vite.close());
  const baseUrl = `http://127.0.0.1:${port}`;

  const browser = await chromium.launch({ headless: true });
  t.after(() => browser.close());
  const page = await browser.newPage();
  const failures = [];
  page.on("pageerror", (error) => failures.push(error.message));
  let secondRequested;
  const secondRequest = new Promise((resolve) => { secondRequested = resolve; });
  let releaseSecond;
  const secondReady = new Promise((resolve) => { releaseSecond = resolve; });
  t.after(() => releaseSecond());
  await page.route("**/packages/**", async (route) => {
    const pathname = new URL(route.request().url()).pathname;
    if (pathname === '/packages/parameter-input/config.json') return route.fulfill({ json: { components: [] } });
    if (pathname.startsWith('/packages/runtime/')) return route.fulfill({ json: { components: [
      { type: 'behavior', namespace: 'Fixture', name: pathname.split('/').at(-2), script: 'unused.js' },
    ] } });
    if (pathname === "/packages/config.json") {
      return route.fulfill({ json: { components: [
        { ...integratedManifest("Model").components[0], sourceConfig: "fixture/model/config.json" },
        { type: "motion", name: "First", src: "first.json", motionGroup: "fixture",
          sourceConfig: "fixture/motions/config.json" },
        { type: "motion", name: "Second", src: "second.json", motionGroup: "fixture",
          sourceConfig: "fixture/motions/config.json" },
      ] } });
    }
    if (pathname === "/packages/fixture/model/config.json") {
      return route.fulfill({ json: integratedManifest("Model") });
    }
    if (pathname === "/packages/fixture/model/model.glb") {
      return route.fulfill({ contentType: "model/gltf-binary", body: minimalGlb("ModelRoot") });
    }
    if (pathname === "/packages/fixture/motions/config.json") {
      return route.fulfill({ json: { components: [
        { type: "motion", name: "First", src: "first.json", motionGroup: "fixture" },
        { type: "motion", name: "Second", src: "second.json", motionGroup: "fixture" },
      ] } });
    }
    if (pathname === "/packages/fixture/motions/first.json") {
      return route.fulfill({ json: emptyTrackMotion(true) });
    }
    if (pathname === "/packages/fixture/motions/second.json") {
      secondRequested();
      await secondReady;
      return route.fulfill({ json: emptyTrackMotion(false) });
    }
    return route.abort();
  });

  await page.goto(baseUrl);
  await page.waitForFunction(() => document.querySelector("#status")?.textContent === "Model", null, { timeout: 15_000 });
  await page.selectOption("#motion", "fixture/motions/config.json#motion:fixture:First");
  await page.waitForFunction(() => !document.querySelector("#stop-motion").disabled);

  await page.selectOption("#motion", "fixture/motions/config.json#motion:fixture:Second");
  await secondRequest;
  await page.evaluate(() => new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve))));
  assert.equal(await page.locator("#stop-motion").isEnabled(), true,
    "the current motion should remain active while the next payload is pending");
  releaseSecond();
  await page.waitForFunction(() => document.querySelector("#motion-note")?.textContent?.includes("Second"));
  assert.equal(await page.locator("#stop-motion").isEnabled(), false);
  assert.deepEqual(failures, []);
});
