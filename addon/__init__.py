"""Editorial Index — an independent UI theme for Anki Desktop."""

from __future__ import annotations

import json
import re
from typing import Any

from aqt import gui_hooks, mw
from aqt.qt import QAction, QDialogButtonBox, qconnect

from .native_theme import apply_native_theme, extend_native_style


DEFAULT_CONFIG: dict[str, Any] = {
    "enabled": True,
    "accent_color": "#2F5BBC",
    "style_native_chrome": True,
    "style_reviewer": True,
    "animations": True,
    "frosted_toolbar": False,
}

LEGACY_DEFAULT_ACCENTS = {"#18A6B8", "#315FC4"}

CONTEXT_NAMES = {
    "DeckBrowser": "deck-browser",
    "Overview": "overview",
    "Reviewer": "reviewer",
    "TopToolbar": "top-toolbar",
    "DeckBrowserBottomBar": "standard-bottom-bar",
    "OverviewBottomBar": "standard-bottom-bar",
    "ReviewerBottomBar": "reviewer-bottom-bar",
    "Editor": "editor",
    "NewDeckStats": "stats",
    "DeckStats": "stats",
    "FindDuplicatesDialog": "native-page",
    "EmptyCards": "native-page",
}

EXTERNAL_PAGE_CONTEXTS = (
    ("deck-options/", "deck-options"),
    ("graphs", "stats"),
    ("card-info/", "native-page"),
    ("change-notetype/", "native-page"),
    ("import-page/", "native-page"),
    ("import-csv/", "native-page"),
    ("import-anki-package/", "native-page"),
    ("image-occlusion/", "native-page"),
    ("congrats", "congrats"),
)

WEBVIEW_KIND_CONTEXTS = {
    "DECK_OPTIONS": "deck-options",
    "DECK_STATS": "stats",
    "LEGACY_DECK_STATS": "stats",
    "CHANGE_NOTETYPE": "native-page",
    "BROWSER_CARD_INFO": "native-page",
    "IMPORT_CSV": "native-page",
    "IMPORT_ANKI_PACKAGE": "native-page",
    "IMPORT_LOG": "native-page",
    "EMPTY_CARDS": "native-page",
    "FIND_DUPLICATES": "native-page",
    "FIELDS": "native-page",
}

STANDALONE_WEB_CONTEXTS = {"editor", "stats", "deck-options", "native-page"}

_HEX_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")
_menu_action: QAction | None = None


def _get_config() -> dict[str, Any]:
    stored = mw.addonManager.getConfig(__name__) or {}
    config = {**DEFAULT_CONFIG, **stored}

    accent = str(config.get("accent_color", DEFAULT_CONFIG["accent_color"]))
    if not _HEX_COLOR.fullmatch(accent):
        accent = DEFAULT_CONFIG["accent_color"]
    elif accent.upper() in LEGACY_DEFAULT_ACCENTS:
        # Preserve custom colors, but migrate untouched defaults from earlier
        # releases so an in-place upgrade receives the accessible editor blue.
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
    if (
        context_name in STANDALONE_WEB_CONTEXTS
        and not config["style_native_chrome"]
    ):
        return
    if context_name in {"reviewer", "reviewer-bottom-bar"} and not config["style_reviewer"]:
        return

    package = mw.addonManager.addon_from_module(__name__)
    if context_name == "editor":
        # Editor pages enforce a CSP that blocks inline marker scripts. Keep
        # their chrome in a dedicated stylesheet and pass only validated,
        # cosmetic settings to a local external script.
        web_content.css.append(f"/_addons/{package}/web/editor.css")
        accent = config["accent_color"].lstrip("#")
        motion = "on" if config["animations"] else "off"
        web_content.js.append(
            f"/_addons/{package}/web/editor-marker.js?accent={accent}&motion={motion}"
        )
        return

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


def _external_page_context(path: str) -> str | None:
    for fragment, context_name in EXTERNAL_PAGE_CONTEXTS:
        if fragment in path:
            return context_name
    return None


def _webview_kind_context(webview: Any) -> str | None:
    kind = getattr(webview, "kind", None)
    kind_name = getattr(kind, "name", None)
    if isinstance(kind_name, str):
        return WEBVIEW_KIND_CONTEXTS.get(kind_name)
    return None


def _inject_external_style(webview: Any) -> None:
    """Theme Anki-owned Svelte pages that live in standalone windows."""

    config = _get_config()
    if not config["enabled"]:
        return

    context_name = _webview_kind_context(webview)
    try:
        path = webview.url().path().lower()
    except Exception:
        path = ""
    if context_name is None:
        context_name = _external_page_context(path)
    if context_name is None:
        return
    if (
        context_name in STANDALONE_WEB_CONTEXTS
        and not config["style_native_chrome"]
    ):
        return

    package = mw.addonManager.addon_from_module(__name__)
    href = f"/_addons/{package}/web/theme.css"
    payload = {
        "href": href,
        "accent": config["accent_color"],
        "motion": "on" if config["animations"] else "off",
        "context": context_name,
    }
    payload_json = json.dumps(payload, ensure_ascii=True)
    webview.eval(
        f"""
(() => {{
  const settings = {payload_json};
  const root = document.documentElement;
  root.dataset.mistlineContext = settings.context;
  root.dataset.mistlineMotion = settings.motion;
  root.style.setProperty("--mist-user-accent", settings.accent);
  if (!document.getElementById("mistline-external-theme")) {{
    const link = document.createElement("link");
    link.id = "mistline-external-theme";
    link.rel = "stylesheet";
    link.href = settings.href;
    document.head.appendChild(link);
  }}
  const keepThemeLast = () => {{
    const link = document.getElementById("mistline-external-theme");
    const styles = document.head.querySelectorAll('link[rel="stylesheet"], style');
    if (link && styles.length && styles[styles.length - 1] !== link) {{
      document.head.appendChild(link);
    }}
  }};
  if (!root._mistlineThemeOrderObserver) {{
    let orderQueued = false;
    root._mistlineThemeOrderObserver = new MutationObserver(() => {{
      if (orderQueued) return;
      orderQueued = true;
      queueMicrotask(() => {{
        orderQueued = false;
        keepThemeLast();
      }});
    }});
    root._mistlineThemeOrderObserver.observe(document.head, {{ childList: true }});
  }}
  keepThemeLast();
  requestAnimationFrame(keepThemeLast);
  setTimeout(keepThemeLast, 250);
}})();
"""
    )


def _sync_menu_action() -> None:
    if _menu_action is not None:
        _menu_action.setChecked(_get_config()["enabled"])


def _apply_current_native_theme() -> None:
    apply_native_theme(mw, _get_config())


def _set_mistline_role(widget: Any, role: str) -> None:
    """Attach visual semantics without changing a control's Qt behaviour."""

    if widget is None or widget.property("mistlineRole") == role:
        return
    widget.setProperty("mistlineRole", role)
    try:
        style = widget.style()
        style.unpolish(widget)
        style.polish(widget)
        widget.update()
    except Exception:
        # The property is set before first show in normal operation. A future
        # Qt wrapper that cannot be repolished will still pick it up on show.
        pass


def _style_add_cards(add_cards: Any) -> None:
    """Complete Add's hierarchy while preserving shortcuts and default roles."""

    config = _get_config()
    if not config["enabled"] or not config["style_native_chrome"]:
        return

    _set_mistline_role(add_cards.addButton, "primary")
    _set_mistline_role(add_cards.historyButton, "quiet")
    _set_mistline_role(add_cards.helpButton, "quiet")
    _set_mistline_role(add_cards.closeButton, "secondary")
    _set_mistline_role(add_cards.form.buttonBox, "actionbar")
    _set_mistline_role(add_cards.notetype_chooser.button, "chooser")
    _set_mistline_role(add_cards.deck_chooser.deck, "chooser")
    _set_mistline_role(getattr(add_cards.notetype_chooser, "label", None), "fieldLabel")
    _set_mistline_role(getattr(add_cards.deck_chooser, "deckLabel", None), "fieldLabel")
    _set_mistline_role(add_cards.form.fieldsArea, "editorCanvas")

    # One spacing scale owns the native frame around the WebView. The editor
    # stylesheet owns everything inside the WebView itself.
    add_cards.form.verticalLayout_3.setContentsMargins(16, 10, 16, 14)
    add_cards.form.verticalLayout_3.setSpacing(12)
    add_cards.form.horizontalLayout.setSpacing(12)
    add_cards.notetype_chooser.setSpacing(8)
    add_cards.deck_chooser.setSpacing(8)
    button_layout = add_cards.form.buttonBox.layout()
    if button_layout is not None:
        button_layout.setSpacing(8)


def _style_managed_dialog(
    _dialog_manager: Any, dialog_name: str, dialog_instance: Any
) -> None:
    """Give managed dialogs semantic actions without reordering Qt buttons."""

    config = _get_config()
    if not config["enabled"] or not config["style_native_chrome"]:
        return
    if dialog_name == "AddCards":
        _style_add_cards(dialog_instance)
        return

    roles = QDialogButtonBox.ButtonRole
    primary_roles = {roles.AcceptRole, roles.YesRole, roles.ApplyRole}
    destructive_roles = {roles.DestructiveRole}
    for button_box in dialog_instance.findChildren(QDialogButtonBox):
        _set_mistline_role(button_box, "actionbar")
        for button in button_box.buttons():
            button_role = button_box.buttonRole(button)
            if button.isDefault() or button_role in primary_roles:
                role = "primary"
            elif button_role in destructive_roles:
                role = "destructive"
            else:
                role = "secondary"
            _set_mistline_role(button, role)


def _style_browser(browser: Any) -> None:
    """Expose stable names for Browser surfaces that have local Qt styles."""

    config = _get_config()
    if not config["enabled"] or not config["style_native_chrome"]:
        return
    browser.sidebar.setObjectName("mistlineSidebarTree")
    browser.sidebar.searchBar.setObjectName("mistlineSidebarSearch")
    browser.sidebar.toolbar.setObjectName("mistlineSidebarToolbar")
    browser.form.searchEdit.setObjectName("searchEdit")
    browser.form.tableView.setObjectName("tableView")


def _style_card_layout(card_layout: Any) -> None:
    """Give Card Layout a clear action hierarchy without touching previews."""

    config = _get_config()
    if not config["enabled"] or not config["style_native_chrome"]:
        return

    layout = getattr(card_layout, "buttons", None)
    if layout is None:
        return
    widgets = []
    for index in range(layout.count()):
        item = layout.itemAt(index)
        widget = item.widget() if item is not None else None
        if widget is not None:
            widgets.append(widget)
    if len(widgets) < 4:
        return

    _set_mistline_role(widgets[0], "quiet")
    for widget in widgets[1:-2]:
        _set_mistline_role(widget, "secondary")
    _set_mistline_role(widgets[-2], "primary")
    _set_mistline_role(widgets[-1], "secondary")
    layout.setSpacing(8)


def _extend_anki_style(style: str) -> str:
    """Official Anki style filter used after theme/widget-style changes."""

    return extend_native_style(style, _get_config())


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


mw.addonManager.setWebExports(
    __name__,
    r"^web/(?:theme\.css|editor\.css|editor-marker\.js|fonts/.*\.(?:woff2|ttf|txt|md))$",
)
mw.addonManager.setConfigUpdatedAction(__name__, _config_updated)

gui_hooks.webview_will_set_content.append(_inject_theme)
gui_hooks.deck_browser_will_render_content.append(_decorate_deck_browser)
gui_hooks.webview_did_inject_style_into_page.append(_inject_external_style)
gui_hooks.style_did_init.append(_extend_anki_style)
gui_hooks.add_cards_did_init.append(_style_add_cards)
gui_hooks.dialog_manager_did_open_dialog.append(_style_managed_dialog)
gui_hooks.browser_will_show.append(_style_browser)
gui_hooks.card_layout_will_show.append(_style_card_layout)
gui_hooks.theme_did_change.append(_apply_current_native_theme)
gui_hooks.main_window_did_init.append(_setup_menu)
