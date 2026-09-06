#!/usr/bin/env python3
"""Import the add-on against a small fake AQT surface and exercise hooks."""

from __future__ import annotations

import base64
import importlib.util
import json
import sys
import types
from urllib.parse import parse_qs, urlparse
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
        self.enabled = True

    def setCheckable(self, _value: bool) -> None:
        pass

    def setChecked(self, value: bool) -> None:
        self.checked = value

    def setEnabled(self, value: bool) -> None:
        self.enabled = value


class FakeActionGroup:
    def __init__(self, parent: object) -> None:
        self.parent = parent
        self.items = []
        self.exclusive = False

    def setExclusive(self, value: bool) -> None:
        self.exclusive = value

    def addAction(self, action: FakeAction) -> None:
        self.items.append(action)


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
    def __init__(self, object_name: str = "") -> None:
        self.properties = {}
        self.object_name = object_name

    def property(self, name: str):
        return self.properties.get(name)

    def setProperty(self, name: str, value) -> None:
        if value is None:
            self.properties.pop(name, None)
        else:
            self.properties[name] = value

    def style(self):
        return FakeStyle()

    def update(self) -> None:
        pass

    def setObjectName(self, name: str) -> None:
        self.object_name = name

    def objectName(self) -> str:
        return self.object_name


class FakeButton(FakeRoleWidget):
    def __init__(self, *, is_default: bool = False) -> None:
        super().__init__()
        self._is_default = is_default

    def isDefault(self) -> bool:
        return self._is_default


class FakeSidebar(FakeRoleWidget):
    def __init__(self, object_name: str = "") -> None:
        super().__init__(object_name)
        self.local_background = "stale-bg"
        self.setup_style_count = 0

    def _setup_style(self) -> None:
        """Mirror Anki's palette-derived, widget-local sidebar stylesheet."""

        app = FakeApplication.instance()
        assert app is not None
        self.local_background = app.palette_background
        self.setup_style_count += 1


class FakeMargins:
    def __init__(self, values: tuple[int, int, int, int]) -> None:
        self.values = values

    def left(self) -> int:
        return self.values[0]

    def top(self) -> int:
        return self.values[1]

    def right(self) -> int:
        return self.values[2]

    def bottom(self) -> int:
        return self.values[3]


class FakeLayout:
    def __init__(
        self,
        widgets=None,
        *,
        spacing: int = -1,
        margins: tuple[int, int, int, int] = (0, 0, 0, 0),
    ) -> None:
        self._spacing = spacing
        self._margins = margins
        self.widgets = list(widgets or [])

    def setSpacing(self, value: int) -> None:
        self._spacing = value

    def spacing(self) -> int:
        return self._spacing

    def setContentsMargins(self, *values: int) -> None:
        self._margins = values

    def contentsMargins(self) -> FakeMargins:
        return FakeMargins(self._margins)

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

    def __init__(self, button_roles=None) -> None:
        super().__init__()
        self._layout = FakeLayout()
        self._button_roles = list(button_roles or [])

    def layout(self):
        return self._layout

    def buttons(self):
        return [button for button, _role in self._button_roles]

    def buttonRole(self, button):
        for candidate, role in self._button_roles:
            if candidate is button:
                return role
        raise ValueError("unknown button")


class FakeSurface:
    def __init__(self, **values) -> None:
        self.__dict__.update(values)


class FakeManagedDialog(FakeSurface):
    def __init__(self, button_boxes) -> None:
        super().__init__()
        self.button_boxes = list(button_boxes)

    def findChildren(self, widget_type):
        assert widget_type is FakeDialogButtonBox
        return list(self.button_boxes)


class FakeApplication:
    _instance = None

    def __init__(self) -> None:
        self._style = "existing-application-style"
        self.palette_background = "editorial-bg"
        FakeApplication._instance = self

    @classmethod
    def instance(cls):
        return cls._instance

    def styleSheet(self) -> str:
        return self._style

    def setStyleSheet(self, style: str) -> None:
        self._style = style

    @staticmethod
    def allWidgets() -> list[object]:
        return []


class FakeMenu:
    def __init__(self, label: str = "", parent: object | None = None) -> None:
        self.label = label
        self.parent = parent
        self.actions = []
        self.enabled = True

    def addSeparator(self) -> None:
        self.actions.append(None)

    def addAction(self, action) -> None:
        self.actions.append(action)

    def addMenu(self, menu):
        child = menu if isinstance(menu, FakeMenu) else FakeMenu(str(menu), self)
        self.actions.append(child)
        return child

    def setEnabled(self, value: bool) -> None:
        self.enabled = value


class FakeAddonManager:
    def __init__(self) -> None:
        self.config = {
            "enabled": True,
            "accent_color": "#2F5BBC",
            "color_theme": "editorial",
            "catppuccin_flavor": "auto",
            "catppuccin_accent": "blue",
            "style_native_chrome": True,
            "style_reviewer": True,
            "animations": True,
            "frosted_toolbar": False,
        }
        self.export_pattern = ""
        self.config_callback = None
        self.write_count = 0

    def getConfig(self, _module):
        return dict(self.config)

    def writeConfig(self, _module, config) -> None:
        self.config = dict(config)
        self.write_count += 1

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
        self.eval_count = 0
        self.unsaved_sentinel = "keep me"

    def url(self):
        return types.SimpleNamespace(path=lambda: self.path)

    def eval(self, script: str) -> None:
        self.script = script
        self.eval_count += 1


def fake_aqt_context(name: str, module_name: str = "aqt.smoke_test"):
    return type(name, (), {"__module__": module_name})()


def fake_third_party_context(name: str):
    return type(name, (), {"__module__": "third_party.addon"})()


def install_fake_aqt() -> tuple[FakeMainWindow, types.SimpleNamespace]:
    hooks = types.SimpleNamespace(
        add_cards_did_init=HookList(),
        browser_will_show=HookList(),
        card_layout_will_show=HookList(),
        dialog_manager_did_open_dialog=HookList(),
        webview_will_set_content=HookList(),
        deck_browser_will_render_content=HookList(),
        deck_browser_did_render=HookList(),
        overview_did_refresh=HookList(),
        reviewer_did_show_question=HookList(),
        reviewer_did_show_answer=HookList(),
        webview_did_inject_style_into_page=HookList(),
        webview_did_receive_js_message=HookList(),
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
    qt.QActionGroup = FakeActionGroup
    qt.QApplication = FakeApplication
    qt.QDialogButtonBox = FakeDialogButtonBox
    qt.QFontDatabase = FakeFontDatabase
    qt.QMenu = FakeMenu
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

    # native_theme's focused test covers real QPalette ownership. This wrapper
    # lets the hook smoke test verify orchestration order: the application
    # palette changes first, then Anki's existing Browser sidebar rebuilds its
    # palette-derived local stylesheet without a Browser/data refresh.
    apply_native_theme = module.apply_native_theme

    def apply_native_theme_with_palette(main_window, config) -> None:
        if not config["enabled"] or not config["style_native_chrome"]:
            fake_mw.app.palette_background = "system-bg"
        elif config["color_theme"] == "catppuccin":
            fake_mw.app.palette_background = f"{config['catppuccin_flavor']}-bg"
        else:
            fake_mw.app.palette_background = "editorial-bg"
        apply_native_theme(main_window, config)

    module.apply_native_theme = apply_native_theme_with_palette

    fake_mw.addonManager.config["accent_color"] = "#18A6B8"
    assert module._get_config()["accent_color"] == "#2F5BBC"
    fake_mw.addonManager.config["accent_color"] = "#315FC4"
    assert module._get_config()["accent_color"] == "#2F5BBC"
    fake_mw.addonManager.config["accent_color"] = "#123456"
    assert module._get_config()["accent_color"] == "#123456"
    fake_mw.addonManager.config["accent_color"] = "#2F5BBC"

    assert fake_mw.addonManager.export_pattern == (
        r"^web/(?:theme\.css|heatmap\.css|cabinet\.css|cabinet\.js|editor\.css|editor-marker\.js|fonts/.*\.(?:woff2|ttf|txt|md))$"
    )
    assert len(hooks.webview_will_set_content) == 1
    assert len(hooks.deck_browser_will_render_content) == 1
    assert len(hooks.style_did_init) == 1
    assert len(hooks.add_cards_did_init) == 1
    assert len(hooks.browser_will_show) == 1
    assert len(hooks.card_layout_will_show) == 1
    assert len(hooks.dialog_manager_did_open_dialog) == 1
    assert len(hooks.theme_did_change) == 1

    add_form = FakeSurface(
        buttonBox=FakeDialogButtonBox(),
        fieldsArea=FakeRoleWidget(),
        verticalLayout_3=FakeLayout(spacing=12, margins=(12, 6, 12, 12)),
        horizontalLayout=FakeLayout(spacing=6),
    )
    notetype = FakeLayout(spacing=8)
    notetype.button = FakeRoleWidget()
    notetype.label = FakeRoleWidget()
    deck = FakeLayout(spacing=8)
    deck.deck = FakeRoleWidget()
    deck.deckLabel = FakeRoleWidget()
    add_cards = FakeSurface(
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
    assert add_form.verticalLayout_3._margins == (16, 10, 16, 14)
    assert add_form.verticalLayout_3.spacing() == 12
    assert add_form.horizontalLayout.spacing() == 12

    accept_button = FakeButton()
    accept_button.setProperty("mistlineRole", "third-party-accept")
    secondary_button = FakeButton()
    secondary_button.setProperty("mistlineRole", "third-party-secondary")
    destructive_button = FakeButton()
    managed_button_box = FakeDialogButtonBox(
        (
            (accept_button, FakeDialogButtonBox.ButtonRole.AcceptRole),
            (secondary_button, "reject"),
            (destructive_button, FakeDialogButtonBox.ButtonRole.DestructiveRole),
        )
    )
    managed_button_box.setProperty("mistlineRole", "third-party-actionbar")
    managed_dialog = FakeManagedDialog([managed_button_box])
    hooks.dialog_manager_did_open_dialog[0](None, "Preferences", managed_dialog)
    assert managed_button_box.property("mistlineRole") == "actionbar"
    assert accept_button.property("mistlineRole") == "primary"
    assert secondary_button.property("mistlineRole") == "secondary"
    assert destructive_button.property("mistlineRole") == "destructive"

    browser = FakeSurface(
        sidebar=FakeSidebar("ankiSidebar"),
        form=FakeSurface(
            searchEdit=FakeRoleWidget("ankiSearchEdit"),
            tableView=FakeRoleWidget("ankiTableView"),
        ),
    )
    browser.sidebar.searchBar = FakeRoleWidget("ankiSidebarSearch")
    browser.sidebar.toolbar = FakeRoleWidget("ankiSidebarToolbar")
    hooks.browser_will_show[0](browser)
    assert browser.sidebar.object_name == "ankiSidebar"
    assert browser.sidebar.searchBar.object_name == "ankiSidebarSearch"
    assert browser.sidebar.toolbar.object_name == "ankiSidebarToolbar"
    assert browser.form.searchEdit.object_name == "ankiSearchEdit"
    assert browser.form.tableView.object_name == "ankiTableView"
    assert browser.sidebar.local_background == "editorial-bg"

    card_layout_buttons = [FakeRoleWidget() for _ in range(5)]
    card_layout = FakeSurface(buttons=FakeLayout(card_layout_buttons, spacing=5))
    hooks.card_layout_will_show[0](card_layout)
    assert card_layout_buttons[0].property("mistlineRole") == "quiet"
    assert card_layout_buttons[1].property("mistlineRole") == "secondary"
    assert card_layout_buttons[2].property("mistlineRole") == "secondary"
    assert card_layout_buttons[3].property("mistlineRole") == "primary"
    assert card_layout_buttons[4].property("mistlineRole") == "secondary"
    assert card_layout.buttons.spacing() == 8
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
    assert fake_mw.addonManager.write_count == 0
    assert module._menu_action.label == "Editorial Index 主题"
    assert module._palette_dialog_action.label == "Editorial Index 配色…"
    assert module._palette_menu.label == "Editorial Index 快速配色"
    assert set(module._palette_actions) == {
        "editorial",
        "auto",
        "latte",
        "frappe",
        "macchiato",
        "mocha",
    }
    assert set(module._accent_actions) == set(module.CATPPUCCIN_ACCENTS)
    assert module._palette_actions["editorial"].checked
    assert module._accent_actions["blue"].checked
    assert module._accent_menu.enabled is False

    content = FakeWebContent()
    deck_browser = fake_aqt_context("DeckBrowser")
    hooks.webview_will_set_content[0](content, deck_browser)
    assert content.css == ["/_addons/mistline_ui/web/theme.css"]
    assert 'mistlineContext = settings.context' in content.head
    assert 'mistlineFonts = "loading"' in content.head
    assert 'mistlineFonts = sans.length && serif.length ? "ready" : "fallback"' in content.head
    assert '"deck-browser"' in content.head

    editor_content = FakeWebContent()
    editor = fake_aqt_context("Editor")
    hooks.webview_will_set_content[0](editor_content, editor)
    assert editor_content.css == ["/_addons/mistline_ui/web/editor.css"]
    assert len(editor_content.js) == 1
    editor_url = editor_content.js[0]
    assert editor_url.startswith("/_addons/mistline_ui/web/editor-marker.js?")
    editor_query = parse_qs(urlparse(editor_url).query)
    encoded_tokens = editor_query["tokens"][0]
    encoded_tokens += "=" * (-len(encoded_tokens) % 4)
    editor_tokens = json.loads(base64.urlsafe_b64decode(encoded_tokens))
    assert editor_query["family"] == ["editorial"]
    assert editor_query["flavor"] == ["editorial-light"]
    assert editor_query["tone"] == ["light"]
    assert editor_query["accent"] == ["custom"]
    assert editor_tokens["--editorial-accent-fill"] == "#2F5BBC"
    assert editor_tokens["--editorial-accent"] == "#2F5BBC"
    assert not editor_content.head

    stats_content = FakeWebContent()
    stats = fake_aqt_context("NewDeckStats")
    hooks.webview_will_set_content[0](stats_content, stats)
    assert stats_content.css == ["/_addons/mistline_ui/web/theme.css"]
    assert '"stats"' in stats_content.head

    empty_cards_content = FakeWebContent()
    empty_cards = fake_aqt_context("EmptyCardsDialog", "aqt.emptycards")
    hooks.webview_will_set_content[0](empty_cards_content, empty_cards)
    assert empty_cards_content.css == ["/_addons/mistline_ui/web/theme.css"]
    assert '"native-page"' in empty_cards_content.head

    deck_content = types.SimpleNamespace(tree="<table>decks</table>")
    hooks.deck_browser_will_render_content[0](deck_browser, deck_content)
    assert "mistline-deck-heading" in deck_content.tree
    assert 'data-mistline-owned="deck-heading" hidden' not in deck_content.tree
    assert deck_content.tree.endswith("<table>decks</table>")

    unrelated = FakeWebContent()
    hooks.webview_will_set_content[0](unrelated, object())
    assert not unrelated.css and not unrelated.head

    for context_name in ("Editor", "Overview", "Reviewer"):
        third_party_context = fake_third_party_context(context_name)
        assert module._context_name(third_party_context) is None
        third_party_content = FakeWebContent()
        hooks.webview_will_set_content[0](third_party_content, third_party_context)
        assert not third_party_content.css
        assert not third_party_content.js
        assert not third_party_content.head

    external = FakeWebView()
    hooks.webview_did_inject_style_into_page[0](external)
    assert "mistline-external-theme" in external.script
    assert 'settings.context' in external.script
    assert 'candidate.href === resolvedHref' in external.script
    assert 'candidate.href.includes(fragment)' not in external.script
    assert 'link[href*="/web/theme.css"]' not in external.script

    deck_options = FakeWebView("/future-route", "DECK_OPTIONS")
    hooks.webview_did_inject_style_into_page[0](deck_options)
    assert '"context": "deck-options"' in deck_options.script

    graphs = FakeWebView("/graphs")
    hooks.webview_did_inject_style_into_page[0](graphs)
    assert '"context": "stats"' in graphs.script

    legacy_graphs = FakeWebView("/_anki/pages/graphs.html")
    hooks.webview_did_inject_style_into_page[0](legacy_graphs)
    assert '"context": "stats"' in legacy_graphs.script

    addon_mygraphs = FakeWebView("/_addons/other_addon/web/mygraphs.html")
    addon_mygraphs._bridge_context = fake_aqt_context("Overview")
    hooks.webview_did_inject_style_into_page[0](addon_mygraphs)
    assert addon_mygraphs.script == ""

    congrats_from_overview = FakeWebView("/congrats")
    congrats_from_overview._bridge_context = fake_aqt_context("Overview")
    hooks.webview_did_inject_style_into_page[0](congrats_from_overview)
    assert '"context": "congrats"' in congrats_from_overview.script
    assert '"context": "overview"' not in congrats_from_overview.script

    for context_name in ("Overview", "Reviewer"):
        third_party_bridge = FakeWebView("/some-unowned-page")
        third_party_bridge._bridge_context = fake_third_party_context(context_name)
        hooks.webview_did_inject_style_into_page[0](third_party_bridge)
        assert third_party_bridge.script == ""

    image_occlusion = FakeWebView("/image-occlusion/123")
    hooks.webview_did_inject_style_into_page[0](image_occlusion)
    assert '"context": "native-page"' in image_occlusion.script

    unrelated_external = FakeWebView("/some-unowned-page")
    hooks.webview_did_inject_style_into_page[0](unrelated_external)
    assert unrelated_external.script == ""

    editor_view = FakeWebView("/editor", "EDITOR")
    hooks.webview_did_inject_style_into_page[0](editor_view)
    assert '"context": "editor"' in editor_view.script
    assert editor_view.unsaved_sentinel == "keep me"

    fake_mw.addonManager.config["style_native_chrome"] = False
    chrome_disabled_editor = FakeWebContent()
    hooks.webview_will_set_content[0](chrome_disabled_editor, editor)
    assert not chrome_disabled_editor.css and not chrome_disabled_editor.js
    chrome_disabled_options = FakeWebView("/deck-options/123", "DECK_OPTIONS")
    hooks.webview_did_inject_style_into_page[0](chrome_disabled_options)
    assert '"style_native_chrome"' not in chrome_disabled_options.script
    assert '"blockedContexts": ["deck-options"' in chrome_disabled_options.script
    chrome_disabled_congrats = FakeWebView("/_anki/pages/congrats")
    hooks.webview_did_inject_style_into_page[0](chrome_disabled_congrats)
    assert "mistline-external-theme" in chrome_disabled_congrats.script
    module._config_updated(None)
    assert add_cards.addButton.property("mistlineRole") is None
    assert add_form.verticalLayout_3._margins == (12, 6, 12, 12)
    assert browser.sidebar.objectName() == "ankiSidebar"
    assert browser.sidebar.local_background == "system-bg"
    assert managed_button_box.property("mistlineRole") == "third-party-actionbar"
    assert accept_button.property("mistlineRole") == "third-party-accept"
    assert secondary_button.property("mistlineRole") == "third-party-secondary"
    assert destructive_button.property("mistlineRole") is None
    assert card_layout_buttons[0].property("mistlineRole") is None
    assert card_layout.buttons.spacing() == 5
    fake_mw.addonManager.config["style_native_chrome"] = True
    module._config_updated(None)
    assert add_cards.addButton.property("mistlineRole") == "primary"
    assert add_form.verticalLayout_3._margins == (16, 10, 16, 14)
    assert browser.sidebar.objectName() == "ankiSidebar"
    assert browser.sidebar.searchBar.objectName() == "ankiSidebarSearch"
    assert browser.sidebar.toolbar.objectName() == "ankiSidebarToolbar"
    assert browser.form.searchEdit.objectName() == "ankiSearchEdit"
    assert browser.form.tableView.objectName() == "ankiTableView"
    assert managed_button_box.property("mistlineRole") == "actionbar"
    assert accept_button.property("mistlineRole") == "primary"
    assert secondary_button.property("mistlineRole") == "secondary"
    assert destructive_button.property("mistlineRole") == "destructive"
    assert card_layout_buttons[0].property("mistlineRole") == "quiet"
    assert card_layout.buttons.spacing() == 8
    assert fake_mw.reset_count == 0

    # Menu choices patch only their owned fields, retain future/unknown config,
    # and broadcast variables to already-open editors without reloading them.
    fake_mw.addonManager.config["future_setting"] = {"keep": True}
    add_cards.historyButton.setProperty("mistlineRole", "third-party")
    add_form.horizontalLayout.setSpacing(31)
    browser.sidebar.toolbar.setObjectName("thirdPartyToolbar")
    card_layout_buttons[1].setProperty("mistlineRole", "third-party")
    module._palette_actions["mocha"].triggered.callback(True)
    assert fake_mw.addonManager.config["color_theme"] == "catppuccin"
    assert fake_mw.addonManager.config["catppuccin_flavor"] == "mocha"
    assert fake_mw.addonManager.config["accent_color"] == "#2F5BBC"
    assert fake_mw.addonManager.config["future_setting"] == {"keep": True}
    assert module._palette_actions["mocha"].checked
    assert module._accent_menu.enabled is True
    assert '"flavor": "mocha"' in editor_view.script
    assert editor_view.unsaved_sentinel == "keep me"
    assert unrelated_external.script == ""
    assert add_cards.historyButton.property("mistlineRole") == "third-party"
    assert add_form.horizontalLayout.spacing() == 31
    assert browser.sidebar.toolbar.objectName() == "thirdPartyToolbar"
    assert browser.sidebar.local_background == "mocha-bg"
    assert card_layout_buttons[1].property("mistlineRole") == "third-party"

    module._accent_actions["yellow"].triggered.callback(True)
    assert fake_mw.addonManager.config["catppuccin_accent"] == "yellow"
    assert module._accent_actions["yellow"].checked
    assert '"accentName": "yellow"' in editor_view.script
    assert fake_mw.addonManager.config["future_setting"] == {"keep": True}

    module._palette_actions["editorial"].triggered.callback(True)
    assert fake_mw.addonManager.config["color_theme"] == "editorial"
    assert fake_mw.addonManager.config["catppuccin_flavor"] == "mocha"
    assert fake_mw.addonManager.config["catppuccin_accent"] == "yellow"
    assert module._accent_menu.enabled is False

    action = module._menu_action
    assert action.triggered.callback
    action.triggered.callback(False)
    assert fake_mw.addonManager.config["enabled"] is False
    assert fake_mw.addonManager.config["future_setting"] == {"keep": True}
    assert "mistline-native-theme:start" not in fake_mw.app.styleSheet()
    assert fake_mw.app.styleSheet() == "existing-application-style"
    assert fake_mw.reset_count == 0
    assert editor_view.unsaved_sentinel == "keep me"
    assert 'root.dataset.mistlineEnabled = "off"' in editor_view.script
    assert add_cards.addButton.property("mistlineRole") is None
    assert add_cards.historyButton.property("mistlineRole") == "third-party"
    assert add_form.verticalLayout_3._margins == (12, 6, 12, 12)
    assert add_form.verticalLayout_3.spacing() == 12
    assert add_form.horizontalLayout.spacing() == 31
    assert add_form.buttonBox.layout().spacing() == -1
    assert browser.sidebar.objectName() == "ankiSidebar"
    assert browser.sidebar.searchBar.objectName() == "ankiSidebarSearch"
    assert browser.sidebar.toolbar.objectName() == "thirdPartyToolbar"
    assert browser.form.searchEdit.objectName() == "ankiSearchEdit"
    assert browser.form.tableView.objectName() == "ankiTableView"
    assert browser.sidebar.local_background == "system-bg"
    assert managed_button_box.property("mistlineRole") == "third-party-actionbar"
    assert accept_button.property("mistlineRole") == "third-party-accept"
    assert secondary_button.property("mistlineRole") == "third-party-secondary"
    assert destructive_button.property("mistlineRole") is None
    assert card_layout_buttons[0].property("mistlineRole") is None
    assert card_layout_buttons[1].property("mistlineRole") == "third-party"
    assert card_layout.buttons.spacing() == 5

    # Hooks keep tracking windows created while native styling is disabled, so
    # they can be themed in place when the user enables it again.
    late_form = FakeSurface(
        buttonBox=FakeDialogButtonBox(),
        fieldsArea=FakeRoleWidget(),
        verticalLayout_3=FakeLayout(spacing=9, margins=(3, 4, 5, 6)),
        horizontalLayout=FakeLayout(spacing=7),
    )
    late_notetype = FakeLayout(spacing=4)
    late_notetype.button = FakeRoleWidget()
    late_notetype.label = FakeRoleWidget()
    late_deck = FakeLayout(spacing=5)
    late_deck.deck = FakeRoleWidget()
    late_deck.deckLabel = FakeRoleWidget()
    late_add = FakeSurface(
        addButton=FakeRoleWidget(),
        historyButton=FakeRoleWidget(),
        helpButton=FakeRoleWidget(),
        closeButton=FakeRoleWidget(),
        form=late_form,
        notetype_chooser=late_notetype,
        deck_chooser=late_deck,
    )
    late_browser = FakeSurface(
        sidebar=FakeSidebar("lateSidebar"),
        form=FakeSurface(
            searchEdit=FakeRoleWidget("lateSearchEdit"),
            tableView=FakeRoleWidget("lateTableView"),
        ),
    )
    late_browser.sidebar.searchBar = FakeRoleWidget("lateSidebarSearch")
    late_browser.sidebar.toolbar = FakeRoleWidget("lateSidebarToolbar")
    late_buttons = [FakeRoleWidget() for _ in range(5)]
    late_card_layout = FakeSurface(buttons=FakeLayout(late_buttons, spacing=6))
    hooks.add_cards_did_init[0](late_add)
    hooks.browser_will_show[0](late_browser)
    hooks.card_layout_will_show[0](late_card_layout)
    assert late_add.addButton.property("mistlineRole") is None
    assert late_form.verticalLayout_3._margins == (3, 4, 5, 6)
    assert late_browser.sidebar.objectName() == "lateSidebar"
    assert late_buttons[0].property("mistlineRole") is None
    assert late_card_layout.buttons.spacing() == 6

    action.triggered.callback(True)
    assert late_add.addButton.property("mistlineRole") == "primary"
    assert late_form.verticalLayout_3._margins == (16, 10, 16, 14)
    assert late_browser.sidebar.objectName() == "lateSidebar"
    assert late_browser.sidebar.searchBar.objectName() == "lateSidebarSearch"
    assert late_browser.sidebar.toolbar.objectName() == "lateSidebarToolbar"
    assert late_browser.form.searchEdit.objectName() == "lateSearchEdit"
    assert late_browser.form.tableView.objectName() == "lateTableView"
    assert late_buttons[0].property("mistlineRole") == "quiet"
    assert late_card_layout.buttons.spacing() == 8
    action.triggered.callback(False)
    assert late_add.addButton.property("mistlineRole") is None
    assert late_form.verticalLayout_3._margins == (3, 4, 5, 6)
    assert late_form.verticalLayout_3.spacing() == 9
    assert late_form.horizontalLayout.spacing() == 7
    assert late_notetype.spacing() == 4
    assert late_deck.spacing() == 5
    assert late_form.buttonBox.layout().spacing() == -1
    assert late_browser.sidebar.objectName() == "lateSidebar"
    assert late_browser.sidebar.searchBar.objectName() == "lateSidebarSearch"
    assert late_browser.sidebar.toolbar.objectName() == "lateSidebarToolbar"
    assert late_browser.form.searchEdit.objectName() == "lateSearchEdit"
    assert late_browser.form.tableView.objectName() == "lateTableView"
    assert late_buttons[0].property("mistlineRole") is None
    assert late_card_layout.buttons.spacing() == 6
    assert fake_mw.reset_count == 0

    # A first deck render while disabled must still leave an owned, inert
    # heading in the DOM so later toggles can reveal/hide it without mw.reset().
    disabled_first_deck = types.SimpleNamespace(tree="<table>late decks</table>")
    hooks.deck_browser_will_render_content[0](deck_browser, disabled_first_deck)
    assert 'data-mistline-owned="deck-heading" hidden' in disabled_first_deck.tree
    assert disabled_first_deck.tree.endswith("<table>late decks</table>")

    disabled_first_view = FakeWebView("/deck-browser")
    disabled_first_view._bridge_context = fake_aqt_context("DeckBrowser")
    hooks.webview_did_inject_style_into_page[0](disabled_first_view)
    assert '"enabled": false' in disabled_first_view.script
    action.triggered.callback(True)
    assert '"enabled": true' in disabled_first_view.script
    assert 'heading.hidden = false' in disabled_first_view.script
    action.triggered.callback(False)
    assert '"enabled": false' in disabled_first_view.script
    assert 'heading.hidden = true' in disabled_first_view.script
    assert fake_mw.reset_count == 0

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
