// Preview-host dependency only. Embedders inject their own licensed Cubism 2
// runtime through CharacterRenderer.configureParameterPlayback().
let pending;
export function loadPreviewParameterRuntime() {
  if (globalThis.Live2DMotion && globalThis.MotionQueueManager) return Promise.resolve(globalThis);
  return pending ??= new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.src = '/lib/live2d.min.js';
    script.onload = () => resolve(globalThis);
    script.onerror = () => { pending = null; script.remove(); reject(new Error('无法加载预览使用的 Cubism 2 运行库')); };
    document.head.append(script);
  });
}
