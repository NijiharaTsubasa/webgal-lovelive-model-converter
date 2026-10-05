import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { CharacterRenderer } from "webgal-lovelive-gltf-renderer/character-renderer.js";
import { expandModelManifest } from "webgal-lovelive-gltf-renderer/model-manifest.js";
import { previewNativeMotion } from './preview-native-motion.js';
import { normalizeFrameDelta } from "webgal-lovelive-gltf-renderer/frame-time.js";
import { expandParameterManifest, ExpressionAdapterRegistry, parameterResourceUrl } from 'webgal-lovelive-gltf-renderer/garupa/manifest.js';
import { loadPreviewParameterRuntime } from './preview-parameter-runtime.js';
import { onSelectIncludingRepeat } from './replayable-select.js';
import "./style.css";

const packagesRoot = "/packages/";
const viewport = document.querySelector("#viewport");
const packageModeSelect = document.querySelector("#package-mode");
const characterSelect = document.querySelector("#character");
const headSelect = document.querySelector("#head");
const bodySelect = document.querySelector("#body");
const headRow = document.querySelector("#head-row");
const bodyRow = document.querySelector("#body-row");
const characterRow = document.querySelector("#character-row");
const eyeOpenInput = document.querySelector("#eye-open");
const eyeOpenValue = document.querySelector("#eye-open-value");
const mouthOpenInput = document.querySelector("#mouth-open");
const mouthOpenValue = document.querySelector("#mouth-open-value");
const motionSelect = document.querySelector("#motion");
const stopMotionButton = document.querySelector("#stop-motion");
const shaderToggle = document.querySelector("#parameterized-rendering-toggle");
const physicsToggle = document.querySelector("#physics-toggle");
const meshClothToggle = document.querySelector("#mesh-cloth-toggle");
const status = document.querySelector("#status");
const motionNote = document.querySelector("#motion-note");
const faceSource = document.querySelector('#face-source');
const parameterExpression = document.querySelector('#parameter-expression');
const parameterSpeech = document.querySelector('#parameter-speech');
const motionSource = document.querySelector('#motion-source');
let parameterEntries = [], standardMotions = [], adapters;
let faceRequest = 0, motionRequest = 0;

// This scene is the preview stage. The character runtime does not own its UI,
// camera controls, lighting or package catalog.
const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, stencil: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.setSize(viewport.clientWidth, viewport.clientHeight);
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.shadowMap.enabled = true;
viewport.append(renderer.domElement);
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x11151b);
scene.fog = new THREE.Fog(0x11151b, 7, 15);
const camera = new THREE.PerspectiveCamera(35, viewport.clientWidth / viewport.clientHeight, 0.01, 100);
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.target.set(0, 1, 0);
scene.add(new THREE.AmbientLight(new THREE.Color(0.02, 0.025, 0.03), 1.0));
const keyLight = new THREE.DirectionalLight(0xffffff, 1.0);
keyLight.position.set(3, 5, 4);
keyLight.castShadow = true;
scene.add(keyLight);
const floor = new THREE.Mesh(
  new THREE.CircleGeometry(3.8, 96),
  new THREE.MeshStandardMaterial({ color: 0x252a31, roughness: 0.88, metalness: 0.08 }),
);
floor.rotation.x = -Math.PI / 2;
floor.receiveShadow = true;
scene.add(floor);

const character = new CharacterRenderer({ renderer, scene, camera,
  fetchResource: globalThis.fetch.bind(globalThis), meshClothEnabled: meshClothToggle.checked });
const timer = new THREE.Timer();
timer.connect(document);
let allComponents = [];
const fullModelManifests = new Map();
let modelSelectionRequest = 0;
let selectedModelEntries = [];

async function resolveModelEntry(entry) {
  let promise = fullModelManifests.get(entry.configPath);
  if (!promise) {
    promise = fetchJson(`${packagesRoot}${entry.configPath}`)
      .then((config) => expandModelManifest(config, entry.configPath));
    fullModelManifests.set(entry.configPath, promise);
    promise.catch(() => fullModelManifests.delete(entry.configPath));
  }
  const models = await promise;
  const full = models.find((item) => item.key === entry.key);
  if (!full) throw new Error(`${entry.configPath}: 找不到模型 ${entry.name}/${entry.component.role}`);
  return full;
}
let componentByKey = new Map();
let motions = [];

async function fetchJson(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`${response.status} ${url}`);
  return response.json();
}

function fillSelect(select, items, map) {
  for (const item of items) {
    const option = document.createElement("option");
    const [value, label] = map(item);
    option.value = value;
    option.textContent = label;
    select.append(option);
  }
}

function resourceOptionLabel(item) {
  const description = item.description ?? item.component?.description;
  return description?.trim() ? `${item.name} — ${description}` : item.name;
}

function resetCamera() {
  if (!character.root) return;
  const box = new THREE.Box3().setFromObject(character.root);
  const size = box.getSize(new THREE.Vector3());
  const center = box.getCenter(new THREE.Vector3());
  const radius = Math.max(size.x, size.y, size.z, 1) * 0.62;
  controls.target.copy(center).add(new THREE.Vector3(0, size.y * 0.05, 0));
  camera.position.copy(center).add(new THREE.Vector3(0, size.y * 0.08, radius * 3.2));
  camera.near = Math.max(radius / 100, 0.01);
  camera.far = radius * 30;
  camera.updateProjectionMatrix();
  controls.update();
}

function syncExpressionControls() {
  const external = faceSource.value === 'garupa' && character.parameterFaceActive;
  const parameterMode = faceSource.value === 'garupa';
  document.querySelector('#parameter-expression-row').hidden = !parameterMode;
  document.querySelector('#parameter-speech-row').hidden = !parameterMode;
  document.querySelector('#parameter-face-note').hidden = !parameterMode;
  document.querySelector('#native-expression-row').hidden = external;
  eyeOpenInput.value = String(1 - (external ? character.parameterPlayer?.blink ?? 0 : character.face?.blink ?? 0));
  mouthOpenInput.value = String(external ? character.parameterPlayer?.speech ?? Number(mouthOpenInput.value) : character.face?.speech ?? 0);
  eyeOpenValue.value = Number(eyeOpenInput.value).toFixed(2);
  mouthOpenValue.value = Number(mouthOpenInput.value).toFixed(2);
  const capabilities = character.faceCapabilities;
  eyeOpenInput.disabled = external ? false : !capabilities?.blink;
  mouthOpenInput.disabled = external ? !parameterSpeech.checked : !capabilities?.speech;
  const groups = document.querySelector("#expression-groups");
  groups.hidden = external;
  groups.replaceChildren();
  const definitions = character.faceDefinition?.expressionGroups ?? [];
  const selection = { ...capabilities?.selections };
  for (const [key, type, title] of [["eye", "eye", "3D眼型"], ["closed", "mouth", "3D闭口"], ["open", "mouth", "3D张口"]]) {
    const group = definitions.find(group => group.type === type);
    if (!group) continue;
    const label = document.createElement("label");
    label.textContent = title;
    const select = document.createElement("select");
    for (const state of group.states) select.add(new Option(state.name, state.name));
    select.value = selection[key];
    onSelectIncludingRepeat(select, (value) => {
      selection[key] = value;
      if (key === "open" || !definitions.some(group => group.type === "mouth")) {
        character.setExpression(selection);
        syncExpressionControls();
      }
    });
    label.append(select);
    groups.append(label);
  }
}

function showLoadedModel(entries, result, preserveView = false) {
  if (!result) return;
  syncExpressionControls();
  document.querySelector("#mesh-count").textContent = result.meshes;
  document.querySelector("#expression-count").textContent = result.faceDefinition.expressionGroups.reduce((sum, group) => sum + group.states.length, 0);
  document.querySelector("#bone-count").textContent = result.bones;
  if (!preserveView) resetCamera();
  const behaviorNote = result.behaviorDiagnostics ? ` · Behavior 降级 ${result.behaviorDiagnostics}` : "";
  if (entries.length === 1) {
    status.textContent = `${entries[0].name}${behaviorNote}`;
  } else {
    const composition = result.composition;
    const fallback = composition.fallbackBones.length
      ? ` · ${composition.fallbackBones.length} 个缺省骨映射到祖先骨` : "";
    status.textContent = `${entries[0].name} + ${entries[1].name} · 单骨架 ${composition.bodyCoreBones} 骨${behaviorNote}${fallback}`;
  }
}

async function loadEntries(entries, { preserveView = false } = {}) {
  selectedModelEntries = entries;
  const request = ++modelSelectionRequest;
  status.textContent = `正在加载 ${entries.map((entry) => entry.name).join(" + ")}`;
  stopMotionButton.disabled = true;
  const resolved = await Promise.all(entries.map(resolveModelEntry));
  if (request !== modelSelectionRequest) return;
  character.meshClothEnabled = meshClothToggle.checked;
  const result = await character.load(resolved, packagesRoot);
  if (!result) return;
  showLoadedModel(entries, result, preserveView);
  await applyFaceSource();
  if (character.root !== result.root) return;
  await describeMotion(motionSelect.value);
}

async function prepareParameters() {
  const runtime = await loadPreviewParameterRuntime();
  character.configureParameterPlayback({ runtime, adapters });
}

async function applyFaceSource() {
  const request = ++faceRequest, root = character.root;
  if (faceSource.value !== 'garupa') {
    await character.setParameterFace(false);
    syncExpressionControls();
    return;
  }
  await prepareParameters();
  if (request !== faceRequest || root !== character.root) return;
  const active = await character.setParameterFace(true);
  if (request !== faceRequest || root !== character.root) return;
  document.querySelector('#parameter-face-note').textContent = active
    ? '直接使用源参数。动作更新时不叠加自动眨眼；说话接管可独立启用。'
    : '该模型未提供可用参数表情适配器，保留原生表情；参数身体动作仍可播放。';
  const entry = parameterEntries.find(item => item.key === parameterExpression.value);
  await character.selectParameterExpression(entry, entry ? parameterResourceUrl(entry, packagesRoot) : undefined);
  if (request !== faceRequest || root !== character.root) return;
  character.setParameterBlink(1 - Number(eyeOpenInput.value));
  character.setParameterSpeech(parameterSpeech.checked ? Number(mouthOpenInput.value) : null);
  syncExpressionControls();
}

function fillMotions() {
  const parameterMode = motionSource.value === 'garupa';
  motions = parameterMode ? parameterEntries.filter(item => item.type === 'garupa-motion') : standardMotions;
  motionSelect.replaceChildren(...(parameterMode
    ? [new Option('静止姿态', '')]
    : [new Option('模型默认', '__default__'), new Option('静止姿态', '')]));
  fillSelect(motionSelect, motions, item => [item.key, resourceOptionLabel(item)]);
}

async function loadCharacter(key) {
  const entry = componentByKey.get(key);
  if (!entry || entry.component.role !== "integrated") throw new Error("一体化模型条目无效");
  await loadEntries([entry]);
}

async function loadComposition(headKey, bodyKey) {
  const head = componentByKey.get(headKey);
  const body = componentByKey.get(bodyKey);
  if (head?.component.role !== "head" || body?.component.role !== "body") {
    throw new Error("组合资源类型无效：必须由 head 和 body 组成");
  }
  await loadEntries([head, body]);
}

async function describeMotion(key) {
  const request = ++motionRequest;
  const defaultEntry = key === "__default__" && character.config?.defaultMotion
    ? motions.find((item) => item.name === character.config.defaultMotion) : undefined;
  const resolvedKey = key === "__default__" ? defaultEntry?.key : key;
  if (!resolvedKey) {
    await character.selectMotion(null);
    motionNote.textContent = "当前为模型静止姿态，可独立切换面部表情。";
    return;
  }
  if (!character.root) {
    motionNote.textContent = "模型加载完成后将播放所选动作。";
    return;
  }
  const entry = motions.find((item) => item.key === resolvedKey);
  if (!entry) throw new Error(`动作索引不存在: ${resolvedKey}`);
  if (entry.type === 'garupa-motion') {
    const root = character.root;
    await prepareParameters();
    if (request !== motionRequest || root !== character.root) return;
    await character.selectParameterMotion(entry, parameterResourceUrl(entry, packagesRoot));
    return;
  }
  const path = `${entry.basePath ? `${entry.basePath}/` : ""}${entry.src}`;
  await character.selectMotion(entry, `${packagesRoot}${path}`);
}

function fillCompatibleBodies(head) {
  const bodies = allComponents.filter((entry) => entry.component.role === "body" && entry.group === head.group);
  bodySelect.replaceChildren();
  fillSelect(bodySelect, bodies, (item) => [item.key, resourceOptionLabel(item)]);
  return bodies;
}

async function applyPackageMode() {
  character.clear();
  stopMotionButton.disabled = true;
  const composed = packageModeSelect.value === "composed";
  characterRow.hidden = composed;
  headRow.hidden = !composed;
  bodyRow.hidden = !composed;
  characterSelect.replaceChildren();
  headSelect.replaceChildren();
  bodySelect.replaceChildren();
  if (composed) {
    const heads = allComponents.filter((entry) => entry.component.role === "head");
    fillSelect(headSelect, heads, (item) => [item.key, resourceOptionLabel(item)]);
    if (heads.length) {
      const bodies = fillCompatibleBodies(heads[0]);
      if (bodies.length) await loadComposition(heads[0].key, bodies[0].key);
      else status.textContent = `没有与 ${heads[0].name} 同组的 body`;
    } else status.textContent = "当前输出目录没有 head 组件";
  } else {
    const integrated = allComponents.filter((entry) => entry.component.role === "integrated");
    fillSelect(characterSelect, integrated, (item) => [item.key, resourceOptionLabel(item)]);
    if (integrated.length) await loadCharacter(integrated[0].key);
    else status.textContent = "当前输出目录没有一体化角色包";
  }
}

async function boot() {
  const catalog = await fetchJson(`${packagesRoot}config.json`);
  if (!Array.isArray(catalog.components)) throw new Error("预览汇总 config.json 缺少 components");
  const bySource = new Map();
  const nativeMotions = catalog.components.filter(component => component.type === 'motion');
  for (const { sourceConfig, ...component } of catalog.components.filter(component => !['motion', 'garupa-motion', 'garupa-expression'].includes(component.type))) {
    if (typeof sourceConfig !== "string" || !sourceConfig.endsWith("/config.json")) {
      throw new Error("预览组件缺少 sourceConfig");
    }
    if (!bySource.has(sourceConfig)) bySource.set(sourceConfig, []);
    bySource.get(sourceConfig).push(component);
  }
  const manifests = [...bySource].map(([configPath, components]) => ({
    configPath, config: { components },
  }));
  const inputResponse = await fetch(`${packagesRoot}parameter-input/config.json`);
  const parameterInput = await inputResponse.json();
  if (!inputResponse.ok) throw new Error(parameterInput.error ?? '无法读取参数动作和表情输入');
  if (parameterInput.components.length) {
    manifests.push({ configPath: 'parameter-input/config.json', config: parameterInput });
  }
  for (const name of ['hasunosora_runtime', 'garupa_runtime', 'llas_runtime']) {
    const configPath = `runtime/${name}/config.json`;
    manifests.push({ configPath, config: await fetchJson(`${packagesRoot}${configPath}`) });
  }
  for (const { config, configPath } of manifests) {
    if (config.components.some(component => ['shader', 'behavior'].includes(component.type))) {
      character.resourcePackages.register(config, `${packagesRoot}${configPath}`);
    }
  }
  allComponents = manifests.flatMap(({ config, configPath }) => config.components
    .filter((component) => component.type === "model")
    .map((component) => ({
      key: `${configPath}#model:${component.name}:${component.role}`,
      name: component.name,
      description: component.description,
      group: component.group,
      motionGroup: component.motionGroup,
      basePath: configPath.slice(0, configPath.lastIndexOf("/")),
      configPath,
      component,
    })));
  componentByKey = new Map(allComponents.map((entry) => [entry.key, entry]));
  standardMotions = nativeMotions.map(previewNativeMotion);
  parameterEntries = manifests.flatMap(({ config, configPath }) => expandParameterManifest(config, configPath));
  adapters = new ExpressionAdapterRegistry(parameterEntries, packagesRoot);
  fillSelect(parameterExpression, parameterEntries.filter(item => item.type === 'garupa-expression'), item => [item.key, resourceOptionLabel(item)]);
  fillMotions();
  const hasIntegrated = allComponents.some((entry) => entry.component.role === "integrated");
  const hasComposed = allComponents.some((entry) => entry.component.role === "head" || entry.component.role === "body");
  packageModeSelect.value = hasIntegrated || !hasComposed ? "integrated" : "composed";
  await applyPackageMode();
}

function showError(error) {
  console.error(error);
  status.textContent = `加载失败: ${error.message}`;
}

characterSelect.addEventListener("change", () => loadCharacter(characterSelect.value).catch(showError));
headSelect.addEventListener("change", () => {
  const head = componentByKey.get(headSelect.value);
  const bodies = head ? fillCompatibleBodies(head) : [];
  if (bodies.length) loadComposition(head.key, bodies[0].key).catch(showError);
  else { character.clear(); status.textContent = `没有与 ${head?.name || "所选 head"} 同组的 body`; }
});
bodySelect.addEventListener("change", () => loadComposition(headSelect.value, bodySelect.value).catch(showError));
packageModeSelect.addEventListener("change", () => applyPackageMode().catch(showError));
eyeOpenInput.addEventListener("input", () => {
  const value = Number(eyeOpenInput.value);
  eyeOpenValue.value = value.toFixed(2);
  if (character.parameterFaceActive) character.setParameterBlink(1 - value);
  else character.setBlink(1 - value);
});
mouthOpenInput.addEventListener("input", () => {
  const value = Number(mouthOpenInput.value);
  mouthOpenValue.value = value.toFixed(2);
  if (character.parameterFaceActive) character.setParameterSpeech(parameterSpeech.checked ? value : null);
  else character.setSpeech(value);
});
faceSource.addEventListener('change', () => applyFaceSource().catch(showError));
parameterExpression.addEventListener('change', () => applyFaceSource().catch(showError));
parameterSpeech.addEventListener('change', () => {
  if (character.parameterFaceActive) character.setParameterSpeech(parameterSpeech.checked ? Number(mouthOpenInput.value) : null);
  mouthOpenInput.disabled = character.parameterFaceActive ? !parameterSpeech.checked : !character.faceCapabilities?.speech;
});
motionSource.addEventListener('change', () => { fillMotions(); describeMotion(motionSelect.value).catch(showError); });
onSelectIncludingRepeat(motionSelect, (key) => describeMotion(key).catch(showError));
stopMotionButton.addEventListener("click", () => {
  if (character.stopMotion()) {
    stopMotionButton.disabled = true;
    motionNote.textContent = "正在播放动作退出段。";
  }
});
shaderToggle.addEventListener("change", () => character.setShadersEnabled(shaderToggle.checked));
physicsToggle.addEventListener("change", () => character.setPhysicsEnabled(physicsToggle.checked));
meshClothToggle.addEventListener("change", () => {
  character.meshClothEnabled = meshClothToggle.checked;
  if (selectedModelEntries.length) loadEntries(selectedModelEntries, { preserveView: true }).catch(showError);
});
document.querySelector("#reset").addEventListener("click", resetCamera);
new ResizeObserver(() => {
  const width = viewport.clientWidth;
  const height = viewport.clientHeight;
  if (!width || !height) return;
  renderer.setSize(width, height);
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
}).observe(viewport);

renderer.setAnimationLoop((timestamp) => {
  timer.update(timestamp);
  const delta = normalizeFrameDelta(timer.getDelta());
  try {
    const changed = character.update(delta);
    if (changed) {
      stopMotionButton.disabled = !changed.canStop;
      const groupNote = changed.groupTracks
        ? `，专属轨道 ${changed.resolvedGroupTracks}/${changed.groupTracks}` : "";
      motionNote.textContent = changed.playing
        ? `正在播放 ${changed.name}${groupNote}${changed.parameterMotion ? '，MTN 播放一次后保留末态。' : '，状态和循环方式来自动作程序。'}`
        : "当前为模型静止姿态，可独立切换面部表情。";
    }
    controls.update();
    character.render();
  } catch (error) {
    showError(error);
    character.clear();
  }
});

boot().catch(showError);
