# Editorial Index 设置

修改 JSON 后点击「保存」，已打开的 Anki 界面会同步刷新。日常切换也可以直接使用「工具」菜单，无需重启 Anki。

- `enabled`：总开关。也可在「工具 → Editorial Index 主题」中切换。
- `color_theme`：`editorial` 或 `catppuccin`。默认保留 Editorial Index 暖纸配色。
- `accent_color`：Editorial Index 配色的强调色，只接受 `#RRGGBB` 格式；选用 Catppuccin 时不使用此值。
- `catppuccin_flavor`：`auto`、`latte`、`frappe`、`macchiato` 或 `mocha`。`auto` 会在 Anki 日间模式使用 Latte，夜间模式使用 Mocha。
- `catppuccin_accent`：`rosewater`、`flamingo`、`pink`、`mauve`、`red`、`maroon`、`peach`、`yellow`、`green`、`teal`、`sky`、`sapphire`、`blue` 或 `lavender`。
- `style_native_chrome`：美化 Add、Browse、Stats、Deck Options、Preferences、原生对话框及其内嵌 Anki 页面。
- `style_reviewer`：美化复习区域的外层界面，不会用通用选择器修改 `#qa` 内部的卡片字段。
- `animations`：启用短促的悬停与出现动画。

「工具 → Editorial Index 配色」提供 Editorial Index、Catppuccin 自动及四种固定 flavor，同一菜单中可以选择 14 种 Catppuccin 强调色。

Catppuccin 原始色板按官方 v1.8.0 完整保留。为了让小字、焦点环和按钮文字保持可读，交互前景色可能使用由原色推导的高对比度色值。所有调色板数据都随插件本地安装，切换配色不会访问网络。

旧版配置中的 `frosted_toolbar` 已没有视觉效果，可以安全删除。运行时仍会识别这个字段，旧配置不会导致插件加载失败。
