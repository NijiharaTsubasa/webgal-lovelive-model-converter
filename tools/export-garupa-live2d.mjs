import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { readParameterInput } from './preview-parameter-input.mjs';

export async function exportGarupaLive2d(input, output) {
  input = path.resolve(input);
  output = path.resolve(output);
  const relative = path.relative(input, output);
  const reverse = path.relative(output, input);
  const nested = value => value === '' || (!value.startsWith('..' + path.sep) && value !== '..' && !path.isAbsolute(value));
  if (nested(relative) || nested(reverse)) throw new Error('输入与输出目录不能相同或互相包含');
  const config = await readParameterInput(input);
  if (!config.components.length) throw new Error(`输入目录没有声明参数动作或表情：${input}`);
  for (const src of new Set(config.components.map(component => component.src))) {
    const relativeFile = src.split('/').map(decodeURIComponent).join(path.sep);
    const destination = path.join(output, relativeFile);
    await fs.mkdir(path.dirname(destination), { recursive: true });
    await fs.copyFile(path.join(input, relativeFile), destination);
  }
  await fs.writeFile(path.join(output, 'config.json'), JSON.stringify(config, null, 2) + '\n', 'utf8');
  return config;
}

if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href) {
  try {
    const output = path.resolve('output_packages/garupa_live2d');
    const config = await exportGarupaLive2d('input_garupa_live2d/.mtn_exp', output);
    console.log(`已导出 ${config.components.length} 个参数动作和表情：${output}`);
  } catch (error) {
    console.error(error.message);
    process.exitCode = 1;
  }
}
