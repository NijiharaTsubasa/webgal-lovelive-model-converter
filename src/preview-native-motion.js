/** Build a preview entry whose selectable identity is its resource-root path. */
export function previewNativeMotion({ sourceMotion, ...component }) {
  const slash = sourceMotion.lastIndexOf('/');
  return {
    key: sourceMotion,
    name: sourceMotion.slice('motion/'.length).replace(/\.(motionbin|json)$/, ''),
    description: component.description ?? '',
    motionGroup: component.motionGroup,
    src: sourceMotion.slice(slash + 1),
    basePath: sourceMotion.slice(0, slash),
    component,
  };
}
