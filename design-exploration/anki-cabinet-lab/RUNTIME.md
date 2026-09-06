# Isolated real-Anki runtime

This is not a browser mock and is not an install into your everyday Anki profile.
It loads the locally installed Anki Python/Qt libraries, launches a separate
`aqt.AnkiQt` instance, and creates a new disposable profile containing only
generated notes. No existing collection is read or copied.

From this directory:

```sh
python3 run.py --verify
python3 run.py --open
```

To exercise the integrated production add-on rather than the experimental copy:

```sh
python3 run.py --production --verify
python3 run.py --production --open
```

`--production` copies the repository's `addon/` into **another newly generated
scratch profile**, under the normal `mistline_ui` package name. It does not install
anything into the user's existing Anki. Only this scratch copy receives test
settings (`layout: cabinet`, Catppuccin Latte, Blue accent, reviewer styling on).
Its reports and screenshots go into `production-evidence/`, keeping the earlier
lab evidence unchanged. The production verifier additionally switches layouts,
Latte/Mocha palettes, and reviewer styling while the same native answer is shown;
it checks that card HTML, card ID and review log remain unchanged and that the
reviewer and rating bar each have exactly one active theme stylesheet (zero when
reviewer styling is disabled). It also checks a rendered canvas color change,
stock card text contrast of at least 4.5:1 (including light-system + Mocha), and a
home-screen Editorial → Cabinet round trip without duplicating the deck tree.
Both active layouts must load the shared Heatmap stylesheet through real CSSOM
imports. The verifier expands and collapses the generated parent deck through
Anki's own command and inspects the visible child-deck options entry without
opening or changing options. It verifies that child names/paths do not overlap
their counters and that Shift-click selects a real deck without opening overview.
After generating notes, the harness waits for all five generated root decks to
reach the native view, refreshing through Anki if its initial empty-profile
asynchronous render won the seed/reset race.
The first screenshot is taken after an extra Qt paint cycle; a ready DOM alone
does not guarantee that Qt WebEngine has presented its initial GPU texture.

`--verify` runs the real deck browser → overview → reviewer question → answer →
Good → undo sequence. It checks the real scheduler's review log and card state,
then checks stock typed-answer, cloze, image, and MathJax templates. The resulting
`runtime-report.json` and `screenshots/` are actual Anki/Qt evidence, not prototype
screenshots. `--open` leaves an independent demo window open for manual inspection.
The verifier also checks an 820-pixel-wide native window, an empty deck, and the
Tools-menu theme toggle in both directions. Screenshot saves and functional
assertions are separately named in the report; not every report entry is a
distinct functionality test.

The runner currently targets the local macOS `/Applications/Anki.app` and a
compatible local Python 3.13. It does not download or install dependencies.
Missing dependencies cause a clear error, not a fallback to mock testing.

Each run creates a new `anki-cabinet-lab-*` temporary directory with a marker file,
its own profile, collection, add-on copy, runtime log, and IPC key. That prevents
Anki's single-instance forwarding from sending commands to the existing app.
Automatic sync and update checks are disabled for this generated profile. Close
the demo window normally; no existing Anki process is stopped. Scratch data is
kept for inspection and can be discarded later using the exact path printed by
the runner. No Git commit, installation into a regular profile, or release occurs.
On macOS, the Python launcher can emit a file-open event for the driver script;
the lab ignores only that exact script path so it is not mistaken for a deck to
import. The scheduler, grading, typed-answer comparison, and undo implementations
are Anki's own.

Scope: passing this local test demonstrates this installed Anki version's native
flows, not support for every operating system, third-party add-on, or card
template. The styling can be toggled off from the lab's Tools menu to compare
against the original native UI.
