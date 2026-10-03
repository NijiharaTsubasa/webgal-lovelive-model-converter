import * as THREE from 'three';
import { CharacterRenderer } from '/renderer/character-renderer.js';

export async function initialize() {
  const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true, preserveDrawingBuffer: true });
  renderer.setSize(384, 448);
  renderer.setClearColor(0, 0);
  const scene = new THREE.Scene();
  scene.add(new THREE.AmbientLight(new THREE.Color(.02, .025, .03), 1));
  const light = new THREE.DirectionalLight(0xffffff, 1);
  light.position.set(3, 5, 4);
  scene.add(light);
  const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, .01, 20);
  const character = new CharacterRenderer({ renderer, scene, camera });
  character.setPhysicsEnabled(false);
  const shaderErrors = [];
  renderer.debug.onShaderError = (gl, program) => shaderErrors.push(gl.getProgramInfoLog(program));
  for (const name of ['hasunosora_runtime', 'garupa_runtime', 'llas_runtime']) {
    const url = `/packages/runtime/${name}/config.json`;
    const response = await fetch(url);
    if (response.status === 404) continue;
    if (!response.ok) throw new Error(`Runtime config: ${response.status} ${url}`);
    character.resourcePackages.register(await response.json(), url);
  }
  return {
    async render(model) {
      shaderErrors.length = 0;
      character.clear({ rememberFace: false });
      // A still image needs the idle pose and Behavior, not simulation resources.
      const { physics, ...component } = model.component;
      if (!await character.load([{ ...model, component }], '/packages/')) throw new Error('Model did not load');
      character.update(0);
      character.root.updateMatrixWorld(true);
      character.root.traverse(node => { if (node.isSkinnedMesh) node.skeleton.update(); });
      const head = character.root.getObjectByName('Head');
      const hips = character.root.getObjectByName('Hips');
      if (!head || !hips) throw new Error('Missing Humanoid Head/Hips');
      const headPosition = head.getWorldPosition(new THREE.Vector3());
      const hipsPosition = hips.getWorldPosition(new THREE.Vector3());
      // Frame the torso using the normalized skeleton, retaining head/hair space.
      const torso = Math.abs(headPosition.y - hipsPosition.y);
      const bottom = hipsPosition.y - torso * .08;
      let top = headPosition.y;
      const vertex = new THREE.Vector3();
      character.root.traverseVisible(node => {
        if (!node.isMesh || !node.geometry.attributes.position) return;
        for (let i = 0; i < node.geometry.attributes.position.count; i++) {
          node.getVertexPosition(i, vertex);
          vertex.applyMatrix4(node.matrixWorld);
          top = Math.max(top, vertex.y);
        }
      });
      top += torso * .06;
      const halfHeight = (top - bottom) / 2;
      const halfWidth = halfHeight * 384 / 448;
      camera.left = -halfWidth; camera.right = halfWidth;
      camera.top = halfHeight; camera.bottom = -halfHeight;
      camera.position.set(headPosition.x, (top + bottom) / 2, headPosition.z + 4);
      camera.lookAt(headPosition.x, (top + bottom) / 2, headPosition.z);
      camera.updateProjectionMatrix();
      character.render();
      // Work around Hasunosora GrabPass execution order: capture the second frame
      // so the eyes use the populated grab texture instead of the dark first frame.
      await new Promise(resolve => requestAnimationFrame(resolve));
      character.update(0);
      character.render();
      if (shaderErrors.length) throw new Error(`Shader error: ${shaderErrors.join('; ')}`);
      const gl = renderer.getContext();
      const pixels = new Uint8Array(384 * 448 * 4);
      gl.readPixels(0, 0, 384, 448, gl.RGBA, gl.UNSIGNED_BYTE, pixels);
      if (!pixels.some((value, index) => index % 4 === 3 && value > 0)) throw new Error('Empty thumbnail');
      if (!pixels.some((value, index) => index % 4 === 3 && value === 0)) throw new Error('Thumbnail lost transparent background');
      const error = gl.getError();
      if (error) throw new Error(`WebGL error: ${error}`);
      const preview = renderer.domElement.toDataURL('image/webp', .82);
      character.clear({ rememberFace: false });
      return preview;
    },
  };
}
