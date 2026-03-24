/**
 * Block Engine — Parameter Bindings
 * Connects UI inputs to engine state with live updates.
 */

export class ParamBindings {
  constructor(engine, assetGenerator, entities) {
    this.engine = engine;
    this.asset = assetGenerator;
    this.entities = entities;

    this._bindScene();
    this._bindAssets();
    this._bindEntity();
    this._bindPhysics();
    this._bindControls();
    this._bindAnimation();
    this._bindEffects();
    this._bindAudio();
    this._bindDialog();
  }

  // Helper: bind a range input to a value display and callback
  _bindRange(id, displayId, format, callback) {
    const input = document.getElementById(id);
    const display = document.getElementById(displayId);
    if (!input) return;

    const update = () => {
      if (display) display.textContent = format(input.value);
      callback(parseFloat(input.value));
    };

    input.addEventListener('input', update);
    update(); // init
  }

  // Helper: bind a color input
  _bindColor(id, displayId, callback) {
    const input = document.getElementById(id);
    const display = document.getElementById(displayId);
    if (!input) return;

    const update = () => {
      if (display) display.textContent = input.value;
      callback(input.value);
    };

    input.addEventListener('input', update);
    update();
  }

  // Helper: bind a checkbox
  _bindCheck(id, callback) {
    const input = document.getElementById(id);
    if (!input) return;
    input.addEventListener('change', () => callback(input.checked));
    callback(input.checked);
  }

  // Helper: bind a select
  _bindSelect(id, callback) {
    const input = document.getElementById(id);
    if (!input) return;
    input.addEventListener('change', () => callback(input.value));
    callback(input.value);
  }

  _bindScene() {
    const eng = this.engine;

    this._bindColor('scene-bg', 'scene-bg-val', (v) => { eng.scene.bg = v; });
    this._bindCheck('scene-grid', (v) => { eng.scene.grid = v; });
    this._bindRange('scene-grid-size', 'scene-grid-size-val', (v) => v + 'px', (v) => { eng.scene.gridSize = v; });
    this._bindColor('scene-grid-color', 'scene-grid-color-val', (v) => { eng.scene.gridColor = v; });

    const widthInput = document.getElementById('scene-width');
    const heightInput = document.getElementById('scene-height');

    if (widthInput) {
      widthInput.addEventListener('change', () => {
        eng.scene.width = parseInt(widthInput.value) || 800;
        eng.resize();
      });
    }

    if (heightInput) {
      heightInput.addEventListener('change', () => {
        eng.scene.height = parseInt(heightInput.value) || 500;
        eng.resize();
      });
    }
  }

  _bindAssets() {
    const asset = this.asset;
    const previewCanvas = document.getElementById('asset-preview');

    const refreshPreview = () => {
      if (previewCanvas) asset.renderPreview(previewCanvas);
      // Also update the first entity's overrides
      if (this.entities[0]) {
        this.entities[0].assetOverrides = { ...asset.config };
      }
    };

    this._bindSelect('asset-shape', (v) => { asset.config.shape = v; refreshPreview(); });
    this._bindRange('asset-size', 'asset-size-val', (v) => v + 'px', (v) => { asset.config.size = v; refreshPreview(); });
    this._bindColor('asset-fill', 'asset-fill-val', (v) => { asset.config.fill = v; refreshPreview(); });
    this._bindCheck('asset-stroke', (v) => { asset.config.stroke = v; refreshPreview(); });
    this._bindColor('asset-stroke-color', 'asset-stroke-color-val', (v) => { asset.config.strokeColor = v; refreshPreview(); });
    this._bindRange('asset-stroke-width', 'asset-stroke-width-val', (v) => v + 'px', (v) => { asset.config.strokeWidth = v; refreshPreview(); });
    this._bindRange('asset-opacity', 'asset-opacity-val', (v) => parseFloat(v).toFixed(1), (v) => { asset.config.opacity = v; refreshPreview(); });

    // Seed
    const seedInput = document.getElementById('asset-seed');
    const seedRand = document.getElementById('asset-seed-rand');
    if (seedInput) {
      seedInput.addEventListener('change', () => {
        asset.config.seed = parseInt(seedInput.value) || 0;
        refreshPreview();
      });
    }
    if (seedRand) {
      seedRand.addEventListener('click', () => {
        const newSeed = Math.floor(Math.random() * 10000);
        if (seedInput) seedInput.value = newSeed;
        asset.config.seed = newSeed;
        refreshPreview();
      });
    }

    // Initial preview
    refreshPreview();
  }

  _bindEntity() {
    const nameInput = document.getElementById('entity-name');
    const xInput = document.getElementById('entity-x');
    const yInput = document.getElementById('entity-y');
    const layerInput = document.getElementById('entity-layer');

    const getActive = () => this.entities[0]; // for now, single entity

    if (nameInput) {
      nameInput.addEventListener('input', () => {
        const e = getActive();
        if (e) e.name = nameInput.value;
      });
    }

    if (xInput) {
      xInput.addEventListener('input', () => {
        const e = getActive();
        if (e) e.x = parseInt(xInput.value) || 0;
      });
    }

    if (yInput) {
      yInput.addEventListener('input', () => {
        const e = getActive();
        if (e) e.y = parseInt(yInput.value) || 0;
      });
    }

    if (layerInput) {
      layerInput.addEventListener('input', () => {
        const e = getActive();
        if (e) e.layer = parseInt(layerInput.value) || 0;
      });
    }

    this._bindSelect('entity-tag', (v) => {
      const e = getActive();
      if (e) e.tag = v;
    });
  }

  _bindPhysics() {
    // Physics params stored on engine for now
    if (!this.engine.physics) {
      this.engine.physics = { enabled: true, gravity: 980, friction: 0.1, bounce: 0.3, mass: 1, collision: 'aabb' };
    }
    const p = this.engine.physics;

    this._bindCheck('phys-enable', (v) => { p.enabled = v; });
    this._bindRange('phys-gravity', 'phys-gravity-val', (v) => Math.round(v), (v) => { p.gravity = v; });
    this._bindRange('phys-friction', 'phys-friction-val', (v) => parseFloat(v).toFixed(2), (v) => { p.friction = v; });
    this._bindRange('phys-bounce', 'phys-bounce-val', (v) => parseFloat(v).toFixed(2), (v) => { p.bounce = v; });
    this._bindRange('phys-mass', 'phys-mass-val', (v) => parseFloat(v).toFixed(1), (v) => { p.mass = v; });
    this._bindSelect('phys-collision', (v) => { p.collision = v; });
  }

  _bindControls() {
    if (!this.engine.controls) {
      this.engine.controls = { mode: 'topdown', speed: 200, jump: 400, dash: false };
    }
    const c = this.engine.controls;

    this._bindSelect('ctrl-mode', (v) => { c.mode = v; });
    this._bindRange('ctrl-speed', 'ctrl-speed-val', (v) => Math.round(v), (v) => { c.speed = v; });
    this._bindRange('ctrl-jump', 'ctrl-jump-val', (v) => Math.round(v), (v) => { c.jump = v; });
    this._bindCheck('ctrl-dash', (v) => { c.dash = v; });
  }

  _bindAnimation() {
    const getActive = () => this.entities[0];

    this._bindSelect('anim-idle', (v) => {
      const e = getActive();
      if (e) e.animation.idle = v;
    });

    this._bindRange('anim-speed', 'anim-speed-val', (v) => parseFloat(v).toFixed(1) + 'x', (v) => {
      const e = getActive();
      if (e) e.animation.speed = v;
    });

    this._bindSelect('anim-easing', (v) => {
      const e = getActive();
      if (e) e.animation.easing = v;
    });

    this._bindCheck('anim-loop', (v) => {
      const e = getActive();
      if (e) e.animation.loop = v;
    });
  }

  _bindEffects() {
    if (!this.engine.effects) {
      this.engine.effects = { particles: false, count: 20, lifetime: 1, color: '#4a9eff', shake: false };
    }
    const fx = this.engine.effects;

    this._bindCheck('fx-particles', (v) => { fx.particles = v; });
    this._bindRange('fx-count', 'fx-count-val', (v) => Math.round(v), (v) => { fx.count = v; });
    this._bindRange('fx-lifetime', 'fx-lifetime-val', (v) => parseFloat(v).toFixed(1) + 's', (v) => { fx.lifetime = v; });
    this._bindColor('fx-color', 'fx-color-val', (v) => { fx.color = v; });
    this._bindCheck('fx-shake', (v) => { fx.shake = v; });
  }

  _bindAudio() {
    if (!this.engine.audio) {
      this.engine.audio = { type: 'jump', wave: 'sine', freq: 440, vol: 0.5 };
    }
    const a = this.engine.audio;

    this._bindSelect('audio-type', (v) => { a.type = v; });
    this._bindSelect('audio-wave', (v) => { a.wave = v; });
    this._bindRange('audio-freq', 'audio-freq-val', (v) => Math.round(v) + ' Hz', (v) => { a.freq = v; });
    this._bindRange('audio-vol', 'audio-vol-val', (v) => parseFloat(v).toFixed(2), (v) => { a.vol = v; });

    // Test sound button
    const testBtn = document.getElementById('audio-test');
    if (testBtn) {
      testBtn.addEventListener('click', () => this._playTestSound());
    }
  }

  _playTestSound() {
    const a = this.engine.audio;
    try {
      const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();

      osc.type = a.wave;
      osc.frequency.value = a.freq;
      gain.gain.value = a.vol;

      // Shape the sound based on type
      const now = audioCtx.currentTime;
      switch (a.type) {
        case 'jump':
          osc.frequency.setValueAtTime(a.freq, now);
          osc.frequency.exponentialRampToValueAtTime(a.freq * 1.5, now + 0.1);
          gain.gain.setValueAtTime(a.vol, now);
          gain.gain.exponentialRampToValueAtTime(0.01, now + 0.3);
          break;
        case 'hit':
          osc.frequency.setValueAtTime(a.freq, now);
          osc.frequency.exponentialRampToValueAtTime(80, now + 0.15);
          gain.gain.setValueAtTime(a.vol, now);
          gain.gain.exponentialRampToValueAtTime(0.01, now + 0.2);
          break;
        case 'pickup':
          osc.frequency.setValueAtTime(a.freq, now);
          osc.frequency.setValueAtTime(a.freq * 1.25, now + 0.08);
          osc.frequency.setValueAtTime(a.freq * 1.5, now + 0.16);
          gain.gain.setValueAtTime(a.vol, now);
          gain.gain.exponentialRampToValueAtTime(0.01, now + 0.3);
          break;
        case 'blip':
          gain.gain.setValueAtTime(a.vol, now);
          gain.gain.exponentialRampToValueAtTime(0.01, now + 0.08);
          break;
      }

      osc.connect(gain);
      gain.connect(audioCtx.destination);
      osc.start(now);
      osc.stop(now + 0.4);
    } catch (e) {
      // Audio not available
    }
  }

  _bindDialog() {
    if (!this.engine.dialog) {
      this.engine.dialog = { text: 'Hello, welcome to the game!', fontSize: 14, speed: 50, style: 'bottom' };
    }
    const d = this.engine.dialog;

    const textInput = document.getElementById('dialog-text');
    if (textInput) {
      textInput.addEventListener('input', () => { d.text = textInput.value; });
    }

    this._bindRange('dialog-font', 'dialog-font-val', (v) => Math.round(v) + 'px', (v) => { d.fontSize = v; });
    this._bindRange('dialog-speed', 'dialog-speed-val', (v) => Math.round(v) + 'ms', (v) => { d.speed = v; });
    this._bindSelect('dialog-style', (v) => { d.style = v; });
  }
}
