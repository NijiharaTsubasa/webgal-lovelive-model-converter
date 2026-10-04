import { test } from 'node:test';
import assert from 'node:assert/strict';
import { previewNativeMotion } from '../src/preview-native-motion.js';

test('preview uses the path as motion identity and retains original metadata name', () => {
  const entry = previewNativeMotion({ sourceMotion: 'motion/llas/ch0009_nik/original1_m.motionbin',
    type: 'motion', name: 'ch0009_nik_original1_m', description: 'Example', motionGroup: 'llas' });
  assert.equal(entry.name, 'llas/ch0009_nik/original1_m');
  assert.equal(entry.component.name, 'ch0009_nik_original1_m');
  assert.equal(entry.basePath, 'motion/llas/ch0009_nik');
  assert.equal(entry.src, 'original1_m.motionbin');
});
