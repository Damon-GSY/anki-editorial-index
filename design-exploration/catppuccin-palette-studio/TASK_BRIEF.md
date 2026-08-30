# Task brief

## Authority and scope

- Controller / user instruction: “我怎么没在这个 Anki 里面看到……用 Latte 的时候只看到比较单一的颜色，contrast 也没展示出来。”
- Deliverable: an Anki-native palette chooser plus the existing Deck Browser state; source remains editable Python, QSS, CSS, HTML fixtures, tests, screenshots, and documentation.
- Interaction policy: revision-led product work on the already approved Editorial Index + Catppuccin direction.

## Reader and truth

- Reader action: see the current flavor/accent, compare all four flavors and fourteen accents, understand the semantic contrast, then switch without editing JSON or restarting Anki.
- Required truth: 56 means mutually selectable combinations, not 14 accents shown simultaneously in the operational interface.
- Required behavior: every click updates open Anki surfaces in place and persists the selected flavor/accent; existing configuration and card/editor state remain intact.
- Refusals: another hidden submenu; a static palette poster disconnected from the switch; showing all 14 accents permanently on the Deck Browser; using decorative color with no UI role.

## Form and state map

- State 1 — operational Deck Browser: remains calm and shows the selected combination plus semantic learning status.
- State 2 — palette studio default: exposes current flavor, current accent, four/five flavor choices, all 14 accents, and a semantic role preview.
- State 3 — palette studio after choice: live preview and checked state update while the dialog remains open.
- Recovery: Close leaves the latest saved selection; the existing Editorial warm-paper option remains available.

## Evidence and density

- Official Catppuccin palette and style-guide relationships remain the color source.
- Product density comes from visible current state, flavor controls, accent controls, semantic preview, immediate feedback, and a clear close path.
- At least four design acts: clear two-level selection hierarchy, swatch-led accent grid, named semantic preview, and live selected-state feedback.

## Revision contract

- Preserve: Editorial layout, typography, live switching, official color values, accessibility, existing quick menu, and all Anki behavior.
- Remove: discoverability failure and the implication that README’s matrix is already visible in Anki.
- Strengthen: visual comparison, current-state visibility, Latte semantic contrast, and documentation.
- Locked: one selected accent at a time; functional colors retain their official roles.
