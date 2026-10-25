import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

export async function discoverModels(root, { includeBodyOnly = true } = {}) {
  const result = [];
  const packages = new Map();
  async function visit(dir) {
    for (const item of await fs.readdir(dir, { withFileTypes: true })) {
      const file = path.join(dir, item.name);
      if (item.isDirectory()) await visit(file);
      else if (item.name === 'config.json' && dir !== root) {
        const config = JSON.parse(await fs.readFile(file, 'utf8'));
        packages.set(file, config);
      }
    }
  }
  await visit(root);
  for (const [file, config] of packages) {
    const dir = path.dirname(file);
    const components = config.components ?? [];
    const heads = components.filter(component => component.type === 'model' && component.role === 'head');
    const bodies = components.filter(component => component.type === 'model' && component.role === 'body');
    if (heads.length > 1 || bodies.length > 1) throw new Error(`Ambiguous head/body package: ${file}`);
    const entry = (component, directory = dir) => ({ component, group: component.group,
      basePath: path.relative(root, directory).replaceAll('\\', '/') });
    for (const [index, component] of components.entries()) {
      if (includeBodyOnly && component.type === 'model' && component.role === 'body' && !heads.length
          && ['garupa', 'garupa-michelle'].includes(component.group) && /^\d{3}_cos_/.test(component.name)) {
        const id = component.name.slice(0, 3);
        const original = component.name.replace(/_another[1-4]$/, '');
        const names = id === '000' ? ['001_cos_live_default'] : [
          ...(original !== component.name ? [original] : []), `${id}_cos_base`, `${id}_cos_live_default`,
        ];
        let headEntry;
        for (const name of names) {
          const headDir = path.join(path.dirname(dir), name);
          const candidates = (packages.get(path.join(headDir, 'config.json'))?.components ?? [])
            .filter(candidate => candidate.type === 'model' && candidate.role === 'head'
              && candidate.group === component.group && candidate.name === name);
          if (candidates.length > 1) throw new Error(`Ambiguous preview head: ${file}`);
          if (candidates[0]) { headEntry = entry(candidates[0], headDir); break; }
        }
        if (!headEntry) throw new Error(`Missing preview head for body-only package: ${file}`);
        result.push({ file, index, component, name: component.name,
          configPath: path.relative(root, file).replaceAll('\\', '/'),
          basePath: path.relative(root, dir).replaceAll('\\', '/'),
          parts: [headEntry, entry(component)],
          previewFile: path.join(path.dirname(dir), 'body_only_thumbnails', `${path.basename(dir)}.webp`) });
        continue;
      }
      let body = bodies[0], bodyDir = dir;
      if (component.type === 'model' && component.role === 'head' && !body
          && ['garupa', 'garupa-michelle'].includes(component.group) && /^\d+_cos_base$/.test(component.name)) {
        bodyDir = path.join(path.dirname(dir), component.name.replace(/_cos_base$/, '_cos_live_default'));
        const candidates = (packages.get(path.join(bodyDir, 'config.json'))?.components ?? [])
          .filter(candidate => candidate.type === 'model' && candidate.role === 'body'
                && candidate.group === component.group
            && candidate.name === component.name.replace(/_cos_base$/, '_cos_live_default'));
        if (candidates.length > 1) throw new Error(`Ambiguous preview body: ${file}`);
        body = candidates[0];
        if (!body) console.warn(`[preview] Missing matching live_default body for ${component.name}; skipping ${file}`);
      }
      const composed = component.type === 'model' && component.role === 'head' && Boolean(body);
      if (component.type === 'model' && (component.role === 'integrated' || composed)) {
        result.push({ file, index, component, configPath: path.relative(root, file).replaceAll('\\', '/'),
          basePath: path.relative(root, dir).replaceAll('\\', '/'), name: component.name,
          ...(composed ? { parts: [entry(component), entry(body, bodyDir)] } : {}) });
      }
    }
  }
  return result.sort((a, b) => a.configPath.localeCompare(b.configPath) || a.index - b.index);
}

export async function writePreview(file, index, preview) {
  if (!/^data:image\/webp;base64,[A-Za-z0-9+/]+=*$/.test(preview)) throw new Error('Invalid WebP data URL');
  const config = JSON.parse(await fs.readFile(file, 'utf8'));
  const component = config.components[index];
  if (component.type !== 'model' || !['integrated', 'head'].includes(component.role)) throw new Error(`Model changed: ${file}`);
  component.preview = preview;
  await fs.writeFile(file, JSON.stringify(config, null, 2) + '\n', 'utf8');
}

export async function writeModelPreview(model, preview) {
  if (!model.previewFile) return writePreview(model.file, model.index, preview);
  if (!/^data:image\/webp;base64,[A-Za-z0-9+/]+=*$/.test(preview)) throw new Error('Invalid WebP data URL');
  await fs.mkdir(path.dirname(model.previewFile), { recursive: true });
  await fs.writeFile(model.previewFile, Buffer.from(preview.slice(preview.indexOf(',') + 1), 'base64'));
}

export async function hasPreview(model) {
  if (!model.previewFile) return Boolean(model.component.preview);
  try { return (await fs.stat(model.previewFile)).size > 0; }
  catch (error) { if (error.code === 'ENOENT') return false; throw error; }
}

export async function syncPreviews(root, target) {
  const sources = new Map();
  for (const model of await discoverModels(root, { includeBodyOnly: false })) {
    if (sources.has(model.name)) throw new Error(`Duplicate model name: ${model.name}`);
    sources.set(model.name, model.component.preview);
  }
  let count = 0;
  for (const model of await discoverModels(target, { includeBodyOnly: false })) {
    const preview = sources.get(model.name);
    if (!preview) { console.warn(`[preview] No generated preview for ${model.name}`); continue; }
    await writePreview(model.file, model.index, preview);
    count++;
  }
  return count;
}

async function main() {
  const args = process.argv.slice(2);
  let root = path.resolve('output_packages'), sync, names, missingOnly = false, browserChannel = 'chromium';
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--output') root = path.resolve(args[++i]);
    else if (args[i] === '--sync') sync = path.resolve(args[++i]);
    else if (args[i] === '--models') names = new Set(args[++i].split(','));
    else if (args[i] === '--missing') missingOnly = true;
    else if (args[i] === '--browser') browserChannel = args[++i];
    else if (args[i] === '--help') {
      console.log('npm run preview:models -- [--output <packages>] [--models <name,name>] [--missing] [--sync <game-model-directory>] [--browser chromium|msedge|chrome]');
      return;
    } else throw new Error(`Unknown argument: ${args[i]}`);
  }
  const discovered = (await discoverModels(root)).filter(model => !names || names.has(model.name));
  if (names && [...names].some(name => !discovered.some(model => model.name === name))) throw new Error('Requested model not found');
  const models = [];
  for (const model of discovered) if (!missingOnly || !await hasPreview(model)) models.push(model);
  if (!models.length) {
    console.log('[preview] No models need preview generation');
    if (sync) console.log(`[preview] Updated ${await syncPreviews(root, sync)} game model configs`);
    return;
  }
  process.env.PACKAGES_DIR = root;
  process.env.PLAYWRIGHT_BROWSERS_PATH ??= '0';
  const { createServer } = await import('vite');
  const { chromium } = await import('playwright');
  const server = await createServer({ configFile: path.resolve('vite.config.js'),
    server: { host: '127.0.0.1', port: 0, hmr: false },
    plugins: [{ name: 'model-preview-page', configureServer(s) {
      s.middlewares.use('/__model_preview__', (_request, response) => {
        response.setHeader('Content-Type', 'text/html');
        response.end('<!doctype html><html><head><link rel="icon" href="data:,"></head><body></body></html>');
      });
    } }] });
  let browser, page;
  const failures = [];
  try {
    await server.listen();
    browser = await chromium.launch({ headless: true, channel: browserChannel });
    const origin = `http://127.0.0.1:${server.httpServer.address().port}`;
    for (const [index, model] of models.entries()) {
      if (!page || index % 25 === 0) {
        if (page) await page.close();
        page = await browser.newPage();
        await page.goto(`${origin}/__model_preview__`);
        await page.evaluate(async () => {
          const { initialize } = await import('/tools/model-preview-renderer.js');
          window.modelPreview = await initialize();
        });
      }
      try {
        const preview = await page.evaluate(model => window.modelPreview.render(model), model);
        await writeModelPreview(model, preview);
        console.log(`[preview ${index + 1}/${models.length}] ${model.name} (${Math.round(preview.length * .75 / 1024)} KiB)`);
      } catch (error) {
        failures.push(model.name);
        console.error(`[preview ${index + 1}/${models.length}] ${model.name}: ${error.message}`);
      }
    }
    if (sync) console.log(`[preview] Updated ${await syncPreviews(root, sync)} game model configs`);
    if (failures.length) throw new Error(`Preview generation failed: ${failures.join(', ')}`);
  } finally {
    await browser?.close();
    await server.close();
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href) {
  main().catch(error => { console.error(error); process.exitCode = 1; });
}
