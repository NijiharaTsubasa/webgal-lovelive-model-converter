import assert from 'node:assert/strict';
import test from 'node:test';
import { chromium } from 'playwright';
import { createServer } from 'vite';
import path from 'node:path';
import { createRequire } from 'node:module';

function glb(name) {
  const text=Buffer.from(JSON.stringify({asset:{version:'2.0'},scene:0,scenes:[{nodes:[0]}],nodes:[{name}]}));
  const length=Math.ceil(text.length/4)*4, out=Buffer.alloc(20+length,0x20);
  out.write('glTF');out.writeUInt32LE(2,4);out.writeUInt32LE(out.length,8);
  out.writeUInt32LE(length,12);out.writeUInt32LE(0x4e4f534a,16);text.copy(out,20);return out;
}

test('preview waits for asynchronous profile preparation and ignores cancelled selections', {timeout:30000}, async t=>{
  const vite=await createServer({logLevel:'silent',server:{host:'127.0.0.1',port:0}});
  await vite.listen();t.after(()=>vite.close());
  const browser=await chromium.launch({headless:true});t.after(()=>browser.close());
  const page=await browser.newPage();page.setDefaultTimeout(5000);
  const failures=[];page.on('pageerror',error=>failures.push(error.message));
  page.on('console',message=>{if(message.type()==='error')failures.push(message.text());});
  await page.route('**/src/main.js',async route=>{
    const response=await route.fetch();
    await route.fulfill({response,body:`${await response.text()}
      window.__profileUpdates=[];
      const originalUpdate=character.update.bind(character);
      character.update=(delta)=>{if(character.root)window.__profileUpdates.push(character.config.name);return originalUpdate(delta);};
      window.__profileActor=()=>character.config?.name;
      window.__emptyProfileRenders=0;
      const originalRender=character.render.bind(character);
      character.render=()=>{if(!character.root)window.__emptyProfileRenders++;return originalRender();};
      window.__clearProfile=()=>character.clear();
    `});
  });
  const model=name=>({type:'model',name,role:'integrated',model:`${name}.glb`,humanoidScale:1,
    morphPoses:[],expressionGroups:[],renderProfile:'delayed'});
  await page.route('**/packages/**',route=>{
    const pathname=new URL(route.request().url()).pathname;
    if(pathname==='/packages/config.json')return route.fulfill({json:{components:[
      ...['First','Second'].map(name=>({...model(name),sourceConfig:'fixture/config.json'})),
      {type:'render-profile',name:'delayed',script:'profile.js',requiredShaders:[],sourceConfig:'profile/config.json'},
    ]}});
    if(pathname==='/packages/fixture/config.json')return route.fulfill({json:{components:['First','Second'].map(model)}});
    if(pathname==='/packages/profile/config.json')return route.fulfill({json:{components:[{type:'render-profile',name:'delayed',script:'profile.js',requiredShaders:[]}]}});
    if(pathname==='/packages/profile/profile.js')return route.fulfill({contentType:'text/javascript',body:`
      window.__profiles=[];
      export function createRenderProfile(){const record={prepared:false,preparing:false,draws:0};window.__profiles.push(record);
       return {attach(){},detach(){},destroy(){},async prepare(){record.preparing=true;await new Promise(resolve=>record.release=resolve);record.prepared=true;},
        render(){if(!record.prepared)throw new Error('Profile rendered before preparation');record.draws++;}};}
    `});
    if(pathname==='/packages/parameter-input/config.json'||pathname.startsWith('/packages/runtime/'))return route.fulfill({json:{components:[]}});
    if(pathname.endsWith('.glb'))return route.fulfill({contentType:'model/gltf-binary',body:glb(pathname.split('/').at(-1).slice(0,-4))});
    return route.abort();
  });
  await page.goto(`http://127.0.0.1:${vite.httpServer.address().port}/`);
  await page.waitForFunction(()=>window.__profiles?.length===1);
  await page.waitForTimeout(150);
  assert.deepEqual(failures,[],'animation loop must not render an unprepared profile');
  assert.deepEqual(await page.evaluate(()=>window.__profileUpdates),[],'animation must remain frozen while preparation is pending');
  assert.equal(await page.evaluate(()=>window.__profiles[0].preparing),true);
  await page.uncheck('#parameterized-rendering-toggle');await page.check('#parameterized-rendering-toggle');
  await page.selectOption('#character','fixture/config.json#model:Second:integrated');
  await page.waitForFunction(()=>window.__profiles?.length===2&&window.__profiles[1].preparing);
  await page.evaluate(()=>window.__profiles[0].release());
  await page.waitForTimeout(100);
  assert.equal(await page.evaluate(()=>window.__profileActor()),'Second');
  assert.deepEqual(await page.evaluate(()=>window.__profileUpdates),[]);
  await page.evaluate(()=>window.__profiles[1].release());
  await page.waitForFunction(()=>window.__profiles[1].draws>0);
  assert.deepEqual(failures,[]);
  assert.equal(await page.locator('#status').textContent(),'Second');
  const emptyRenders=await page.evaluate(()=>window.__emptyProfileRenders);
  await page.evaluate(()=>window.__clearProfile());
  await page.waitForFunction(previous=>window.__emptyProfileRenders>previous,emptyRenders);
});

test('thumbnail renderer registers Yohane profiles and prepares after camera framing', {timeout:30000}, async t=>{
  const rendererSource=path.dirname(createRequire(import.meta.url).resolve('webgal-lovelive-gltf-renderer'));
  const vite=await createServer({logLevel:'silent',resolve:{alias:{'/renderer':rendererSource}},server:{host:'127.0.0.1',port:0}});
  await vite.listen();t.after(()=>vite.close());
  const browser=await chromium.launch({headless:true});t.after(()=>browser.close());
  const page=await browser.newPage();const failures=[];page.on('pageerror',error=>failures.push(error.message));
  const base=`http://127.0.0.1:${vite.httpServer.address().port}`;
  await page.route('**/thumbnail-test',route=>route.fulfill({contentType:'text/html',body:'<!doctype html><html></html>'}));
  await page.route('**/packages/**',route=>{
    const pathname=new URL(route.request().url()).pathname;
    if(pathname==='/packages/runtime/yohane_runtime/config.json')return route.fulfill({json:{components:[
      {type:'render-profile',name:'thumbnail',script:'profile.js',requiredShaders:[]},
    ]}});
    if(pathname.endsWith('/config.json'))return route.fulfill({status:404,body:''});
    if(pathname.endsWith('/profile.js'))return route.fulfill({contentType:'text/javascript',body:`
      export function createRenderProfile({THREE,renderer}){let prepared=false,mesh;
       return {attach(root){mesh=new THREE.Mesh(new THREE.BoxGeometry(.3,.3,.3),new THREE.MeshBasicMaterial({color:0xff0000}));mesh.position.y=1.4;root.add(mesh);},detach(root){root.remove(mesh);},destroy(){mesh.geometry.dispose();mesh.material.dispose();},
        async prepare(frame){if(frame.camera.position.z<3)throw new Error('Camera not framed');await new Promise(resolve=>setTimeout(resolve,30));prepared=true;window.__thumbnailPrepared=true;},
        render(frame){if(!prepared)throw new Error('Thumbnail profile rendered before preparation');renderer.render(frame.scene,frame.camera);}};}
    `});
    if(pathname.endsWith('/model.glb')){
      const text=Buffer.from(JSON.stringify({asset:{version:'2.0'},scene:0,scenes:[{nodes:[0]}],nodes:[{name:'Root',children:[1,2]},{name:'Hips',translation:[0,.8,0]},{name:'Head',translation:[0,1.5,0]}]}));
      const length=Math.ceil(text.length/4)*4,out=Buffer.alloc(20+length,0x20);out.write('glTF');out.writeUInt32LE(2,4);out.writeUInt32LE(out.length,8);out.writeUInt32LE(length,12);out.writeUInt32LE(0x4e4f534a,16);text.copy(out,20);
      return route.fulfill({contentType:'model/gltf-binary',body:out});
    }
    return route.abort();
  });
  await page.goto(`${base}/thumbnail-test`);
  const result=await page.evaluate(async()=>{
    const {initialize}=await import('/tools/model-preview-renderer.js');
    const thumbnail=await initialize();
    return thumbnail.render({name:'Fixture',basePath:'fixture/',configPath:'fixture/config.json',component:{
      type:'model',name:'Fixture',role:'integrated',model:'model.glb',humanoidScale:1,renderProfile:'thumbnail',morphPoses:[],expressionGroups:[],
    }});
  });
  assert.match(result,/^data:image\/webp;base64,/);assert.equal(await page.evaluate(()=>window.__thumbnailPrepared),true);
  assert.deepEqual(failures,[]);
});
