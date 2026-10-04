// Offline cross-package/reference audit; game validators cover detailed geometry,
// and browser tests cover script execution and private Behavior parameters.
import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { validateResourceManifest } from "webgal-lovelive-gltf-renderer/resource-manifest.js";
import { validateModelManifest } from "webgal-lovelive-gltf-renderer/model-manifest.js";
import { expandParameterManifest } from "webgal-lovelive-gltf-renderer/garupa/manifest.js";
import { validateBehaviorPackage } from "webgal-lovelive-gltf-renderer/model-behaviors.js";
import { validatePhysics } from "webgal-lovelive-gltf-renderer/model-physics.js";
import { HUMANOID_BONE_NAMES } from "webgal-lovelive-gltf-renderer/skeleton-composer.js";
import { validateShaderPasses, resolveMaterialPasses } from "webgal-lovelive-gltf-renderer/shader-passes.js";
import { validateSamplerDescriptors } from "webgal-lovelive-gltf-renderer/sampler-bindings.js";
import { buildMorphNodeIndex, validateTargetMap } from "./glb-reference-validation.mjs";
import { motionFiles, readMotionFile, validateData, validateMotionResource } from "./validate-all-motions.mjs";

const require = (condition, message) => { if (!condition) throw new Error(message); };
const json = async (file) => JSON.parse(await fs.readFile(file, "utf8"));
const portable = (file) => file.replaceAll("\\", "/");

function packageFile(directory, relative) {
  require(typeof relative === "string" && relative.trim(), "缺少包内相对路径");
  const normalized = portable(relative);
  require(!normalized.startsWith("/") && !/^[A-Za-z][A-Za-z0-9+.-]*:/.test(normalized)
    && !normalized.split("/").includes(".."), `非法包内路径 ${relative}`);
  const result = path.resolve(directory, normalized);
  require(path.relative(directory, result) !== "", `文件路径不能指向包目录 ${relative}`);
  return result;
}

async function existingFile(directory, relative) {
  const file = packageFile(directory, relative);
  require((await fs.stat(file)).isFile(), `不是文件 ${file}`);
  return file;
}

async function configFiles(directory) {
  const result = [];
  for (const entry of await fs.readdir(directory, { withFileTypes: true })) {
    const file = path.join(directory, entry.name);
    if (entry.isDirectory()) result.push(...await configFiles(file));
    else if (entry.isFile() && entry.name === "config.json") result.push(file);
  }
  return result;
}

async function readGlb(file) {
  const bytes = await fs.readFile(file);
  require(bytes.length >= 20 && bytes.toString("ascii", 0, 4) === "glTF"
    && bytes.readUInt32LE(4) === 2 && bytes.readUInt32LE(8) === bytes.length, "无效 GLB 头");
  let document, binary;
  for (let offset = 12; offset < bytes.length;) {
    require(offset + 8 <= bytes.length, "GLB chunk 头截断");
    const length = bytes.readUInt32LE(offset), type = bytes.readUInt32LE(offset + 4);
    const start = offset + 8, end = start + length;
    require(end <= bytes.length, "GLB chunk 截断");
    if (type === 0x4e4f534a) document = JSON.parse(bytes.toString("utf8", start, end));
    if (type === 0x004e4942) binary = bytes.subarray(start, end);
    offset = end;
  }
  require(document, "GLB 缺少 JSON");
  const buffers = await Promise.all((document.buffers || []).map(async (buffer, index) => {
    if (buffer.uri === undefined) { require(index === 0 && binary, "GLB 缺少 BIN"); return binary; }
    if (buffer.uri.startsWith("data:")) {
      const match = /^data:[^,]*;base64,(.*)$/s.exec(buffer.uri);
      require(match, "无效 buffer data URI");
      return Buffer.from(match[1], "base64");
    }
    return fs.readFile(await existingFile(path.dirname(file), buffer.uri));
  }));
  for (const image of document.images || []) {
    if (image.uri && !image.uri.startsWith("data:")) await existingFile(path.dirname(file), image.uri);
  }
  return { document, buffers };
}

// Only the scalar triangle index accessor needs binary data here. Support sparse
// accessors too, so the audit does not impose a converter-specific layout.
function indexValues(document, buffers, index) {
  const accessor = document.accessors?.[index];
  require(accessor?.type === "SCALAR", `索引 accessor ${index} 不是 SCALAR`);
  const read = (viewIndex, offset, componentType, count) => {
    const view = document.bufferViews?.[viewIndex], bytes = buffers[view?.buffer];
    const sizes = { 5121: 1, 5123: 2, 5125: 4 }, size = sizes[componentType];
    require(view && bytes && size, `无效索引 bufferView ${viewIndex}`);
    return Array.from({ length: count }, (_, i) => {
      const local = (offset || 0) + i * (view.byteStride || size);
      require(local + size <= view.byteLength, "索引超出 bufferView");
      return bytes.readUIntLE((view.byteOffset || 0) + local, size);
    });
  };
  const result = accessor.bufferView === undefined ? Array(accessor.count).fill(0)
    : read(accessor.bufferView, accessor.byteOffset, accessor.componentType, accessor.count);
  if (accessor.sparse) {
    const { indices, values, count } = accessor.sparse;
    const slots = read(indices.bufferView, indices.byteOffset, indices.componentType, count);
    const replacements = read(values.bufferView, values.byteOffset, accessor.componentType, count);
    slots.forEach((slot, i) => { require(slot < result.length, "稀疏索引越界"); result[slot] = replacements[i]; });
  }
  return result;
}

export function validatePhysicsReferences(document, buffers, physics) {
  if (physics === undefined) return;
  validatePhysics(physics);
  const node = (index) => {
    require(Number.isSafeInteger(index) && index >= 0 && document.nodes?.[index], `physics node ${index} 不存在`);
    return document.nodes[index];
  };
  for (const collider of physics.colliders) {
    node(collider.node);
    if (collider.tail) node(collider.tail.node);
  }
  for (const spring of physics.springs) {
    require(!HUMANOID_BONE_NAMES.has(node(spring.node).name), `摆动骨不能控制核心骨 ${spring.node}`);
  }
  for (const cloth of physics.cloths || []) {
    const meshNode = node(cloth.node), skin = document.skins?.[meshNode.skin];
    const primitive = document.meshes?.[meshNode.mesh]?.primitives?.[cloth.primitive];
    require(primitive && (primitive.mode ?? 4) === 4, `cloth primitive ${cloth.node}/${cloth.primitive} 不是三角形网格`);
    require(skin && primitive.attributes?.JOINTS_0 !== undefined && primitive.attributes?.WEIGHTS_0 !== undefined,
      `cloth ${cloth.node}/${cloth.primitive} 缺少蒙皮`);
    for (const joint of skin.joints) node(joint);
    const position = document.accessors?.[primitive.attributes.POSITION];
    require(position?.type === "VEC3", "cloth 缺少 POSITION");
    const indices = primitive.indices === undefined ? Array.from({ length: position.count }, (_, i) => i)
      : indexValues(document, buffers, primitive.indices);
    require(indices.length > 0 && indices.length % 3 === 0, "cloth 需要三角形拓扑");
    require(indices.every((i) => i >= 0 && i < position.count), "cloth 三角形顶点越界");
    const used = new Set(indices);
    for (const fixed of cloth.fixed) {
      require(fixed < position.count, `cloth fixed ${fixed} 超出 POSITION`);
      require(used.has(fixed), `cloth fixed ${fixed} 未被 primitive 使用`);
    }
  }
}

export function validateMaterialReferences(document, shaders) {
  for (const [index, material] of (document.materials || []).entries()) {
    const extras = material.extras;
    if (extras?.shader === undefined) continue; // Standard PBR remains valid.
    const shader = shaders.get(extras.shader);
    require(shader, `material ${index}: 缺少 Shader ${extras.shader}`);
    for (const pass of resolveMaterialPasses(shader, extras, `material ${index}`)) {
      for (const sampler of shader.samplers) {
        const value = pass.textures[sampler.name];
        if (value === undefined) {
          require(sampler.missing.behavior !== "error", `material ${index}/${pass.id}: 缺少 sampler ${sampler.name}`);
          continue;
        }
        const indices = sampler.type === "sampler2DArray" ? value : [value];
        require(Array.isArray(indices) && indices.length > 0, `sampler ${sampler.name}: 需要非空纹理数组`);
        for (const textureIndex of indices) {
          const texture = document.textures?.[textureIndex];
          require(Number.isSafeInteger(textureIndex) && textureIndex >= 0 && texture, `sampler ${sampler.name}: texture ${textureIndex} 不存在`);
          require(["srgb", "linear"].includes(texture.extras?.colorSpace), `texture ${textureIndex}: 缺少有效 colorSpace`);
        }
      }
    }
  }
}

export async function auditResourcePackages(output, options = {}) {
  const root = path.resolve(output), errors = [], warnings = [];
  const counts = { configs: 0, model: 0, motion: 0, shader: 0, behavior: 0,
    "garupa-motion": 0, "garupa-expression": 0, "garupa-expression-adapter": 0, cloths: 0, springs: 0 };
  const check = async (label, action) => {
    try { await action(); } catch (error) { errors.push({ source: label, message: error.message }); }
  };
  const indexFile = path.join(root, "index.json");
  const hasIndex = await fs.stat(indexFile).then(() => true, error => {
    if (error.code === "ENOENT") return false;
    throw error;
  });
  const indexed = new Set();
  if (hasIndex) await check(indexFile, async () => {
    const index = await json(indexFile);
    require(Array.isArray(index.configs), "index.json 缺少 configs 数组");
    for (const entry of index.configs) {
      const resolved = packageFile(root, entry);
      require(!indexed.has(resolved), `重复 config ${entry}`); indexed.add(resolved);
    }
  });
  const disk = new Set(await configFiles(root));
  // The root config next to index.json is the preview's merged catalogue, not
  // another package: its relative paths belong to the original package configs.
  if (hasIndex) disk.delete(path.join(root, "config.json"));
  if (hasIndex) {
    for (const file of indexed) if (!disk.has(file)) errors.push({ source: file, message: "索引指向不存在的 config" });
    for (const file of disk) if (!indexed.has(file)) errors.push({ source: file, message: "磁盘 config 未被索引收录" });
  }
  let runtime = options.runtime;
  if (runtime === undefined) {
    runtime = process.env.GAME_RUNTIME_DIR;
    if (!runtime) {
      const candidate = path.resolve("../webgal-lovelive-game-runtime/packages");
      if (await fs.stat(candidate).then(stat => stat.isDirectory(), () => false)) runtime = candidate;
    }
  }
  const files = new Set(disk);
  if (runtime) await check(String(runtime), async () => {
    for (const file of await configFiles(path.resolve(runtime))) files.add(file);
  });
  const packages = [], shaders = new Map(), behaviors = new Set();
  for (const file of files) await check(file, async () => {
    const config = validateResourceManifest(await json(file), file);
    validateModelManifest(config, file); validateBehaviorPackage(config, file);
    expandParameterManifest(config, portable(file));
    packages.push({ file, directory: path.dirname(file), config }); counts.configs++;
  });
  for (const { file, directory, config } of packages) for (const component of config.components) {
    await check(`${file} ${component.type}:${component.name}`, async () => {
      if (!Object.hasOwn(counts, component.type) || ["configs", "motion", "cloths", "springs"].includes(component.type)) return;
      counts[component.type]++;
      if (component.type === "shader") {
        require(typeof component.name === "string" && component.name.trim(), "Shader name 不能为空");
        require(!shaders.has(component.name), `重复 Shader ${component.name}`);
        validateShaderPasses(component); validateSamplerDescriptors(component.samplers);
        shaders.set(component.name, component);
        const glsl = await fs.readFile(await existingFile(directory, component.src), "utf8");
        const sections = new Set([...glsl.matchAll(/\/\/ @section (\S+)\r?\n([\s\S]*?)\r?\n\/\/ @end/g)].map((m) => m[1]));
        for (const pass of component.passes) for (const names of Object.values(pass.sections)) {
          for (const name of Array.isArray(names) ? names : [names]) require(sections.has(name), `Shader section ${name} 不存在`);
        }
        if (component.script !== undefined) await existingFile(directory, component.script);
        for (const sampler of component.samplers) if (sampler.missing.behavior === "resource") await existingFile(directory, sampler.missing.uri);
      } else if (component.type === "behavior") {
        const name = `${component.namespace}.${component.name}`;
        require(!behaviors.has(name), `重复 Behavior ${name}`); behaviors.add(name);
        await existingFile(directory, component.script);
      } else if (component.type.startsWith("garupa-")) {
        await existingFile(directory, component.type === "garupa-expression-adapter" ? component.script : component.src);
      }
    });
  }
  for (const { file, directory, config } of packages) for (const component of config.components) {
    await check(`${file} ${component.type}:${component.name}`, async () => {
      if (component.type !== "model") return;
      const { document, buffers } = await readGlb(await existingFile(directory, component.model));
      const morphs = buildMorphNodeIndex(document, component.name);
      for (const pose of component.morphPoses || []) validateTargetMap(pose.targets, morphs, pose.name);
      validatePhysicsReferences(document, buffers, component.physics);
      counts.cloths += component.physics?.cloths?.length || 0;
      counts.springs += component.physics?.springs?.length || 0;
      validateMaterialReferences(document, shaders);
      for (const declaration of component.behaviors || []) if (!behaviors.has(declaration.name)) {
        if (declaration.required) throw new Error(`缺少 required Behavior ${declaration.name}`);
        warnings.push({ source: file, message: `未提供 optional Behavior ${declaration.name}` });
      }
    });
  }
  await check(root, async () => {
    for (const file of await motionFiles(root)) await check(file, async () => {
      const payload = await readMotionFile(file);
      validateMotionResource(payload, file);
      validateData(payload, file);
      counts.motion++;
    });
  });
  return { passed: errors.length === 0, counts, errors, warnings };
}

async function main() {
  const options = { output: "output_packages" };
  for (let i = 2; i < process.argv.length; i++) {
    const key = process.argv[i].replace(/^--/, "");
    require(["output", "report", "runtime"].includes(key) && process.argv[i + 1], `未知或缺值参数 ${process.argv[i]}`);
    options[key] = process.argv[++i];
  }
  const report = await auditResourcePackages(options.output, { runtime: options.runtime });
  if (options.report) {
    await fs.mkdir(path.dirname(path.resolve(options.report)), { recursive: true });
    await fs.writeFile(options.report, JSON.stringify(report, null, 2) + "\n", "utf8");
  }
  console.log(JSON.stringify(report, null, 2));
  if (!report.passed) process.exitCode = 1;
}
if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href) {
  main().catch((error) => { console.error(error); process.exitCode = 1; });
}
