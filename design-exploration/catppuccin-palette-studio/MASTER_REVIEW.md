# Master review · Catppuccin palette studio

## Surface and evidence

- Surface: native Anki product UI, not a poster or slide sequence.
- Master render: `screenshots/themes/catppuccin-palette-studio.png`, 760 × 636.
- Product evidence: actual Anki 25.09.4 Qt dialog loaded from the installed add-on; no collection or card content appears in the capture.
- Reference family: the user's Editorial Index direction for editorial hierarchy, plus the official Catppuccin palette and semantic role guidance recorded in `DESIGN_CONTROL.md`.

## Benchmark comparison

- Type levels: the user benchmark has four practical levels (display title, navigation/section title, label, data); the master also has four (dialog title, current-selection summary, section label, control/data label).
- Text anchors and reading loop: the benchmark moves title → navigation → content table → action; the master moves title → current combination → flavor → accent → semantic result → close. Both use one dominant upper-left anchor and progressively denser information below it.
- Main-image operations: neither surface depends on a hero image. The master performs its work through a 7 × 2 official swatch grid, a selected-state outline, a 4 × 2 semantic result grid, and a live current-combination band.
- Craft family: editorial index hierarchy translated into a native configuration tool; warm field, serif display heading, restrained rules, compact data cells, and Catppuccin role colors.
- Dense and quiet zones: the title/current block is the quiet orientation zone; flavor and accent grids are the dense selection zone; semantic results are a second dense verification zone; the footer is deliberately quiet.

The master reaches the benchmark's hierarchy and close-reading density without copying its split-screen review composition, which would be inappropriate for a settings dialog.

## Authored operations

1. Exposed all 14 official accents in one 7 × 2 selection field instead of a nested menu.
2. Separated flavor choice from accent choice so the 4 × 14 data model is visible.
3. Added a live summary band containing resolved flavor, accent name, and raw upstream hex.
4. Mapped eight fixed semantic roles into a balanced 4 × 2 verification grid.
5. Used each semantic color for its own text and border rather than as decoration.
6. Preserved an Anki-native dialog, focus behavior, and compact quick menu alongside the studio.
7. Added low-saturation New / Learn / Due header surfaces to the operational deck browser instead of placing all accents there.

## Required views

- Full size: first attention is the title, then the blue current-selection band, then the 14-color field. All labels and hex values are readable; no collision or dead control was found.
- Thumbnail (280 px): title, current selection, selected Blue outline, 14-color rhythm, and the two semantic rows remain distinct. Small copy appropriately becomes secondary.
- Copy-hidden: the selection groups, swatch rhythm, current band, and semantic grid remain structurally legible, but exact roles cannot be decoded. Labels are therefore necessary content, not apparatus.
- Image-hidden: not applicable; the surface contains no image or atmospheric asset.
- Same-scale reference: compared with the user-supplied Editorial Index reference. The master retains the editorial type contrast and calm field but uses the denser control rhythm required by the palette task.
- Bottom-edge inspection: the final semantic row and Close button have clear bottom breathing room; no clipping is present at 760 × 636.

## Veto and risk review

- P0: none. No overflow, clipped footer, missing option, inaccessible blank swatch, or private user data remains.
- P1: none. Color marks state or semantic function; the accent matrix is not inserted into the everyday deck workflow.
- P2: Windows and Linux Qt font metrics have automated layout coverage but have not been visually captured on those operating systems.
- P3: English Catppuccin token names remain untranslated to preserve official naming and make configuration values easy to match.

Decision: approved for release. The operational surface stays calm, while the configuration surface now makes the complete choice set and actual contrast behavior inspectable.
