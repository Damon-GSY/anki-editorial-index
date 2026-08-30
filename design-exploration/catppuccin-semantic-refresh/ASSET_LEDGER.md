# Asset ledger

| Asset | Role | Source / local path | Rights / status | Factual or interpretive | Use rule |
| --- | --- | --- | --- | --- | --- |
| Catppuccin repository | reference | https://github.com/catppuccin/catppuccin | MIT; official upstream | factual | Design philosophy and source provenance only; do not copy repository layout. |
| Catppuccin style guide | reference | https://github.com/catppuccin/catppuccin/blob/d09787dd98ca6fba08af5ef2ae94a7e09f17daca/docs/style-guide.md | MIT; official upstream | factual | Semantic role authority for backgrounds, typography, states, selection, cursor, and focus. |
| Pinned palette snapshot | project evidence | `../../addon/catppuccin.json` | MIT; exact Palette v1.8.0 data | factual | Raw values stay unchanged; never overwrite them with derived colors. |
| Production fixture | project evidence | `../production-preview/index.html` | project-owned | factual | Render actual add-on CSS and representative Anki DOM states. |
| README theme captures | project evidence | `../../screenshots/themes/` | project-generated | factual | Regenerate from the runtime contract after implementation; no manual recoloring. |

