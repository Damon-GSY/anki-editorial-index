#!/usr/bin/env python3
"""Import the add-on against a small fake AQT surface and exercise hooks."""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ADDON = ROOT / "addon"


class HookList(list):
    pass


class FakeSignal:
    def __init__(self) -> None:
        self.callback = None

    def connect(self, callback) -> None:
        self.callback = callback


class FakeAction:
    def __init__(self, label: str, parent: object) -> None:
        self.label = label
        self.parent = parent
        self.triggered = FakeSignal()
        self.checked = False

    def setCheckable(self, _value: bool) -> None:
        pass

    def setChecked(self, value: bool) -> None:
        self.checked = value


class FakeFontDatabase:
    registered_paths: list[str] = []

    @classmethod
    def addApplicationFont(cls, path: str) -> int:
        assert Path(path).is_file()
        cls.registered_paths.append(path)
        return len(cls.registered_paths) - 1

    @staticmethod
    def applicationFontFamilies(_font_id: int) -> list[str]:
        return ["Inter"]


class FakeMenu:
    def __init__(self) -> None:
        self.actions = []

    def addSeparator(self) -> None:
        self.actions.append(None)

    def addAction(self, action) -> None:
        self.actions.append(action)


class FakeAddonManager:
    def __init__(self) -> None:
        self.config = {
            "enabled": True,
            "accent_color": "#315FC4",
            "style_native_chrome": True,
            "style_reviewer": True,
            "animations": True,
            "frosted_toolbar": False,
        }
        self.export_pattern = ""
        self.config_callback = None

    def getConfig(self, _module):
        return dict(self.config)

    def writeConfig(self, _module, config) -> None:
        self.config = dict(config)

    @staticmethod
    def addon_from_module(module: str) -> str:
        return module.split(".", 1)[0]

    def setWebExports(self, _module, pattern: str) -> None:
        self.export_pattern = pattern

    def setConfigUpdatedAction(self, _module, callback) -> None:
        self.config_callback = callback


class FakeMainWindow:
    def __init__(self) -> None:
        self.addonManager = FakeAddonManager()
        self.form = types.SimpleNamespace(menuTools=FakeMenu())
        self.col = object()
        self._style = "existing-addon-style"
        self.reset_count = 0

    def styleSheet(self) -> str:
        return self._style

    def setStyleSheet(self, style: str) -> None:
        self._style = style

    def reset(self) -> None:
        self.reset_count += 1


class FakeWebContent:
    def __init__(self) -> None:
        self.css = []
        self.head = ""


class FakeWebView:
    def __init__(self) -> None:
        self.script = ""

    def url(self):
        return types.SimpleNamespace(path=lambda: "/_anki/pages/congrats")

    def eval(self, script: str) -> None:
        self.script = script


def install_fake_aqt() -> tuple[FakeMainWindow, types.SimpleNamespace]:
    hooks = types.SimpleNamespace(
        webview_will_set_content=HookList(),
        deck_browser_will_render_content=HookList(),
        webview_did_inject_style_into_page=HookList(),
        main_window_did_init=HookList(),
        theme_did_change=HookList(),
    )
    fake_mw = FakeMainWindow()

    aqt = types.ModuleType("aqt")
    aqt.gui_hooks = hooks
    aqt.mw = fake_mw

    qt = types.ModuleType("aqt.qt")
    qt.QAction = FakeAction
    qt.QFontDatabase = FakeFontDatabase
    qt.qconnect = lambda signal, callback: signal.connect(callback)

    theme = types.ModuleType("aqt.theme")
    theme.theme_manager = types.SimpleNamespace(night_mode=False)

    sys.modules["aqt"] = aqt
    sys.modules["aqt.qt"] = qt
    sys.modules["aqt.theme"] = theme
    return fake_mw, hooks


def main() -> None:
    fake_mw, hooks = install_fake_aqt()
    spec = importlib.util.spec_from_file_location(
        "mistline_ui",
        ADDON / "__init__.py",
        submodule_search_locations=[str(ADDON)],
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["mistline_ui"] = module
    spec.loader.exec_module(module)

    fake_mw.addonManager.config["accent_color"] = "#18A6B8"
    assert module._get_config()["accent_color"] == "#315FC4"
    fake_mw.addonManager.config["accent_color"] = "#123456"
    assert module._get_config()["accent_color"] == "#123456"
    fake_mw.addonManager.config["accent_color"] = "#315FC4"

    assert fake_mw.addonManager.export_pattern == r"^web/(?:theme\.css|fonts/.*\.(?:woff2|ttf|txt|md))$"
    assert len(hooks.webview_will_set_content) == 1
    assert len(hooks.deck_browser_will_render_content) == 1
    assert len(hooks.main_window_did_init) == 1

    hooks.main_window_did_init[0]()
    assert "mistline-native-theme:start" in fake_mw.styleSheet()
    assert 'font-family: "Inter"' in fake_mw.styleSheet()
    assert len(FakeFontDatabase.registered_paths) == 2
    assert fake_mw.form.menuTools.actions[-1].label == "Editorial Index 主题"

    content = FakeWebContent()
    deck_browser = type("DeckBrowser", (), {})()
    hooks.webview_will_set_content[0](content, deck_browser)
    assert content.css == ["/_addons/mistline_ui/web/theme.css"]
    assert 'mistlineContext = settings.context' in content.head
    assert 'mistlineFonts = "loading"' in content.head
    assert 'mistlineFonts = sans.length && serif.length ? "ready" : "fallback"' in content.head
    assert '"deck-browser"' in content.head

    deck_content = types.SimpleNamespace(tree="<table>decks</table>")
    hooks.deck_browser_will_render_content[0](deck_browser, deck_content)
    assert "mistline-deck-heading" in deck_content.tree
    assert deck_content.tree.endswith("<table>decks</table>")

    unrelated = FakeWebContent()
    hooks.webview_will_set_content[0](unrelated, object())
    assert not unrelated.css and not unrelated.head

    external = FakeWebView()
    hooks.webview_did_inject_style_into_page[0](external)
    assert "mistline-external-theme" in external.script

    action = fake_mw.form.menuTools.actions[-1]
    assert action.triggered.callback
    action.triggered.callback(False)
    assert fake_mw.addonManager.config["enabled"] is False
    assert "mistline-native-theme:start" not in fake_mw.styleSheet()
    assert fake_mw.reset_count == 1

    print("Editorial Index hook smoke test passed")


if __name__ == "__main__":
    main()
