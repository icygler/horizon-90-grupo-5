import assert from 'node:assert/strict';
import test from 'node:test';

import { nextSlideIndex } from '../src/horizon90/static/pitch.js';

test('deck navigation advances, retreats, and stays inside the six-slide presentation', () => {
  assert.equal(nextSlideIndex(0, 1, 6), 1);
  assert.equal(nextSlideIndex(5, 1, 6), 5);
  assert.equal(nextSlideIndex(3, -1, 6), 2);
  assert.equal(nextSlideIndex(0, -1, 6), 0);
});
