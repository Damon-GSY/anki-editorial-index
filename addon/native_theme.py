"""Reversible application-level Qt stylesheet for Editorial Index."""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    from .color_themes import (
        ColorTokens as _ThemeTokens,
        _contrast_text,
        _mix_hex,
        resolve_color_tokens,
    )
except ImportError:  # pragma: no cover - direct-module compatibility for tests
    from color_themes import (  # type: ignore[no-redef]
        ColorTokens as _ThemeTokens,
        _contrast_text,
        _mix_hex,
        resolve_color_tokens,
    )

_native_fonts_registered = False
_native_font_family = "Inter"

_QSS_START = "/* mistline-native-theme:start */"
_QSS_END = "/* mistline-native-theme:end */"


_palette_target: Any | None = None
_palette_before_theme: Any | None = None
_palette_owned: Any | None = None


def _build_tokens(accent: str, dark: bool) -> _ThemeTokens:
    """Compatibility wrapper for the original Editorial helper API."""

    return resolve_color_tokens(
        {"color_theme": "editorial", "accent_color": accent},
        dark,
    )


def _build_tokens_for_config(config: dict[str, Any], dark: bool) -> _ThemeTokens:
    """Resolve every native color from the shared cross-surface contract."""

    return resolve_color_tokens(config, dark)


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
    """Compatibility wrapper for callers that pass an Editorial accent."""

    return _build_qss_from_tokens(_build_tokens(accent, dark), font_family)


def _build_qss_for_config(
    config: dict[str, Any], dark: bool, font_family: str = "Inter"
) -> str:
    return _build_qss_from_tokens(_build_tokens_for_config(config, dark), font_family)


def _build_qss_from_tokens(
    tokens: _ThemeTokens, font_family: str = "Inter"
) -> str:
    accent = tokens.accent
    accent_text = tokens.accent_text
    focus = tokens.focus
    canvas = tokens.canvas
    surface = tokens.surface
    crust = tokens.crust
    raised = tokens.raised
    field = tokens.field
    text = tokens.text
    label = tokens.label
    muted = tokens.muted
    border = tokens.border
    hover = tokens.hover
    accent_hover = tokens.accent_hover
    accent_pressed = tokens.accent_pressed
    accent_soft = tokens.accent_soft
    selection = tokens.selection
    disabled = tokens.disabled
    danger = tokens.danger
    danger_text = tokens.danger_text
    on_accent = tokens.on_accent
    on_danger = tokens.on_danger

    return f"""
{_QSS_START}
QMainWindow,
QDialog,
QMenu,
QToolTip {{
    color: {text};
    font-family: "{font_family}", "PingFang SC", "Microsoft YaHei UI", sans-serif;
}}
QMainWindow,
QDialog {{
    background-color: {canvas};
    color: {text};
}}
QWidget#centralwidget,
QWidget#mainWindow {{
    background-color: {canvas};
}}
QLabel {{
    color: {text};
    background: transparent;
}}
QCheckBox,
QRadioButton {{
    min-height: 20px;
    padding: 2px 0;
    spacing: 8px;
    color: {text};
    background: transparent;
}}
QCheckBox:disabled,
QRadioButton:disabled {{
    color: {disabled};
}}
QFrame {{
    border-color: {border};
}}
QGroupBox {{
    margin-top: 12px;
    padding: 14px 12px 10px;
    border: 1px solid {border};
    border-radius: 10px;
    background-color: transparent;
    font-weight: 600;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 5px;
    color: {label};
    background-color: {canvas};
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
    border-radius: 7px;
    background: transparent;
}}
QMenuBar::item:selected {{
    color: {text};
    background-color: {hover};
}}
QMenu {{
    padding: 6px;
    border: 1px solid {border};
    border-radius: 9px;
    color: {text};
    background-color: {surface};
}}
QMenu::item {{
    min-height: 16px;
    padding: 5px 28px 5px 12px;
    border-radius: 7px;
}}
QMenu::item:selected {{
    color: {text};
    background-color: {hover};
}}
QMenu::item:checked {{
    color: {accent_text};
    font-weight: 600;
}}
QMenu::item:disabled {{
    color: {disabled};
    background: transparent;
}}
QMenu::separator {{
    height: 1px;
    margin: 6px 8px;
    background-color: {border};
}}
QStatusBar {{
    border-top: 1px solid {border};
    color: {muted};
    background-color: {crust};
}}
QStatusBar::item {{ border: 0; }}
QToolTip {{
    padding: 6px 9px;
    border: 1px solid {border};
    border-radius: 7px;
    color: {text};
    background-color: {raised};
}}
QPushButton {{
    min-width: 48px;
    min-height: 20px;
    padding: 7px 12px;
    border: 1px solid {border};
    border-radius: 9px;
    color: {text};
    background-color: {surface};
    font-weight: 600;
}}
QPushButton:hover {{
    border-color: {focus};
    background-color: {accent_soft};
}}
QPushButton:pressed {{
    padding-top: 8px;
    padding-bottom: 6px;
    border-color: {accent_pressed};
    background-color: {raised};
}}
QPushButton:focus {{
    padding: 6px 11px;
    border: 2px solid {focus};
}}
QPushButton:default {{
    border-color: {accent};
    color: {on_accent};
    background-color: {accent};
}}
QPushButton:default:hover {{
    border-color: {accent_hover};
    background-color: {accent_hover};
}}
QPushButton:default:pressed {{
    border-color: {accent_pressed};
    background-color: {accent_pressed};
}}
QPushButton:default:focus {{
    border-color: {focus};
}}
QPushButton:disabled {{
    border-color: {border};
    color: {disabled};
    background-color: {raised};
}}
QPushButton[mistlineRole="primary"] {{
    border-color: {accent};
    color: {on_accent};
    background-color: {accent};
    font-weight: 600;
}}
QPushButton[mistlineRole="primary"]:hover {{
    border-color: {accent_hover};
    background-color: {accent_hover};
}}
QPushButton[mistlineRole="primary"]:pressed {{
    border-color: {accent_pressed};
    background-color: {accent_pressed};
}}
QPushButton[mistlineRole="primary"]:focus {{
    padding: 6px 11px;
    border: 2px solid {focus};
}}
QPushButton[mistlineRole="primary"]:disabled {{
    border-color: {border};
    color: {disabled};
    background-color: {raised};
}}
QPushButton[mistlineRole="secondary"] {{
    border-color: {focus};
    color: {accent_text};
    background-color: {surface};
}}
QPushButton[mistlineRole="secondary"]:hover {{
    border-color: {focus};
    background-color: {accent_soft};
}}
QPushButton[mistlineRole="secondary"]:pressed {{
    border-color: {accent_pressed};
    background-color: {raised};
}}
QPushButton[mistlineRole="secondary"]:focus {{
    padding: 6px 11px;
    border: 2px solid {focus};
}}
QPushButton[mistlineRole="secondary"]:disabled {{
    border-color: {border};
    color: {disabled};
    background-color: {raised};
}}
QPushButton[mistlineRole="destructive"] {{
    border-color: {danger_text};
    color: {danger_text};
    background-color: {surface};
}}
QPushButton[mistlineRole="destructive"]:hover {{
    border-color: {danger};
    color: {on_danger};
    background-color: {danger};
}}
QPushButton[mistlineRole="destructive"]:pressed {{
    border-color: {danger};
    color: {on_danger};
    background-color: {danger};
}}
QPushButton[mistlineRole="destructive"]:focus {{
    padding: 6px 11px;
    border: 2px solid {danger_text};
}}
QPushButton[mistlineRole="destructive"]:disabled {{
    border-color: {border};
    color: {disabled};
    background-color: {raised};
}}
QPushButton[mistlineRole="quiet"] {{
    border-color: transparent;
    color: {muted};
    background: transparent;
    font-weight: 400;
}}
QPushButton[mistlineRole="quiet"]:hover {{
    border-color: transparent;
    color: {text};
    background-color: {hover};
}}
QPushButton[mistlineRole="quiet"]:pressed {{
    border-color: {accent_pressed};
    color: {text};
    background-color: {raised};
}}
QPushButton[mistlineRole="quiet"]:focus {{
    padding: 6px 11px;
    border: 2px solid {focus};
}}
QPushButton[mistlineRole="quiet"]:disabled {{
    border-color: transparent;
    color: {disabled};
    background: transparent;
}}
QPushButton[mistlineRole="chooser"] {{
    min-height: 24px;
    padding: 7px 12px;
    border-color: {border};
    color: {text};
    background-color: {field};
    font-weight: 400;
    text-align: left;
}}
QPushButton[mistlineRole="chooser"]:hover {{
    border-color: {focus};
    background-color: {accent_soft};
}}
QPushButton[mistlineRole="chooser"]:pressed {{
    border-color: {accent_pressed};
    background-color: {raised};
}}
QPushButton[mistlineRole="chooser"]:focus {{
    padding: 6px 11px;
    border: 2px solid {focus};
}}
QPushButton[mistlineRole="chooser"]:disabled {{
    border-color: {border};
    color: {disabled};
    background-color: {raised};
}}
QLabel[mistlineRole="fieldLabel"] {{
    color: {label};
    font-weight: 600;
}}
QWidget[mistlineRole="actionbar"] {{
    margin-top: 2px;
    padding-top: 10px;
    border-top: 1px solid {border};
    background-color: {crust};
}}
QWidget[mistlineRole="actionbar"] QPushButton {{
    min-height: 20px;
}}
QWidget[mistlineRole="editorCanvas"] {{
    background-color: {canvas};
}}
QDialogButtonBox QPushButton {{
    min-width: 72px;
}}
QToolBar {{
    padding: 4px;
    border: 0;
    border-bottom: 1px solid {border};
    spacing: 4px;
    background-color: {surface};
}}
QToolBar::separator {{
    width: 1px;
    margin: 5px 6px;
    background-color: {border};
}}
QToolButton {{
    min-width: 20px;
    min-height: 20px;
    border: 1px solid transparent;
    border-radius: 8px;
    padding: 5px;
    color: {text};
    background: transparent;
}}
QToolButton:hover {{
    border-color: {focus};
    background-color: {accent_soft};
}}
QToolButton:pressed {{
    border-color: {accent_pressed};
    background-color: {raised};
}}
QToolButton:focus {{
    padding: 4px;
    border: 2px solid {focus};
}}
QToolButton:checked {{
    border-color: {focus};
    color: {accent_text};
    background-color: {accent_soft};
}}
QToolButton:disabled {{
    border-color: transparent;
    color: {disabled};
    background: transparent;
}}
QLineEdit,
QTextEdit,
QPlainTextEdit,
QComboBox,
QSpinBox,
QDoubleSpinBox,
QDateEdit,
QTimeEdit,
QDateTimeEdit,
QKeySequenceEdit {{
    min-height: 20px;
    padding: 5px 9px;
    border: 1px solid {border};
    border-radius: 8px;
    color: {text};
    selection-color: {text};
    selection-background-color: {selection};
    background-color: {field};
}}
QLineEdit:focus,
QTextEdit:focus,
QPlainTextEdit:focus,
QComboBox:focus,
QSpinBox:focus,
QDoubleSpinBox:focus,
QDateEdit:focus,
QTimeEdit:focus,
QDateTimeEdit:focus,
QKeySequenceEdit:focus {{
    padding: 4px 8px;
    border: 2px solid {focus};
}}
QLineEdit:disabled,
QTextEdit:disabled,
QPlainTextEdit:disabled,
QComboBox:disabled,
QSpinBox:disabled,
QDoubleSpinBox:disabled,
QDateEdit:disabled,
QTimeEdit:disabled,
QDateTimeEdit:disabled,
QKeySequenceEdit:disabled {{
    color: {disabled};
    background-color: {raised};
}}
QComboBox {{
    padding-right: 30px;
}}
QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 26px;
    border: 0;
    border-left: 1px solid {border};
    background: transparent;
}}
QComboBox::drop-down:hover {{
    background-color: {accent_soft};
}}
QComboBox:disabled {{
    color: {disabled};
    background-color: {raised};
}}
QSpinBox,
QDoubleSpinBox,
QDateEdit,
QTimeEdit,
QDateTimeEdit {{
    padding-right: 28px;
}}
QSpinBox::up-button,
QSpinBox::down-button,
QDoubleSpinBox::up-button,
QDoubleSpinBox::down-button,
QDateEdit::up-button,
QDateEdit::down-button,
QTimeEdit::up-button,
QTimeEdit::down-button,
QDateTimeEdit::up-button,
QDateTimeEdit::down-button {{
    subcontrol-origin: border;
    width: 22px;
    border: 0;
    border-left: 1px solid {border};
    background-color: {raised};
}}
QSpinBox::up-button,
QDoubleSpinBox::up-button,
QDateEdit::up-button,
QTimeEdit::up-button,
QDateTimeEdit::up-button {{
    subcontrol-position: top right;
    border-bottom: 1px solid {border};
    border-top-right-radius: 7px;
}}
QSpinBox::down-button,
QDoubleSpinBox::down-button,
QDateEdit::down-button,
QTimeEdit::down-button,
QDateTimeEdit::down-button {{
    subcontrol-position: bottom right;
    border-bottom-right-radius: 7px;
}}
QSpinBox::up-button:hover,
QSpinBox::down-button:hover,
QDoubleSpinBox::up-button:hover,
QDoubleSpinBox::down-button:hover,
QDateEdit::up-button:hover,
QDateEdit::down-button:hover,
QTimeEdit::up-button:hover,
QTimeEdit::down-button:hover,
QDateTimeEdit::up-button:hover,
QDateTimeEdit::down-button:hover {{
    background-color: {hover};
}}
QComboBox QAbstractItemView {{
    padding: 4px;
    border: 1px solid {border};
    border-radius: 8px;
    background-color: {surface};
    selection-color: {text};
    selection-background-color: {selection};
}}
QAbstractScrollArea {{
    border: 1px solid {border};
    border-radius: 8px;
    background-color: {surface};
}}
QScrollArea {{
    background-color: {surface};
}}
QScrollArea > QWidget > QWidget {{
    background-color: transparent;
}}
QAbstractItemView {{
    border: 1px solid {border};
    border-radius: 8px;
    color: {text};
    alternate-background-color: {canvas};
    background-color: {surface};
    selection-color: {text};
    selection-background-color: {selection};
    outline: 0;
}}
QAbstractItemView::item {{
    min-height: 20px;
    padding: 4px 7px;
    border: 0;
}}
QAbstractItemView::item:hover {{
    background-color: {accent_soft};
}}
QHeaderView {{
    background-color: {canvas};
}}
QHeaderView::section {{
    padding: 7px 9px;
    border: 0;
    border-right: 1px solid {border};
    border-bottom: 1px solid {border};
    color: {label};
    background-color: {raised};
    font-weight: 600;
}}
QTableCornerButton::section {{
    border: 0;
    border-right: 1px solid {border};
    border-bottom: 1px solid {border};
    background-color: {raised};
}}
QTabWidget::pane {{
    border: 1px solid {border};
    border-radius: 9px;
    background-color: {surface};
}}
QTabBar::tab {{
    min-height: 18px;
    padding: 7px 13px;
    margin-right: 3px;
    border: 1px solid {border};
    border-radius: 8px;
    color: {muted};
    background-color: {surface};
}}
QTabBar::tab:hover {{
    border-color: {focus};
    color: {text};
    background-color: {accent_soft};
}}
QTabBar::tab:selected {{
    border-color: {focus};
    color: {accent_text};
    background-color: {accent_soft};
    font-weight: 600;
}}
QDockWidget {{
    color: {text};
    background-color: {canvas};
}}
QDockWidget::title {{
    padding: 7px 10px;
    border-bottom: 1px solid {border};
    color: {muted};
    background-color: {surface};
}}
QSplitter::handle {{
    background-color: {border};
}}
QSplitter::handle:hover {{
    background-color: {accent};
}}
QSlider::groove:horizontal {{
    height: 4px;
    border-radius: 2px;
    background-color: {raised};
}}
QSlider::sub-page:horizontal {{
    border-radius: 2px;
    background-color: {accent};
}}
QSlider::handle:horizontal {{
    width: 16px;
    margin: -6px 0;
    border: 1px solid {focus};
    border-radius: 8px;
    background-color: {surface};
}}
QSlider::handle:horizontal:hover {{
    background-color: {accent_soft};
}}
QSlider::groove:vertical {{
    width: 4px;
    border-radius: 2px;
    background-color: {raised};
}}
QSlider::sub-page:vertical {{
    border-radius: 2px;
    background-color: {accent};
}}
QSlider::handle:vertical {{
    height: 16px;
    margin: 0 -6px;
    border: 1px solid {focus};
    border-radius: 8px;
    background-color: {surface};
}}
QSlider::handle:vertical:hover {{
    background-color: {accent_soft};
}}
QProgressBar {{
    min-height: 14px;
    border: 1px solid {border};
    border-radius: 7px;
    color: {text};
    background-color: {raised};
    text-align: center;
}}
QProgressBar::chunk {{
    border-radius: 6px;
    background-color: {accent};
}}
QScrollBar:vertical {{
    width: 12px;
    margin: 2px;
    border: 0;
    background: transparent;
}}
QScrollBar::handle:vertical {{
    min-height: 32px;
    border-radius: 5px;
    background-color: {border};
}}
QScrollBar::handle:vertical:hover {{
    background-color: {muted};
}}
QScrollBar:horizontal {{
    height: 12px;
    margin: 2px;
    border: 0;
    background: transparent;
}}
QScrollBar::handle:horizontal {{
    min-width: 32px;
    border-radius: 5px;
    background-color: {border};
}}
QScrollBar::handle:horizontal:hover {{
    background-color: {muted};
}}
QScrollBar::add-line,
QScrollBar::sub-line,
QScrollBar::add-page,
QScrollBar::sub-page {{
    width: 0;
    height: 0;
    background: transparent;
}}
QDialog#Preferences {{
    background-color: {canvas};
}}
QDialog#Preferences QTabWidget#tabWidget::pane {{
    margin-top: 8px;
    border-color: {border};
    background-color: {surface};
}}
QDialog#Preferences QGroupBox {{
    margin-top: 14px;
    padding: 16px 12px 10px;
    background-color: {surface};
}}
QDialog#Preferences QGroupBox::title {{
    background-color: {surface};
}}
QDialog#Preferences QPushButton#resetWindowSizes,
QDialog#Preferences QPushButton#resetWindowSizes:default {{
    border-color: {border};
    color: {text};
    background-color: {field};
}}
QDialog#Preferences QPushButton#resetWindowSizes:hover {{
    border-color: {focus};
    color: {accent_text};
    background-color: {accent_soft};
}}
QDialog#Preferences QPushButton#resetWindowSizes:pressed {{
    border-color: {accent_pressed};
    color: {text};
    background-color: {raised};
}}
QDialog#Preferences QPushButton#resetWindowSizes:focus {{
    padding: 6px 11px;
    border: 2px solid {focus};
}}
QDialog#Preferences QDialogButtonBox {{
    padding-top: 8px;
    background: transparent;
}}
{_QSS_END}
"""


def _without_owned_qss(style: str) -> str:
    """Remove every previously injected block without touching Anki's QSS."""

    remaining = style
    while _QSS_START in remaining:
        before, _marker, after_start = remaining.partition(_QSS_START)
        _owned, end_marker, after = after_start.partition(_QSS_END)
        if not end_marker:
            # A partial block should not make us discard unrelated trailing QSS.
            return before.rstrip()
        remaining = f"{before}{after}"
    return remaining.rstrip()


def extend_native_style(style: str, config: dict[str, Any]) -> str:
    """Return Anki's stylesheet with exactly one owned theme block appended."""

    base = _without_owned_qss(style)
    should_apply = bool(config.get("enabled")) and bool(
        config.get("style_native_chrome")
    )
    if not should_apply:
        return base

    font_family = _register_native_fonts()
    owned = _build_qss_for_config(config, _theme_is_dark(), font_family).strip()
    return f"{base}\n{owned}" if base else owned


def _application_style_target(main_window: Any) -> Any:
    """Use QApplication so future standalone windows inherit the theme."""

    try:
        from aqt.qt import QApplication

        application = QApplication.instance()
        if application is not None:
            return application
    except Exception:
        pass
    return main_window


def _clone_palette(palette: Any, palette_type: Any) -> Any:
    try:
        return palette_type(palette)
    except Exception:
        try:
            return palette.copy()
        except Exception:
            return palette


def _palettes_equal(left: Any, right: Any) -> bool:
    try:
        return bool(left == right)
    except Exception:
        # If a binding does not expose comparison, restoring the recorded
        # baseline is safer than leaving our colors behind after opt-out.
        return True


def _palette_from_tokens(base_palette: Any, tokens: _ThemeTokens) -> Any | None:
    """Create a palette from the same tokens that render the QSS."""

    try:
        from aqt.qt import QColor, QPalette
    except Exception:
        return None

    palette = _clone_palette(base_palette, QPalette)
    if palette is base_palette:
        # Never mutate the baseline in place. Older or partial Qt bindings can
        # safely fall back to the owned stylesheet instead.
        return None
    color_role = getattr(QPalette, "ColorRole", QPalette)
    roles = {
        "Window": tokens.canvas,
        "WindowText": tokens.text,
        "Base": tokens.field,
        "AlternateBase": tokens.surface,
        "ToolTipBase": tokens.raised,
        "ToolTipText": tokens.text,
        "Text": tokens.text,
        "Button": tokens.surface,
        "ButtonText": tokens.text,
        "BrightText": tokens.on_accent,
        "Highlight": tokens.selection,
        "HighlightedText": tokens.text,
        "Link": tokens.link,
        "LinkVisited": tokens.link,
        "PlaceholderText": tokens.muted,
        "Light": tokens.raised,
        "Midlight": tokens.raised,
        "Mid": tokens.border,
        "Dark": tokens.muted,
        "Shadow": tokens.text,
    }
    for role_name, color_value in roles.items():
        role = getattr(color_role, role_name, None)
        if role is None:
            continue
        try:
            palette.setColor(role, QColor(color_value))
        except Exception:
            continue

    color_group = getattr(QPalette, "ColorGroup", None)
    disabled_group = getattr(color_group, "Disabled", None)
    if disabled_group is not None:
        for role_name in ("WindowText", "Text", "ButtonText", "PlaceholderText"):
            role = getattr(color_role, role_name, None)
            if role is None:
                continue
            try:
                palette.setColor(disabled_group, role, QColor(tokens.disabled))
            except Exception:
                continue
        for role_name, color_value in (
            ("Base", tokens.raised),
            ("Button", tokens.raised),
            ("Highlight", tokens.border),
            ("HighlightedText", tokens.disabled),
        ):
            role = getattr(color_role, role_name, None)
            if role is None:
                continue
            try:
                palette.setColor(disabled_group, role, QColor(color_value))
            except Exception:
                continue

    return palette


def _restore_application_palette(target: Any) -> None:
    """Restore our exact pre-theme palette without undoing a newer owner."""

    global _palette_target, _palette_before_theme, _palette_owned
    if target is not _palette_target:
        return

    try:
        from aqt.qt import QPalette

        current = target.palette()
        if _palette_before_theme is not None and (
            _palette_owned is None or _palettes_equal(current, _palette_owned)
        ):
            target.setPalette(_clone_palette(_palette_before_theme, QPalette))
    except Exception:
        pass
    finally:
        _palette_target = None
        _palette_before_theme = None
        _palette_owned = None


def _apply_application_palette(target: Any, tokens: _ThemeTokens) -> None:
    """Install an owned palette while retaining a reversible baseline."""

    global _palette_target, _palette_before_theme, _palette_owned
    if not hasattr(target, "palette") or not hasattr(target, "setPalette"):
        return

    if _palette_target is not None and _palette_target is not target:
        _restore_application_palette(_palette_target)

    try:
        from aqt.qt import QPalette

        current = _clone_palette(target.palette(), QPalette)
        if _palette_target is not target:
            _palette_target = target
            _palette_before_theme = current
            _palette_owned = None
        elif _palette_owned is not None and not _palettes_equal(current, _palette_owned):
            # Anki/Qt replaced the palette after a light/dark or platform-style
            # change. Treat that newer palette as the baseline rather than
            # restoring stale colors when Editorial Index is disabled.
            _palette_before_theme = current

        themed = _palette_from_tokens(_palette_before_theme, tokens)
        if themed is None:
            return
        target.setPalette(themed)
        _palette_owned = _clone_palette(themed, QPalette)
    except Exception:
        # Palette coverage is additive; QSS remains the compatibility path for
        # Qt bindings that omit one of the APIs above.
        return


def apply_native_theme(main_window: Any, config: dict[str, Any]) -> None:
    """Replace only our owned QSS/palette, preserving Anki and other add-ons."""

    target = _application_style_target(main_window)
    should_apply = bool(config.get("enabled")) and bool(
        config.get("style_native_chrome")
    )
    if should_apply:
        _apply_application_palette(
            target,
            _build_tokens_for_config(config, _theme_is_dark()),
        )
    else:
        _restore_application_palette(target)
    target.setStyleSheet(extend_native_style(target.styleSheet(), config))
