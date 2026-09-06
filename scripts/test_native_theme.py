#!/usr/bin/env python3
"""Focused tests for Editorial Index's reversible native Qt theme."""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "addon" / "native_theme.py"


class FakeColor(str):
    pass


class FakePalette:
    class ColorRole:
        Window = "Window"
        WindowText = "WindowText"
        Base = "Base"
        AlternateBase = "AlternateBase"
        ToolTipBase = "ToolTipBase"
        ToolTipText = "ToolTipText"
        Text = "Text"
        Button = "Button"
        ButtonText = "ButtonText"
        BrightText = "BrightText"
        Highlight = "Highlight"
        HighlightedText = "HighlightedText"
        Link = "Link"
        LinkVisited = "LinkVisited"
        PlaceholderText = "PlaceholderText"
        Light = "Light"
        Midlight = "Midlight"
        Mid = "Mid"
        Dark = "Dark"
        Shadow = "Shadow"

    class ColorGroup:
        Disabled = "Disabled"

    def __init__(self, other: "FakePalette | None" = None) -> None:
        self.colors = dict(other.colors) if other is not None else {}

    def setColor(self, *args: object) -> None:
        if len(args) == 2:
            role, color = args
            self.colors[("All", role)] = str(color)
        elif len(args) == 3:
            group, role, color = args
            self.colors[(group, role)] = str(color)
        else:
            raise TypeError("unexpected setColor overload")

    def __eq__(self, other: object) -> bool:
        return isinstance(other, FakePalette) and self.colors == other.colors


class FakeFontDatabase:
    @staticmethod
    def addApplicationFont(_path: str) -> int:
        return -1

    @staticmethod
    def applicationFontFamilies(_font_id: int) -> list[str]:
        return []


class FakeApplication:
    _instance: "FakeApplication | None" = None

    def __init__(self) -> None:
        self._style = "anki-style"
        self._palette = FakePalette()
        self._palette.setColor(FakePalette.ColorRole.Window, FakeColor("original-window"))
        FakeApplication._instance = self

    @classmethod
    def instance(cls) -> "FakeApplication | None":
        return cls._instance

    def styleSheet(self) -> str:
        return self._style

    def setStyleSheet(self, style: str) -> None:
        self._style = style

    def palette(self) -> FakePalette:
        return FakePalette(self._palette)

    def setPalette(self, palette: FakePalette) -> None:
        self._palette = FakePalette(palette)


def load_module():
    aqt = types.ModuleType("aqt")
    qt = types.ModuleType("aqt.qt")
    qt.QApplication = FakeApplication
    qt.QColor = FakeColor
    qt.QFontDatabase = FakeFontDatabase
    qt.QPalette = FakePalette
    theme = types.ModuleType("aqt.theme")
    theme.theme_manager = types.SimpleNamespace(night_mode=False)
    sys.modules["aqt"] = aqt
    sys.modules["aqt.qt"] = qt
    sys.modules["aqt.theme"] = theme

    spec = importlib.util.spec_from_file_location("native_theme_under_test", SOURCE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    addon_dir = str(SOURCE.parent)
    sys.path.insert(0, addon_dir)
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.remove(addon_dir)
    return module


def main() -> None:
    native = load_module()
    colors = sys.modules["color_themes"]
    tokens = native._build_tokens("#2F5BBC", False)
    qss = native._build_qss("#2F5BBC", False)
    dark_tokens = native._build_tokens("#2F5BBC", True)

    assert tokens.accent == "#2F5BBC"
    assert tokens.on_accent == "#FFFFFF"
    assert tokens.on_danger == "#FFFFFF"
    assert dark_tokens.accent == "#7894D3"
    assert dark_tokens.on_accent == "#1D1D1B"
    assert dark_tokens.on_danger == "#1D1D1B"
    assert tokens.family == "editorial"
    assert qss == native._build_qss_for_config(
        {"color_theme": "editorial", "accent_color": "#2F5BBC"}, False
    )

    assert tokens.canvas in qss
    assert tokens.accent in qss
    assert tokens.on_accent in qss
    assert tokens.on_danger in qss
    assert 'QPushButton[mistlineRole="destructive"]:hover' in qss
    assert 'QPushButton[mistlineRole="destructive"]:disabled' in qss
    assert f"color: {tokens.on_danger};\n    background-color: {tokens.danger};" in qss
    assert (
        f'QPushButton[mistlineRole="destructive"]:disabled {{\n'
        f"    border-color: {tokens.border};\n"
        f"    color: {tokens.disabled};\n"
        f"    background-color: {tokens.raised};\n"
        "}"
    ) in qss

    # Destructive controls use text chosen from their own fixed danger token,
    # not from an unrelated user accent that may be much lighter or darker.
    pale_accent_qss = native._build_qss("#FFF2A8", False)
    deep_accent_qss = native._build_qss("#101820", True)
    assert "color: #FFFFFF;\n    background-color: #B9382F;" in pale_accent_qss
    assert "color: #1D1D1B;\n    background-color: #E16D61;" in deep_accent_qss
    for role in (
        "primary",
        "secondary",
        "destructive",
        "quiet",
        "chooser",
        "fieldLabel",
        "actionbar",
        "editorCanvas",
    ):
        assert f'mistlineRole="{role}"' in qss
    for selector in (
        "QCheckBox,",
        "QRadioButton",
        "QSlider::groove:horizontal",
        "QAbstractScrollArea",
        "QTableCornerButton::section",
        "QMenu::item:disabled",
        "QMenu::item:checked",
        "QComboBox::drop-down",
        "QSpinBox::up-button",
        "QDialog#Preferences",
        "QPushButton#resetWindowSizes",
    ):
        assert selector in qss
    assert "QCheckBox::indicator" not in qss
    assert "QRadioButton::indicator" not in qss
    assert "QPushButton {\n    min-width: 48px;\n    min-height: 20px;" in qss
    assert "QTabBar::tab {\n    min-height: 18px;" in qss
    # A thicker selected/focus border must consume padding, not grow the tile.
    assert 'QPushButton[mistlineRole="paletteChoice"] {\n    min-height: 26px;\n    padding: 8px 11px;\n    border: 1px solid' in qss
    for state in ("focus", "checked"):
        assert (f'QPushButton[mistlineRole="paletteChoice"]:{state} {{\n'
                f'    border: 2px solid {tokens.focus};\n    padding: 7px 10px;') in qss

    # Every official Catppuccin flavor/accent pair resolves through the same
    # token contract that the web surfaces use. Raw swatches remain exact,
    # while text and focus roles meet their contrast targets.
    expected_blue = {
        "latte": ("#EFF1F5", "#1E66F5", False),
        "frappe": ("#303446", "#8CAAEE", True),
        "macchiato": ("#24273A", "#8AADF4", True),
        "mocha": ("#1E1E2E", "#89B4FA", True),
    }
    for flavor, (base, blue, is_dark) in expected_blue.items():
        blue_tokens = native._build_tokens_for_config(
            {
                "color_theme": "catppuccin",
                "catppuccin_flavor": flavor,
                "catppuccin_accent": "blue",
            },
            False,
        )
        assert blue_tokens.family == "catppuccin"
        assert blue_tokens.flavor == flavor
        assert blue_tokens.canvas == base
        assert blue_tokens.accent == blue
        assert blue_tokens.accent_raw == blue
        assert blue_tokens.surface == blue_tokens.palette["mantle"]
        assert blue_tokens.crust == blue_tokens.palette["crust"]
        assert blue_tokens.raised == blue_tokens.palette["surface0"]
        assert blue_tokens.field == blue_tokens.palette["surface0"]
        assert blue_tokens.link == colors._chromatic_text(
            blue_tokens.palette["blue"],
            (
                blue_tokens.canvas,
                blue_tokens.surface,
                blue_tokens.raised,
                blue_tokens.field,
            ),
            4.5,
            blue_tokens.dark,
        )
        assert blue_tokens.dark is is_dark

        for accent_name in colors.CATPPUCCIN_ACCENTS:
            flavor_tokens = native._build_tokens_for_config(
                {
                    "color_theme": "catppuccin",
                    "catppuccin_flavor": flavor,
                    "catppuccin_accent": accent_name,
                },
                not is_dark,
            )
            assert flavor_tokens.accent == colors.catppuccin_color(
                flavor, accent_name
            )
            assert min(
                colors.contrast_ratio(flavor_tokens.accent_text, background)
                for background in (
                    flavor_tokens.canvas,
                    flavor_tokens.surface,
                    flavor_tokens.raised,
                )
            ) >= 4.5
            assert min(
                colors.contrast_ratio(flavor_tokens.focus, background)
                for background in (
                    flavor_tokens.canvas,
                    flavor_tokens.surface,
                    flavor_tokens.raised,
                    flavor_tokens.field,
                )
            ) >= 3.0
            assert min(
                colors.contrast_ratio(flavor_tokens.disabled, background)
                for background in (
                    flavor_tokens.canvas,
                    flavor_tokens.surface,
                    flavor_tokens.raised,
                    flavor_tokens.field,
                )
            ) >= 3.0
            assert min(
                colors.contrast_ratio(flavor_tokens.on_accent, background)
                for background in (
                    flavor_tokens.accent,
                    flavor_tokens.accent_hover,
                    flavor_tokens.accent_pressed,
                )
            ) >= 4.5

    auto_light = native._build_tokens_for_config(
        {
            "color_theme": "catppuccin",
            "catppuccin_flavor": "auto",
            "catppuccin_accent": "blue",
        },
        False,
    )
    auto_dark = native._build_tokens_for_config(
        {
            "color_theme": "catppuccin",
            "catppuccin_flavor": "auto",
            "catppuccin_accent": "blue",
        },
        True,
    )
    assert auto_light.flavor == "latte"
    assert auto_dark.flavor == "mocha"

    auto_enabled = {
        "enabled": True,
        "style_native_chrome": True,
        "color_theme": "catppuccin",
        "catppuccin_flavor": "auto",
        "catppuccin_accent": "blue",
    }
    theme_manager = sys.modules["aqt.theme"].theme_manager
    theme_manager.night_mode = False
    assert auto_light.canvas in native.extend_native_style(
        "anki-style", auto_enabled
    )
    theme_manager.night_mode = True
    assert auto_dark.canvas in native.extend_native_style(
        "anki-style", auto_enabled
    )
    theme_manager.night_mode = False

    latte_yellow_config = {
        "color_theme": "catppuccin",
        "catppuccin_flavor": "latte",
        "catppuccin_accent": "yellow",
    }
    latte_yellow = native._build_tokens_for_config(latte_yellow_config, False)
    latte_yellow_qss = native._build_qss_for_config(
        latte_yellow_config, False
    )
    assert latte_yellow.accent == "#DF8E1D"
    assert latte_yellow.accent_text != latte_yellow.accent
    assert (
        f'QPushButton[mistlineRole="primary"] {{\n'
        f"    border-color: {latte_yellow.accent};\n"
        f"    color: {latte_yellow.on_accent};\n"
        f"    background-color: {latte_yellow.accent};"
    ) in latte_yellow_qss
    assert (
        f'QPushButton[mistlineRole="secondary"] {{\n'
        f"    border-color: {latte_yellow.focus};\n"
        f"    color: {latte_yellow.accent_text};"
    ) in latte_yellow_qss
    assert f"border: 2px solid {latte_yellow.focus};" in latte_yellow_qss
    assert (
        f"QMenu::item:checked {{\n    color: {latte_yellow.accent_text};"
        in latte_yellow_qss
    )

    app = FakeApplication()
    original_palette = app.palette()
    enabled = {
        "enabled": True,
        "style_native_chrome": True,
        "accent_color": "#2F5BBC",
    }
    native.apply_native_theme(object(), enabled)
    assert "mistline-native-theme:start" in app.styleSheet()
    assert app.palette() != original_palette
    assert app.palette().colors[("All", FakePalette.ColorRole.Window)] == tokens.canvas
    assert app.palette().colors[("All", FakePalette.ColorRole.Highlight)] == tokens.selection

    enabled["accent_color"] = "#A4502A"
    native.apply_native_theme(object(), enabled)
    custom_tokens = native._build_tokens("#A4502A", False)
    assert (
        app.palette().colors[("All", FakePalette.ColorRole.Highlight)]
        == custom_tokens.selection
    )

    disabled = {**enabled, "enabled": False}
    native.apply_native_theme(object(), disabled)
    assert app.styleSheet() == "anki-style"
    assert app.palette() == original_palette

    # If Anki replaces the palette (for example during a light/dark change),
    # disabling the add-on must not overwrite that newer external palette.
    enabled["enabled"] = True
    native.apply_native_theme(object(), enabled)
    external_palette = FakePalette()
    external_palette.setColor(FakePalette.ColorRole.Window, FakeColor("new-anki-window"))
    app.setPalette(external_palette)
    native.apply_native_theme(object(), disabled)
    assert app.palette() == external_palette

    # A later enable/disable cycle now owns and restores that newer baseline.
    native.apply_native_theme(object(), enabled)
    assert app.palette() != external_palette
    native.apply_native_theme(object(), disabled)
    assert app.palette() == external_palette

    # QPalette mirrors the upstream semantic split: Overlay 2 tint for
    # selection, normal Text on that tint, and Blue for links. This catches
    # regressions that QSS-only fixtures cannot see.
    catppuccin_enabled = {
        **latte_yellow_config,
        "enabled": True,
        "style_native_chrome": True,
    }
    native.apply_native_theme(object(), catppuccin_enabled)
    cat_palette = app.palette().colors
    assert cat_palette[("All", FakePalette.ColorRole.Window)] == latte_yellow.canvas
    assert (
        cat_palette[("All", FakePalette.ColorRole.Highlight)]
        == latte_yellow.selection
    )
    assert (
        cat_palette[("All", FakePalette.ColorRole.HighlightedText)]
        == latte_yellow.text
    )
    assert (
        cat_palette[("All", FakePalette.ColorRole.Link)]
        == latte_yellow.link
    )
    native.apply_native_theme(object(), {**catppuccin_enabled, "enabled": False})
    assert app.palette() == external_palette

    print("Editorial Index + Catppuccin native Qt theme tests passed")


if __name__ == "__main__":
    main()
