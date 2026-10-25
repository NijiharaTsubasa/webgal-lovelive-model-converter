import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { discoverModels, writePreview, writeModelPreview, hasPreview, syncPreviews } from '../tools/generate-model-previews.mjs';

const preview = 'data:image/webp;base64,UklGRg==';
test('Michelle body previews pair within the separate composition group', async () => {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), 'michelle-thumbnails-'));
  try {
    for (const [name, role] of [['015_cos_base', 'head'], ['015_cos_live_default', 'body'], ['015_cos_other', 'body']]) {
      const directory = path.join(root, 'bangdream', name);
      await fs.mkdir(directory, { recursive: true });
      await fs.writeFile(path.join(directory, 'config.json'), JSON.stringify({ components: [
        { type: 'model', group: 'garupa-michelle', name, role, model: role + '.glb' },
      ] }));
    }
    const models = await discoverModels(root);
    const body = models.find(model => model.name === '015_cos_other');
    assert.deepEqual(body.parts.map(part => part.component.name), ['015_cos_base', '015_cos_other']);
    assert.ok(body.parts.every(part => part.group === 'garupa-michelle'));
    assert.equal(models.find(model => model.name === '015_cos_base').parts[1].component.name, '015_cos_live_default');
  } finally { await fs.rm(root, { recursive: true, force: true }); }
});

test('body-only thumbnails follow head priority and are written outside model configs', async () => {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), 'body-thumbnails-'));
  try {
    const put = async (name, role) => {
      const dir = path.join(root, 'bangdream', name);
      await fs.mkdir(dir, { recursive: true });
      await fs.writeFile(path.join(dir, 'config.json'), JSON.stringify({ components: [
        { type: 'model', name, role, group: 'garupa', model: `${role}.glb`, preview: 'source-owned' },
      ] }));
    };
    for (const name of ['001_cos_live_default', '003_cos_live_default', '003_cos_base', '003_cos_party']) await put(name, 'head');
    for (const name of ['003_cos_party_another1', '000_cos_monthly_2023_10']) await put(name, 'body');
    const find = async name => (await discoverModels(root)).find(model => model.name === name);
    const name = '003_cos_party_another1';
    let model = await find(name);
    assert.deepEqual(model.parts.map(part => part.component.name), ['003_cos_party', name]);
    assert.equal((await find('000_cos_monthly_2023_10')).parts[0].component.name, '001_cos_live_default');
    assert.equal(model.previewFile, path.join(root, 'bangdream', 'body_only_thumbnails', name + '.webp'));
    const configBefore = await fs.readFile(model.file, 'utf8');
    assert.equal(await hasPreview(model), false, 'embedded body preview does not count as generated thumbnail');
    await writeModelPreview(model, preview);
    assert.deepEqual(await fs.readFile(model.previewFile), Buffer.from('UklGRg==', 'base64'));
    assert.equal(await fs.readFile(model.file, 'utf8'), configBefore);
    assert.equal(await hasPreview(model), true);
    await fs.rm(path.join(root, 'bangdream', '003_cos_party'), { recursive: true });
    model = await find(name);
    assert.equal(model.parts[0].component.name, '003_cos_base');
    assert.equal(model.parts[1].basePath, 'bangdream/' + name);
    await fs.rm(path.join(root, 'bangdream', '003_cos_base'), { recursive: true });
    assert.equal((await find(name)).parts[0].component.name, '003_cos_live_default');
    await fs.rm(path.join(root, 'bangdream', '003_cos_live_default'), { recursive: true });
    await assert.rejects(discoverModels(root), /Missing preview head/);
  } finally { await fs.rm(root, { recursive: true, force: true }); }
});

test('base head preview borrows only its matching default body and updates only the head', async () => {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), 'model-previews-base-'));
  try {
    const head = { type: 'model', role: 'head', group: 'garupa', name: '003_cos_base', model: 'head.glb' };
    const defaultBody = { type: 'model', role: 'body', group: 'garupa', name: '003_cos_live_default', model: 'body.glb', preview: 'body-owned' };
    const write = async (name, components) => {
      const directory = path.join(root, 'bangdream', name);
      await fs.mkdir(directory, { recursive: true });
      await fs.writeFile(path.join(directory, 'config.json'), JSON.stringify({ components }));
    };
    // Discover the head before its sibling default package.
    await write(head.name, [head]);
    await write(defaultBody.name, [{ ...head, name: defaultBody.name }, defaultBody]);
    await write('004_cos_live_default', [{ ...head, name: '004_cos_live_default' }, { ...defaultBody, name: '004_cos_live_default' }]);
    const model = (await discoverModels(root)).find(item => item.name === head.name);
    assert.deepEqual(model.parts.map(item => item.component), [head, defaultBody]);
    assert.deepEqual(model.parts.map(item => item.basePath), ['bangdream/003_cos_base', 'bangdream/003_cos_live_default']);
    await writePreview(model.file, model.index, preview);
    assert.deepEqual(JSON.parse(await fs.readFile(model.file, 'utf8')), { components: [{ ...head, preview }] });
    const bodyConfig = JSON.parse(await fs.readFile(path.join(root, 'bangdream', defaultBody.name, 'config.json'), 'utf8'));
    assert.deepEqual(bodyConfig.components[1], defaultBody);
    // Local bodies take priority; no cross-package pairing is used for other games.
    await write(head.name, [head, { ...defaultBody, name: head.name }]);
    assert.equal((await discoverModels(root)).find(item => item.name === head.name).parts[1].basePath, 'bangdream/003_cos_base');
    await write(head.name, [{ ...head, group: 'other' }]);
    assert.ok(!(await discoverModels(root)).some(item => item.name === head.name));
    // A subset missing the same character's default body cannot borrow another character.
    await write(head.name, [head]);
    await fs.rm(path.join(root, 'bangdream', defaultBody.name), { recursive: true });
    const warnings = [];
    const warn = console.warn;
    try {
      console.warn = message => warnings.push(message);
      assert.ok(!(await discoverModels(root)).some(item => item.name === head.name));
    } finally { console.warn = warn; }
    assert.match(warnings.join(), /Missing matching live_default body/);
  } finally { await fs.rm(root, { recursive: true, force: true }); }
});

test('discover integrated components and sync only preview by name', async () => {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), 'model-previews-'));
  try {
    const output = path.join(root, 'output'), game = path.join(root, 'game');
    const source = path.join(output, 'source/config.json');
    const target = path.join(game, '自定义目录/config.json');
    await fs.mkdir(path.dirname(source), { recursive: true });
    await fs.mkdir(path.dirname(target), { recursive: true });
    const model = { type: 'model', name: 'Ruby', role: 'integrated', description: '説明', model: 'ruby.glb' };
    const sourceConfig = { components: [model, { type: 'motion', name: 'Idle' }] };
    const targetConfig = { components: [{ ...model, description: '用户说明', model: 'custom.glb', behaviors: [{ name: 'custom' }] }] };
    await fs.writeFile(source, JSON.stringify(sourceConfig));
    await fs.writeFile(target, JSON.stringify(targetConfig));
    await fs.writeFile(path.join(output, 'config.json'), JSON.stringify(sourceConfig));
    assert.equal((await discoverModels(output)).length, 1);
    await writePreview(source, 0, preview);
    assert.equal(await syncPreviews(output, game), 1);
    assert.deepEqual(JSON.parse(await fs.readFile(target, 'utf8')), {
      components: [{ ...targetConfig.components[0], preview }],
    });
    assert.deepEqual(JSON.parse(await fs.readFile(source, 'utf8')).components[1], sourceConfig.components[1]);
    await assert.rejects(writePreview(source, 0, 'data:image/png;base64,AAAA'), /WebP/);
  } finally { await fs.rm(root, { recursive: true, force: true }); }
});

test('duplicate source identities cannot silently select a thumbnail', async () => {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), 'model-previews-'));
  try {
    const output = path.join(root, 'output'), game = path.join(root, 'game');
    await fs.mkdir(game);
    for (const directory of ['one', 'two']) {
      await fs.mkdir(path.join(output, directory), { recursive: true });
      await fs.writeFile(path.join(output, directory, 'config.json'), JSON.stringify({
        components: [{ type: 'model', role: 'integrated', name: 'Same', preview }],
      }));
    }
    await assert.rejects(syncPreviews(output, game), /Duplicate model name/);
  } finally { await fs.rm(root, { recursive: true, force: true }); }
});

test('paired models render in head-body order and write only the head preview', async () => {
  const root=await fs.mkdtemp(path.join(os.tmpdir(),'model-previews-pair-'));
  try {
    const output=path.join(root,'output'), game=path.join(root,'game');
    const head={type:'model',role:'head',name:'Head',model:'head.glb',group:'garupa'};
    const body={type:'model',role:'body',name:'Body',model:'body.glb',group:'garupa',preview:'body-owned'};
    for(const dir of [output,game]) {
      await fs.mkdir(path.join(dir,'pair'),{recursive:true});
      await fs.writeFile(path.join(dir,'pair/config.json'),JSON.stringify({components:[body,head]}));
    }
    const [model]=await discoverModels(output);
    assert.equal(model.index,1);assert.equal(model.component.role,'head');
    assert.deepEqual(model.parts.map(entry=>entry.component.role),['head','body']);
    assert.ok(model.parts.every(entry=>entry.basePath==='pair' && entry.group==='garupa'));
    await writePreview(model.file,model.index,preview);
    assert.equal(await syncPreviews(output,game),1);
    for(const dir of [output,game]) {
      const config=JSON.parse(await fs.readFile(path.join(dir,'pair/config.json'),'utf8'));
      assert.deepEqual(config.components,[body,{...head,preview}]);
    }
    await assert.rejects(writePreview(model.file,0,preview),/Model changed/);
    await fs.writeFile(model.file,JSON.stringify({components:[head,head,body]}));
    await assert.rejects(discoverModels(output),/Ambiguous/);
  } finally {await fs.rm(root,{recursive:true,force:true});}
});
