"""Render Anki's existing due tree without querying or mutating a collection.

The input is ``aqt.deckbrowser.RenderData.tree`` (a DeckTreeNode container),
not a list of decks. Counts already include Anki's scheduler limits and child
decks; this renderer deliberately never recomputes or sums them.
"""

from __future__ import annotations

from html import escape


_TONES = ("lilac", "peach", "sage")
_COUNTS = (("new_count", "new", "新卡片"),
           ("learn_count", "learn", "学习中"),
           ("review_count", "review", "待复习"))
_FIELDS = ("deck_id", "name", "level", "collapsed", "filtered", "children",
           "new_count", "learn_count", "review_count")


def _validate_node(node: object, *, container: bool = False) -> None:
    missing = [field for field in _FIELDS if not hasattr(node, field)]
    if missing:
        raise TypeError("Cabinet requires Anki DeckTreeNode fields: " + ", ".join(missing))
    if not isinstance(node.name, str):
        raise TypeError("DeckTreeNode.name must be a string")
    for field in ("deck_id", "level", "new_count", "learn_count", "review_count"):
        value = getattr(node, field)
        if type(value) is not int or value < 0:
            raise TypeError(f"DeckTreeNode.{field} must be a nonnegative integer")
    if not container and node.deck_id == 0:
        raise ValueError("A displayed deck must have a positive deck_id")
    for field in ("collapsed", "filtered"):
        if type(getattr(node, field)) is not bool:
            raise TypeError(f"DeckTreeNode.{field} must be a boolean")
    try:
        children = iter(node.children)
    except TypeError as error:
        raise TypeError("DeckTreeNode.children must be iterable") from error
    for child in children:
        _validate_node(child)


def _contains(node: object, current_id: int) -> bool:
    return node.deck_id == current_id or any(
        _contains(child, current_id) for child in node.children
    )


def _deck_count(node: object) -> int:
    return 1 + sum(_deck_count(child) for child in node.children)


def _counts(node: object, *, compact: bool = False) -> str:
    klass = "cabinet-counts compact" if compact else "cabinet-counts"
    items = []
    for field, kind, label in _COUNTS:
        number = getattr(node, field)
        zero = " zero" if number == 0 else ""
        items.append(
            f'<div class="cabinet-count {kind}{zero}">'
            f'<dt>{label}</dt><dd>{number:,}</dd></div>'
        )
    return f'<dl class="{klass}">' + "".join(items) + "</dl>"


def _filtered(node: object) -> str:
    return '<span class="cabinet-filtered">筛选牌组</span>' if node.filtered else ""


def _collapse(node: object) -> str:
    if not node.children:
        return '<span class="cabinet-collapse-spacer" aria-hidden="true"></span>'
    expanded = str(not node.collapsed).lower()
    action = "展开" if node.collapsed else "折叠"
    symbol = "+" if node.collapsed else "−"
    label = escape(f"{action} {node.name} 的子牌组", quote=True)
    return (
        f'<button type="button" class="cabinet-collapse" '
        f'data-cabinet-command="collapse:{node.deck_id}" '
        f'aria-expanded="{expanded}" aria-label="{label}">{symbol}</button>'
    )


def _children(node: object, path: tuple[str, ...], current_id: int) -> str:
    if not node.children or node.collapsed:
        return ""
    items = []
    for child in node.children:
        child_path = (*path, child.name)
        path_text = escape(" / ".join(child_path), quote=True)
        current = child.deck_id == current_id
        current_class = " current" if current else ""
        current_attr = ' aria-current="true"' if current else ""
        items.append(
            f'<li class="cabinet-child{current_class}" data-cabinet-deck-id="{child.deck_id}">'
            '<div class="cabinet-child-row">'
            + _collapse(child)
            + '<div class="cabinet-child-name">'
            f'<a class="cabinet-child-link" href="#" data-cabinet-command="open:{child.deck_id}"'
            f'{current_attr} title="{path_text}">{escape(child.name)}</a>'
            f'<small class="cabinet-child-path">{path_text}</small>'
            + _filtered(child)
            + "</div>"
            + _counts(child, compact=True)
            + f'<button type="button" class="cabinet-child-options" data-cabinet-command="opts:{child.deck_id}" '
            f'aria-label="{escape(child.name, quote=True)} 的牌组选项" title="牌组选项">⋯</button>'
            + "</div>"
            + _children(child, child_path, current_id)
            + "</li>"
        )
    return '<ul class="cabinet-children">' + "".join(items) + "</ul>"


def _folder(node: object, index: int, current_id: int, *, folded: bool = False) -> str:
    selected = _contains(node, current_id)
    selected_class = " selected" if selected else ""
    folded_class = " is-folded" if folded else ""
    hidden = " hidden" if folded else ""
    expanded = str(not folded).lower()
    fold_label = "展开卡匣" if folded else "收起卡匣"
    summary = '<div class="cabinet-folded-summary">' + _counts(node, compact=True) + '</div>' if folded else ""
    selected_attr = str(selected).lower()
    name = escape(node.name)
    name_attr = escape(node.name, quote=True)
    descendants = _deck_count(node) - 1
    child_summary = f"{descendants} 个子牌组" if descendants else "独立牌组"
    collapsed_note = (
        '<p class="cabinet-collapsed-note">子牌组已折叠</p>'
        if node.children and node.collapsed else ""
    )
    return (
        f'<article class="cabinet-folder tone-{_TONES[index % len(_TONES)]}{selected_class}{folded_class}" '
        f'data-cabinet-deck-id="{node.deck_id}" aria-labelledby="cabinet-name-{node.deck_id}">'
        f'<button type="button" class="cabinet-tab" data-cabinet-select="{node.deck_id}" '
        f'aria-pressed="{selected_attr}" aria-label="选择卡匣 {name_attr}">'
        f'<span class="cabinet-folder-number" aria-hidden="true">{index + 1:02d}</span>'
        f'<span class="cabinet-tab-name">{name}</span></button>'
        f'<button type="button" class="cabinet-fold" data-cabinet-display="fold:{node.deck_id}" '
        f'aria-controls="cabinet-details-{node.deck_id}" aria-expanded="{expanded}" '
        f'aria-label="{fold_label} {name_attr}" title="{fold_label}">'
        '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m6 9 6 6 6-6"/></svg></button>'
        '<div class="cabinet-folder-body">' + summary
        + f'<div class="cabinet-folder-inner" id="cabinet-details-{node.deck_id}"{hidden}>'
        '<div class="cabinet-folder-meta">'
        f'<span>{child_summary}</span>' + _filtered(node) + '</div>'
        '<div class="cabinet-folder-title">'
        + _collapse(node)
        + f'<h2 id="cabinet-name-{node.deck_id}">{name}</h2></div>'
        + _counts(node)
        + _children(node, (node.name,), current_id)
        + collapsed_note
        + '</div><footer class="cabinet-folder-footer">'
        f'<button type="button" class="cabinet-open" data-cabinet-command="open:{node.deck_id}">'
        '打开牌组<span aria-hidden="true"> →</span></button>'
        f'<button type="button" class="cabinet-options" data-cabinet-command="opts:{node.deck_id}" '
        f'aria-label="{name_attr} 的牌组选项" title="牌组选项">'
        '<span aria-hidden="true">⋯</span></button>'
        '</footer></div></article>'
    )


def render_deck_tree(tree: object, current_id: int, *, hidden_ids=(), folded_ids=()) -> str:
    """Return one nine-column table row compatible with DeckBrowserContent.tree.

    All metadata must be Anki's actual cached due-tree data. An unsupported
    schema raises clearly so the integration hook can preserve the native UI.
    Selection only changes the presentation; command dispatch belongs to the
    caller's bridge allowlist, with native Anki handling open/collapse/opts.
    """
    if type(current_id) is not int or current_id < 0:
        raise TypeError("current_id must be a nonnegative integer")
    _validate_node(tree, container=True)
    all_roots = list(tree.children)
    roots = [(index, node) for index, node in enumerate(all_roots) if node.deck_id not in hidden_ids]
    total = sum(_deck_count(node) for _, node in roots)
    hidden_count = len(all_roots) - len(roots)
    hidden_note = f" · 已隐藏 {hidden_count}" if hidden_count else ""
    disabled = "" if roots else " disabled"
    if roots:
        content = '<div class="cabinet-folders">' + "".join(
            _folder(node, index, current_id, folded=node.deck_id in folded_ids) for index, node in roots
        ) + '</div>'
    elif all_roots:
        content = (
            '<div class="cabinet-empty"><h2>所有卡匣已隐藏</h2>'
            '<p>牌组没有被删除，学习安排也没有改变。通过右上角「展示设置」重新显示。</p></div>'
        )
    else:
        content = (
            '<div class="cabinet-empty"><h2>还没有牌组</h2>'
            '<p>使用 Anki 下方的「创建牌组」或「导入」开始。</p></div>'
        )
    return (
        '<tr class="cabinet-root-row"><td colspan="9">'
        '<section id="cabinet-home" aria-labelledby="cabinet-home-title">'
        '<header class="cabinet-home-header cabinet-heading"><div>'
        '<h1 id="cabinet-home-title">牌组</h1>'
        f'<p>{len(roots)} 个卡匣 · {total} 个牌组{hidden_note}</p></div>'
        '<div class="cabinet-display-controls" aria-label="首页展示">'
        f'<button type="button" data-cabinet-display="unfold-all"{disabled}>全部展开</button>'
        f'<button type="button" data-cabinet-display="fold-all"{disabled}>全部收起</button>'
        '<button type="button" data-cabinet-display="settings">展示设置</button>'
        '<button type="button" class="cabinet-palette" data-cabinet-display="palette" '
        'aria-haspopup="dialog" aria-label="打开配色调色板">'
        '<span class="cabinet-palette-swatch" aria-hidden="true"></span>配色'
        '<span class="cabinet-palette-current" aria-hidden="true"></span></button></div></header>'
        + content
        + '<p class="cabinet-home-note cabinet-footer">计数遵循 Anki 当前每日上限；父牌组已包含子牌组。</p>'
        '</section></td></tr>'
    )
