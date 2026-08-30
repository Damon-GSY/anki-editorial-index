# Design control

Design schema: v3.1

## Gate 1 — Proposition

Gate 1 status: released
Image role status: approved
Image role: reference
Image placement: not-placed
Image role approval evidence: user supplied `https://github.com/catppuccin/catppuccin` as the mandatory reference.
Image role source/rights: official public Catppuccin repository, MIT license.
Brief status: approved
Direction status: approved
Direction preview shown: yes — existing Editorial Index production captures and README theme gallery.
Proposed direction: `catppuccin-semantic-port-01`
Approved direction: `catppuccin-semantic-port-01`
Brief approval evidence: the user requested adjustment of every theme in the existing project.
Direction approval evidence: “必须要参考这里面的配色…你都去调整下。”
Reference family: official application palette port / desktop product UI.
Technique rationale: expose the full neutral, typography, interaction, and status ladders defined by Catppuccin instead of tinting most roles with the selected accent.
Target density: complete functional states plus at least four visible design acts per state: layered neutral field, typographic hierarchy, semantic status colors, and distinct interaction feedback.
Revision contract: preserve Editorial Index composition and type; remove accent-role collapse; strengthen official semantic token use; lock exact raw palette values, accessibility, and user theme switching; match the reference level of Catppuccin's published style guide.
Interpretive copy status: none.

### Palette and type cause record

| Decision | Cause | Rejected alternative |
| --- | --- | --- |
| Base as the main field | official background-pane mapping | reusing Surface or an arbitrary tinted grey as the canvas |
| Mantle / Crust for secondary panes | official secondary-pane mapping | making every layer the same Base color |
| Surface 0 / 1 / 2 for controls and elevation | official surface-element mapping | deriving all controls from the chosen accent |
| Text / Subtext 0 / Subtext 1 / Overlay 1 for hierarchy | official typography mapping | one purple-grey text color at every level |
| Blue links, Green success, Yellow warning, Red error | official typography semantics | selected accent reused for links and statuses |
| Rosewater cursor and Lavender focus/active border | official general/terminal interaction guidance | selected accent reused for cursor and keyboard focus |
| Inter + Source Serif Pro unchanged | existing user-approved Editorial Index direction and bundled CJK-safe fallback | introducing a new type voice during a color-only revision |

### Fact provenance

- Catppuccin repository design philosophy: official upstream README, commit `d09787dd98ca6fba08af5ef2ae94a7e09f17daca`.
- Catppuccin semantic mapping: official upstream `docs/style-guide.md` at the same commit.
- Raw palette values: file-recorded pinned Catppuccin Palette v1.8.0 snapshot.
- Anki-specific state mapping: system-inferred from official semantic roles plus existing Anki conventions; covered by contrast and UI regression tests.

Source route: local add-on and tests → official Catppuccin repository/style guide → no generated or third-party visual assets.
Source policy: upstream relationships are translated into Anki semantics; the website/repository layout is not copied.
Contact sheet: `../production-preview/captures/` and `../../screenshots/themes/`.
Asset ledger: `ASSET_LEDGER.md`.
Hero source: none.
Generation exception: none.

## Gate 2 — Master

Decision: released for verification and delivery.
HTML master: `../production-preview/index.html`.
Approved renders: `../../screenshots/themes/catppuccin-latte-blue.png`, `catppuccin-frappe-blue.png`, `catppuccin-macchiato-blue.png`, `catppuccin-mocha-blue.png`, and `catppuccin-semantic-roles.png`.
User approval: revision authority granted by the explicit request to apply every official theme combination; final implementation review remains available after release.
Approval evidence: “必须要参考这里面的配色…每个不同的theme里面都有不同的颜色组合你都去调整下。”
Visual review: full-size and thumbnail review completed for all four interface renders and the semantic-role sheet. No clipped bottom edge, overflow, collision, unreadable text, or unexplained decorative color remains. The selected row, table header, status columns, heatmap, and quiet field retain distinct roles in every flavor.

### Required-view review

- Full size: first attention is Deck Home, then current deck, then New / Learn / Due; the role sheet reads flavor first and semantic role second.
- Thumbnail: the four backgrounds and functional color families remain visibly distinct; no state depends on tiny labels alone.
- Copy-hidden: Base / Mantle / Surface / selection and status-color distribution still communicate hierarchy.
- Image-hidden: no external or generated imagery carries product meaning; the interface and its generated evidence remain intact.
- Bottom edge: all four 1440 × 1000 renders and the 1800 × 1753 role sheet were inspected at native resolution with no clipped content.
- Remaining risk: the README gallery demonstrates representative Deck Browser states, while popup and Editor surfaces are proved by automated regression rather than a second screenshot set. Classified P3 because those surfaces use the same tested tokens.

### Benchmark comparison

Equal-height comparison: `benchmark-comparison.png` (user-approved Editorial Index direction on the left, Catppuccin Latte master on the right).

- Type levels: benchmark 4 visible levels (brand/title, page heading/question, row/answer, metadata); master 4 (page title, parent deck, leaf deck, table/heatmap metadata).
- Text anchors and reading loop: benchmark moves top navigation → deck tree → reviewer action; master moves page heading → deck hierarchy → selected row → heatmap summary. The master retains the same left-to-right status scan inside the deck table.
- Operations inside the main interface: neutral-layer separation, typographic hierarchy, semantic status coloring, selected-accent state, and history/forecast heatmap distinction.
- Craft family: restrained editorial desktop UI with Source Serif display type, Inter controls, ruled index rows, and compact state notation. The Catppuccin treatment changes color ownership, not the approved craft family.
- Dense / quiet distribution: benchmark splits two dense work panes with quiet margins; the single-state master keeps one dense table band and one compact heatmap band inside a quiet Base field. The apparent extra quiet area is intentional state focus, not missing functionality.

## Gate 3 — Delivery

Decision: product source and installable Anki package are the requested editable/interactive delivery; no Figma translation requested.
Editable format: Python / CSS / JSON / HTML.
Editable Figma file: not requested.
Primary frame/node: not applicable.
Figma node audit: not applicable.
Figma comparison: not applicable.
Interactive HTML: `../production-preview/index.html`.
Motion inventory: existing 150–240 ms state feedback only; reduced-motion behavior preserved.
