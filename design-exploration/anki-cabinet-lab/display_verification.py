"""Native settings + WebEngine checks on the harness's generated decks only."""

import json
from pathlib import Path

from aqt.qt import QLineEdit, QPushButton, QTreeWidget, Qt
from PyQt6.QtTest import QTest


class DisplayVerification:
    def __init__(self, driver):
        self.d = driver
        self.mw = driver.mw
        self.addon = driver.production_addon
        self.before = self.fingerprint()
        self.open_settings(self.cancel_draft)

    def fingerprint(self):
        return (self.mw.col.db.all("select id,did,queue,type,due,ivl,factor,reps,lapses from cards order by id"),
                self.mw.col.note_count(), self.mw.col.db.scalar("select count(*) from revlog"))

    def open_settings(self, then):
        self.d.click('[data-cabinet-display="settings"]', lambda: self.d.later(350, then))

    def dialog(self):
        dialog = self.mw._editorial_cabinet_display_dialog
        self.d.check("Display settings opens a real native dialog", dialog is not None and dialog.isVisible())
        return dialog

    def rows(self, dialog):
        tree = dialog.findChild(QTreeWidget, "CabinetDisplayDecks")
        return {int(tree.topLevelItem(i).data(0, Qt.ItemDataRole.UserRole)): tree.topLevelItem(i)
                for i in range(tree.topLevelItemCount())}

    def set_checked(self, row, column, value):
        row.setCheckState(column, Qt.CheckState.Checked if value else Qt.CheckState.Unchecked)

    def button(self, dialog, name):
        dialog.findChild(QPushButton, "CabinetDisplay" + name).click()

    def cancel_draft(self):
        dialog = self.dialog()
        rows = self.rows(dialog)
        self.d.check("Display settings lists only top-level decks", len(rows) == 5 and self.d.decks["phrases"] not in rows)
        tree = dialog.findChild(QTreeWidget, "CabinetDisplayDecks")
        tree.setFocus()
        tree.setCurrentItem(rows[self.d.decks["empty"]], 1)
        QTest.keyClick(tree, Qt.Key.Key_Space)
        self.d.check("Native display checkbox supports keyboard Space", rows[self.d.decks["empty"]].checkState(1) == Qt.CheckState.Unchecked)
        QTest.keyClick(tree, Qt.Key.Key_Space)
        self.config_before = self.addon._get_config()["cabinet_display"]
        self.set_checked(rows[self.d.decks["empty"]], 1, False)
        self.button(dialog, "Cancel")
        self.d.check("Cancel discards display drafts", self.addon._get_config()["cabinet_display"] == self.config_before)
        self.d.later(200, lambda: self.open_settings(self.save_choices))

    def save_choices(self):
        dialog = self.dialog()
        rows = self.rows(dialog)
        self.set_checked(rows[self.d.decks["empty"]], 1, False)
        self.set_checked(rows[self.d.decks["english"]], 2, True)
        search = dialog.findChild(QLineEdit, "CabinetDisplaySearch")
        search.setText("English")
        self.d.check("Searching settings filters without losing checkbox drafts",
                     sum(not row.isHidden() for row in rows.values()) == 1
                     and rows[self.d.decks["empty"]].checkState(1) == Qt.CheckState.Unchecked)
        search.clear()
        path = Path(self.d.report["screenshots"][0]).parent / "17-display-settings.png"
        self.d.check("Qt settings screenshot", dialog.grab().save(str(path)))
        self.d.report["screenshots"].append(str(path))
        self.button(dialog, "Save")
        self.d.later(850, self.check_choices)

    def home_state(self, then):
        self.d.js("""(()=>{const folders=[...document.querySelectorAll('.cabinet-folder')];return {
          count:folders.length,ids:folders.map(e=>+e.dataset.cabinetDeckId),
          folds:folders.filter(e=>e.classList.contains('is-folded')).map(e=>+e.dataset.cabinetDeckId),
          compressed:folders.filter(e=>e.classList.contains('is-folded')).every(e=>{
            const inner=e.querySelector('.cabinet-folder-inner');const button=e.querySelector('.cabinet-fold');
            return !inner.checkVisibility() && e.getBoundingClientRect().height<250 &&
              e.querySelector('.cabinet-open').checkVisibility() && e.querySelector('.cabinet-counts').checkVisibility() &&
              button.getAttribute('aria-expanded')==='false' && !!document.getElementById(button.getAttribute('aria-controls'));
          }),settings:!!document.querySelector('[data-cabinet-display=settings]'),
          noOverflow:document.documentElement.scrollWidth<=innerWidth+2,
          focusedAction:document.activeElement?.dataset.cabinetDisplay || '',
          empty:document.querySelector('#cabinet-home').innerText.includes('所有卡匣已隐藏')};})()""", then)

    def check_choices(self):
        def after(state):
            self.d.check("Saved hidden cabinet is removed from home", state["count"] == 4 and self.d.decks["empty"] not in state["ids"], state)
            self.d.check("Saved fold compresses cabinet while retaining controls/counts",
                         state["folds"] == [self.d.decks["english"]] and state["compressed"], state)
            metadata = json.loads((Path(self.d.report["scratch"]) / "addons21/mistline_ui/meta.json").read_text())
            expected = {"hidden_decks": [self.d.decks["empty"]], "folded_decks": [self.d.decks["english"]]}
            self.d.check("Display preferences persist to Anki add-on metadata", metadata["config"]["cabinet_display"][self.mw.pm.name] == expected)
            self.d.capture("18-hidden-and-folded-home")
            self.mw.deckBrowser.refresh()
            self.d.later(650, lambda: self.open_settings(self.reopen_choices))
        self.home_state(after)

    def reopen_choices(self):
        dialog = self.dialog()
        rows = self.rows(dialog)
        self.d.check("Rebuilt home and reopened dialog retain saved choices",
                     rows[self.d.decks["empty"]].checkState(1) == Qt.CheckState.Unchecked
                     and rows[self.d.decks["english"]].checkState(2) == Qt.CheckState.Checked)
        self.button(dialog, "Cancel")
        self.d.later(150, lambda: self.d.click('[data-cabinet-display="fold:' + str(self.d.decks["english"]) + '"]',
                     lambda: self.d.later(650, self.check_single_unfold)))

    def check_single_unfold(self):
        def after(state):
            self.d.check("Individual fold control expands and persists", state["folds"] == [])
            self.d.check("Folding preserves keyboard focus after native rerender", state["focusedAction"] == 'fold:' + str(self.d.decks["english"]), state)
            self.d.click('[data-cabinet-display="fold-all"]', lambda: self.d.later(650, self.check_all_folded))
        self.home_state(after)

    def check_all_folded(self):
        def after(state):
            self.d.check("Fold all affects all visible cabinets", len(state["folds"]) == 4 and state["compressed"], state)
            self.mw.resize(820, 760)
            self.d.later(450, self.narrow_folded)
        self.home_state(after)

    def narrow_folded(self):
        def after(state):
            self.d.check("Folded controls fit a narrow Anki window", state["noOverflow"] and state["compressed"], state)
            self.d.capture("19-folded-home-820")
            self.mw.resize(1280, 860)
            self.d.click('[data-cabinet-display="unfold-all"]', lambda: self.d.later(650, self.check_all_unfolded))
        self.home_state(after)

    def check_all_unfolded(self):
        def after(state):
            self.d.check("Expand all preserves hidden choices", state["count"] == 4 and not state["folds"], state)
            self.open_settings(self.hide_everything)
        self.home_state(after)

    def hide_everything(self):
        dialog = self.dialog()
        for row in self.rows(dialog).values():
            self.set_checked(row, 1, False)
        self.button(dialog, "Save")
        self.d.later(650, self.check_all_hidden)

    def check_all_hidden(self):
        def after(state):
            self.d.check("All-hidden home explains how to recover and keeps settings", state["count"] == 0 and state["settings"] and state["empty"], state)
            self.d.capture("20-all-hidden-recovery")
            self.open_settings(self.cancel_reset)
        self.home_state(after)

    def cancel_reset(self):
        dialog = self.dialog()
        self.button(dialog, "Reset")
        self.d.check("Reset fills the default draft", all(row.checkState(1) == Qt.CheckState.Checked and row.checkState(2) == Qt.CheckState.Unchecked for row in self.rows(dialog).values()))
        self.button(dialog, "Cancel")
        self.d.later(200, self.check_reset_cancel)

    def check_reset_cancel(self):
        def after(state):
            self.d.check("Cancel after Reset does not apply the reset", state["count"] == 0)
            self.open_settings(self.save_reset)
        self.home_state(after)

    def save_reset(self):
        dialog = self.dialog()
        self.button(dialog, "Reset")
        self.button(dialog, "Save")
        self.d.later(650, self.check_reset_saved)

    def check_reset_saved(self):
        def after(state):
            self.d.check("Saving Reset recovers every cabinet expanded", state["count"] == 5 and not state["folds"])
            self.d.check("Display operations do not change cards, notes, scheduling or review log", self.before == self.fingerprint())
            before = self.addon._get_config()["cabinet_display"]
            self.addon._cabinet_display_message((False, None), "editorial-cabinet:fold-all", self.mw.reviewer)
            self.addon._cabinet_display_message((True, "owned"), "editorial-cabinet:fold-all", self.mw.deckBrowser)
            self.d.check("Display bridge rejects reviewer/previously handled messages", before == self.addon._get_config()["cabinet_display"])
            self.addon._select_palette("mocha")
            self.d.later(650, lambda: self.open_settings(self.dark_settings))
        self.home_state(after)

    def dark_settings(self):
        dialog = self.dialog()
        path = Path(self.d.report["screenshots"][0]).parent / "21-display-settings-mocha.png"
        self.d.check("Qt dark settings screenshot", dialog.grab().save(str(path)))
        self.d.report["screenshots"].append(str(path))
        self.button(dialog, "Cancel")
        self.addon._select_palette("latte")
        self.d.later(350, self.d.start_palette_checks)
