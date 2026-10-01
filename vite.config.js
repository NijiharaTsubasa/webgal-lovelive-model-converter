import { defineConfig } from "vite";
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
import { previewParameterInput } from './tools/preview-parameter-input.mjs';

const packagesRoot = path.resolve(process.env.PACKAGES_DIR ?? "output_packages");
const rendererRoot = path.dirname(path.dirname(createRequire(import.meta.url).resolve('webgal-lovelive-gltf-renderer')));
const gameRuntimeRoot = path.resolve(process.env.GAME_RUNTIME_DIR ?? '../webgal-lovelive-game-runtime/packages');

export default defineConfig({
  // Keep the cloth solver's import.meta.url relative to its packaged WASM.
  optimizeDeps: { exclude: ['webgal-lovelive-gltf-renderer'] },
  resolve: {
    alias: { '/renderer': path.join(rendererRoot, 'src'), '/game-runtime': gameRuntimeRoot },
    dedupe: ['three'],
  },
  server: {
    fs: { allow: [process.cwd(), rendererRoot, gameRuntimeRoot] },
    watch: {
      // Asset corpora are read on request, not compiled or hot-reloaded.
      // Watching them stalls the dev server during full conversion runs.
      ignored: [
        "**/input_*/**", "**/output_packages/**", "**/baked_motions/**",
        "**/validation/**", "**/.tmp/**", "**/converter/unity_baker/Temp/**",
        "**/converter/unity_baker/Library/**",
      ],
    },
  },
  plugins: [previewParameterInput(), {
    name: "serve-output-packages",
    configureServer(server) {
      // Runtime resources belong to the standalone repository, not converter output.
      server.middlewares.use("/packages", async (request, response, next) => {
        const relative = decodeURIComponent(request.url.split("?")[0]).replace(/^\/+/, "");
        const isRuntime = relative.startsWith('runtime/');
        const root = isRuntime ? gameRuntimeRoot : packagesRoot;
        const file = path.resolve(root, isRuntime ? relative.slice('runtime/'.length) : relative);
        if (!file.startsWith(root + path.sep) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) return next();
        const extension = path.extname(file);
        const type = ({ '.json': 'application/json', '.js': 'application/javascript', '.mjs': 'application/javascript',
          '.mtn': 'text/plain; charset=utf-8', '.glsl': 'text/plain; charset=utf-8' })[extension] ?? 'application/octet-stream';
        response.setHeader("Content-Type", type);
        if (extension === '.js' || extension === '.mjs') {
          try {
            const transformed = await server.transformRequest(`/@fs/${file.replaceAll('\\', '/')}`);
            if (transformed) return response.end(transformed.code);
          } catch (error) { return next(error); }
        }
        fs.createReadStream(file).pipe(response);
      });
    },
  }],
});
