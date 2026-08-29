"""Editorial Index — an independent UI theme for Anki Desktop."""

from __future__ import annotations

import json
import re
from typing import Any

from aqt import gui_hooks, mw
from aqt.qt import QAction, qconnect

from .native_theme import apply_native_theme


DEFAULT_CONFIG: dict[str, Any] = {
    "enabled": True,
    "accent_color": "#315FC4",
    "style_native_chrome": True,
    "style_reviewer": True,
    "animations": True,
    "frosted_toolbar": False,
}

LEGACY_DEFAULT_ACCENT = "#18A6B8"

CONTEXT_NAMES = {
    "DeckBrowser": "deck-browser",
    "Overview": "overview",
    "Reviewer": "reviewer",
    "TopToolbar": "top-toolbar",
    "DeckBrowserBottomBar": "standard-bottom-bar",
    "OverviewBottomBar": "standard-bottom-bar",
    "ReviewerBottomBar": "reviewer-bottom-bar",
}

_HEX_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")
_menu_action: QAction | None = None


def _get_config() -> dict[str, Any]:
    stored = mw.addonManager.getConfig(__name__) or {}
    config = {**DEFAULT_CONFIG, **stored}

    accent = str(config.get("accent_color", DEFAULT_CONFIG["accent_color"]))
    if not _HEX_COLOR.fullmatch(accent):
        accent = DEFAULT_CONFIG["accent_color"]
    elif accent.upper() == LEGACY_DEFAULT_ACCENT:
        # Preserve custom colors, but migrate the previous theme's untouched
        # default so an in-place upgrade receives Editorial Index blue.
        accent = DEFAULT_CONFIG["accent_color"]

    return {
        "enabled": bool(config.get("enabled", True)),
        "accent_color": accent.upper(),
        "style_native_chrome": bool(config.get("style_native_chrome", True)),
        "style_reviewer": bool(config.get("style_reviewer", True)),
        "animations": bool(config.get("animations", True)),
        "frosted_toolbar": bool(config.get("frosted_toolbar", False)),
    }


def _context_name(context: object | None) -> str | None:
    if context is None:
        return None
    return CONTEXT_NAMES.get(type(context).__name__)


def _inject_theme(web_content: Any, context: object | None) -> None:
    config = _get_config()
    if not config["enabled"]:
        return

    context_name = _context_name(context)
    if context_name is None:
        return
    if context_name in {"reviewer", "reviewer-bottom-bar"} and not config["style_reviewer"]:
        return

    package = mw.addonManager.addon_from_module(__name__)
    web_content.css.append(f"/_addons/{package}/web/theme.css")

    settings = {
        "context": context_name,
        "motion": "on" if config["animations"] else "off",
        "glass": "on" if config["frosted_toolbar"] else "off",
    }
    settings_json = json.dumps(settings, ensure_ascii=True)
    accent = config["accent_color"]

    # The marker lives on <html>, because Reviewer replaces body.className on
    # every card. Values are JSON-encoded and the accent is allow-listed above.
    web_content.head += f"""
<style>:root {{ --mist-user-accent: {accent}; }}</style>
<script>
(() => {{
  const settings = {settings_json};
  const root = document.documentElement;
    root.dataset.mistlineContext = settings.context;
    root.dataset.mistlineMotion = settings.motion;
    root.dataset.mistlineGlass = settings.glass;
    root.dataset.mistlineFonts = "loading";
    const verifyFonts = async () => {{
      await document.fonts.ready;
      const [sans, serif] = await Promise.all([
        document.fonts.load('400 16px "Mist Inter"'),
        document.fonts.load('600 32px "Mist Source Serif"'),
      ]);
      root.dataset.mistlineFonts = sans.length && serif.length ? "ready" : "fallback";
    }};
    requestAnimationFrame(() => void verifyFonts());
}})();
</script>
"""


def _decorate_deck_browser(_deck_browser: Any, content: Any) -> None:
    """Add one owned heading without replacing Anki's deck tree."""

    if not _get_config()["enabled"]:
        return

    marker = 'data-mistline-owned="deck-heading"'
    if marker in content.tree:
        return
    heading = f"""
<section class="mistline-deck-heading" {marker}>
  <h1>Deck Home</h1>
  <p>Memory index</p>
</section>
"""
    content.tree = f"{heading}{content.tree}"


def _refresh_main_screen() -> None:
    if mw.col is None:
        return
    try:
        mw.reset()
    except Exception:
        # A refresh is cosmetic. Do not block Anki if a future release changes
        # the reset lifecycle; the theme will apply on the next navigation.
        pass


def _inject_external_style(webview: Any) -> None:
    """Apply a light, DOM-agnostic layer to Anki's Congratulations page."""

    config = _get_config()
    if not config["enabled"]:
        return

    try:
        path = webview.url().path().lower()
    except Exception:
        return
    if "congrats" not in path:
        return

    package = mw.addonManager.addon_from_module(__name__)
    href = f"/_addons/{package}/web/theme.css"
    payload = {
        "href": href,
        "accent": config["accent_color"],
        "motion": "on" if config["animations"] else "off",
    }
    payload_json = json.dumps(payload, ensure_ascii=True)
    webview.eval(
        f"""
(() => {{
  const settings = {payload_json};
  const root = document.documentElement;
  root.dataset.mistlineContext = "congrats";
  root.dataset.mistlineMotion = settings.motion;
  root.style.setProperty("--mist-user-accent", settings.accent);
  if (!document.getElementById("mistline-external-theme")) {{
    const link = document.createElement("link");
    link.id = "mistline-external-theme";
    link.rel = "stylesheet";
    link.href = settings.href;
    document.head.appendChild(link);
  }}
}})();
"""
    )


def _sync_menu_action() -> None:
    if _menu_action is not None:
        _menu_action.setChecked(_get_config()["enabled"])


def _apply_current_native_theme() -> None:
    apply_native_theme(mw, _get_config())


def _toggle_theme(checked: bool) -> None:
    config = _get_config()
    config["enabled"] = bool(checked)
    mw.addonManager.writeConfig(__name__, config)
    _apply_current_native_theme()
    _refresh_main_screen()


def _setup_menu() -> None:
    global _menu_action
    if _menu_action is not None:
        return

    action = QAction("Editorial Index 主题", mw)
    action.setCheckable(True)
    action.setChecked(_get_config()["enabled"])
    qconnect(action.triggered, _toggle_theme)
    mw.form.menuTools.addSeparator()
    mw.form.menuTools.addAction(action)
    _menu_action = action
    _apply_current_native_theme()


def _config_updated(_new_config: Any) -> None:
    _sync_menu_action()
    _apply_current_native_theme()
    _refresh_main_screen()


mw.addonManager.setWebExports(__name__, r"^web/(?:theme\.css|fonts/.*\.(?:woff2|ttf|txt|md))$")
mw.addonManager.setConfigUpdatedAction(__name__, _config_updated)

gui_hooks.webview_will_set_content.append(_inject_theme)
gui_hooks.deck_browser_will_render_content.append(_decorate_deck_browser)
gui_hooks.webview_did_inject_style_into_page.append(_inject_external_style)
gui_hooks.main_window_did_init.append(_setup_menu)
gui_hooks.theme_did_change.append(_apply_current_native_theme)
