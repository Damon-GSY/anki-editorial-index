(() => {
  const current = document.currentScript;
  if (!current) {
    return;
  }

  const settings = new URL(current.src).searchParams;
  const root = document.documentElement;
  const tokenNames = new Set([
    "--mist-user-accent",
    "--mist-accent-fill",
    "--mist-accent",
    "--mist-focus",
    "--mist-accent-hover",
    "--mist-accent-pressed",
    "--mist-accent-soft",
    "--mist-on-accent",
    "--mist-paper",
    "--mist-paper-light",
    "--mist-paper-deep",
    "--mist-paper-field",
    "--mist-field",
    "--mist-ink",
    "--mist-muted",
    "--mist-faint",
    "--mist-rule",
    "--mist-rule-strong",
    "--mist-disabled",
    "--mist-danger-fill",
    "--mist-danger",
    "--mist-on-danger",
    "--mist-new",
    "--mist-learn",
    "--mist-due",
    "--mist-good",
    "--mist-easy",
    "--editorial-user-accent",
    "--editorial-accent-fill",
    "--editorial-accent",
    "--editorial-focus",
    "--editorial-accent-hover",
    "--editorial-accent-pressed",
    "--editorial-soft-accent",
    "--editorial-on-accent",
    "--editorial-paper",
    "--editorial-surface",
    "--editorial-field",
    "--editorial-raised",
    "--editorial-ink",
    "--editorial-muted",
    "--editorial-disabled",
    "--editorial-rule",
    "--editorial-rule-strong",
  ]);
  const valuePattern = /^#[0-9a-f]{6}$/i;
  const encodedTokens = settings.get("tokens") || "";

  if (encodedTokens && encodedTokens.length <= 16384) {
    try {
      const base64 = encodedTokens.replace(/-/g, "+").replace(/_/g, "/");
      const padded = base64.padEnd(
        base64.length + ((4 - (base64.length % 4)) % 4),
        "=",
      );
      const tokens = JSON.parse(atob(padded));
      if (tokens && typeof tokens === "object" && !Array.isArray(tokens)) {
        for (const [name, value] of Object.entries(tokens)) {
          if (
            tokenNames.has(name) &&
            typeof value === "string" &&
            (valuePattern.test(value) || value === "none")
          ) {
            root.style.setProperty(name, value);
          }
        }
      }
    } catch (_error) {
      // A malformed payload must never prevent Anki's editor from loading.
    }
  }

  const families = new Set(["editorial", "catppuccin"]);
  const flavors = new Set([
    "editorial-light",
    "editorial-dark",
    "latte",
    "frappe",
    "macchiato",
    "mocha",
  ]);
  const family = settings.get("family") || "";
  const flavor = settings.get("flavor") || "";
  if (families.has(family)) {
    root.dataset.mistlineFamily = family;
    root.dataset.editorialFamily = family;
  }
  if (flavors.has(flavor)) {
    root.dataset.mistlinePalette = flavor;
    root.dataset.editorialFlavor = flavor;
  }
  const tone = settings.get("tone") || "";
  if (tone === "light" || tone === "dark") {
    root.dataset.mistlineTone = tone;
    root.dataset.editorialTone = tone;
    root.style.colorScheme = tone;
    root.dataset.mistlineOwnsColorScheme = "true";
  }
  const accents = new Set([
    "custom",
    "rosewater",
    "flamingo",
    "pink",
    "mauve",
    "red",
    "maroon",
    "peach",
    "yellow",
    "green",
    "teal",
    "sky",
    "sapphire",
    "blue",
    "lavender",
  ]);
  const accent = settings.get("accent") || "";
  if (accents.has(accent)) {
    root.dataset.mistlineAccent = accent;
    root.dataset.editorialAccent = accent;
  }
  const motion = settings.get("motion") === "off" ? "off" : "on";
  root.dataset.mistlineContext = "editor";
  root.dataset.mistlineMotion = motion;
  root.dataset.mistlineEnabled = "on";
})();
