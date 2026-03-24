/**
 * Block Engine — Procedural Asset Generator
 * Generates consistent-style shapes from parameters.
 */

export class AssetGenerator {
  constructor() {
    this.config = {
      shape: 'rect',
      size: 32,
      fill: '#4a9eff',
      stroke: true,
      strokeColor: '#e8e8e8',
      strokeWidth: 1,
      opacity: 1,
      seed: 42,
    };
  }

  /**
   * Draw a generated asset at position (x, y) on a canvas context.
   */
  draw(ctx, x, y, overrides = {}) {
    const c = { ...this.config, ...overrides };
    const half = c.size / 2;

    ctx.save();
    ctx.globalAlpha = c.opacity;
    ctx.translate(x, y);

    ctx.fillStyle = c.fill;
    ctx.strokeStyle = c.strokeColor;
    ctx.lineWidth = c.strokeWidth;

    ctx.beginPath();

    switch (c.shape) {
      case 'rect':
        ctx.rect(-half, -half, c.size, c.size);
        break;

      case 'circle':
        ctx.arc(0, 0, half, 0, Math.PI * 2);
        break;

      case 'triangle':
        ctx.moveTo(0, -half);
        ctx.lineTo(half, half);
        ctx.lineTo(-half, half);
        ctx.closePath();
        break;

      case 'diamond':
        ctx.moveTo(0, -half);
        ctx.lineTo(half, 0);
        ctx.lineTo(0, half);
        ctx.lineTo(-half, 0);
        ctx.closePath();
        break;

      case 'hexagon':
        for (let i = 0; i < 6; i++) {
          const angle = (Math.PI / 3) * i - Math.PI / 2;
          const px = Math.cos(angle) * half;
          const py = Math.sin(angle) * half;
          if (i === 0) ctx.moveTo(px, py);
          else ctx.lineTo(px, py);
        }
        ctx.closePath();
        break;

      case 'star': {
        const spikes = 5;
        const outerR = half;
        const innerR = half * 0.4;
        for (let i = 0; i < spikes * 2; i++) {
          const r = i % 2 === 0 ? outerR : innerR;
          const angle = (Math.PI / spikes) * i - Math.PI / 2;
          const px = Math.cos(angle) * r;
          const py = Math.sin(angle) * r;
          if (i === 0) ctx.moveTo(px, py);
          else ctx.lineTo(px, py);
        }
        ctx.closePath();
        break;
      }
    }

    ctx.fill();
    if (c.stroke && c.strokeWidth > 0) {
      ctx.stroke();
    }

    ctx.restore();
  }

  /**
   * Render a preview into a small canvas element.
   */
  renderPreview(canvas) {
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    this.draw(ctx, canvas.width / 2, canvas.height / 2);
  }
}
