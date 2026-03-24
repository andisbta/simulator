/**
 * Block Engine — App Entry
 * Initializes engine, UI, and connects everything.
 */

import { Engine } from './engine/core.js';
import { AssetGenerator } from './engine/assets.js';
import { Entity } from './engine/entity.js';
import { BlockManager } from './ui/block-manager.js';
import { ParamBindings } from './ui/param-bindings.js';

// --- Init ---
const canvas = document.getElementById('game-canvas');
const engine = new Engine(canvas);

// Asset generator
const assetGen = new AssetGenerator();

// Create default player entity
const player = new Entity('Player', assetGen);
player.x = 400;
player.y = 250;
engine.entities.push(player);

// --- UI ---
const blockManager = new BlockManager();
const bindings = new ParamBindings(engine, assetGen, engine.entities);

// FPS display
engine.onFpsUpdate = (fps) => {
  document.getElementById('fps-display').textContent = fps + ' FPS';
};

// Mouse position in status bar
canvas.addEventListener('mousemove', () => {
  document.getElementById('status-mouse').textContent =
    `X: ${engine.mouse.x}  Y: ${engine.mouse.y}`;
});

// Entity count
const updateEntityCount = () => {
  document.getElementById('status-entities').textContent =
    `Entities: ${engine.entities.length}`;
};

// --- Play / Stop ---
const playBtn = document.getElementById('btn-play');
const playIcon = document.getElementById('play-icon');
const statusMode = document.getElementById('status-mode');

let isPlaying = false;

playBtn.addEventListener('click', () => {
  isPlaying = !isPlaying;
  playBtn.classList.toggle('playing', isPlaying);
  playIcon.textContent = isPlaying ? '■' : '▶';
  playBtn.querySelector('span:last-child') || null;

  // Update button text
  const textNodes = [...playBtn.childNodes].filter(n => n.nodeType === 3);
  if (textNodes.length > 0) {
    textNodes[textNodes.length - 1].textContent = isPlaying ? ' Stop' : ' Play';
  }

  statusMode.textContent = isPlaying ? 'Play Mode' : 'Edit Mode';

  if (isPlaying) {
    engine.start();
  } else {
    engine.stop();
  }
});

// --- Zoom ---
let zoomLevel = 100;
const zoomDisplay = document.getElementById('zoom-display');
const canvasWrap = document.getElementById('canvas-wrap');

const applyZoom = () => {
  canvas.style.transform = `scale(${zoomLevel / 100})`;
  zoomDisplay.textContent = zoomLevel + '%';
};

document.getElementById('preview-zoom-in').addEventListener('click', () => {
  zoomLevel = Math.min(200, zoomLevel + 10);
  applyZoom();
});

document.getElementById('preview-zoom-out').addEventListener('click', () => {
  zoomLevel = Math.max(30, zoomLevel - 10);
  applyZoom();
});

document.getElementById('preview-reset').addEventListener('click', () => {
  zoomLevel = 100;
  applyZoom();
  // Reset entity position
  player.x = Math.round(engine.scene.width / 2);
  player.y = Math.round(engine.scene.height / 2);
  document.getElementById('entity-x').value = player.x;
  document.getElementById('entity-y').value = player.y;
});

// --- Save / Load / Export ---
document.getElementById('btn-save').addEventListener('click', () => {
  const state = {
    scene: engine.scene,
    physics: engine.physics,
    controls: engine.controls,
    effects: engine.effects,
    audio: engine.audio,
    dialog: engine.dialog,
    asset: assetGen.config,
    entities: engine.entities.map(e => ({
      name: e.name,
      x: e.x,
      y: e.y,
      layer: e.layer,
      tag: e.tag,
      animation: e.animation,
      assetOverrides: e.assetOverrides,
    })),
  };

  const blob = new Blob([JSON.stringify(state, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'block-engine-project.json';
  a.click();
  URL.revokeObjectURL(url);
});

document.getElementById('btn-export').addEventListener('click', () => {
  const state = {
    scene: engine.scene,
    physics: engine.physics,
    controls: engine.controls,
    effects: engine.effects,
    audio: engine.audio,
    dialog: engine.dialog,
    asset: assetGen.config,
    entities: engine.entities.map(e => ({
      name: e.name,
      x: e.x,
      y: e.y,
      layer: e.layer,
      tag: e.tag,
      animation: e.animation,
    })),
  };

  console.log('Block Engine Export:', JSON.stringify(state, null, 2));
  alert('Project exported to console. Check DevTools (F12).');
});

// --- Start engine in edit mode (always rendering) ---
engine.start();
updateEntityCount();
