/**
 * Block Engine — Entity
 * Represents a game object with position, asset, and optional behaviors.
 */

let entityIdCounter = 0;

export class Entity {
  constructor(name, assetGenerator) {
    this.id = 'entity_' + (entityIdCounter++);
    this.name = name;
    this.x = 400;
    this.y = 250;
    this.layer = 1;
    this.tag = 'player';
    this.asset = assetGenerator;
    this.assetOverrides = {};

    // Animation state
    this.animTime = 0;
    this.animation = {
      idle: 'pulse',
      speed: 1,
      easing: 'ease-out',
      loop: true,
    };
  }

  update(dt) {
    this.animTime += dt * this.animation.speed;
  }

  render(ctx) {
    ctx.save();

    // Apply idle animation
    let scale = 1;
    let offsetY = 0;
    const t = this.animTime;

    switch (this.animation.idle) {
      case 'pulse': {
        scale = 1 + Math.sin(t * 3) * 0.05;
        break;
      }
      case 'breathe': {
        scale = 1 + Math.sin(t * 2) * 0.08;
        break;
      }
      case 'float': {
        offsetY = Math.sin(t * 2) * 4;
        break;
      }
      case 'rotate': {
        ctx.translate(this.x, this.y + offsetY);
        ctx.rotate(t * 2);
        ctx.scale(scale, scale);
        this.asset.draw(ctx, 0, 0, this.assetOverrides);
        ctx.restore();
        return;
      }
    }

    ctx.translate(this.x, this.y + offsetY);
    ctx.scale(scale, scale);
    this.asset.draw(ctx, 0, 0, this.assetOverrides);

    ctx.restore();
  }
}
