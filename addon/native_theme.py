"""Reversible application-level Qt stylesheet for Editorial Index."""

from __future__ import annotations

from pathlib import Path
from typing import Any

_native_fonts_registered = False
_native_font_family = "Inter"

_QSS_START = "/* mistline-native-theme:start */"
_QSS_END = "/* mistline-native-theme:end */"


def _mix_hex(source: str, target: str, target_weight: float) -> str:
    """Mix two #RRGGBB colors without depending on a live Qt application."""

    try:
        source_channels = [int(source[index : index + 2], 16) for index in (1, 3, 5)]
        target_channels = [int(target[index : index + 2], 16) for index in (1, 3, 5)]
    except (TypeError, ValueError):
        return source

    weight = min(1.0, max(0.0, target_weight))
    mixed = [
        round(source_channel * (1 - weight) + target_channel * weight)
        for source_channel, target_channel in zip(source_channels, target_channels)
    ]
    return "#" + "".join(f"{channel:02X}" for channel in mixed)


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
        field = "#27231E"
        text = "#F1EADF"
        muted = "#B3AB9E"
        border = "#514A40"
        hover = "#302B25"
        accent_hover = _mix_hex(accent, "#FFFFFF", 0.14)
        accent_pressed = _mix_hex(accent, "#000000", 0.16)
    else:
        canvas = "#F1EDE4"
        surface = "#F8F5ED"
        raised = "#E7E0D4"
        field = "#FCFAF4"
        text = "#1D1D1B"
        muted = "#77736B"
        border = "#CFC8BC"
        hover = "#E7E0D4"
        accent_hover = _mix_hex(accent, "#FFFFFF", 0.12)
        accent_pressed = _mix_hex(accent, "#000000", 0.14)

    accent_soft = _mix_hex(accent, surface, 0.86)
    selection = _mix_hex(accent, surface, 0.74)
    disabled = _mix_hex(muted, surface, 0.62)

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
    color: {muted};
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
    min-height: 26px;
    padding: 6px 28px 6px 12px;
    border-radius: 7px;
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
    padding: 6px 9px;
    border: 1px solid {border};
    border-radius: 7px;
    color: {text};
    background-color: {raised};
}}
QPushButton {{
    min-width: 48px;
    min-height: 34px;
    padding: 7px 12px;
    border: 1px solid {border};
    border-radius: 9px;
    color: {text};
    background-color: {surface};
    font-weight: 600;
}}
QPushButton:hover {{
    border-color: {accent};
    background-color: {accent_soft};
}}
QPushButton:pressed {{
    padding-top: 8px;
    padding-bottom: 6px;
    border-color: {accent_pressed};
    background-color: {raised};
}}
QPushButton:focus {{
    border: 2px solid {accent};
}}
QPushButton:default {{
    border-color: {accent};
    color: #FFFFFF;
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
QPushButton:disabled {{
    border-color: {border};
    color: {disabled};
    background-color: {raised};
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
    min-width: 28px;
    min-height: 28px;
    border: 1px solid transparent;
    border-radius: 8px;
    padding: 4px 6px;
    color: {text};
    background: transparent;
}}
QToolButton:hover {{
    border-color: {accent};
    background-color: {accent_soft};
}}
QToolButton:pressed {{
    border-color: {accent_pressed};
    background-color: {raised};
}}
QToolButton:checked {{
    border-color: {accent};
    color: {accent};
    background-color: {accent_soft};
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
    min-height: 32px;
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
QDoubleSpinBox:focus {{
    border: 2px solid {accent};
}}
QComboBox {{
    padding-right: 28px;
}}
QComboBox::drop-down {{
    width: 24px;
    border: 0;
    border-left: 1px solid {border};
    background-color: {raised};
}}
QComboBox QAbstractItemView {{
    padding: 4px;
    border: 1px solid {border};
    border-radius: 8px;
    background-color: {surface};
    selection-color: {text};
    selection-background-color: {selection};
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
    min-height: 28px;
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
    color: {muted};
    background-color: {raised};
    font-weight: 600;
}}
QTabWidget::pane {{
    border: 1px solid {border};
    border-radius: 9px;
    background-color: {surface};
}}
QTabBar::tab {{
    min-height: 30px;
    padding: 7px 13px;
    margin-right: 3px;
    border: 1px solid {border};
    border-radius: 8px;
    color: {muted};
    background-color: {surface};
}}
QTabBar::tab:hover {{
    border-color: {accent};
    color: {text};
    background-color: {accent_soft};
}}
QTabBar::tab:selected {{
    border-color: {accent};
    color: {accent};
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

    accent = str(config.get("accent_color", "#315FC4"))
    font_family = _register_native_fonts()
    owned = _build_qss(accent, _theme_is_dark(), font_family).strip()
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


def apply_native_theme(main_window: Any, config: dict[str, Any]) -> None:
    """Replace only our global QSS block, preserving Anki and other add-ons."""

    target = _application_style_target(main_window)
    target.setStyleSheet(extend_native_style(target.styleSheet(), config))
