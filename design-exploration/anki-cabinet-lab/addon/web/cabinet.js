// Select a visible folder locally; actual deck operations remain Anki commands.
(() => {
  'use strict';
  document.addEventListener('click', event => {
    const select = event.target.closest('[data-cabinet-select]');
    if (select) {
      const id = select.dataset.cabinetSelect;
      if (!/^\d+$/.test(id)) return;
      document.querySelectorAll('.cabinet-folder').forEach(folder => {
        const active = folder.dataset.cabinetDeckId === id;
        folder.classList.toggle('selected', active);
        folder.querySelector('.cabinet-tab')?.setAttribute('aria-pressed', String(active));
      });
      return;
    }
    const command = event.target.closest('[data-cabinet-command]');
    if (!command) return;
    event.preventDefault();
    const value = command.dataset.cabinetCommand;
    if (/^(open|opts|collapse):\d+$/.test(value) || ['create', 'import'].includes(value)) {
      pycmd(value);
    }
  });
})();
