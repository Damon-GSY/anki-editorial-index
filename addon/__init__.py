"""Editorial Index — an independent UI theme for Anki Desktop."""

from __future__ import annotations

import base64
import json
import re
import weakref
from typing import Any

from aqt import gui_hooks, mw
from aqt.qt import (
    QAction,
    QActionGroup,
    QApplication,
    QDialogButtonBox,
    QMenu,
    qconnect,
)
from aqt.theme import theme_manager

from .color_themes import (
    CATPPUCCIN_ACCENTS,
    CATPPUCCIN_FLAVOR_OPTIONS,
    MANAGED_COLOR_VARIABLES,
    catppuccin_palette,
    normalize_catppuccin_accent,
    normalize_catppuccin_flavor,
    normalize_color_theme,
    resolve_color_tokens,
    web_color_variables,
)
from .native_theme import apply_native_theme, extend_native_style
from . import cabinet, cabinet_display


DEFAULT_CONFIG: dict[str, Any] = {
    "enabled": True,
    "layout": "editorial",
    "cabinet_display": {},
    "accent_color": "#2F5BBC",
    "color_theme": "editorial",
    "catppuccin_flavor": "auto",
    "catppuccin_accent": "blue",
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
    "EmptyCardsDialog": "native-page",
}

EXTERNAL_PAGE_CONTEXTS = {
    "deck-options": "deck-options",
    "graphs": "stats",
    "card-info": "native-page",
    "change-notetype": "native-page",
    "import-page": "native-page",
    "import-csv": "native-page",
    "import-anki-package": "native-page",
    "image-occlusion": "native-page",
    "congrats": "congrats",
}

WEBVIEW_KIND_CONTEXTS = {
    "EDITOR": "editor",
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
_palette_dialog_action: QAction | None = None
_palette_dialog_ref: weakref.ReferenceType[Any] | None = None
_palette_menu: QMenu | None = None
_accent_menu: QMenu | None = None
_palette_group: QActionGroup | None = None
_accent_group: QActionGroup | None = None
_palette_actions: dict[str, QAction] = {}
_accent_actions: dict[str, QAction] = {}
_layout_actions: dict[str, QAction] = {}
_layout_group: QActionGroup | None = None
_observed_webviews: weakref.WeakSet[Any] = weakref.WeakSet()
_observed_add_cards: weakref.WeakSet[Any] = weakref.WeakSet()
_observed_managed_dialogs: weakref.WeakSet[Any] = weakref.WeakSet()
_observed_browsers: weakref.WeakSet[Any] = weakref.WeakSet()
_observed_card_layouts: weakref.WeakSet[Any] = weakref.WeakSet()
_NATIVE_STATE_ATTR = "_mistline_owned_native_state"


def _get_config() -> dict[str, Any]:
    raw_stored = mw.addonManager.getConfig(__name__)
    stored = raw_stored if isinstance(raw_stored, dict) else {}
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
        "layout": "cabinet" if config.get("layout") == "cabinet" else "editorial",
        "cabinet_display": config.get("cabinet_display") if isinstance(config.get("cabinet_display"), dict) else {},
        "accent_color": accent.upper(),
        "color_theme": normalize_color_theme(config.get("color_theme")),
        "catppuccin_flavor": normalize_catppuccin_flavor(
            config.get("catppuccin_flavor")
        ),
        "catppuccin_accent": normalize_catppuccin_accent(
            config.get("catppuccin_accent")
        ),
        "style_native_chrome": bool(config.get("style_native_chrome", True)),
        "style_reviewer": bool(config.get("style_reviewer", True)),
        "animations": bool(config.get("animations", True)),
        "frosted_toolbar": bool(config.get("frosted_toolbar", False)),
    }


def _write_config_patch(**changes: object) -> None:
    """Persist only the values a user changed and preserve unknown settings."""

    stored = mw.addonManager.getConfig(__name__)
    raw = dict(stored) if isinstance(stored, dict) else {}
    raw.update(changes)
    mw.addonManager.writeConfig(__name__, raw)


def _system_is_dark() -> bool:
    return bool(getattr(theme_manager, "night_mode", False))


def _resolved_tokens(config: dict[str, Any] | None = None):
    return resolve_color_tokens(config or _get_config(), _system_is_dark())


def _theme_metadata(config: dict[str, Any] | None = None) -> dict[str, Any]:
    current = config or _get_config()
    tokens = _resolved_tokens(current)
    variables = web_color_variables(tokens)
    if current.get("layout") == "cabinet" and tokens.family == "catppuccin":
        variables.update({
            "--cabinet-lilac": tokens.palette["mauve"],
            "--cabinet-peach": tokens.palette["peach"],
            "--cabinet-sage": tokens.palette["green"],
        })
    return {
        "layout": current.get("layout", "editorial"),
        "family": tokens.family,
        "flavor": tokens.flavor,
        "tone": "dark" if tokens.dark else "light",
        "accentName": tokens.accent_name,
        "variables": variables,
    }


def _context_name(context: object | None) -> str | None:
    if context is None:
        return None
    context_type = type(context)
    module_name = str(getattr(context_type, "__module__", ""))
    if module_name != "aqt" and not module_name.startswith("aqt."):
        return None
    return CONTEXT_NAMES.get(context_type.__name__)


def _context_is_enabled(config: dict[str, Any], context_name: str | None) -> bool:
    if not config["enabled"]:
        return False
    if (
        context_name in STANDALONE_WEB_CONTEXTS
        and not config["style_native_chrome"]
    ):
        return False
    if (
        context_name in {"reviewer", "reviewer-bottom-bar"}
        and not config["style_reviewer"]
    ):
        return False
    return True


def _encoded_editor_tokens(variables: dict[str, str]) -> str:
    raw = json.dumps(variables, ensure_ascii=True, separators=(",", ":")).encode(
        "ascii"
    )
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _inject_theme(web_content: Any, context: object | None) -> None:
    config = _get_config()
    context_name = _context_name(context)
    if context_name is None:
        return
    if not _context_is_enabled(config, context_name):
        return

    package = mw.addonManager.addon_from_module(__name__)
    metadata = _theme_metadata(config)
    if context_name == "editor":
        # Editor pages enforce a CSP that blocks inline marker scripts. Keep
        # their chrome in a dedicated stylesheet and pass a base64url JSON
        # token bundle to a local external script. The script independently
        # allow-lists every property before applying it.
        web_content.css.append(f"/_addons/{package}/web/editor.css")
        motion = "on" if config["animations"] else "off"
        encoded = _encoded_editor_tokens(metadata["variables"])
        web_content.js.append(
            f"/_addons/{package}/web/editor-marker.js?tokens={encoded}"
            f"&family={metadata['family']}&flavor={metadata['flavor']}"
            f"&tone={metadata['tone']}&accent={metadata['accentName']}"
            f"&motion={motion}"
        )
        return

    cabinet_context = cabinet.context(config, context_name)
    stylesheet = "cabinet.css" if cabinet_context else "theme.css"
    web_content.css.append(f"/_addons/{package}/web/{stylesheet}")
    if cabinet_context == "deck":
        web_content.js.append(f"/_addons/{package}/web/cabinet.js")

    settings = {
        "context": context_name,
        "cabinetContext": cabinet_context,
        "motion": "on" if config["animations"] else "off",
        "glass": "on" if config["frosted_toolbar"] else "off",
        **metadata,
    }
    settings_json = json.dumps(settings, ensure_ascii=True)
    declarations = " ".join(
        f"{name}: {value};" for name, value in metadata["variables"].items()
    )

    # The marker lives on <html>, because Reviewer replaces body.className on
    # every card. Values come from the validated, bundled color contract.
    web_content.head += f"""
<style>:root {{ {declarations} }}</style>
<script>
(() => {{
  const settings = {settings_json};
  const root = document.documentElement;
    Object.entries(settings.variables).forEach(([name, value]) =>
      root.style.setProperty(name, value)
    );
    root.dataset.mistlineContext = settings.context;
    root.dataset.mistlineMotion = settings.motion;
    root.dataset.mistlineGlass = settings.glass;
    root.dataset.mistlineFamily = settings.family;
    root.dataset.mistlinePalette = settings.flavor;
    root.dataset.mistlineTone = settings.tone;
    root.dataset.mistlineAccent = settings.accentName;
    root.dataset.mistlineEnabled = "on";
    root.dataset.mistlineLayout = settings.layout;
    if (settings.cabinetContext) {{
      root.dataset.cabinetContext = settings.cabinetContext;
      root.dataset.cabinetTone = settings.tone;
    }}
    root.dataset.mistlineFonts = "loading";
    const verifyFonts = async () => {{
      await document.fonts.ready;
      if (settings.cabinetContext) {{
        const fonts = await document.fonts.load('400 16px CabinetInter');
        root.dataset.mistlineFonts = fonts.length ? "ready" : "fallback";
        return;
      }}
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
    """Use real deck data for Cabinet, with the original tree as fallback."""

    config = _get_config()
    if config["enabled"] and config["layout"] == "cabinet":
        if cabinet.render_home(_deck_browser, content, config):
            return

    marker = 'data-mistline-owned="deck-heading"'
    if marker in content.tree:
        return
    hidden = "" if _get_config()["enabled"] else " hidden"
    heading = f"""
<section class="mistline-deck-heading" {marker}{hidden}>
  <h1>Deck Home</h1>
  <p>Memory index</p>
</section>
"""
    content.tree = f"{heading}{content.tree}"


def _is_addon_page(path: str) -> bool:
    segments = [segment for segment in path.lower().split("/") if segment]
    return bool(segments and segments[0] == "_addons")


def _external_page_context(path: str) -> str | None:
    """Resolve only Anki-owned root or legacy page routes, never add-on URLs."""

    segments = [segment for segment in path.lower().split("/") if segment]
    if not segments or _is_addon_page(path):
        return None

    if segments[:2] == ["_anki", "pages"]:
        if len(segments) < 3:
            return None
        route = segments[2]
        if route.endswith(".html"):
            if len(segments) != 3:
                return None
            route = route.removesuffix(".html")
        return EXTERNAL_PAGE_CONTEXTS.get(route)

    return EXTERNAL_PAGE_CONTEXTS.get(segments[0])


def _webview_kind_context(webview: Any) -> str | None:
    bridge_context = _context_name(getattr(webview, "_bridge_context", None))
    if bridge_context is not None:
        return bridge_context
    kind = getattr(webview, "kind", None)
    kind_name = getattr(kind, "name", None)
    if isinstance(kind_name, str):
        return WEBVIEW_KIND_CONTEXTS.get(kind_name)
    return None


def _webview_context(webview: Any) -> str | None:
    try:
        path = webview.url().path().lower()
    except Exception:
        path = ""
    if _is_addon_page(path):
        return None
    route_context = _external_page_context(path)
    if route_context is not None:
        return route_context
    return _webview_kind_context(webview)


def _remember_webview(webview: Any) -> None:
    try:
        _observed_webviews.add(webview)
    except TypeError:
        # PyQt wrappers normally support weak references. If a future wrapper
        # does not, QApplication.allWidgets() remains the fallback below.
        pass


def _iter_open_webviews():
    seen: set[int] = set()
    for webview in list(_observed_webviews):
        if callable(getattr(webview, "eval", None)) and id(webview) not in seen:
            seen.add(id(webview))
            yield webview
    all_widgets = getattr(QApplication, "allWidgets", None)
    if not callable(all_widgets):
        return
    try:
        widgets = all_widgets()
    except Exception:
        return
    for widget in widgets:
        if callable(getattr(widget, "eval", None)) and id(widget) not in seen:
            seen.add(id(widget))
            yield widget


def _runtime_theme_script(
    config: dict[str, Any], context_name: str | None
) -> str:
    package = mw.addonManager.addon_from_module(__name__)
    metadata = _theme_metadata(config)
    blocked_contexts: list[str] = []
    if not config["style_native_chrome"]:
        blocked_contexts.extend(sorted(STANDALONE_WEB_CONTEXTS))
    if not config["style_reviewer"]:
        blocked_contexts.extend(["reviewer", "reviewer-bottom-bar"])
    payload = {
        "enabled": config["enabled"],
        "context": context_name,
        "blockedContexts": blocked_contexts,
        "managedVariables": (*MANAGED_COLOR_VARIABLES, "--cabinet-lilac", "--cabinet-peach", "--cabinet-sage"),
        "themeHref": f"/_addons/{package}/web/theme.css",
        "editorHref": f"/_addons/{package}/web/editor.css",
        "cabinetHref": f"/_addons/{package}/web/cabinet.css",
        "cabinetContext": cabinet.context(config, context_name),
        "motion": "on" if config["animations"] else "off",
        "glass": "on" if config["frosted_toolbar"] else "off",
        **metadata,
    }
    payload_json = json.dumps(payload, ensure_ascii=True)
    return f"""
(() => {{
  const settings = {payload_json};
  const root = document.documentElement;
  if (!root) return;
  const context = settings.context || root.dataset.mistlineContext || "";
  const enabled = settings.enabled && !settings.blockedContexts.includes(context);
  const absoluteHref = (href) => {{
    try {{
      return new URL(href, document.baseURI).href;
    }} catch (_error) {{
      return href;
    }}
  }};
  const ownedIds = new Set([
    "mistline-external-theme",
    "mistline-editor-theme",
    "mistline-cabinet-theme",
  ]);
  const ownedHrefs = new Set([
    absoluteHref(settings.themeHref),
    absoluteHref(settings.editorHref),
    absoluteHref(settings.cabinetHref),
  ]);
  const themeLinks = () => Array.from(
    document.querySelectorAll('link[rel="stylesheet"]')
  ).filter((link) => ownedIds.has(link.id) || ownedHrefs.has(link.href));
  const ensureLink = (id, href) => {{
    const resolvedHref = absoluteHref(href);
    let link = document.querySelector(`link[rel="stylesheet"]#${{id}}`);
    if (!link) {{
      link = Array.from(document.querySelectorAll('link[rel="stylesheet"]'))
        .find((candidate) => candidate.href === resolvedHref);
    }}
    if (!link) {{
      link = document.createElement("link");
      link.rel = "stylesheet";
      link.href = href;
      document.head.appendChild(link);
    }}
    link.id = id;
    link.dataset.mistlineOwned = "stylesheet";
    return link;
  }};

  if (!enabled) {{
    delete root.dataset.cabinetContext;
    settings.managedVariables.forEach((name) => root.style.removeProperty(name));
    themeLinks().forEach((link) => {{ link.disabled = true; }});
    if (root.dataset.mistlineOwnsColorScheme === "true") {{
      root.style.removeProperty("color-scheme");
      delete root.dataset.mistlineOwnsColorScheme;
    }}
    if (context === "deck-browser") {{
      document.querySelectorAll('[data-mistline-owned="deck-heading"]')
        .forEach((heading) => {{ heading.hidden = true; }});
    }}
    if (root._mistlineThemeOrderObserver) {{
      root._mistlineThemeOrderObserver.disconnect();
      delete root._mistlineThemeOrderObserver;
    }}
    root.dataset.mistlineEnabled = "off";
    return;
  }}

  settings.managedVariables.forEach((name) => root.style.removeProperty(name));
  Object.entries(settings.variables).forEach(([name, value]) =>
    root.style.setProperty(name, value)
  );
  if (context) root.dataset.mistlineContext = context;
  root.dataset.mistlineMotion = settings.motion;
  root.dataset.mistlineGlass = settings.glass;
  root.dataset.mistlineFamily = settings.family;
  root.dataset.mistlinePalette = settings.flavor;
  root.dataset.mistlineTone = settings.tone;
  root.dataset.mistlineAccent = settings.accentName;
  root.dataset.mistlineEnabled = "on";
  root.dataset.mistlineLayout = settings.layout;
  if (settings.cabinetContext) {{
    root.dataset.cabinetContext = settings.cabinetContext;
    root.dataset.cabinetTone = settings.tone;
  }} else {{
    delete root.dataset.cabinetContext;
  }}
  if (context === "deck-browser") {{
    document.querySelectorAll('[data-mistline-owned="deck-heading"]')
      .forEach((heading) => {{ heading.hidden = false; }});
  }}
  if (context !== "reviewer" && context !== "reviewer-bottom-bar") {{
    root.style.colorScheme = settings.tone;
    root.dataset.mistlineOwnsColorScheme = "true";
  }} else if (root.dataset.mistlineOwnsColorScheme === "true") {{
    root.style.removeProperty("color-scheme");
    delete root.dataset.mistlineOwnsColorScheme;
  }}

  let activeLink = null;
  if (context === "editor") {{
    activeLink = ensureLink("mistline-editor-theme", settings.editorHref);
  }} else if (settings.cabinetContext) {{
    activeLink = ensureLink("mistline-cabinet-theme", settings.cabinetHref);
  }} else if (context) {{
    activeLink = ensureLink("mistline-external-theme", settings.themeHref);
  }}
  themeLinks().forEach((link) => {{ link.disabled = link !== activeLink; }});

  // The observer owns one active stylesheet. Layout changes must release the
  // previous observer, or two closures would continually reorder each other.
  if (root._mistlineThemeOrderObserver) {{
    root._mistlineThemeOrderObserver.disconnect();
    delete root._mistlineThemeOrderObserver;
  }}

  const external = context === "editor" ? null : activeLink;
  const keepThemeLast = () => {{
    const styles = document.head.querySelectorAll('link[rel="stylesheet"], style');
    if (external && styles.length && styles[styles.length - 1] !== external) {{
      document.head.appendChild(external);
    }}
  }};
  if (external && !root._mistlineThemeOrderObserver) {{
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


def _inject_external_style(webview: Any) -> None:
    """Observe every Anki WebView and theme owned standalone surfaces."""

    _remember_webview(webview)
    config = _get_config()
    context_name = _webview_context(webview)
    if context_name is None:
        return
    try:
        webview.eval(_runtime_theme_script(config, context_name))
    except (RuntimeError, TypeError):
        pass


def _broadcast_web_theme(config: dict[str, Any] | None = None) -> None:
    """Update open WebViews without reloads or editor content loss."""

    current = config or _get_config()
    for webview in _iter_open_webviews():
        context_name = _webview_context(webview)
        if context_name is None:
            # Browser previews, card templates and third-party WebViews are not
            # owned by Editorial Index. Never broadcast theme state to them.
            continue
        try:
            webview.eval(_runtime_theme_script(current, context_name))
        except (RuntimeError, TypeError):
            # A WebView can disappear while Qt is iterating top-level widgets.
            continue


def _sync_menu_actions() -> None:
    config = _get_config()
    if _menu_action is not None:
        _menu_action.setChecked(config["enabled"])
    selected_palette = (
        "editorial"
        if config["color_theme"] == "editorial"
        else config["catppuccin_flavor"]
    )
    for key, action in _palette_actions.items():
        action.setChecked(key == selected_palette)
    for key, action in _accent_actions.items():
        action.setChecked(key == config["catppuccin_accent"])
    for key, action in _layout_actions.items():
        action.setChecked(key == config["layout"])
    requested_flavor = config["catppuccin_flavor"]
    preview_flavor = (
        "mocha" if _system_is_dark() else "latte"
    ) if requested_flavor == "auto" else requested_flavor
    preview_palette = catppuccin_palette(preview_flavor)
    try:
        from aqt.qt import QColor, QIcon, QPixmap

        for key, action in _accent_actions.items():
            swatch = QPixmap(14, 14)
            swatch.fill(QColor(preview_palette[key]))
            action.setIcon(QIcon(swatch))
    except Exception:
        # Text labels remain complete on bindings/platforms without menu icons.
        pass
    if _accent_menu is not None:
        _accent_menu.setEnabled(config["color_theme"] == "catppuccin")
    palette_dialog = _palette_dialog_ref() if _palette_dialog_ref is not None else None
    refresh_dialog = getattr(palette_dialog, "_mistline_refresh", None)
    if callable(refresh_dialog):
        refresh_dialog()


def _apply_current_theme() -> None:
    config = _get_config()
    _sync_menu_actions()
    apply_native_theme(mw, config)
    _sync_open_native_surfaces(config)
    _broadcast_web_theme(config)
    cabinet.refresh(mw, config)


def _select_layout(layout: str) -> None:
    if layout not in {"editorial", "cabinet"}:
        return
    _write_config_patch(layout=layout)
    _apply_current_theme()


def _save_cabinet_display(profiles: dict) -> None:
    _write_config_patch(cabinet_display=profiles)
    _apply_current_theme()


def _show_cabinet_display():
    return cabinet_display.show_settings(mw, _get_config, _save_cabinet_display)


def _cabinet_display_message(handled, message: str, context):
    prefix = "editorial-cabinet:"
    if handled[0] or not message.startswith(prefix):
        return handled
    config = _get_config()
    if _context_name(context) != "deck-browser" or not config["enabled"] or config["layout"] != "cabinet":
        return (True, None)
    action = message[len(prefix):]
    if action == "settings":
        _show_cabinet_display()
    elif action == "palette":
        _show_palette_dialog()
    else:
        cabinet_display.apply_action(mw, config, action, _save_cabinet_display)
    return (True, None)


def _cabinet_review_shown(*_args) -> None:
    config = _get_config()
    if config["enabled"] and config["layout"] == "cabinet" and config["style_reviewer"]:
        cabinet.mark_review(mw)
        cabinet.fit_toolbars(mw)


def _cabinet_page_rendered(*_args) -> None:
    if _get_config()["layout"] == "cabinet":
        cabinet.fit_toolbars(mw)


def _repolish_widget(widget: Any) -> None:
    try:
        style = widget.style()
        style.unpolish(widget)
        style.polish(widget)
        widget.update()
    except Exception:
        pass


def _layout_margins(layout: Any) -> tuple[int, int, int, int]:
    margins = layout.contentsMargins()
    return (margins.left(), margins.top(), margins.right(), margins.bottom())


def _read_native_value(kind: str, target: Any, name: str | None) -> Any:
    if kind == "property":
        return target.property(name)
    if kind == "objectName":
        return target.objectName()
    if kind == "spacing":
        return target.spacing()
    if kind == "margins":
        return _layout_margins(target)
    raise ValueError(f"unknown native value kind: {kind}")


def _write_native_value(kind: str, target: Any, name: str | None, value: Any) -> None:
    if kind == "property":
        target.setProperty(name, value)
        _repolish_widget(target)
    elif kind == "objectName":
        target.setObjectName(value)
        _repolish_widget(target)
    elif kind == "spacing":
        target.setSpacing(value)
    elif kind == "margins":
        target.setContentsMargins(*value)
    else:
        raise ValueError(f"unknown native value kind: {kind}")


def _own_native_value(
    root: Any,
    key: str,
    target: Any,
    kind: str,
    owned: Any,
    name: str | None = None,
) -> None:
    if target is None:
        return
    state = getattr(root, _NATIVE_STATE_ATTR, None)
    if state is None:
        state = {}
        setattr(root, _NATIVE_STATE_ATTR, state)
    if key in state:
        return
    try:
        before = _read_native_value(kind, target, name)
        _write_native_value(kind, target, name, owned)
    except (AttributeError, RuntimeError, TypeError, ValueError):
        return
    state[key] = (kind, target, name, before, owned)


def _restore_native_values(root: Any) -> None:
    state = getattr(root, _NATIVE_STATE_ATTR, None)
    if not isinstance(state, dict):
        return
    for kind, target, name, before, owned in reversed(list(state.values())):
        try:
            if _read_native_value(kind, target, name) == owned:
                _write_native_value(kind, target, name, before)
        except (AttributeError, RuntimeError, TypeError, ValueError):
            continue
    try:
        delattr(root, _NATIVE_STATE_ATTR)
    except (AttributeError, RuntimeError):
        pass


def _remember_native_surface(surfaces: weakref.WeakSet[Any], surface: Any) -> None:
    try:
        surfaces.add(surface)
    except TypeError:
        pass


def _native_chrome_enabled(config: dict[str, Any]) -> bool:
    return bool(config["enabled"] and config["style_native_chrome"])


def _sync_add_cards(add_cards: Any, enabled: bool) -> None:
    if not enabled:
        _restore_native_values(add_cards)
        return

    roles = (
        ("add", add_cards.addButton, "primary"),
        ("history", add_cards.historyButton, "quiet"),
        ("help", add_cards.helpButton, "quiet"),
        ("close", add_cards.closeButton, "secondary"),
        ("actionbar", add_cards.form.buttonBox, "actionbar"),
        ("notetype", add_cards.notetype_chooser.button, "chooser"),
        ("deck", add_cards.deck_chooser.deck, "chooser"),
        ("notetype-label", getattr(add_cards.notetype_chooser, "label", None), "fieldLabel"),
        ("deck-label", getattr(add_cards.deck_chooser, "deckLabel", None), "fieldLabel"),
        ("editor", add_cards.form.fieldsArea, "editorCanvas"),
    )
    for key, widget, role in roles:
        _own_native_value(
            add_cards, f"role:{key}", widget, "property", role, "mistlineRole"
        )

    _own_native_value(
        add_cards,
        "add:margins",
        add_cards.form.verticalLayout_3,
        "margins",
        (16, 10, 16, 14),
    )
    _own_native_value(
        add_cards,
        "add:vertical-spacing",
        add_cards.form.verticalLayout_3,
        "spacing",
        12,
    )
    _own_native_value(
        add_cards,
        "add:horizontal-spacing",
        add_cards.form.horizontalLayout,
        "spacing",
        12,
    )
    _own_native_value(
        add_cards,
        "add:notetype-spacing",
        add_cards.notetype_chooser,
        "spacing",
        8,
    )
    _own_native_value(
        add_cards, "add:deck-spacing", add_cards.deck_chooser, "spacing", 8
    )
    _own_native_value(
        add_cards,
        "add:button-spacing",
        add_cards.form.buttonBox.layout(),
        "spacing",
        8,
    )


def _style_add_cards(add_cards: Any) -> None:
    """Complete Add's hierarchy while preserving shortcuts and default roles."""

    _remember_native_surface(_observed_add_cards, add_cards)
    _sync_add_cards(add_cards, _native_chrome_enabled(_get_config()))


def _style_managed_dialog(
    _dialog_manager: Any, dialog_name: str, dialog_instance: Any
) -> None:
    """Give managed dialogs semantic actions without reordering Qt buttons."""

    if dialog_name == "AddCards":
        _style_add_cards(dialog_instance)
        return

    _remember_native_surface(_observed_managed_dialogs, dialog_instance)
    _sync_managed_dialog(
        dialog_instance, _native_chrome_enabled(_get_config())
    )


def _sync_managed_dialog(dialog_instance: Any, enabled: bool) -> None:
    if not enabled:
        _restore_native_values(dialog_instance)
        return

    roles = QDialogButtonBox.ButtonRole
    primary_roles = {roles.AcceptRole, roles.YesRole, roles.ApplyRole}
    destructive_roles = {roles.DestructiveRole}
    for button_box in dialog_instance.findChildren(QDialogButtonBox):
        _own_native_value(
            dialog_instance,
            f"role:button-box:{id(button_box)}",
            button_box,
            "property",
            "actionbar",
            "mistlineRole",
        )
        for button in button_box.buttons():
            button_role = button_box.buttonRole(button)
            if button.isDefault() or button_role in primary_roles:
                role = "primary"
            elif button_role in destructive_roles:
                role = "destructive"
            else:
                role = "secondary"
            _own_native_value(
                dialog_instance,
                f"role:button:{id(button)}",
                button,
                "property",
                role,
                "mistlineRole",
            )


def _refresh_browser_sidebar_style(browser: Any) -> None:
    """Rebuild Anki's palette-derived, widget-local sidebar stylesheet."""

    try:
        setup_style = getattr(browser.sidebar, "_setup_style", None)
        if callable(setup_style):
            setup_style()
    except (AttributeError, RuntimeError, TypeError):
        # Older Anki versions may not expose this implementation detail, and a
        # Browser can be destroyed while a menu-triggered theme sync is running.
        pass


def _style_browser(browser: Any) -> None:
    """Track Browser so its palette-derived sidebar style stays current."""

    _remember_native_surface(_observed_browsers, browser)
    _refresh_browser_sidebar_style(browser)


def _style_card_layout(card_layout: Any) -> None:
    """Give Card Layout a clear action hierarchy without touching previews."""

    _remember_native_surface(_observed_card_layouts, card_layout)
    if not _native_chrome_enabled(_get_config()):
        _restore_native_values(card_layout)
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

    role_widgets = [(widgets[0], "quiet")]
    role_widgets.extend((widget, "secondary") for widget in widgets[1:-2])
    role_widgets.extend(((widgets[-2], "primary"), (widgets[-1], "secondary")))
    for index, (widget, role) in enumerate(role_widgets):
        _own_native_value(
            card_layout,
            f"role:button:{index}",
            widget,
            "property",
            role,
            "mistlineRole",
        )
    _own_native_value(card_layout, "card-layout:spacing", layout, "spacing", 8)


def _sync_open_native_surfaces(config: dict[str, Any]) -> None:
    enabled = _native_chrome_enabled(config)
    for surface in list(_observed_add_cards):
        try:
            _sync_add_cards(surface, enabled)
        except (AttributeError, RuntimeError, TypeError):
            continue
    for surface in list(_observed_managed_dialogs):
        try:
            _sync_managed_dialog(surface, enabled)
        except (AttributeError, RuntimeError, TypeError):
            continue
    for surface in list(_observed_browsers):
        try:
            _refresh_browser_sidebar_style(surface)
        except (AttributeError, RuntimeError, TypeError):
            continue
    for surface in list(_observed_card_layouts):
        try:
            if enabled:
                _style_card_layout(surface)
            else:
                _restore_native_values(surface)
        except (AttributeError, RuntimeError, TypeError):
            continue


def _extend_anki_style(style: str) -> str:
    """Official Anki style filter used after theme/widget-style changes."""

    return extend_native_style(style, _get_config())


def _toggle_theme(checked: bool) -> None:
    _write_config_patch(enabled=bool(checked))
    _apply_current_theme()


def _select_palette(palette_id: str) -> None:
    if palette_id == "editorial":
        _write_config_patch(color_theme="editorial")
    else:
        _write_config_patch(
            color_theme="catppuccin",
            catppuccin_flavor=normalize_catppuccin_flavor(palette_id),
        )
    _apply_current_theme()


def _select_catppuccin_accent(accent_name: str) -> None:
    _write_config_patch(
        catppuccin_accent=normalize_catppuccin_accent(accent_name)
    )
    _apply_current_theme()


def _show_palette_dialog() -> None:
    """Show every flavor, accent, and semantic role inside Anki itself."""

    global _palette_dialog_ref
    existing = _palette_dialog_ref() if _palette_dialog_ref is not None else None
    if existing is not None:
        try:
            existing.show()
            existing.raise_()
            existing.activateWindow()
            return
        except RuntimeError:
            _palette_dialog_ref = None

    # Keep these imports lazy so Anki can import the add-on in headless test
    # environments without constructing native widgets.
    from aqt.qt import (
        QButtonGroup,
        QColor,
        QDialog,
        QFrame,
        QGridLayout,
        QHBoxLayout,
        QIcon,
        QLabel,
        QPainter,
        QPixmap,
        QPushButton,
        QScrollArea,
        QSizePolicy,
        QTabWidget,
        Qt,
        QVBoxLayout,
        QWidget,
    )

    dialog = QDialog(mw)
    dialog.setObjectName("EditorialIndexPaletteStudio")
    dialog.setWindowTitle("Editorial Index 配色")
    dialog.setMinimumSize(680, 600)
    dialog.resize(840, 760)
    dialog.setModal(False)

    outer = QVBoxLayout(dialog)
    outer.setContentsMargins(24, 24, 24, 20)
    outer.setSpacing(16)

    title = QLabel("Catppuccin 配色工作台", dialog)
    title.setObjectName("EditorialIndexPaletteTitle")
    subtitle = QLabel(
        "点选主题与强调色后立即应用并记住。评分颜色保持各自含义。",
        dialog,
    )
    subtitle.setObjectName("EditorialIndexPaletteSubtitle")
    subtitle.setWordWrap(True)
    current = QLabel(dialog)
    current.setObjectName("EditorialIndexPaletteCurrent")
    current.setWordWrap(True)
    heading = QVBoxLayout()
    heading.setSpacing(6)
    heading.addWidget(title)
    heading.addWidget(subtitle)
    outer.addLayout(heading)
    outer.addWidget(current)

    controls = QWidget(dialog)
    controls.setObjectName("EditorialIndexPaletteChoices")
    controls_layout = QVBoxLayout(controls)
    controls_layout.setContentsMargins(0, 0, 0, 0)
    controls_layout.setSpacing(0)
    scroll = QScrollArea(dialog)
    scroll.setObjectName("EditorialIndexPaletteScroll")
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.Shape.NoFrame)
    scroll.setWidget(controls)
    outer.addWidget(scroll, 1)

    flavor_label = QLabel("界面主题", controls)
    flavor_label.setProperty("mistlineRole", "fieldLabel")
    controls_layout.addWidget(flavor_label)
    controls_layout.addSpacing(8)

    flavor_panel = QWidget(dialog)
    flavor_grid = QGridLayout(flavor_panel)
    flavor_grid.setContentsMargins(0, 0, 0, 0)
    flavor_grid.setHorizontalSpacing(8)
    flavor_grid.setVerticalSpacing(8)
    for column in range(3):
        flavor_grid.setColumnStretch(column, 1)
    flavor_group = QButtonGroup(dialog)
    flavor_group.setExclusive(True)
    flavor_labels = {
        "editorial": "Editorial 暖纸",
        "auto": "自动 · Latte / Mocha",
        "latte": "Latte · Light",
        "frappe": "Frappé · Dark",
        "macchiato": "Macchiato · Dark",
        "mocha": "Mocha · Dark",
    }
    flavor_buttons: dict[str, Any] = {}
    for index, palette_id in enumerate(("editorial", *CATPPUCCIN_FLAVOR_OPTIONS)):
        button = QPushButton(flavor_labels[palette_id], flavor_panel)
        button.setObjectName("PaletteFlavor_" + palette_id)
        button.setCheckable(True)
        button.setProperty("mistlineRole", "paletteChoice")
        button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        # Resolve the themed size hint before the grid's first layout pass.
        button.ensurePolished()
        flavor_group.addButton(button)
        flavor_grid.addWidget(button, index // 3, index % 3)
        qconnect(
            button.clicked,
            lambda _checked=False, selected=palette_id: _select_palette(selected),
        )
        flavor_buttons[palette_id] = button
    controls_layout.addWidget(flavor_panel)
    controls_layout.addSpacing(20)

    accent_label = QLabel("强调色 · 14 种", dialog)
    accent_label.setProperty("mistlineRole", "fieldLabel")
    controls_layout.addWidget(accent_label)
    controls_layout.addSpacing(8)

    accent_panel = QWidget(dialog)
    accent_grid = QGridLayout(accent_panel)
    accent_grid.setContentsMargins(0, 0, 0, 0)
    accent_grid.setHorizontalSpacing(8)
    accent_grid.setVerticalSpacing(8)
    for column in range(5):
        accent_grid.setColumnStretch(column, 1)
    accent_group = QButtonGroup(dialog)
    accent_group.setExclusive(True)
    accent_buttons: dict[str, Any] = {}
    for index, accent_name in enumerate(CATPPUCCIN_ACCENTS):
        button = QPushButton(accent_name.capitalize(), accent_panel)
        button.setObjectName("PaletteAccent_" + accent_name)
        button.setCheckable(True)
        button.setProperty("mistlineRole", "paletteChoice")
        button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        button.ensurePolished()
        accent_group.addButton(button)
        accent_grid.addWidget(button, index // 5, index % 5)
        qconnect(
            button.clicked,
            lambda _checked=False, selected=accent_name: _select_catppuccin_accent(
                selected
            ),
        )
        accent_buttons[accent_name] = button
    controls_layout.addWidget(accent_panel)
    controls_layout.addStretch(1)

    from .palette_preview import create_preview
    preview_tabs = QTabWidget(dialog)
    preview_tabs.setObjectName("EditorialIndexPaletteTabs")
    preview_tabs.setFixedHeight(212)
    preview_web = create_preview(preview_tabs)
    preview_tabs.addTab(preview_web, "界面预览")

    preview_panel = QWidget(dialog)
    preview_grid = QGridLayout(preview_panel)
    preview_grid.setContentsMargins(16, 16, 16, 16)
    preview_grid.setHorizontalSpacing(8)
    preview_grid.setVerticalSpacing(8)
    preview_roles = (
        ("link", "链接"),
        ("focus", "焦点"),
        ("cursor", "光标"),
        ("new", "New"),
        ("learn", "Learn"),
        ("due", "Due"),
        ("good", "Good"),
        ("easy", "Easy"),
    )
    preview_chips: dict[str, tuple[Any, Any]] = {}
    for index, (role, role_label) in enumerate(preview_roles):
        chip = QFrame(preview_panel)
        chip.setProperty("mistlineRole", "semanticPreview")
        chip.setMinimumHeight(48)
        chip_layout = QVBoxLayout(chip)
        chip_layout.setContentsMargins(10, 7, 10, 7)
        chip_text = QLabel(role_label, chip)
        chip_text.setWordWrap(True)
        chip_layout.addWidget(chip_text)
        preview_grid.addWidget(chip, index // 4, index % 4)
        preview_chips[role] = (chip, chip_text)
    preview_tabs.addTab(preview_panel, "颜色用途与色值")
    outer.addWidget(preview_tabs)

    bottom = QHBoxLayout()
    bottom.addStretch(1)
    close_button = QPushButton("关闭", dialog)
    close_button.setObjectName("PaletteClose")
    close_button.setProperty("mistlineRole", "secondary")
    qconnect(close_button.clicked, dialog.accept)
    bottom.addWidget(close_button)
    outer.addLayout(bottom)

    source_names = {
        "link": lambda _tokens: "Blue",
        "focus": lambda _tokens: "Lavender",
        "cursor": lambda _tokens: "Rosewater",
        "new": lambda _tokens: "Teal",
        "learn": lambda _tokens: "Yellow",
        "due": lambda _tokens: "Red",
        "good": lambda _tokens: "Green",
        "easy": lambda _tokens: "Blue",
    }

    def swatch_icon(color: str) -> Any:
        swatch = QPixmap(18, 18)
        swatch.fill(Qt.GlobalColor.transparent)
        painter = QPainter(swatch)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor(color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(1, 1, 16, 16)
        painter.end()
        return QIcon(swatch)

    def refresh() -> None:
        config = _get_config()
        palette_id = (
            "editorial"
            if config["color_theme"] == "editorial"
            else config["catppuccin_flavor"]
        )
        for key, button in flavor_buttons.items():
            button.setChecked(key == palette_id)
        requested_flavor = config["catppuccin_flavor"]
        resolved_flavor = (
            "mocha" if _system_is_dark() else "latte"
        ) if requested_flavor == "auto" else requested_flavor
        palette = catppuccin_palette(resolved_flavor)
        catppuccin_enabled = config["color_theme"] == "catppuccin"
        accent_label.setEnabled(catppuccin_enabled)
        accent_panel.setEnabled(catppuccin_enabled)
        for key, button in accent_buttons.items():
            button.setChecked(key == config["catppuccin_accent"])
            button.setIcon(swatch_icon(palette[key]))
            button.setToolTip(f"{key.capitalize()} · {palette[key]}")

        tokens = _resolved_tokens(config)
        flavor_name = (
            "Editorial 暖纸"
            if tokens.family == "editorial"
            else tokens.flavor.capitalize()
        )
        current.setText(
            f"当前：{flavor_name} · {tokens.accent_name.capitalize()} · "
            f"{tokens.accent_raw}" + (" · 主题当前已关闭" if not config["enabled"] else "")
        )
        preview_web.eval(_runtime_theme_script(
            {**config, "enabled": True, "style_reviewer": True}, "reviewer-bottom-bar"
        ))
        role_colors = {
            "link": (tokens.link, tokens.link, tokens.field, tokens.link),
            "focus": (tokens.focus, tokens.focus, tokens.field, tokens.focus),
            "cursor": (tokens.cursor, tokens.cursor, tokens.field, tokens.cursor),
            "new": (tokens.new, tokens.new, tokens.field, tokens.new),
            "learn": (tokens.learn, tokens.learn, tokens.field, tokens.learn),
            "due": (tokens.due, tokens.due, tokens.field, tokens.due),
            "good": (tokens.good, tokens.good, tokens.field, tokens.good),
            "easy": (tokens.easy, tokens.easy, tokens.field, tokens.easy),
        }
        for role, role_label in preview_roles:
            color, foreground, background, border = role_colors[role]
            source = (
                source_names[role](tokens)
                if tokens.family == "catppuccin"
                else "Editorial"
            )
            chip, chip_text = preview_chips[role]
            chip.setStyleSheet(
                f"border: 1px solid {border};"
                "border-radius: 8px;"
                f"background-color: {background};"
            )
            chip_text.setText(f"{role_label} · {source}\n{color}")
            chip_text.setStyleSheet(
                "border: 0;"
                "background: transparent;"
                f"color: {foreground};"
                "font-weight: 600;"
            )

    dialog._mistline_refresh = refresh
    _palette_dialog_ref = weakref.ref(dialog)
    def clear_dialog_ref(_result: int = 0) -> None:
        global _palette_dialog_ref
        _palette_dialog_ref = None
        preview_web.cleanup()
        dialog.deleteLater()

    qconnect(dialog.finished, clear_dialog_ref)
    refresh()
    dialog.show()
    dialog.raise_()
    dialog.activateWindow()


def _setup_menu() -> None:
    global _accent_group, _accent_menu, _menu_action, _palette_dialog_action
    global _palette_group, _palette_menu
    global _layout_group
    if _menu_action is not None:
        return

    action = QAction("Editorial Index 主题", mw)
    action.setCheckable(True)
    qconnect(action.triggered, _toggle_theme)

    palette_dialog_action = QAction("Editorial Index 配色…", mw)
    qconnect(
        palette_dialog_action.triggered,
        lambda _checked=False: _show_palette_dialog(),
    )

    palette_menu = QMenu("Editorial Index 快速配色", mw)
    palette_group = QActionGroup(palette_menu)
    palette_group.setExclusive(True)
    palette_labels = {
        "editorial": "Editorial Index（暖纸默认）",
        "auto": "Catppuccin 自动（Latte / Mocha）",
        "latte": "Catppuccin Latte",
        "frappe": "Catppuccin Frappé",
        "macchiato": "Catppuccin Macchiato",
        "mocha": "Catppuccin Mocha",
    }
    for palette_id in ("editorial", *CATPPUCCIN_FLAVOR_OPTIONS):
        palette_action = QAction(palette_labels[palette_id], palette_menu)
        palette_action.setCheckable(True)
        palette_group.addAction(palette_action)
        palette_menu.addAction(palette_action)
        qconnect(
            palette_action.triggered,
            lambda _checked=False, selected=palette_id: _select_palette(selected),
        )
        _palette_actions[palette_id] = palette_action

    palette_menu.addSeparator()
    accent_menu = palette_menu.addMenu("Catppuccin 强调色")
    accent_group = QActionGroup(accent_menu)
    accent_group.setExclusive(True)
    for accent_name in CATPPUCCIN_ACCENTS:
        accent_action = QAction(accent_name.capitalize(), accent_menu)
        accent_action.setCheckable(True)
        accent_group.addAction(accent_action)
        accent_menu.addAction(accent_action)
        qconnect(
            accent_action.triggered,
            lambda _checked=False, selected=accent_name: _select_catppuccin_accent(
                selected
            ),
        )
        _accent_actions[accent_name] = accent_action

    mw.form.menuTools.addSeparator()
    mw.form.menuTools.addAction(action)
    mw.form.menuTools.addAction(palette_dialog_action)
    mw.form.menuTools.addMenu(palette_menu)
    layout_menu = QMenu("Editorial Index 布局", mw)
    _layout_group = QActionGroup(layout_menu)
    _layout_group.setExclusive(True)
    for layout, label in (("cabinet", "卡匣 Cabinet"), ("editorial", "经典 Editorial")):
        layout_action = QAction(label, layout_menu)
        layout_action.setCheckable(True)
        _layout_group.addAction(layout_action)
        layout_menu.addAction(layout_action)
        qconnect(layout_action.triggered, lambda _checked=False, selected=layout: _select_layout(selected))
        _layout_actions[layout] = layout_action
    mw.form.menuTools.addMenu(layout_menu)
    display_action = QAction("Editorial Index 首页展示…", mw)
    qconnect(display_action.triggered, lambda _checked=False: _show_cabinet_display())
    mw.form.menuTools.addAction(display_action)
    _menu_action = action
    _palette_dialog_action = palette_dialog_action
    _palette_menu = palette_menu
    _accent_menu = accent_menu
    _palette_group = palette_group
    _accent_group = accent_group
    _sync_menu_actions()
    _apply_current_theme()


def _config_updated(_new_config: Any) -> None:
    _apply_current_theme()


def _theme_did_change() -> None:
    # Auto follows Anki light/dark; explicit Catppuccin flavors stay fixed.
    _apply_current_theme()


mw.addonManager.setWebExports(
    __name__,
    r"^web/(?:theme\.css|heatmap\.css|cabinet\.css|cabinet\.js|editor\.css|editor-marker\.js|fonts/.*\.(?:woff2|ttf|txt|md))$",
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
gui_hooks.theme_did_change.append(_theme_did_change)
gui_hooks.main_window_did_init.append(_setup_menu)
gui_hooks.deck_browser_did_render.append(_cabinet_page_rendered)
gui_hooks.overview_did_refresh.append(_cabinet_page_rendered)
gui_hooks.reviewer_did_show_question.append(_cabinet_review_shown)
gui_hooks.reviewer_did_show_answer.append(_cabinet_review_shown)
gui_hooks.webview_did_receive_js_message.append(_cabinet_display_message)
