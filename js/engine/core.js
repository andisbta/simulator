/**
 * Block Engine — Core
 * Main game loop, canvas management, and state.
 */

export class Engine {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.running = false;
    this.lastTime = 0;
    this.fps = 0;
    this.frameCount = 0;
    this.fpsTimer = 0;
    this.zoom = 1;

    // Scene config
    this.scene = {
      bg: '#0a0a0f',
      grid: true,
      gridSize: 32,
      gridColor: '#1a1a25',
      width: 800,
      height: 500,
    };

    // Entities
    this.entities = [];

    // Mouse tracking
    this.mouse = { x: 0, y: 0 };

    this._bindMouse();
    this.resize();
  }

  resize() {
    this.canvas.width = this.scene.width;
    this.canvas.height = this.scene.height;
  }

  _bindMouse() {
    this.canvas.addEventListener('mousemove', (e) => {
      const rect = this.canvas.getBoundingClientRect();
      const scaleX = this.canvas.width / rect.width;
      const scaleY = this.canvas.height / rect.height;
      this.mouse.x = Math.round((e.clientX - rect.left) * scaleX);
      this.mouse.y = Math.round((e.clientY - rect.top) * scaleY);
    });
  }

  start() {
    if (this.running) return;
    this.running = true;
    this.lastTime = performance.now();
    this._loop(this.lastTime);
  }

  stop() {
    this.running = false;
  }

  _loop(now) {
    if (!this.running) return;

    const dt = Math.min((now - this.lastTime) / 1000, 0.05);
    this.lastTime = now;

    // FPS counter
    this.frameCount++;
    this.fpsTimer += dt;
    if (this.fpsTimer >= 0.5) {
      this.fps = Math.round(this.frameCount / this.fpsTimer);
      this.frameCount = 0;
      this.fpsTimer = 0;
      if (this.onFpsUpdate) this.onFpsUpdate(this.fps);
    }

    this.update(dt);
    this.render();

    requestAnimationFrame((t) => this._loop(t));
  }

  update(dt) {
    for (const entity of this.entities) {
      if (entity.update) entity.update(dt);
    }
  }

  render() {
    const { ctx, canvas } = this;
    const { bg, grid, gridSize, gridColor } = this.scene;

    // Clear
    ctx.fillStyle = bg;
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Grid
    if (grid) {
      ctx.strokeStyle = gridColor;
      ctx.lineWidth = 0.5;
      ctx.beginPath();
      for (let x = gridSize; x < canvas.width; x += gridSize) {
        ctx.moveTo(x + 0.5, 0);
        ctx.lineTo(x + 0.5, canvas.height);
      }
      for (let y = gridSize; y < canvas.height; y += gridSize) {
        ctx.moveTo(0, y + 0.5);
        ctx.lineTo(canvas.width, y + 0.5);
      }
      ctx.stroke();
    }

    // Entities sorted by layer
    const sorted = [...this.entities].sort((a, b) => (a.layer || 0) - (b.layer || 0));
    for (const entity of sorted) {
      if (entity.render) entity.render(ctx);
    }
  }
}
