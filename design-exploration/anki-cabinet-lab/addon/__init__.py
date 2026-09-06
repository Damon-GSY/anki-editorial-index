"""Card Cabinet integration lab — local pilot, not a released Anki theme.

Owns the deck listing and surrounding web chrome only. Anki owns the
collection, overview, card HTML, scheduling, media, shortcuts and undo.
"""

from __future__ import annotations

import json

from aqt import gui_hooks, mw
from aqt.qt import QAction, qconnect
from aqt.theme import theme_manager

from .decks import render_deck_tree

CONTEXTS = {
    "DeckBrowser": "deck",
    "Overview": "overview",
    "Reviewer": "reviewer",
    "TopToolbar": "top",
    "DeckBrowserBottomBar": "bottom",
    "OverviewBottomBar": "bottom",
    "ReviewerBottomBar": "reviewer-bottom",
}
_action = None


def enabled() -> bool:
    config = mw.addonManager.getConfig(__name__) or {}
    return bool(config.get("enabled", True))


def _context(context: object) -> str | None:
    kind = type(context)
    if not kind.__module__.startswith("aqt."):
        return None
    return CONTEXTS.get(kind.__name__)


def _mark_script(context: str) -> str:
    return (
        "document.documentElement.dataset.cabinetContext="
        + json.dumps(context)
        + ";document.documentElement.dataset.cabinetTone="
        + json.dumps("dark" if theme_manager.night_mode else "light")
        + ";"
    )


def inject(web_content, context: object) -> None:
    surface = _context(context)
    if not enabled() or not surface:
        return
    package = mw.addonManager.addon_from_module(__name__)
    web_content.css.append(f"/_addons/{package}/web/cabinet.css")
    # These Anki-owned legacy WebViews allow inline head markers. We deliberately
    # do not inject into the CSP-restricted Editor or third-party add-on pages.
    web_content.head += f"<script>{_mark_script(surface)}</script>"
    if surface == "deck":
        web_content.js.append(f"/_addons/{package}/web/cabinet.js")


def render_home(deck_browser, content) -> None:
    if not enabled():
        return
    # Observed in the installed Anki 26.05b1; this private RenderData bridge
    # is a version-sensitive integration point, not a universal compatibility claim.
    data = getattr(deck_browser, "_render_data", None)
    if data is None or not hasattr(data, "tree"):
        return  # preserve the original listing on an unsupported Anki build
    try:
        content.tree = render_deck_tree(data.tree, int(data.current_deck_id))
    except (TypeError, ValueError) as error:
        # Schema guards deliberately preserve the native tree, instead of
        # stranding the user on an empty home screen after an Anki upgrade.
        print(f"Cabinet lab: native deck list preserved ({error})")
    # Keep content.stats untouched, including other add-on contributions.


def mark_review(card) -> None:
    if not enabled():
        return
    deck = mw.col.decks.get(card.current_deck_id())
    name = deck["name"] if deck else ""
    # Do not prepend/duplicate/rewrite card HTML. The label is outside the
    # original content via CSS; #typeans and card scripts stay native.
    mw.web.eval(
        "(() => {const qa=document.getElementById('qa');"
        "if(qa)qa.dataset.cabinetDeck=" + json.dumps(name) + ";})();"
    )
    _fit_toolbars()


def _fit_toolbars(*_args) -> None:
    if not enabled():
        return
    # Measure each real WebView after CSS/font layout; never assume CSS padding
    # alone can increase the Qt widget's allocated height.
    def fit() -> None:
        if mw.state in {"deckBrowser", "overview", "review"}:
            mw.toolbarWeb.adjustHeightToFit()
            if mw.state == "review":
                mw.bottomWeb.show()
            else:
                mw.bottomWeb.adjustHeightToFit()

    mw.progress.single_shot(180, fit, False)


def set_enabled(value: bool) -> None:
    config = mw.addonManager.getConfig(__name__) or {}
    config["enabled"] = bool(value)
    mw.addonManager.writeConfig(__name__, config)
    if _action:
        _action.setChecked(value)
    # Disabling removes our marker even from still-open review WebViews.
    if not value:
        for web in (mw.web, mw.toolbarWeb, mw.bottomWeb):
            web.eval("delete document.documentElement.dataset.cabinetContext;")
    if mw.state == "deckBrowser":
        mw.deckBrowser.refresh()
    elif mw.state == "overview":
        mw.overview.refresh()
    elif mw.state == "review":
        if value:
            mw.web.eval(_mark_script("reviewer"))
            mw.bottomWeb.eval(_mark_script("reviewer-bottom"))
            if mw.reviewer.card:
                mark_review(mw.reviewer.card)
    mw.toolbar.redraw()
    # Recalculate native height on both enable and disable.
    mw.progress.single_shot(220, lambda: mw.toolbarWeb.adjustHeightToFit(), False)
    mw.progress.single_shot(220, lambda: mw.bottomWeb.adjustHeightToFit(), False)


def setup_menu(*_args) -> None:
    global _action
    if _action is not None:
        return
    _action = QAction("卡匣实验主题（仅测试）", mw)
    _action.setCheckable(True)
    _action.setChecked(enabled())
    qconnect(_action.triggered, set_enabled)
    mw.form.menuTools.addAction(_action)


mw.addonManager.setWebExports(__name__, r"^web/(cabinet\.(css|js)|fonts/.*\.(woff2|txt))$")
gui_hooks.webview_will_set_content.append(inject)
gui_hooks.deck_browser_will_render_content.append(render_home)
gui_hooks.deck_browser_did_render.append(_fit_toolbars)
gui_hooks.overview_did_refresh.append(_fit_toolbars)
gui_hooks.reviewer_did_show_question.append(mark_review)
gui_hooks.reviewer_did_show_answer.append(mark_review)
gui_hooks.main_window_did_init.append(setup_menu)
