"""Homepage preference regressions; stdlib only, with no real Anki collection."""

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import unittest


MODULE_PATH = Path(__file__).resolve().parents[1] / "addon" / "cabinet_display.py"
spec = importlib.util.spec_from_file_location("cabinet_display", MODULE_PATH)
display = importlib.util.module_from_spec(spec)
spec.loader.exec_module(display)


class ReadOnlyDecks:
    """Expose only the read API that this UI feature is allowed to use."""

    def __init__(self):
        self.entries = (
            SimpleNamespace(id=1, name="English"),
            SimpleNamespace(id=2, name="English::Phrases"),
            SimpleNamespace(id=3, name="日本語"),
            SimpleNamespace(id=4, name="Archive"),
        )
        self.calls = []

    def all_names_and_ids(self, *, skip_empty_default=False):
        self.calls.append({"skip_empty_default": skip_empty_default})
        return self.entries


def main_window(profile="Study"):
    return SimpleNamespace(pm=SimpleNamespace(name=profile),
                           col=SimpleNamespace(decks=ReadOnlyDecks()))


class PreferenceTests(unittest.TestCase):
    def test_missing_preferences_default_to_visible_and_expanded(self):
        self.assertEqual(display.preferences({}, "Study"), (set(), set()))

    def test_malformed_mapping_or_profile_does_not_hide_decks(self):
        for value in (None, [], "broken", 1, True):
            with self.subTest(value=value):
                self.assertEqual(display.preferences({"cabinet_display": value}, "Study"),
                                 (set(), set()))
                self.assertEqual(display.preferences({"cabinet_display": {"Study": value}}, "Study"),
                                 (set(), set()))

    def test_malformed_id_containers_are_ignored(self):
        for value in (None, {}, "123", 123, True):
            with self.subTest(value=value):
                config = {"cabinet_display": {"Study": {
                    "hidden_decks": value, "folded_decks": value}}}
                self.assertEqual(display.preferences(config, "Study"), (set(), set()))

    def test_ids_only_keep_positive_ascii_integer_values_in_range(self):
        raw = [1, "2", "0003", 1, True, False, 0, "0", -1, "-1", 1.0,
               None, {}, [], " 4", "4 ", "+4", "1.0", "1e2", "١", "２",
               2**63 - 1, 2**63, str(2**63), ""]
        config = {"cabinet_display": {"Study": {"hidden_decks": raw, "folded_decks": raw}}}
        expected = {1, 2, 3, 2**63 - 1}
        self.assertEqual(display.preferences(config, "Study"), (expected, expected))

    def test_oversized_digit_strings_are_ignored_without_raising(self):
        config = {"cabinet_display": {"Study": {
            "hidden_decks": ["9" * 5000, 1], "folded_decks": ["9" * 5000, 3]}}}
        self.assertEqual(display.preferences(config, "Study"), ({1}, {3}))

    def test_supported_id_containers_are_normalized_to_sets(self):
        for constructor in (list, tuple, set, frozenset):
            with self.subTest(container=constructor.__name__):
                config = {"cabinet_display": {"Study": {
                    "hidden_decks": constructor(["3", 1]),
                    "folded_decks": constructor([4])}}}
                self.assertEqual(display.preferences(config, "Study"), ({1, 3}, {4}))

    def test_profiles_do_not_share_visibility_or_fold_state(self):
        config = {"cabinet_display": {
            "Study": {"hidden_decks": [1], "folded_decks": [3]},
            "Work": {"hidden_decks": [3], "folded_decks": [1]},
        }}
        self.assertEqual(display.preferences(config, "Study"), ({1}, {3}))
        self.assertEqual(display.preferences(config, "Work"), ({3}, {1}))
        self.assertEqual(display.preferences(config, "New"), (set(), set()))

    def test_updating_copies_state_preserves_other_profiles_and_unknown_fields(self):
        config = {"layout": "cabinet", "cabinet_display": {
            "Study": {"hidden_decks": [1], "folded_decks": [3], "future_setting": {"density": 2}},
            "Work": {"hidden_decks": [8], "future_setting": True},
        }}
        before = deepcopy(config)
        result = display.updated_preferences(config, "Study", ["4", 3, 3, -1], ["4", 1])
        self.assertEqual(result["Study"], {"hidden_decks": [3, 4], "folded_decks": [1, 4],
                                         "future_setting": {"density": 2}})
        self.assertEqual(result["Work"], before["cabinet_display"]["Work"])
        self.assertEqual(config, before)
        self.assertIsNot(result, config["cabinet_display"])
        self.assertIsNot(result["Study"], config["cabinet_display"]["Study"])

    def test_update_repairs_malformed_mapping_or_current_profile(self):
        for stored in (None, [], "broken", {"Study": []}):
            with self.subTest(stored=stored):
                result = display.updated_preferences({"cabinet_display": stored}, "Study", {3}, set())
                self.assertEqual(result, {"Study": {"hidden_decks": [3], "folded_decks": []}})

    def test_saved_preferences_survive_json_roundtrip(self):
        saved = display.updated_preferences({}, "账户1", {4, 1}, {3, 4})
        config = json.loads(json.dumps({"cabinet_display": saved}))
        self.assertEqual(display.preferences(config, "账户1"), ({1, 4}, {3, 4}))

    def test_read_returns_independent_sets(self):
        config = {"cabinet_display": {"Study": {"hidden_decks": [1], "folded_decks": [3]}}}
        hidden, folded = display.preferences(config, "Study")
        hidden.clear()
        folded.add(4)
        self.assertEqual(display.preferences(config, "Study"), ({1}, {3}))


class DisplayActionTests(unittest.TestCase):
    def setUp(self):
        self.mw = main_window()
        self.saved = []
        self.config = {"cabinet_display": {
            "Study": {"hidden_decks": [4], "folded_decks": [4, 999], "future_setting": True},
            "Other": {"hidden_decks": [1], "folded_decks": [3]},
        }}

    def apply(self, action, config=None):
        return display.apply_action(self.mw, self.config if config is None else config,
                                    action, self.saved.append)

    def test_root_list_excludes_children_without_editing_deck_data(self):
        original = repr(self.mw.col.decks.entries)
        self.assertEqual([item.id for item in display.root_decks(self.mw)], [1, 3, 4])
        self.assertEqual(self.mw.col.decks.calls, [{"skip_empty_default": True}])
        self.assertEqual(repr(self.mw.col.decks.entries), original)

    def test_single_visible_root_toggles_and_persists_without_input_mutation(self):
        before = deepcopy(self.config)
        self.assertTrue(self.apply("fold:1"))
        self.assertEqual(self.saved[-1]["Study"]["folded_decks"], [1, 4, 999])
        updated = {"cabinet_display": self.saved[-1]}
        self.assertTrue(self.apply("fold:1", updated))
        self.assertEqual(self.saved[-1]["Study"]["folded_decks"], [4, 999])
        self.assertEqual(self.config, before)

    def test_child_hidden_or_absent_ids_cannot_be_toggled(self):
        for action in ("fold:2", "fold:4", "fold:999", "fold:0", "fold:9223372036854775808"):
            with self.subTest(action=action):
                self.assertFalse(self.apply(action))
        self.assertEqual(self.saved, [])

    def test_unknown_or_malformed_actions_do_not_save(self):
        for action in ("", "settings", "open:1", "fold", "fold:", "fold:-1", "fold:+1",
                       "fold:1.0", "fold:1 ", "fold: 1", "fold:１", "fold:١", "fold:1\n",
                       "fold-all:1", "unfold-all:1"):
            with self.subTest(action=action):
                self.assertFalse(self.apply(action))
        self.assertEqual(self.saved, [])

    def test_oversized_digit_action_is_rejected_without_raising(self):
        self.assertFalse(self.apply("fold:" + "9" * 5000))
        self.assertEqual(self.saved, [])

    def test_fold_all_adds_only_visible_roots_and_retains_hidden_fold_state(self):
        self.assertTrue(self.apply("fold-all"))
        self.assertEqual(self.saved[-1]["Study"], {
            "hidden_decks": [4], "folded_decks": [1, 3, 4, 999], "future_setting": True})
        self.assertEqual(self.saved[-1]["Other"], self.config["cabinet_display"]["Other"])

    def test_unfold_all_leaves_hidden_and_stale_fold_state_unchanged(self):
        self.config["cabinet_display"]["Study"]["folded_decks"] = [1, 2, 3, 4, 999]
        self.assertTrue(self.apply("unfold-all"))
        self.assertEqual(self.saved[-1]["Study"]["folded_decks"], [2, 4, 999])
        self.assertEqual(self.saved[-1]["Study"]["hidden_decks"], [4])

    def test_all_hidden_bulk_actions_do_not_drop_existing_preferences(self):
        self.config["cabinet_display"]["Study"]["hidden_decks"] = [1, 3, 4]
        original = deepcopy(self.config["cabinet_display"])
        self.assertTrue(self.apply("fold-all"))
        self.assertTrue(self.apply("unfold-all"))
        self.assertEqual(self.saved, [original, original])

    def test_missing_active_profile_or_collection_never_saves(self):
        for profile in (None, ""):
            self.mw.pm.name = profile
            self.assertFalse(self.apply("fold-all"))
        self.mw.pm.name = "Study"
        self.mw.col = None
        self.assertFalse(self.apply("fold-all"))
        self.assertEqual(self.saved, [])

    def test_deck_rename_keeps_id_based_preferences(self):
        self.mw.col.decks.entries[0].name = "Renamed"
        self.assertTrue(self.apply("fold:1"))
        self.assertIn(1, self.saved[-1]["Study"]["folded_decks"])

    def test_display_actions_do_not_mutate_collection_or_access_scheduler(self):
        original = repr(self.mw.col.decks.entries)
        for action in ("fold:1", "fold-all", "unfold-all"):
            self.assertTrue(self.apply(action))
        self.assertEqual(repr(self.mw.col.decks.entries), original)
        self.assertEqual(set(vars(self.mw.col)), {"decks"})
        self.assertEqual(self.mw.col.decks.calls, [{"skip_empty_default": True}] * 3)


if __name__ == "__main__":
    unittest.main()
