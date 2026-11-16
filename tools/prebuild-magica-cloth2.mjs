// Conversion-time MagicaCloth2 build (converter/common/magica_prebuild.py runs this once per model).
// stdin: physics.source.magicaCloth2 JSON.  stdout: { report, components: { <component index>: runtimePreBuild } }
// The renderer's prebuild.js runs the game's runtime build for every MagicaCloth without usable PreBuild data;
// only the new runtimePreBuild objects go back, so the converter keeps writing the rest of the JSON itself.
import { prebuildMagicaCloth2 } from 'webgal-lovelive-gltf-renderer/magica-cloth2/prebuild.js';

const chunks = [];
for await (const chunk of process.stdin) chunks.push(chunk);
const source = JSON.parse(Buffer.concat(chunks).toString('utf8'));
const report = prebuildMagicaCloth2(source);
const components = {};
source.components.forEach((component, index) => {
  if (component.runtimePreBuild) components[index] = component.runtimePreBuild;
});
process.stdout.write(JSON.stringify({ report, components }));
