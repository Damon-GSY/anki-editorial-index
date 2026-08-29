"""Small, reversible Qt stylesheet for Editorial Index window chrome."""

from __future__ import annotations

from pathlib import Path
from typing import Any

_injected_qss = ""
_native_fonts_registered = False
_native_font_family = "Inter"


def _register_native_fonts() -> str:
    """Register the bundled Inter faces for Qt-owned Anki chrome."""

    global _native_fonts_registered, _native_font_family
    if _native_fonts_registered:
        return _native_font_family

    try:
        from aqt.qt import QFontDatabase
    except Exception:
        return _native_font_family

    font_dir = Path(__file__).resolve().parent / "web" / "fonts"
    for filename in ("inter-regular.ttf", "inter-semibold.ttf"):
        try:
            font_id = QFontDatabase.addApplicationFont(str(font_dir / filename))
            if font_id < 0:
                continue
            families = QFontDatabase.applicationFontFamilies(font_id)
            if families:
                _native_font_family = str(families[0])
        except Exception:
            continue

    _native_fonts_registered = True
    return _native_font_family


def _theme_is_dark() -> bool:
    try:
        from aqt.theme import theme_manager

        return bool(theme_manager.night_mode)
    except Exception:
        return False


def _build_qss(accent: str, dark: bool, font_family: str = "Inter") -> str:
    if dark:
        canvas = "#1B1916"
        surface = "#221F1A"
        raised = "#2B2721"
        text = "#F1EADF"
        muted = "#B3AB9E"
        border = "#514A40"
        hover = "#302B25"
    else:
        canvas = "#F1EDE4"
        surface = "#F8F5ED"
        raised = "#E7E0D4"
        text = "#1D1D1B"
        muted = "#77736B"
        border = "#CFC8BC"
        hover = "#E7E0D4"

    return f"""
/* mistline-native-theme:start */
QMainWindow {{
    background-color: {canvas};
    color: {text};
    font-family: "{font_family}";
}}
QMenuBar {{
    border: 0;
    border-bottom: 1px solid {border};
    color: {text};
    background-color: {surface};
    spacing: 4px;
}}
QMenuBar::item {{
    margin: 2px 1px;
    padding: 5px 10px;
    border-radius: 2px;
    background: transparent;
}}
QMenuBar::item:selected {{
    color: {text};
    background-color: {hover};
}}
QMenu {{
    padding: 5px;
    border: 1px solid {border};
    border-radius: 3px;
    color: {text};
    background-color: {surface};
}}
QMenu::item {{
    min-height: 24px;
    padding: 5px 24px 5px 10px;
    border-radius: 2px;
}}
QMenu::item:selected {{
    color: {text};
    background-color: {hover};
}}
QMenu::separator {{
    height: 1px;
    margin: 6px 8px;
    background-color: {border};
}}
QStatusBar {{
    border-top: 1px solid {border};
    color: {muted};
    background-color: {surface};
}}
QStatusBar::item {{ border: 0; }}
QToolTip {{
    padding: 5px 8px;
    border: 1px solid {border};
    border-radius: 2px;
    color: {text};
    background-color: {raised};
}}
QToolButton {{
    border: 1px solid transparent;
    border-radius: 2px;
    padding: 5px 8px;
    color: {text};
    background: transparent;
}}
QToolButton:hover {{
    border-color: {border};
    background-color: {hover};
}}
QToolButton:checked {{
    border-color: {accent};
    background-color: {raised};
}}
/* mistline-native-theme:end */
"""


def apply_native_theme(main_window: Any, config: dict[str, Any]) -> None:
    """Replace only the QSS block previously injected by this add-on."""

    global _injected_qss
    current = main_window.styleSheet()
    if _injected_qss:
        current = current.replace(_injected_qss, "")
        _injected_qss = ""

    should_apply = bool(config.get("enabled")) and bool(
        config.get("style_native_chrome")
    )
    if should_apply:
        accent = str(config.get("accent_color", "#315FC4"))
        font_family = _register_native_fonts()
        _injected_qss = _build_qss(accent, _theme_is_dark(), font_family)
        current = f"{current}\n{_injected_qss}"

    main_window.setStyleSheet(current)
