"""Profile-local home preferences stored in add-on config, never in cards."""

from __future__ import annotations

from typing import Any, Callable


def _ids(value: Any) -> set[int]:
    if not isinstance(value, (list, tuple, set, frozenset)):
        return set()
    result = set()
    for item in value:
        if isinstance(item, bool) or not isinstance(item, (int, str)):
            continue
        digits = str(item)
        if len(digits) <= 19 and digits.isascii() and digits.isdigit() and 0 < int(digits) < 2**63:
            result.add(int(digits))
    return result


def preferences(config: dict, profile: str) -> tuple[set[int], set[int]]:
    profiles = config.get("cabinet_display", {})
    data = profiles.get(profile, {}) if isinstance(profiles, dict) else {}
    if not isinstance(data, dict):
        data = {}
    return _ids(data.get("hidden_decks")), _ids(data.get("folded_decks"))


def updated_preferences(config: dict, profile: str, hidden, folded) -> dict:
    stored = config.get("cabinet_display", {})
    profiles = dict(stored) if isinstance(stored, dict) else {}
    previous = profiles.get(profile, {})
    data = dict(previous) if isinstance(previous, dict) else {}
    data.update(hidden_decks=sorted(_ids(hidden)), folded_decks=sorted(_ids(folded)))
    profiles[profile] = data
    return profiles


def root_decks(mw: Any):
    return [deck for deck in mw.col.decks.all_names_and_ids(skip_empty_default=True)
            if "::" not in deck.name]


def apply_action(mw: Any, config: dict, action: str, save: Callable[[dict], None]) -> bool:
    profile = getattr(mw.pm, "name", None)
    if not profile or mw.col is None:
        return False
    hidden, folded = preferences(config, profile)
    visible = {int(deck.id) for deck in root_decks(mw)} - hidden
    if action == "fold-all":
        folded |= visible
    elif action == "unfold-all":
        folded -= visible
    elif action.startswith("fold:") and _ids([action[5:]]):
        deck_id = int(action[5:])
        if deck_id not in visible:
            return False
        folded.symmetric_difference_update({deck_id})
    else:
        return False
    save(updated_preferences(config, profile, hidden, folded))
    return True


def show_settings(mw: Any, read_config: Callable[[], dict], save: Callable[[dict], None]):
    """A native, non-blocking modal editor: Save applies, Cancel changes nothing."""
    if mw.col is None or not mw.pm.name:
        return None
    existing = getattr(mw, "_editorial_cabinet_display_dialog", None)
    if existing is not None:
        existing.show()
        existing.raise_()
        existing.activateWindow()
        return existing

    from aqt.qt import (
        QAbstractItemView, QDialog, QDialogButtonBox, QHeaderView, QHBoxLayout,
        QLabel, QLineEdit, QPushButton, QTreeWidget, QTreeWidgetItem, QVBoxLayout,
        Qt, qconnect,
    )

    profile = mw.pm.name
    hidden, folded = preferences(read_config(), profile)
    dialog = QDialog(mw)
    dialog.setObjectName("EditorialIndexCabinetDisplay")
    dialog.setWindowTitle("卡匣 · 首页展示设置")
    dialog.setWindowModality(Qt.WindowModality.WindowModal)
    dialog.resize(660, 560)
    dialog.setMinimumSize(530, 400)
    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(24, 22, 24, 20)
    layout.setSpacing(14)
    title = QLabel("决定首页留下哪些卡匣", dialog)
    title.setStyleSheet("font-size: 19px; font-weight: 600;")
    note = QLabel("只管理当前账户的顶层牌组。隐藏不会删除、暂停卡片或改变学习安排。\n"
                  "「收起内容」会保留名称、计数和打开入口。此处点击保存后生效。", dialog)
    note.setWordWrap(True)
    layout.addWidget(title)
    layout.addWidget(note)
    search = QLineEdit(dialog)
    search.setObjectName("CabinetDisplaySearch")
    search.setPlaceholderText("搜索卡匣名称…")
    search.setClearButtonEnabled(True)
    layout.addWidget(search)
    tree = QTreeWidget(dialog)
    tree.setObjectName("CabinetDisplayDecks")
    tree.setColumnCount(3)
    tree.setHeaderLabels(["卡匣 / 牌组", "首页显示", "收起内容"])
    tree.setRootIsDecorated(False)
    tree.setUniformRowHeights(True)
    tree.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
    tree.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
    tree.setTabKeyNavigation(True)
    tree.header().setStretchLastSection(False)
    tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
    for column in (1, 2):
        tree.header().setSectionResizeMode(column, QHeaderView.ResizeMode.ResizeToContents)
    rows = []
    for deck in root_decks(mw):
        item = QTreeWidgetItem([deck.name, "", ""])
        item.setData(0, Qt.ItemDataRole.UserRole, int(deck.id))
        item.setToolTip(0, deck.name)
        item.setCheckState(1, Qt.CheckState.Unchecked if int(deck.id) in hidden else Qt.CheckState.Checked)
        item.setCheckState(2, Qt.CheckState.Checked if int(deck.id) in folded else Qt.CheckState.Unchecked)
        tree.addTopLevelItem(item)
        rows.append(item)
    layout.addWidget(tree, 1)

    def filter_rows(text):
        for row in rows:
            row.setHidden(text.casefold() not in row.text(0).casefold())
    qconnect(search.textChanged, filter_rows)

    buttons = QHBoxLayout()
    restore = QPushButton("恢复默认（全部显示并展开）", dialog)
    restore.setObjectName("CabinetDisplayReset")
    def reset_rows():
        search.clear()
        for row in rows:
            row.setCheckState(1, Qt.CheckState.Checked)
            row.setCheckState(2, Qt.CheckState.Unchecked)
    qconnect(restore.clicked, reset_rows)
    buttons.addWidget(restore)
    buttons.addStretch()
    box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel, dialog)
    box.button(QDialogButtonBox.StandardButton.Save).setObjectName("CabinetDisplaySave")
    box.button(QDialogButtonBox.StandardButton.Cancel).setObjectName("CabinetDisplayCancel")
    buttons.addWidget(box)
    layout.addLayout(buttons)

    def accept():
        if mw.col is None or mw.pm.name != profile:
            dialog.reject()
            return
        hidden_now = {row.data(0, Qt.ItemDataRole.UserRole) for row in rows if row.checkState(1) == Qt.CheckState.Unchecked}
        folded_now = {row.data(0, Qt.ItemDataRole.UserRole) for row in rows if row.checkState(2) == Qt.CheckState.Checked}
        save(updated_preferences(read_config(), profile, hidden_now, folded_now))
        dialog.accept()
    qconnect(box.accepted, accept)
    qconnect(box.rejected, dialog.reject)
    def closed(_result):
        mw._editorial_cabinet_display_dialog = None
        dialog.deleteLater()
    qconnect(dialog.finished, closed)
    mw._editorial_cabinet_display_dialog = dialog
    dialog.show()
    return dialog
