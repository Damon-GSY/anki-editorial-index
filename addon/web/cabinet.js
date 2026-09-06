// Select a visible folder locally; actual deck operations remain Anki commands.
(() => {
  'use strict';
  const root = document.documentElement;
  const updatePaletteBadge = () => {
    const button = document.querySelector('.cabinet-palette');
    if (!button) return;
    const flavor = root.dataset.mistlinePalette || '';
    const label = root.dataset.mistlineFamily === 'catppuccin'
      ? flavor.charAt(0).toUpperCase() + flavor.slice(1) : '暖纸';
    button.querySelector('.cabinet-palette-current').textContent = label;
    const accent = root.dataset.mistlineAccent || '';
    const color = getComputedStyle(root).getPropertyValue('--mist-user-accent').trim();
    button.title = `配色 · 当前 ${label} · ${accent} ${color}`;
    button.setAttribute('aria-label', '打开调色板，当前配色 ' + label + '，' + accent);
  };
  updatePaletteBadge();
  new MutationObserver(updatePaletteBadge).observe(root, {
    attributes: true, attributeFilter: ['data-mistline-palette', 'data-mistline-family', 'data-mistline-accent', 'style'],
  });
  const focusKey = 'editorial-cabinet-pending-focus';
  // Anki rebuilds the deck page after saving. Restore the triggering control,
  // keeping its position in view; display preferences themselves live in Python.
  try {
    const pending = JSON.parse(sessionStorage.getItem(focusKey) || 'null');
    sessionStorage.removeItem(focusKey);
    if (pending && /^(fold:\d+|fold-all|unfold-all)$/.test(pending.action) && Number.isFinite(pending.top)) {
      requestAnimationFrame(() => requestAnimationFrame(() => {
        const control = document.querySelector('[data-cabinet-display="' + pending.action + '"]');
        if (!control) return;
        control.focus({preventScroll: true});
        window.scrollBy(0, control.getBoundingClientRect().top - pending.top);
      }));
    }
  } catch (_) { /* Storage is optional; the controls still work without it. */ }
  document.addEventListener('click', event => {
    const display = event.target.closest('[data-cabinet-display]');
    if (display) {
      event.preventDefault();
      const action = display.dataset.cabinetDisplay;
      if (!display.disabled && /^(fold:\d+|fold-all|unfold-all|settings|palette)$/.test(action)) {
        if (action !== 'settings' && action !== 'palette') {
          try {
            sessionStorage.setItem(focusKey, JSON.stringify({action, top: display.getBoundingClientRect().top}));
          } catch (_) { /* A blocked WebView store must not block the action. */ }
        }
        pycmd('editorial-cabinet:' + action);
      }
      return;
    }
    // Preserve Anki's Shift-click selection without starting a review.
    if (event.shiftKey) {
      const deck = event.target.closest('[data-cabinet-deck-id]');
      const id = deck?.dataset.cabinetDeckId;
      if (id && /^\d+$/.test(id)) {
        event.preventDefault();
        pycmd('select:' + id);
        return;
      }
    }
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
