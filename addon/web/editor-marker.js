(() => {
  const current = document.currentScript;
  if (!current) {
    return;
  }

  const settings = new URL(current.src).searchParams;
  const accent = settings.get("accent") || "";
  if (/^[0-9a-f]{6}$/i.test(accent)) {
    document.documentElement.style.setProperty("--editorial-user-accent", `#${accent}`);
  }
  document.documentElement.dataset.editorialMotion =
    settings.get("motion") === "off" ? "off" : "on";
})();
