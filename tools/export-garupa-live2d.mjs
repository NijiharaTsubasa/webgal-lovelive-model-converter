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
  const sourceConfig = await readParameterInput(input);
  if (!sourceConfig.components.length) throw new Error(`输入目录没有声明参数动作或表情：${input}`);
  const destinations = new Set();
  const copies = sourceConfig.components.map(component => {
    const segments = component.name.split('/');
    if (segments.some(segment => !segment || segment === '.' || segment === '..')
      || /[\\:]/.test(component.name)) throw new Error(`资源名称不能作为包内路径：${component.name}`);
    const extension = component.type === 'garupa-motion' ? '.mtn' : '.exp.json';
    const relativeFile = component.name + extension;
    const destination = path.resolve(output, relativeFile);
    const identity = process.platform === 'win32' ? destination.toLowerCase() : destination;
    if (destinations.has(identity)) throw new Error(`资源输出路径冲突：${relativeFile}`);
    destinations.add(identity);
    return { component, destination };
  });
  for (const { component, destination } of copies) {
    const relativeFile = component.src.split('/').map(decodeURIComponent).join(path.sep);
    await fs.mkdir(path.dirname(destination), { recursive: true });
    await fs.copyFile(path.join(input, relativeFile), destination);
  }
  return copies.length;
}

if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href) {
  try {
    const output = path.resolve('output_packages/mtn_exp');
    const count = await exportGarupaLive2d('input_garupa_live2d/.mtn_exp', output);
    console.log(`已导出 ${count} 个参数动作和表情：${output}`);
  } catch (error) {
    console.error(error.message);
    process.exitCode = 1;
  }
}
