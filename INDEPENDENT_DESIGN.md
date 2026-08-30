# Independent design record

Editorial Index is an independent, from-scratch UI theme for Anki Desktop.

## What was studied

- BewlyCat and BewlyBewly were reviewed only as public examples of soft desktop UI systems.
- Anki's official source and add-on documentation were used to identify supported hooks, stable DOM anchors and theme variables.
- Catppuccin's official Palette v1.8.0 was used as the data source for the optional Catppuccin color system.

## What was not copied

- No CSS, TypeScript, Python or component implementation from either reference project.
- No logos, cat artwork, Bilibili characters, icons, fonts or other media assets.
- No upstream package names, namespaces or product branding.
- No patching or redistribution of Anki core files.

## Independent design decisions

- Product name and compatibility package: `Editorial Index` / `mistline_ui`.
- Default accent: `#2F5BBC`; custom user accents remain supported.
- Original semantic palette based on warm paper, deep ink, editorial blue, amber, vermilion and green.
- The warm-paper palette remains the default for new installations and upgrades; Catppuccin is an explicit user choice.
- Anki-native status semantics remain distinct for Again, Hard, Good and Easy.
- The interface uses continuous ledgers and reading planes instead of glass or card grids.
- Runtime styles are split by official Anki WebView context and never injected globally.

## Catppuccin data and implementation boundary

Editorial Index bundles a compact snapshot of all 26 official hexadecimal tokens for Latte, Frappé, Macchiato, and Mocha from Catppuccin Palette v1.8.0, commit `07d02aa110ef9eb7e7427afca5c73ba9cf7f8ebd`. The snapshot is distributed under Catppuccin's MIT license. It is read locally; the add-on does not fetch palette data at runtime.

The following parts are independent Editorial Index work:

- mapping raw Catppuccin tokens to Anki and Qt interface roles;
- deriving readable text, focus, disabled, destructive, and status colors while preserving the raw official swatches;
- synchronizing one selection across native Qt windows, Anki WebViews, the reviewer, and Add / Browse editors;
- the Tools menu switcher, compatibility behavior, tests, and packaging.

Editorial Index is not the official Catppuccin Anki port and does not depend on Catppuccin's ReColor configuration. The Catppuccin name identifies the optional upstream palette only; no endorsement is implied.

## Reference and license boundary

BewlyCat's custom license restricts integration into desktop or mobile clients. Editorial Index therefore does not incorporate or derive code or assets from that project. The reference is acknowledged only as design research:

- <https://github.com/keleus/BewlyCat>
- <https://github.com/BewlyBewly/BewlyBewly>
- <https://github.com/ankitects/anki>
- <https://github.com/catppuccin/palette/blob/v1.8.0/palette.json>
- <https://github.com/catppuccin/palette/blob/v1.8.0/LICENSE>
- <https://github.com/catppuccin/anki>

The bundled attribution is available in [`addon/THIRD_PARTY_NOTICES.md`](./addon/THIRD_PARTY_NOTICES.md), with the license text in [`addon/CATPPUCCIN_LICENSE`](./addon/CATPPUCCIN_LICENSE).

This record is a project provenance note, not legal advice.
