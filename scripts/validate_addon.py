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


def check_python() -> None:
    for path in ADDON.glob("*.py"):
        compile(path.read_text(encoding="utf-8"), str(path), "exec")


def check_json() -> None:
    manifest = json.loads((ADDON / "manifest.json").read_text(encoding="utf-8"))
    config = json.loads((ADDON / "config.json").read_text(encoding="utf-8"))
    assert manifest["package"] == "mistline_ui"
    assert manifest["name"]
    assert manifest["human_version"] == "0.2.0"
    assert manifest["homepage"] == "https://github.com/Damon-GSY/anki-editorial-index"
    assert isinstance(config["enabled"], bool)
    assert re.fullmatch(r"#[0-9A-Fa-f]{6}", config["accent_color"])


def check_runtime_scope() -> None:
    source = (ADDON / "__init__.py").read_text(encoding="utf-8")
    css = (ADDON / "web" / "theme.css").read_text(encoding="utf-8")
    for hook in (
        "webview_will_set_content",
        "deck_browser_will_render_content",
        "main_window_did_init",
        "theme_did_change",
        "webview_did_inject_style_into_page",
    ):
        assert hook in source
    for context in (
        "DeckBrowser",
        "Overview",
        "Reviewer",
        "TopToolbar",
        "ReviewerBottomBar",
    ):
        assert context in source
    assert "#qa *" not in css
    assert "congrats" in source
    assert css.count("{") == css.count("}")
    runtime = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in ADDON.rglob("*")
        if path.is_file()
    ).lower()
    assert "bewlycat" not in runtime
    assert "bewlybewly" not in runtime
    assert "bilibili" not in runtime


def check_archive() -> None:
    assert ARCHIVE.is_file(), "run scripts/package_addon.py first"
    with zipfile.ZipFile(ARCHIVE) as archive:
        entries = set(archive.namelist())
    for required in (
        "__init__.py",
        "LICENSE",
        "native_theme.py",
        "manifest.json",
        "config.json",
        "config.md",
        "web/theme.css",
        "web/fonts/inter-regular.woff2",
        "web/fonts/inter-semibold.woff2",
        "web/fonts/inter-regular.ttf",
        "web/fonts/inter-semibold.ttf",
        "web/fonts/source-serif-regular.woff2",
        "web/fonts/source-serif-semibold.woff2",
        "web/fonts/OFL.txt",
        "web/fonts/NOTICE.md",
    ):
        assert required in entries

    digest = hashlib.sha256(ARCHIVE.read_bytes()).hexdigest()
    assert CHECKSUMS.read_text(encoding="utf-8") == f"{digest}  {ARCHIVE.name}\n"


def main() -> None:
    check_python()
    check_json()
    check_runtime_scope()
    check_archive()
    print("Editorial Index add-on validation passed")


if __name__ == "__main__":
    main()
