#!/usr/bin/env python3
"""Static validation that does not require an Anki installation."""

from __future__ import annotations

import json
import hashlib
import re
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ADDON = ROOT / "addon"
ARCHIVE = ROOT / "dist" / "Editorial-Index.ankiaddon"
CHECKSUMS = ROOT / "dist" / "SHA256SUMS"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def check_python() -> None:
    for path in ADDON.glob("*.py"):
        compile(path.read_text(encoding="utf-8"), str(path), "exec")


def check_json() -> None:
    manifest = json.loads((ADDON / "manifest.json").read_text(encoding="utf-8"))
    config = json.loads((ADDON / "config.json").read_text(encoding="utf-8"))
    require(manifest["package"] == "mistline_ui", "unexpected add-on package name")
    require(bool(manifest["name"]), "manifest name is required")
    require(manifest["human_version"] == "0.2.4", "manifest version must be 0.2.4")
    require(manifest["homepage"] == "https://github.com/Damon-GSY/anki-editorial-index", "manifest homepage mismatch")
    require(isinstance(config["enabled"], bool), "enabled must be boolean")
    require(bool(re.fullmatch(r"#[0-9A-Fa-f]{6}", config["accent_color"])), "accent_color must be a six-digit hex color")
    require(config["accent_color"].upper() == "#2F5BBC", "default accent must meet warm-paper contrast")


def check_runtime_scope() -> None:
    source = (ADDON / "__init__.py").read_text(encoding="utf-8")
    native_source = (ADDON / "native_theme.py").read_text(encoding="utf-8")
    css = (ADDON / "web" / "theme.css").read_text(encoding="utf-8")
    editor_css = (ADDON / "web" / "editor.css").read_text(encoding="utf-8")
    editor_js = (ADDON / "web" / "editor-marker.js").read_text(encoding="utf-8")
    for hook in (
        "webview_will_set_content",
        "deck_browser_will_render_content",
        "main_window_did_init",
        "style_did_init",
        "webview_did_inject_style_into_page",
        "add_cards_did_init",
        "browser_will_show",
        "dialog_manager_did_open_dialog",
        "card_layout_will_show",
        "theme_did_change",
    ):
        require(hook in source, f"missing Anki hook: {hook}")
    for context in (
        "DeckBrowser",
        "Overview",
        "Reviewer",
        "TopToolbar",
        "ReviewerBottomBar",
        "Editor",
        "NewDeckStats",
        "DeckStats",
    ):
        require(context in source, f"missing UI context: {context}")
    require("#qa *" not in css, "reviewer content must not be globally restyled")
    require(
        ':where(:not([data-mistline-context="reviewer"])) button' in css,
        "generic controls must exclude user-owned reviewer content",
    )
    require(
        ':root[data-mistline-context] button' not in css,
        "unscoped reviewer button selector is unsafe",
    )
    require(
        ':root[data-mistline-motion="off"] *' not in css,
        "animation switch must not suppress user-owned card motion",
    )
    reviewer_body = re.search(
        r':root\[data-mistline-context="reviewer"\] body\.card\s*\{([^}]*)\}',
        css,
        re.DOTALL,
    )
    reviewer_qa = re.search(
        r':root\[data-mistline-context="reviewer"\] #qa\s*\{([^}]*)\}',
        css,
        re.DOTALL,
    )
    require(reviewer_body is not None and reviewer_qa is not None, "reviewer shell blocks missing")
    require(
        not re.search(r"(?m)^\s*(?:color|font-family|line-height|overflow-wrap)\s*:", reviewer_body.group(1)),
        "reviewer body must not override inherited user card typography",
    )
    require(
        not re.search(r"(?m)^\s*(?:color|font-family|line-height|overflow-wrap)\s*:", reviewer_qa.group(1)),
        "reviewer #qa must not override inherited user card typography",
    )
    require('#outer #ansbut' in css, "Show Answer action style missing")
    require('padding-block: var(--mist-space-1) var(--mist-space-2)' in css, "reviewer bottom spacing token missing")
    require('center > table[width="400"]' in css, "overview compatibility selector missing")
    require('tr.deck:has(a.collapse)' in css, "parent deck selector missing")
    require('.decktd' in css and 'min-width: 0' in css, "compact deck width fallback missing")
    require('table-layout: fixed' in css, "compact table layout fallback missing")
    require('width: calc(25%' not in css, "fragile fixed rating width returned")
    require("congrats" in source, "Congratulations surface hook missing")
    require("deck-options/" in source, "Deck Options surface hook missing")
    require("graphs" in source, "Stats surface hook missing")
    require("image-occlusion/" in source, "Image Occlusion surface hook missing")
    require("QApplication" in native_source, "native theme must target QApplication")
    require("QPalette" in native_source, "native theme must synchronize QPalette")
    require('mistlineRole="primary"' in native_source, "native primary action role missing")
    require('mistlineRole="chooser"' in native_source, "native chooser role missing")
    require(
        'QPushButton[mistlineRole="destructive"]:disabled' in native_source,
        "native destructive disabled-state override missing",
    )
    for selector in ("QDialog", "QPushButton", "QLineEdit", "QAbstractItemView"):
        require(selector in native_source, f"native popup selector missing: {selector}")
    require("mistline-native-theme:start" in native_source, "owned QSS marker missing")
    require("editor.css" in source and "editor-marker.js" in source, "Editor CSP-safe assets missing")
    require(".editor-toolbar" in editor_css, "Editor toolbar style missing")
    require(".editor-field" in editor_css, "Editor field style missing")
    require(".note-editor .field-container" in editor_css, "stable Editor field specificity missing")
    require(".editor-field.dupe" in editor_css, "Editor duplicate danger state missing")
    require(".autocomplete-item" in editor_css, "Editor tag autocomplete style missing")
    require("keepThemeLast" in source, "standalone Svelte theme ordering guard missing")
    require(".spin-box" in css, "Deck Options spinbox component style missing")
    require(".form-switch" in css, "Deck Options switch component style missing")
    require(".range-box" in css, "Stats filter shelf style missing")
    require(
        ':root:is([data-mistline-context="deck-browser"], [data-mistline-context="overview"]) .rh-container .streak .sstats'
        in css,
        "scoped Review Heatmap contrast guard missing",
    )
    require("grid-template-columns: repeat(4, max-content max-content)" in css, "Review Heatmap desktop rhythm guard missing")
    require("grid-template-columns: max-content max-content" in css, "Review Heatmap compact rhythm guard missing")
    require("--mist-learn: #8f5200" in css, "warm-paper learning color contrast guard missing")
    require("--mist-good: #28704f" in css, "rating Good hover contrast guard missing")
    require("--mist-easy: #346492" in css, "rating Easy hover contrast guard missing")
    require("document.currentScript" in editor_js, "Editor external marker bootstrap missing")
    require("--editorial-user-accent" in editor_js, "Editor dark-safe accent bootstrap missing")
    require(css.count("{") == css.count("}"), "theme.css brace count mismatch")
    require(editor_css.count("{") == editor_css.count("}"), "editor.css brace count mismatch")
    runtime = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in ADDON.rglob("*")
        if path.is_file()
    ).lower()
    require("bewlycat" not in runtime, "runtime contains BewlyCat attribution")
    require("bewlybewly" not in runtime, "runtime contains BewlyBewly attribution")
    require("bilibili" not in runtime, "runtime contains unrelated Bilibili content")


def check_archive() -> None:
    require(ARCHIVE.is_file(), "run scripts/package_addon.py first")
    source_files = {
        path.relative_to(ADDON).as_posix(): path
        for path in ADDON.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
    }
    with zipfile.ZipFile(ARCHIVE) as archive:
        entries = set(archive.namelist())
        expected_entries = set(source_files)
        require(entries == expected_entries, f"archive file set mismatch; missing={sorted(expected_entries - entries)}, extra={sorted(entries - expected_entries)}")
        for relative, source_path in source_files.items():
            require(archive.read(relative) == source_path.read_bytes(), f"archive content is stale: {relative}")
    for required in (
        "__init__.py",
        "LICENSE",
        "native_theme.py",
        "manifest.json",
        "config.json",
        "config.md",
        "web/theme.css",
        "web/editor.css",
        "web/editor-marker.js",
        "web/fonts/inter-regular.woff2",
        "web/fonts/inter-semibold.woff2",
        "web/fonts/inter-regular.ttf",
        "web/fonts/inter-semibold.ttf",
        "web/fonts/source-serif-regular.woff2",
        "web/fonts/source-serif-semibold.woff2",
        "web/fonts/OFL.txt",
        "web/fonts/NOTICE.md",
    ):
        require(required in entries, f"archive missing required file: {required}")

    digest = hashlib.sha256(ARCHIVE.read_bytes()).hexdigest()
    require(CHECKSUMS.read_text(encoding="utf-8") == f"{digest}  {ARCHIVE.name}\n", "archive checksum is stale")


def main() -> None:
    check_python()
    check_json()
    check_runtime_scope()
    check_archive()
    print("Editorial Index add-on validation passed")


if __name__ == "__main__":
    main()
