"""Cabinet layout adapter. Anki retains all collection and reviewer operations."""

from __future__ import annotations

import json
from typing import Any

from .cabinet_decks import render_deck_tree
from .cabinet_display import preferences


CONTEXTS = {
    "deck-browser": "deck",
    "overview": "overview",
    "reviewer": "reviewer",
    "top-toolbar": "top",
    "standard-bottom-bar": "bottom",
    "reviewer-bottom-bar": "reviewer-bottom",
}
_last_layout_state: tuple | None = None


def context(config: dict[str, Any], name: str | None) -> str | None:
    if config.get("layout") != "cabinet":
        return None
    return CONTEXTS.get(name)


def render_home(deck_browser: Any, content: Any, config: dict | None = None) -> bool:
    data = getattr(deck_browser, "_render_data", None)
    if data is None:
        return False
    try:
        profile = getattr(getattr(deck_browser.mw, "pm", None), "name", "")
        hidden, folded = preferences(config or {}, profile)
        content.tree = render_deck_tree(data.tree, int(data.current_deck_id), hidden_ids=hidden, folded_ids=folded)
    except (AttributeError, TypeError, ValueError) as error:
        # This render-data bridge is version-sensitive. Preserve the original
        # tree on unsupported versions instead of showing an empty home screen.
        print(f"Editorial Index: native deck list preserved ({error})")
        return False
    return True


def mark_review(mw: Any) -> None:
    card = getattr(getattr(mw, "reviewer", None), "card", None)
    if card is None or mw.col is None:
        return
    deck = mw.col.decks.get(card.current_deck_id())
    name = deck["name"] if deck else ""
    # Only a dataset on Anki's existing wrapper; never rewrite card fields,
    # template HTML, typed answers, media, or the scheduler queue.
    mw.web.eval(
        "(() => {const qa=document.getElementById('qa');"
        "if(qa)qa.dataset.cabinetDeck=" + json.dumps(name) + ";})();"
    )
    # A user can choose a dark palette while their template still uses Anki's
    # light-mode black text. Change our paper, not the template's foreground.
    mw.web.eval("""
(() => {
  const qa = document.getElementById('qa');
  const root = document.documentElement;
  if (!qa || root.dataset.cabinetContext !== 'reviewer') return;
  qa.style.removeProperty('--cabinet-card-paper');
  const rgb = color => {
    const channels = color.match(/[\\d.]+/g)?.map(Number);
    return channels && channels.length >= 3 ? channels.slice(0, 3) : null;
  };
  const luminance = color => rgb(color)?.reduce((sum, channel, i) => {
    const v = channel / 255;
    return sum + (v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4) * [0.2126, 0.7152, 0.0722][i];
  }, 0);
  const contrast = (a, b) => {
    const x = luminance(a), y = luminance(b);
    return x == null || y == null ? 0 : (Math.max(x, y) + .05) / (Math.min(x, y) + .05);
  };
  const ink = getComputedStyle(qa).color;
  if (contrast(ink, getComputedStyle(qa).backgroundColor) >= 4.5) return;
  const context = root.dataset.cabinetContext;
  delete root.dataset.cabinetContext;
  const originalPaper = getComputedStyle(document.body).backgroundColor;
  root.dataset.cabinetContext = context;
  const opaque = !originalPaper.startsWith('rgba') || originalPaper.endsWith(', 1)');
  const paper = opaque && contrast(ink, originalPaper) >= 4.5 ? originalPaper
    : contrast(ink, 'rgb(255,255,255)') >= contrast(ink, 'rgb(0,0,0)') ? '#fffdf8' : '#25242c';
  qa.style.setProperty('--cabinet-card-paper', paper);
})();
""")


def fit_toolbars(mw: Any) -> None:
    progress = getattr(mw, "progress", None)
    if progress is None:
        return

    def fit() -> None:
        if mw.state not in {"deckBrowser", "overview", "review"}:
            return
        mw.toolbarWeb.adjustHeightToFit()
        if mw.state == "review":
            mw.bottomWeb.show()
        else:
            mw.bottomWeb.adjustHeightToFit()

    progress.single_shot(220, fit, False)


def refresh(mw: Any, config: dict[str, Any]) -> None:
    global _last_layout_state
    profile = getattr(getattr(mw, "pm", None), "name", "")
    hidden, folded = preferences(config, profile)
    state = (config["enabled"], config["layout"], profile, tuple(sorted(hidden)), tuple(sorted(folded)))
    changed = _last_layout_state is not None and state != _last_layout_state
    _last_layout_state = state
    # Only rebuild home when its structure changes. In review, applying a
    # layout/color must not reset the card, flip state, or user's typed input.
    if changed and getattr(mw, "state", None) == "deckBrowser":
        mw.deckBrowser.refresh()
    if config["enabled"] and config["layout"] == "cabinet" and config["style_reviewer"]:
        if getattr(mw, "state", None) == "review":
            mark_review(mw)
    fit_toolbars(mw)
