const sideButtons = document.querySelectorAll('[data-side-target]');
const previewSides = document.querySelectorAll('[data-preview-side]');
const themeToggle = document.querySelector('#theme-toggle');

function showSide(side) {
  sideButtons.forEach((button) => {
    const active = button.dataset.sideTarget === side;
    button.classList.toggle('is-active', active);
    button.setAttribute('aria-pressed', String(active));
  });

  previewSides.forEach((panel) => {
    panel.hidden = panel.dataset.previewSide !== side;
  });
}

sideButtons.forEach((button) => {
  button.addEventListener('click', () => showSide(button.dataset.sideTarget));
});

themeToggle.addEventListener('click', () => {
  const dark = document.documentElement.dataset.theme !== 'dark';
  document.documentElement.dataset.theme = dark ? 'dark' : 'light';
  themeToggle.setAttribute('aria-pressed', String(dark));
  themeToggle.textContent = dark ? '切换浅色' : '切换深色';
});

document.addEventListener('keydown', (event) => {
  if (event.code === 'Space' && event.target === document.body) {
    event.preventDefault();
    const backVisible = !document.querySelector('[data-preview-side="back"]').hidden;
    showSide(backVisible ? 'front' : 'back');
  }
});
