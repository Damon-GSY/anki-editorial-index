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


class FakeStyle:
    def unpolish(self, _widget) -> None:
        pass

    def polish(self, _widget) -> None:
        pass


class FakeRoleWidget:
    def __init__(self) -> None:
        self.properties = {}
        self.object_name = ""

    def property(self, name: str):
        return self.properties.get(name)

    def setProperty(self, name: str, value) -> None:
        self.properties[name] = value

    def style(self):
        return FakeStyle()

    def update(self) -> None:
        pass

    def setObjectName(self, name: str) -> None:
        self.object_name = name


class FakeLayout:
    def __init__(self, widgets=None) -> None:
        self.spacing = None
        self.margins = None
        self.widgets = list(widgets or [])

    def setSpacing(self, value: int) -> None:
        self.spacing = value

    def setContentsMargins(self, *values: int) -> None:
        self.margins = values

    def count(self) -> int:
        return len(self.widgets)

    def itemAt(self, index: int):
        if index < 0 or index >= len(self.widgets):
            return None
        return types.SimpleNamespace(widget=lambda: self.widgets[index])


class FakeDialogButtonBox(FakeRoleWidget):
    class ButtonRole:
        AcceptRole = "accept"
        YesRole = "yes"
        ApplyRole = "apply"
        DestructiveRole = "destructive"

    def __init__(self) -> None:
        super().__init__()
        self._layout = FakeLayout()

    def layout(self):
        return self._layout


class FakeApplication:
    _instance = None

    def __init__(self) -> None:
        self._style = "existing-application-style"
        FakeApplication._instance = self

    @classmethod
    def instance(cls):
        return cls._instance

    def styleSheet(self) -> str:
        return self._style

    def setStyleSheet(self, style: str) -> None:
        self._style = style


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
            "accent_color": "#2F5BBC",
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
        self.app = FakeApplication()
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
        self.js = []
        self.head = ""


class FakeWebView:
    def __init__(
        self, path: str = "/_anki/pages/congrats", kind: str | None = None
    ) -> None:
        self.script = ""
        self.path = path
        self.kind = types.SimpleNamespace(name=kind) if kind else None

    def url(self):
        return types.SimpleNamespace(path=lambda: self.path)

    def eval(self, script: str) -> None:
        self.script = script


def install_fake_aqt() -> tuple[FakeMainWindow, types.SimpleNamespace]:
    hooks = types.SimpleNamespace(
        add_cards_did_init=HookList(),
        browser_will_show=HookList(),
        card_layout_will_show=HookList(),
        dialog_manager_did_open_dialog=HookList(),
        webview_will_set_content=HookList(),
        deck_browser_will_render_content=HookList(),
        webview_did_inject_style_into_page=HookList(),
        style_did_init=HookList(),
        main_window_did_init=HookList(),
        theme_did_change=HookList(),
    )
    fake_mw = FakeMainWindow()

    aqt = types.ModuleType("aqt")
    aqt.gui_hooks = hooks
    aqt.mw = fake_mw

    qt = types.ModuleType("aqt.qt")
    qt.QAction = FakeAction
    qt.QApplication = FakeApplication
    qt.QDialogButtonBox = FakeDialogButtonBox
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
    assert module._get_config()["accent_color"] == "#2F5BBC"
    fake_mw.addonManager.config["accent_color"] = "#315FC4"
    assert module._get_config()["accent_color"] == "#2F5BBC"
    fake_mw.addonManager.config["accent_color"] = "#123456"
    assert module._get_config()["accent_color"] == "#123456"
    fake_mw.addonManager.config["accent_color"] = "#2F5BBC"

    assert fake_mw.addonManager.export_pattern == (
        r"^web/(?:theme\.css|editor\.css|editor-marker\.js|fonts/.*\.(?:woff2|ttf|txt|md))$"
    )
    assert len(hooks.webview_will_set_content) == 1
    assert len(hooks.deck_browser_will_render_content) == 1
    assert len(hooks.style_did_init) == 1
    assert len(hooks.add_cards_did_init) == 1
    assert len(hooks.browser_will_show) == 1
    assert len(hooks.card_layout_will_show) == 1
    assert len(hooks.dialog_manager_did_open_dialog) == 1
    assert len(hooks.theme_did_change) == 1

    add_form = types.SimpleNamespace(
        buttonBox=FakeDialogButtonBox(),
        fieldsArea=FakeRoleWidget(),
        verticalLayout_3=FakeLayout(),
        horizontalLayout=FakeLayout(),
    )
    notetype = types.SimpleNamespace(
        button=FakeRoleWidget(), label=FakeRoleWidget(), setSpacing=lambda value: None
    )
    deck = types.SimpleNamespace(
        deck=FakeRoleWidget(), deckLabel=FakeRoleWidget(), setSpacing=lambda value: None
    )
    add_cards = types.SimpleNamespace(
        addButton=FakeRoleWidget(),
        historyButton=FakeRoleWidget(),
        helpButton=FakeRoleWidget(),
        closeButton=FakeRoleWidget(),
        form=add_form,
        notetype_chooser=notetype,
        deck_chooser=deck,
    )
    hooks.add_cards_did_init[0](add_cards)
    assert add_cards.addButton.property("mistlineRole") == "primary"
    assert add_cards.historyButton.property("mistlineRole") == "quiet"
    assert add_cards.helpButton.property("mistlineRole") == "quiet"
    assert add_cards.closeButton.property("mistlineRole") == "secondary"
    assert add_form.buttonBox.property("mistlineRole") == "actionbar"
    assert notetype.button.property("mistlineRole") == "chooser"
    assert deck.deck.property("mistlineRole") == "chooser"
    assert add_form.fieldsArea.property("mistlineRole") == "editorCanvas"
    assert add_form.verticalLayout_3.margins == (16, 10, 16, 14)
    assert add_form.verticalLayout_3.spacing == 12

    browser = types.SimpleNamespace(
        sidebar=FakeRoleWidget(),
        form=types.SimpleNamespace(searchEdit=FakeRoleWidget(), tableView=FakeRoleWidget()),
    )
    browser.sidebar.searchBar = FakeRoleWidget()
    browser.sidebar.toolbar = FakeRoleWidget()
    hooks.browser_will_show[0](browser)
    assert browser.sidebar.object_name == "mistlineSidebarTree"
    assert browser.sidebar.searchBar.object_name == "mistlineSidebarSearch"
    assert browser.sidebar.toolbar.object_name == "mistlineSidebarToolbar"

    card_layout_buttons = [FakeRoleWidget() for _ in range(5)]
    card_layout = types.SimpleNamespace(buttons=FakeLayout(card_layout_buttons))
    hooks.card_layout_will_show[0](card_layout)
    assert card_layout_buttons[0].property("mistlineRole") == "quiet"
    assert card_layout_buttons[1].property("mistlineRole") == "secondary"
    assert card_layout_buttons[2].property("mistlineRole") == "secondary"
    assert card_layout_buttons[3].property("mistlineRole") == "primary"
    assert card_layout_buttons[4].property("mistlineRole") == "secondary"
    assert card_layout.buttons.spacing == 8
    assert len(hooks.main_window_did_init) == 1

    filtered_style = hooks.style_did_init[0]("anki-base-style")
    assert filtered_style.startswith("anki-base-style")
    assert filtered_style.count("mistline-native-theme:start") == 1
    assert hooks.style_did_init[0](filtered_style).count("mistline-native-theme:start") == 1

    hooks.main_window_did_init[0]()
    assert "mistline-native-theme:start" in fake_mw.app.styleSheet()
    assert 'font-family: "Inter"' in fake_mw.app.styleSheet()
    assert "QDialog" in fake_mw.app.styleSheet()
    assert "QPushButton:default" in fake_mw.app.styleSheet()
    assert "QAbstractItemView" in fake_mw.app.styleSheet()
    assert "QLineEdit" in fake_mw.app.styleSheet()
    assert fake_mw.styleSheet() == "existing-addon-style"
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

    editor_content = FakeWebContent()
    editor = type("Editor", (), {})()
    hooks.webview_will_set_content[0](editor_content, editor)
    assert editor_content.css == ["/_addons/mistline_ui/web/editor.css"]
    assert editor_content.js == [
        "/_addons/mistline_ui/web/editor-marker.js?accent=2F5BBC&motion=on"
    ]
    assert not editor_content.head

    stats_content = FakeWebContent()
    stats = type("NewDeckStats", (), {})()
    hooks.webview_will_set_content[0](stats_content, stats)
    assert stats_content.css == ["/_addons/mistline_ui/web/theme.css"]
    assert '"stats"' in stats_content.head

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
    assert 'settings.context' in external.script

    deck_options = FakeWebView("/future-route", "DECK_OPTIONS")
    hooks.webview_did_inject_style_into_page[0](deck_options)
    assert '"context": "deck-options"' in deck_options.script

    graphs = FakeWebView("/graphs")
    hooks.webview_did_inject_style_into_page[0](graphs)
    assert '"context": "stats"' in graphs.script

    image_occlusion = FakeWebView("/image-occlusion/123")
    hooks.webview_did_inject_style_into_page[0](image_occlusion)
    assert '"context": "native-page"' in image_occlusion.script

    unrelated_external = FakeWebView("/some-unowned-page")
    hooks.webview_did_inject_style_into_page[0](unrelated_external)
    assert unrelated_external.script == ""

    fake_mw.addonManager.config["style_native_chrome"] = False
    chrome_disabled_editor = FakeWebContent()
    hooks.webview_will_set_content[0](chrome_disabled_editor, editor)
    assert not chrome_disabled_editor.css and not chrome_disabled_editor.js
    chrome_disabled_options = FakeWebView("/deck-options/123", "DECK_OPTIONS")
    hooks.webview_did_inject_style_into_page[0](chrome_disabled_options)
    assert chrome_disabled_options.script == ""
    chrome_disabled_congrats = FakeWebView("/_anki/pages/congrats")
    hooks.webview_did_inject_style_into_page[0](chrome_disabled_congrats)
    assert "mistline-external-theme" in chrome_disabled_congrats.script
    fake_mw.addonManager.config["style_native_chrome"] = True

    action = fake_mw.form.menuTools.actions[-1]
    assert action.triggered.callback
    action.triggered.callback(False)
    assert fake_mw.addonManager.config["enabled"] is False
    assert "mistline-native-theme:start" not in fake_mw.app.styleSheet()
    assert fake_mw.app.styleSheet() == "existing-application-style"
    assert fake_mw.reset_count == 1

    native_style_disabled = hooks.style_did_init[0]("anki-base-style")
    assert native_style_disabled == "anki-base-style"

    disabled_editor = FakeWebContent()
    hooks.webview_will_set_content[0](disabled_editor, editor)
    assert not disabled_editor.css and not disabled_editor.js and not disabled_editor.head

    native_theme = sys.modules["mistline_ui.native_theme"]
    assert native_theme._mix_hex("#000000", "#FFFFFF", 0.5) == "#808080"

    print("Editorial Index hook smoke test passed")


if __name__ == "__main__":
    main()
