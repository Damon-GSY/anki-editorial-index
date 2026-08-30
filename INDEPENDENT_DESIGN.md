# Independent design record

Editorial Index is an independent, from-scratch UI theme for Anki Desktop.

## What was studied

- BewlyCat and BewlyBewly were reviewed only as public examples of soft desktop UI systems.
- Anki's official source and add-on documentation were used to identify supported hooks, stable DOM anchors and theme variables.

## What was not copied

- No CSS, TypeScript, Python or component implementation from either reference project.
- No logos, cat artwork, Bilibili characters, icons, fonts or other media assets.
- No upstream package names, namespaces or product branding.
- No patching or redistribution of Anki core files.

## Independent design decisions

- Product name and compatibility package: `Editorial Index` / `mistline_ui`.
- Default accent: `#2F5BBC`; custom user accents remain supported.
- Original semantic palette based on warm paper, deep ink, editorial blue, amber, vermilion and green.
- Anki-native status semantics remain distinct for Again, Hard, Good and Easy.
- The interface uses continuous ledgers and reading planes instead of glass or card grids.
- Runtime styles are split by official Anki WebView context and never injected globally.

## Reference and license boundary

BewlyCat's custom license restricts integration into desktop or mobile clients. Editorial Index therefore does not incorporate or derive code or assets from that project. The reference is acknowledged only as design research:

- <https://github.com/keleus/BewlyCat>
- <https://github.com/BewlyBewly/BewlyBewly>
- <https://github.com/ankitects/anki>

This record is a project provenance note, not legal advice.
