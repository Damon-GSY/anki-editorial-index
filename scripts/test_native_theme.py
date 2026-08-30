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
    spec.loader.exec_module(module)
    return module


def main() -> None:
    native = load_module()
    tokens = native._build_tokens("#2F5BBC", False)
    qss = native._build_qss("#2F5BBC", False)
    dark_tokens = native._build_tokens("#2F5BBC", True)

    assert tokens.accent == "#2F5BBC"
    assert tokens.on_accent == "#FFFFFF"
    assert tokens.on_danger == "#FFFFFF"
    assert dark_tokens.accent == "#7894D3"
    assert dark_tokens.on_accent == "#1D1D1B"
    assert dark_tokens.on_danger == "#1D1D1B"

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
    assert app.palette().colors[("All", FakePalette.ColorRole.Highlight)] == tokens.accent

    enabled["accent_color"] = "#A4502A"
    native.apply_native_theme(object(), enabled)
    assert app.palette().colors[("All", FakePalette.ColorRole.Highlight)] == "#A4502A"

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

    print("Editorial Index native Qt theme tests passed")


if __name__ == "__main__":
    main()
