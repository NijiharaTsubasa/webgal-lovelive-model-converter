import fs from 'node:fs/promises';
import path from 'node:path';

export const PARAMETER_INPUT_CONFIG = 'parameter-input/config.json';

function inside(root, file) {
  const relative = path.relative(root, file);
  return relative !== '' && relative !== '..' && !relative.startsWith('..' + path.sep) && !path.isAbsolute(relative);
}

function sourceFile(root, reference) {
  if (typeof reference !== 'string' || !reference.trim()
    || /^(?:[a-z][a-z\d+.-]*:|[/\\])/i.test(reference)) throw new Error(`非法参数文件路径：${reference}`);
  const file = path.resolve(root, reference.replaceAll('\\', '/'));
  if (!inside(root, file)) throw new Error(`参数文件路径超出 .mtn_exp 目录：${reference}`);
  return file;
}

async function localFile(root, file) {
  const actualRoot = await fs.realpath(root), actualFile = await fs.realpath(file);
  if (!inside(actualRoot, actualFile) || !(await fs.stat(actualFile)).isFile()) throw new Error(`不是 .mtn_exp 内的文件：${file}`);
  return actualFile;
}

export async function readParameterInput(root) {
  root = path.resolve(root);
  try { await fs.stat(root); }
  catch (error) { if (error.code === 'ENOENT') return { components: [] }; throw error; }
  const modelFile = path.join(root, 'model.json');
  let model;
  try { model = JSON.parse(await fs.readFile(modelFile, 'utf8')); }
  catch (error) { throw new Error(`无法读取 ${modelFile}：${error.message}`); }
  const components = [], identities = new Set();
  async function add(type, name, definition) {
    if (typeof name !== 'string' || !name.trim()) throw new Error(`${type} 缺少名称`);
    const identity = `${type}:${name}`;
    if (identities.has(identity)) throw new Error(`重复参数资源：${identity}`);
    identities.add(identity);
    const file = sourceFile(root, definition?.file);
    const extension = type === 'garupa-motion' ? '.mtn' : '.exp.json';
    if (!file.endsWith(extension)) throw new Error(`${name} 的文件必须是 ${extension}：${definition?.file}`);
    try { await localFile(root, file); }
    catch (error) { throw new Error(`${name} 的参数文件不可用：${definition.file}（${error.message}）`); }
    const src = path.relative(root, file).split(path.sep).map(encodeURIComponent).join('/');
    const component = { type, name, src };
    for (const field of ['fade_in', 'fade_out']) {
      if (definition[field] !== undefined) {
        if (!Number.isFinite(definition[field])) throw new Error(`${name} 的 ${field} 必须是有限数值`);
        component[field] = definition[field];
      }
    }
    components.push(component);
  }
  if (model.motions !== undefined && (!model.motions || Array.isArray(model.motions) || typeof model.motions !== 'object')) {
    throw new Error(`${modelFile} 的 motions 必须是对象`);
  }
  for (const [name, entries] of Object.entries(model.motions ?? {})) {
    if (!Array.isArray(entries) || !entries.length) throw new Error(`${name} 的动作列表为空或格式错误`);
    for (let index = 0; index < entries.length; index++) {
      await add('garupa-motion', entries.length === 1 ? name : `${name}/${index + 1}`, entries[index]);
    }
  }
  if (model.expressions !== undefined && !Array.isArray(model.expressions)) throw new Error(`${modelFile} 的 expressions 必须是数组`);
  for (const definition of model.expressions ?? []) await add('garupa-expression', definition?.name, definition);
  return { components };
}

export function previewParameterInput(root = path.resolve('input_garupa_live2d/.mtn_exp')) {
  return { name: 'preview-parameter-input', configureServer(server) {
    server.middlewares.use('/packages/parameter-input', async (request, response) => {
      try {
        const relative = decodeURIComponent((request.url ?? '').split('?')[0]).replace(/^\/+/, '');
        response.setHeader('Cache-Control', 'no-store');
        if (relative === 'config.json') {
          response.setHeader('Content-Type', 'application/json; charset=utf-8');
          return response.end(JSON.stringify(await readParameterInput(root)));
        }
        if (!relative.endsWith('.mtn') && !relative.endsWith('.exp.json')) {
          response.statusCode = 404; return response.end('未找到参数动作或表情文件');
        }
        const file = await localFile(root, sourceFile(root, relative));
        response.setHeader('Content-Type', relative.endsWith('.mtn') ? 'text/plain; charset=utf-8' : 'application/json; charset=utf-8');
        response.end(await fs.readFile(file));
      } catch (error) {
        response.statusCode = 400;
        response.setHeader('Content-Type', 'application/json; charset=utf-8');
        response.end(JSON.stringify({ error: error.message }));
      }
    });
  } };
}
