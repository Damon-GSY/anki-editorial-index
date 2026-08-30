<div align="center">

# Editorial Index

An editorial, warm-paper desktop theme for Anki

[中文](./README.md) · [Download](https://github.com/Damon-GSY/anki-editorial-index/releases/latest) · [Configuration](./docs/CONFIGURATION.md) · [Troubleshooting](./docs/TROUBLESHOOTING.md)

[![Latest release](https://img.shields.io/github/v/release/Damon-GSY/anki-editorial-index?label=release)](https://github.com/Damon-GSY/anki-editorial-index/releases/latest)
[![Anki](https://img.shields.io/badge/Anki-25.09.4%2B-2F5BBC)](https://apps.ankiweb.net/)
[![License](https://img.shields.io/github/license/Damon-GSY/anki-editorial-index)](./LICENSE)

</div>

![Editorial Index deck browser](./screenshots/deck-browser.png)

Editorial Index restyles Anki Desktop's deck browser, reviewer shell, navigation, and standalone Add, Browse, Stats, Deck Options, and Preferences windows. It leaves your collection, scheduling, shortcuts, and card templates intact.

## Install

1. Open the [latest release](https://github.com/Damon-GSY/anki-editorial-index/releases/latest).
2. Download `Editorial-Index.ankiaddon` from Assets.
3. In Anki Desktop, open Tools > Add-ons.
4. Choose Install from file and select the downloaded file.
5. Restart Anki.

The Tools menu will now contain an Editorial Index theme toggle. See the [installation guide](./docs/INSTALLATION.md) for upgrading, removal, and checksum verification.

## What it styles

- Deck browser and deck tree
- Deck overview and Study Now action
- Top navigation and bottom toolbars
- Reviewer shell and answer controls
- Add, Browse, Stats, Deck Options, Preferences, and native dialogs
- Native menus, fields, lists, tabs, and the status bar
- Light and dark modes

The add-on does not modify your collection, notes, card templates, FSRS settings, or scheduling data. Disabling or removing it restores Anki's standard interface.

![Editorial Index reviewer](./screenshots/reviewer-answer.png)

## Configure

Open Tools > Add-ons, select Editorial Index, and choose Config.

| Key | Default | Purpose |
| --- | --- | --- |
| `enabled` | `true` | Enable the complete theme |
| `accent_color` | `#2F5BBC` | Set the accent used for actions and focus states |
| `style_native_chrome` | `true` | Style standalone windows, dialogs, native controls, and their Anki-owned embedded pages |
| `style_reviewer` | `true` | Style the reviewer shell and rating controls |
| `animations` | `true` | Enable brief entrance and hover motion |

The accent must use the six-digit `#RRGGBB` format. Invalid values fall back to the default blue.

## Compatibility

- Anki Desktop 25.09.4 or newer
- Locally verified on macOS
- Windows and Linux use the same add-on interfaces; device reports are welcome
- Not available on AnkiMobile, AnkiDroid, or AnkiWeb
- Full-interface themes may conflict with each other

## Privacy

Editorial Index makes no network requests, collects no telemetry, and does not read or modify card content. It loads bundled fonts and styles through Anki's add-on hooks.

## Development

```bash
python3 scripts/package_addon.py
python3 scripts/validate_addon.py
python3 scripts/smoke_test_addon.py
python3 scripts/test_native_theme.py
npm ci
npx playwright install chromium
npm run test:ui
```

Source code is licensed under the [MIT License](./LICENSE). Bundled Inter and Source Serif Pro fonts use the [SIL Open Font License 1.1](./addon/web/fonts/OFL.txt). Contributions are described in [CONTRIBUTING.md](./CONTRIBUTING.md).
