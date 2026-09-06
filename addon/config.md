# Editorial Index 设置

修改 JSON 后点击「保存」，已打开的 Anki 界面会同步刷新。日常切换也可以直接使用「工具」菜单，无需重启 Anki。

- `enabled`：总开关。也可在「工具 → Editorial Index 主题」中切换。
- `layout`：`editorial`（经典）或 `cabinet`（卡匣）。在「工具 → Editorial Index 布局」中切换；不会修改卡片模板或复习记录。布局与配色独立，卡匣支持现有 Catppuccin 配色选择。旧配置默认保留经典布局。
- `cabinet_display`：卡匣首页的展示偏好，按 Anki 账户分别保存。建议通过首页「展示设置」或「工具 → Editorial Index 首页展示…」管理，无需手动填写牌组 ID。没有设置时，全部卡匣默认显示并展开。
- `color_theme`：`editorial` 或 `catppuccin`。默认保留 Editorial Index 暖纸配色。
- `accent_color`：Editorial Index 配色的强调色，只接受 `#RRGGBB` 格式；选用 Catppuccin 时不使用此值。
- `catppuccin_flavor`：`auto`、`latte`、`frappe`、`macchiato` 或 `mocha`。`auto` 会在 Anki 日间模式使用 Latte，夜间模式使用 Mocha。
- `catppuccin_accent`：`rosewater`、`flamingo`、`pink`、`mauve`、`red`、`maroon`、`peach`、`yellow`、`green`、`teal`、`sky`、`sapphire`、`blue` 或 `lavender`。
- `style_native_chrome`：美化 Add、Browse、Stats、Deck Options、Preferences、原生对话框及其内嵌 Anki 页面。
- `style_reviewer`：美化复习区域的外层界面，不会用通用选择器修改 `#qa` 内部的卡片字段。
- `animations`：启用短促的悬停与出现动画。

「工具 → Editorial Index 配色」提供 Editorial Index、Catppuccin 自动及四种固定 flavor，同一菜单中可以选择 14 种 Catppuccin 强调色。

卡匣首页右上角的「配色」按钮也可打开同一个调色板，色样与主题名称会随切换同步更新。调色板点选后立即应用、自动记住；「界面预览」使用当前布局的插件样式，示例按钮不会操作卡片；「颜色用途与色值」可查看具体色值。评分颜色保持各自含义，不跟随强调色变成单色。

Catppuccin 原始色板按官方 v1.8.0 完整保留。为了让小字、焦点环和按钮文字保持可读，交互前景色可能使用由原色推导的高对比度色值。所有调色板数据都随插件本地安装，切换配色不会访问网络。

旧版配置中的 `frosted_toolbar` 已没有视觉效果，可以安全删除。运行时仍会识别这个字段，旧配置不会导致插件加载失败。

卡匣布局保留原生牌组及子牌组选项菜单；拖拽整理层级请暂时切回经典布局。卡片正文仍遵循原模板，如果所选配色与模板字色冲突，卡匣会优先回退纸面底色，避免改掉模板的语义颜色。

## 首页显示与折叠

「展示设置」只管理当前账户的**顶层牌组**：取消「首页显示」会隐藏整只卡匣及其中的子牌组；勾选「收起内容」会压缩卡匣，保留名称、计数和打开入口。设置窗口中点击「保存」才会应用；「取消」不会保存本次修改。

卡匣右上角的收起按钮，以及首页「全部收起／全部展开」，会立即记住状态，重启 Anki 后仍保留。「全部」仅影响当前可见的卡匣，不改变隐藏卡匣原有的折叠偏好。原生子牌组的折叠操作仍单独保留。

隐藏只影响卡匣首页，**不会删除或暂停卡片，也不会把它们从复习安排中移除**。即使全部隐藏，首页仍有「展示设置」入口；也可从「工具」菜单进入，点击「恢复默认（全部显示并展开）」后保存。新建的顶层牌组默认显示、展开。

内部保存结构为 `cabinet_display → 账户名称 → hidden_decks / folded_decks`，两项均为牌组 ID 数组。偏好跟随牌组 ID，重命名牌组不会丢失；这些数据保存在本机插件配置中，不是卡片模板或调度数据。
