import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

export async function discoverModels(root) {
  const result = [];
  async function visit(dir) {
    for (const item of await fs.readdir(dir, { withFileTypes: true })) {
      const file = path.join(dir, item.name);
      if (item.isDirectory()) await visit(file);
      else if (item.name === 'config.json' && dir !== root) {
        const config = JSON.parse(await fs.readFile(file, 'utf8'));
        for (const [index, component] of (config.components ?? []).entries()) {
          if (component.type === 'model' && component.role === 'integrated') {
            result.push({ file, index, component, configPath: path.relative(root, file).replaceAll('\\', '/'),
              basePath: path.relative(root, dir).replaceAll('\\', '/'), name: component.name });
          }
        }
      }
    }
  }
  await visit(root);
  return result.sort((a, b) => a.configPath.localeCompare(b.configPath) || a.index - b.index);
}

export async function writePreview(file, index, preview) {
  if (!/^data:image\/webp;base64,[A-Za-z0-9+/]+=*$/.test(preview)) throw new Error('Invalid WebP data URL');
  const config = JSON.parse(await fs.readFile(file, 'utf8'));
  const component = config.components[index];
  if (component.type !== 'model' || component.role !== 'integrated') throw new Error(`Model changed: ${file}`);
  component.preview = preview;
  await fs.writeFile(file, JSON.stringify(config, null, 2) + '\n', 'utf8');
}

export async function syncPreviews(root, target) {
  const sources = new Map();
  for (const model of await discoverModels(root)) {
    if (sources.has(model.name)) throw new Error(`Duplicate model name: ${model.name}`);
    sources.set(model.name, model.component.preview);
  }
  let count = 0;
  for (const model of await discoverModels(target)) {
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
  const models = discovered.filter(model => !missingOnly || !model.component.preview);
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
        await writePreview(model.file, model.index, preview);
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
