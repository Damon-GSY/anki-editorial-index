"""Standard-library regression tests; no Anki installation or collection access."""

import importlib.util
from html.parser import HTMLParser
from pathlib import Path
from types import SimpleNamespace
import unittest


MODULE_PATH = Path(__file__).resolve().parents[1] / "addon" / "cabinet_decks.py"
spec = importlib.util.spec_from_file_location("cabinet_decks", MODULE_PATH)
decks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(decks)


def node(deck_id, name, *, children=(), **overrides):
    data = dict(deck_id=deck_id, name=name, children=list(children), level=1,
                new_count=0, learn_count=0, review_count=0,
                collapsed=False, filtered=False)
    data.update(overrides)
    return SimpleNamespace(**data)


def tree(*children):
    return node(0, "", children=children, level=0)


class Elements(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.elements = []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, dict(attrs)))

    def find(self, tag):
        return [attrs for kind, attrs in self.elements if kind == tag]


class DeckRenderingTests(unittest.TestCase):
    def test_palette_entry_is_visible_even_when_all_cabinets_are_hidden(self):
        html = decks.render_deck_tree(tree(node(1, "Hidden")), 1, hidden_ids={1})
        buttons = Elements(html).find("button")
        palette = next(button for button in buttons if button.get("data-cabinet-display") == "palette")
        self.assertEqual(palette["aria-haspopup"], "dialog")
        self.assertNotIn("disabled", palette)
        self.assertIn("cabinet-palette-swatch", html)

    def test_hidden_roots_disappear_without_recalculating_parent_counts(self):
        original = tree(node(1, "Visible", new_count=9), node(2, "Hidden", children=[node(3, "Child")]))
        html = decks.render_deck_tree(original, 2, hidden_ids={2})
        self.assertNotIn('data-cabinet-deck-id="2"', html)
        self.assertNotIn("Child", html)
        self.assertIn("9</dd>", html)
        self.assertIn("已隐藏 1", html)
        self.assertEqual(len(original.children), 2)

    def test_all_hidden_still_has_recovery_control(self):
        html = decks.render_deck_tree(tree(node(1, "Hidden")), 1, hidden_ids={1, 999})
        self.assertIn("所有卡匣已隐藏", html)
        self.assertIn('data-cabinet-display="settings"', html)
        self.assertNotIn('class="cabinet-folder ', html)

    def test_folded_card_preserves_open_options_and_count_summary(self):
        html = decks.render_deck_tree(tree(node(1, "English", new_count=4)), 1, folded_ids={1})
        self.assertIn("is-folded", html)
        self.assertIn('aria-controls="cabinet-details-1" aria-expanded="false"', html)
        self.assertIn('id="cabinet-details-1" hidden', html)
        self.assertIn('data-cabinet-command="open:1"', html)
        self.assertIn('data-cabinet-command="opts:1"', html)
        self.assertIn("cabinet-folded-summary", html)

    def test_each_child_keeps_its_native_options_menu(self):
        html = self.render(node(1, "Parent", children=[node(2, "Child", children=[node(3, "Nested")])]))
        for deck_id in (1, 2, 3):
            self.assertIn(f'data-cabinet-command="opts:{deck_id}"', html)

    def render(self, *roots, selected=1):
        return decks.render_deck_tree(tree(*roots), selected)

    def test_wraps_own_layout_inside_one_nine_column_table_row(self):
        markup = self.render(node(1, "Default"))
        parsed = Elements(markup)
        self.assertEqual(parsed.find("tr"), [{"class": "cabinet-root-row"}])
        self.assertEqual(parsed.find("td"), [{"colspan": "9"}])
        self.assertIn('id="cabinet-home"', markup)

    def test_uses_scheduler_counts_without_summing_children_again(self):
        markup = self.render(node(1, "Root", new_count=7, learn_count=3,
                                  review_count=11, children=[node(2, "Sub", new_count=5)]))
        self.assertIn('<dt>新卡片</dt><dd>7</dd>', markup)
        self.assertIn('<dt>学习中</dt><dd>3</dd>', markup)
        self.assertIn('<dt>待复习</dt><dd>11</dd>', markup)
        self.assertNotIn('<dd>12</dd>', markup)

    def test_child_selection_marks_root_and_current_link(self):
        markup = self.render(node(1, "Root", children=[node(2, "Sub")]), selected=2)
        self.assertIn('class="cabinet-folder tone-lilac selected"', markup)
        self.assertIn('data-cabinet-command="open:2" aria-current="true"', markup)
        self.assertIn('Root / Sub', markup)

    def test_collapsed_children_are_not_rendered_but_selection_is_preserved(self):
        markup = self.render(node(1, "Root", collapsed=True,
                                  children=[node(2, "Hidden")]), selected=2)
        self.assertIn('tone-lilac selected', markup)
        self.assertIn('data-cabinet-command="collapse:1" aria-expanded="false"', markup)
        self.assertNotIn('data-cabinet-command="open:2"', markup)
        self.assertNotIn('Hidden', markup)

    def test_nested_fold_and_filtered_state(self):
        markup = self.render(node(1, "Root", children=[
            node(2, "Filtered", filtered=True, collapsed=True, children=[node(3, "Leaf")])]))
        self.assertIn('class="cabinet-filtered">筛选牌组', markup)
        self.assertIn('data-cabinet-command="collapse:2" aria-expanded="false"', markup)
        self.assertNotIn('data-cabinet-command="open:3"', markup)

    def test_user_names_cannot_inject_elements_or_commands(self):
        name = '\"><img src=x onerror=alert(1)> & \'quotes\''
        markup = self.render(node(1, name, children=[node(2, name)]))
        parsed = Elements(markup)
        self.assertEqual(parsed.find("img"), [])
        self.assertIn('&lt;img', markup)
        self.assertIn('&amp;', markup)
        self.assertNotIn('onclick=', markup)
        for _, attrs in parsed.elements:
            if "data-cabinet-command" in attrs:
                self.assertRegex(attrs["data-cabinet-command"], r"^(open|opts|collapse):[12]$")

    def test_every_root_is_rendered_and_palette_cycles(self):
        markup = self.render(*(node(i, f"Deck {i}") for i in range(1, 34)))
        folders = Elements(markup).find("article")
        self.assertEqual(len(folders), 33)
        self.assertEqual(folders[0]["class"], "cabinet-folder tone-lilac selected")
        self.assertEqual(folders[1]["class"], "cabinet-folder tone-peach")
        self.assertEqual(folders[2]["class"], "cabinet-folder tone-sage")
        self.assertIn('33 个卡匣 · 33 个牌组', markup)

    def test_long_names_and_duplicate_child_names_keep_full_paths(self):
        long_name = "学術読解" * 40
        markup = self.render(node(1, long_name, children=[node(2, "同名")]),
                             node(3, "Second", children=[node(4, "同名")]))
        self.assertIn(long_name, markup)
        self.assertIn(long_name + " / 同名", markup)
        self.assertIn("Second / 同名", markup)

    def test_empty_tree_and_empty_default_deck(self):
        self.assertIn('class="cabinet-empty"', self.render())
        self.assertIn('还没有牌组', self.render())
        self.assertIn('cabinet-tab-name">Default', self.render(node(1, "Default")))

    def test_tab_does_not_open_or_change_the_collection(self):
        markup = self.render(node(1, "Default"))
        tabs = [item for item in Elements(markup).find("button") if "data-cabinet-select" in item]
        self.assertEqual(len(tabs), 1)
        self.assertNotIn("data-cabinet-command", tabs[0])

    def test_invalid_ids_and_missing_schema_fail_clearly(self):
        with self.assertRaisesRegex(TypeError, "deck_id"):
            self.render(node('1\" onclick=', "Invalid"))
        with self.assertRaisesRegex(TypeError, "new_count"):
            self.render(node(1, "Invalid", new_count=True))
        with self.assertRaisesRegex(TypeError, "current_id"):
            decks.render_deck_tree(tree(), True)
        broken = node(1, "Old API")
        del broken.review_count
        with self.assertRaisesRegex(TypeError, "review_count"):
            self.render(broken)

    def test_render_does_not_mutate_input(self):
        root = node(1, "Root", children=[node(2, "Child")])
        before = repr(root)
        self.render(root)
        self.assertEqual(repr(root), before)


if __name__ == "__main__":
    unittest.main()
