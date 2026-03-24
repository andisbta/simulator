/**
 * Block Engine — Block Manager
 * Handles sidebar navigation and block panel switching.
 */

export class BlockManager {
  constructor() {
    this.tabs = document.querySelectorAll('.block-tab');
    this.panels = document.querySelectorAll('.block-content');
    this.activeBlock = 'scene';

    this._bind();
  }

  _bind() {
    this.tabs.forEach((tab) => {
      tab.addEventListener('click', () => {
        this.setActive(tab.dataset.block);
      });
    });
  }

  setActive(blockName) {
    this.activeBlock = blockName;

    this.tabs.forEach((tab) => {
      tab.classList.toggle('active', tab.dataset.block === blockName);
    });

    this.panels.forEach((panel) => {
      panel.classList.toggle('active', panel.dataset.block === blockName);
    });
  }
}
