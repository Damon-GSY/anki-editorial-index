#!/usr/bin/env python3
"""Build a deterministic .ankiaddon archive from addon/."""

from __future__ import annotations

import json
import hashlib
import re
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ADDON_DIR = ROOT / "addon"
DIST_DIR = ROOT / "dist"
OUTPUT = DIST_DIR / "Editorial-Index.ankiaddon"
CHECKSUMS = DIST_DIR / "SHA256SUMS"
REQUIRED = {
    "__init__.py",
    "CATPPUCCIN_LICENSE",
    "LICENSE",
    "THIRD_PARTY_NOTICES.md",
    "catppuccin.json",
    "color_themes.py",
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
}


def validate_manifest() -> dict[str, object]:
    manifest = json.loads((ADDON_DIR / "manifest.json").read_text(encoding="utf-8"))
    if not manifest.get("package") or not manifest.get("name"):
        raise ValueError("manifest.json requires package and name")
    if not re.fullmatch(r"[A-Za-z0-9_]+", str(manifest["package"])):
        raise ValueError("manifest package must be a valid Anki add-on folder name")
    return manifest


def build() -> Path:
    missing = sorted(path for path in REQUIRED if not (ADDON_DIR / path).is_file())
    if missing:
        raise FileNotFoundError(f"missing required add-on files: {', '.join(missing)}")
    validate_manifest()

    DIST_DIR.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUTPUT, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(ADDON_DIR.rglob("*")):
            if not path.is_file() or "__pycache__" in path.parts or path.suffix == ".pyc":
                continue
            relative = path.relative_to(ADDON_DIR).as_posix()
            info = zipfile.ZipInfo(relative, date_time=(2026, 8, 25, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, path.read_bytes())

    digest = hashlib.sha256(OUTPUT.read_bytes()).hexdigest()
    CHECKSUMS.write_text(f"{digest}  {OUTPUT.name}\n", encoding="utf-8")

    return OUTPUT


if __name__ == "__main__":
    result = build()
    print(f"Built {result} ({result.stat().st_size} bytes)")
