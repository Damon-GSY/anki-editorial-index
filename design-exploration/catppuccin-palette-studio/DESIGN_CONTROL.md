# Design control

Design schema: v3.1

## Gate 1 — Proposition

Gate 1 status: released
Image role status: approved
Image role: reference
Image placement: not-placed
Image role approval evidence: the user refers to the shipped README palette matrices and actual Anki Latte UI as comparison evidence.
Image role source/rights: project-owned screenshots and official Catppuccin palette data.
Brief status: approved through explicit corrective feedback on the existing product surface.
Direction status: approved as a revision of the existing selected direction, not a new visual family.
Direction preview shown: yes — README’s four-flavor interface gallery, accent matrix, and installed Latte UI.
Proposed direction: `catppuccin-palette-studio-01`
Approved direction: `catppuccin-palette-studio-01`
Brief approval evidence: “只看到比较单一的颜色，contrast 也没展示出来。”
Direction approval evidence: the feedback explicitly asks for the missing in-Anki visibility and contrast to be corrected.
Reference family: native desktop appearance/palette chooser.
Technique rationale: move comparison into the decision surface; keep the operational Deck Browser focused.
Target density: complete flavor/accent/state/semantic-preview/recovery flow without redundant controls.
Revision contract: preserve current product foundations; remove hidden-only selection; strengthen visible contrast and feedback; lock official semantics and user data.
Interpretive copy status: none — labels name actual palette roles and controls.

### Form-cause record

| Choice | Cause | Viewer effect |
| --- | --- | --- |
| Native palette dialog | selection currently hidden in a third-level menu | all choices become visible without leaving Anki |
| Flavor controls above accent grid | flavor determines every neutral/text token; accent is subordinate | correct mental model before choosing color |
| Fourteen icon swatches | README promises fourteen selectable accent values | immediate comparison and recognition |
| Semantic preview row | focus/caret/status roles are mostly interaction-only | contrast becomes visible before committing |
| Quick menu retained | existing users already depend on it | no workflow regression |

## Gate 2 — Master

Decision: pending rendered review.
HTML master: existing Anki production fixtures plus native dialog implementation.
Approved render: pending.
User approval: pending after installed screenshot review.
Approval evidence: pending.
Visual review: pending.
Benchmark comparison: pending.

## Gate 3 — Delivery

Decision: native Anki plugin is the requested interactive editable delivery.
Editable format: Python / QSS / CSS / HTML.
Interactive HTML: production regression fixtures.
Motion inventory: 150 ms in-place theme transitions only; reduced-motion behavior preserved.
