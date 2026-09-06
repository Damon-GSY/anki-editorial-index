# Editorial Index 配置说明

进入「工具 > 插件」，选中 Editorial Index，再点击「配置」。修改 JSON 后点击保存。主界面、已打开的独立窗口和 Editor 会同步更新，不会重载正在编辑的卡片内容。

下面的 JSON 是字段示例。已有用户请只修改需要的字段，保留当前的 `layout` 和 `cabinet_display`；不要整段覆盖现有配置，除非希望重置布局和首页展示偏好。

## 默认配置

```json
{
  "enabled": true,
  "layout": "editorial",
  "cabinet_display": {},
  "accent_color": "#2F5BBC",
  "color_theme": "editorial",
  "catppuccin_flavor": "auto",
  "catppuccin_accent": "blue",
  "style_native_chrome": true,
  "style_reviewer": true,
  "animations": true
}
```

JSON 对逗号、引号和布尔值的写法有严格要求。`true` 与 `false` 不需要引号。

## 设置说明

| 设置 | 类型 | 默认值 | 保存后的结果 |
| --- | --- | --- | --- |
| `enabled` | 布尔值 | `true` | 控制整个主题。关闭后恢复 Anki 原有界面 |
| `layout` | 字符串 | `editorial` | 本分支支持 `editorial` 经典或 `cabinet` 卡匣；也可在工具菜单选择 |
| `cabinet_display` | 对象 | `{}` | 按 Anki 账户保存隐藏／收起的顶层牌组，由「首页展示设置」管理，无需手填牌组编号 |
| `color_theme` | 字符串 | `editorial` | 选择 `editorial` 暖纸配色或 `catppuccin` 配色系统 |
| `accent_color` | 字符串 | `#2F5BBC` | 改变 Editorial Index 配色的按钮、链接和焦点色；Catppuccin 不使用此值 |
| `catppuccin_flavor` | 字符串 | `auto` | 选择 `auto`、`latte`、`frappe`、`macchiato` 或 `mocha` |
| `catppuccin_accent` | 字符串 | `blue` | 选择 14 种官方 Catppuccin 强调色之一 |
| `style_native_chrome` | 布尔值 | `true` | 控制 Add、Browse、Stats、Deck Options、Preferences、原生对话框及其内嵌 Anki 页面 |
| `style_reviewer` | 布尔值 | `true` | 控制复习卡片外层、显示答案按钮和评分按钮 |
| `animations` | 布尔值 | `true` | 控制牌组进入、悬停和按下时的短动画 |

## 直接在「工具」菜单切换

日常使用不需要编辑 JSON。打开「工具 → Editorial Index 配色…」，会出现完整可视化工作台：

- 上方选择 Editorial 暖纸、Catppuccin 自动或四种固定 flavor
- 中间一次展示全部 14 种 Catppuccin 强调色；每次启用其中一种
- 本分支下方的「界面预览」显示当前布局的标题、按钮和评分样式；「颜色用途与色值」保留链接、焦点、光标和评分等语义色

如果已经知道要选什么，也可以使用「工具 → Editorial Index 快速配色」直接切换。56 种 Catppuccin 选择指 4 个 flavor × 14 个 accent 的组合矩阵，不会把 14 种强调色同时塞进日常牌组页。

选择后会立即同步到 Anki 主界面、复习页、原生窗口与 Add / Browse Editor，无需重启。「Editorial Index 主题」仍是总开关；关闭时更换配色只会保存选择，不会自动重新启用主题。

## 卡匣首页（当前预览分支）

在「工具 → Editorial Index 布局 → 卡匣 Cabinet」启用。首页右上角「配色」与工具菜单打开同一个面板；「展示设置」可选择默认显示／隐藏与收起状态，点击「保存」生效。卡匣右上角和「全部收起／全部展开」可直接切换，不删除或暂停卡片。回到「经典 Editorial」即可恢复传统首页。

这些偏好保存在当前电脑，显示设置按 Anki 账户区分，不随牌组或学习进度同步。分享插件不等于分享你的个人配置。完整说明见 [卡匣指南](./CABINET.md)。

## Editorial Index 暖纸强调色

`accent_color` 只接受 `#RRGGBB` 格式，并且只在 `color_theme` 为 `editorial` 时生效。下面这些都可以直接使用。

| 名称 | 色值 | 感觉 |
| --- | --- | --- |
| 编辑蓝 | `#2F5BBC` | 默认，在暖纸和选中行上保持可读 |
| 墨绿 | `#0F766E` | 安静，适合长时间阅读 |
| 深紫 | `#6D4AFF` | 更鲜明，仍能保持对比度 |
| 焦糖棕 | `#A14F16` | 更接近纸张和印刷品 |

过浅的颜色会降低按钮文字和键盘焦点的辨识度。建议使用中等或偏深的颜色。

## Catppuccin 配色

`catppuccin_flavor` 支持以下值。

| 值 | 显示名称 | 行为 |
| --- | --- | --- |
| `auto` | 自动 | Anki 日间模式使用 Latte，夜间模式使用 Mocha |
| `latte` | Latte | 固定使用浅色配色 |
| `frappe` | Frappé | 固定使用深色配色 |
| `macchiato` | Macchiato | 固定使用深色配色 |
| `mocha` | Mocha | 固定使用深色配色 |

`catppuccin_accent` 支持全部 14 种官方强调色：

`rosewater`、`flamingo`、`pink`、`mauve`、`red`、`maroon`、`peach`、`yellow`、`green`、`teal`、`sky`、`sapphire`、`blue`、`lavender`。

推荐的自动配置：

```json
{
  "enabled": true,
  "accent_color": "#2F5BBC",
  "color_theme": "catppuccin",
  "catppuccin_flavor": "auto",
  "catppuccin_accent": "blue",
  "style_native_chrome": true,
  "style_reviewer": true,
  "animations": true
}
```

固定 Mocha 与 Mauve 强调色：

```json
{
  "enabled": true,
  "accent_color": "#2F5BBC",
  "color_theme": "catppuccin",
  "catppuccin_flavor": "mocha",
  "catppuccin_accent": "mauve",
  "style_native_chrome": true,
  "style_reviewer": true,
  "animations": true
}
```

插件内置的是 [Catppuccin Palette v1.8.0](https://github.com/catppuccin/palette/blob/v1.8.0/palette.json) 官方 26 色 token 快照，并按 [官方 Style Guide](https://github.com/catppuccin/catppuccin/blob/main/docs/style-guide.md) 分配语义角色。四种 flavor 会完整切换中性层、文字层与功能色；`catppuccin_accent` 只控制主操作、当前牌组和历史热力图，不会取代固定的 Blue 链接、Lavender 焦点、Rosewater 光标和状态色。完整表格见 [Catppuccin 语义配色映射](./CATPPUCCIN_MAPPING.md)。

原始色值保持不变；为了保证浅色小字、键盘焦点和状态文字可读，Editorial Index 会沿原色相推导高对比度交互前景色。色板在安装包内本地读取，不会为配色下载或发送任何网络请求。

## Review Heatmap 配色

如果安装了 Review Heatmap，Editorial Index 会让它在牌组页、牌组概览和统计页自动跟随当前配色，无需增加配置字段：

- 历史复习活动使用当前强调色的四档强度
- 未来到期预测使用中性的四档强度，不会和已经完成的活动混在一起
- 空白日、年份标签、导航按钮、提示框、今日与选中日期边框使用同一套界面 token

这里只接管 Review Heatmap 的显示颜色，不会重建热力图，也不会修改它的数据、日期导航或自身设置。关闭「Editorial Index 主题」后会恢复 Review Heatmap 原来的配色。

## 只美化牌组页

如果希望卡片复习区保持原样，可以使用下面的配置。

```json
{
  "enabled": true,
  "accent_color": "#2F5BBC",
  "color_theme": "editorial",
  "catppuccin_flavor": "auto",
  "catppuccin_accent": "blue",
  "style_native_chrome": true,
  "style_reviewer": false,
  "animations": true
}
```

## 保留系统窗口外观

如果只希望改变主界面与复习网页区域，可以关闭原生窗口样式。Add / Browse 编辑器和 Stats / Deck Options 内嵌页面也会一起恢复 Anki 默认外观。

```json
{
  "enabled": true,
  "accent_color": "#2F5BBC",
  "color_theme": "editorial",
  "catppuccin_flavor": "auto",
  "catppuccin_accent": "blue",
  "style_native_chrome": false,
  "style_reviewer": true,
  "animations": true
}
```

## 关闭动画

把 `animations` 改为 `false`。操作状态仍会保留，只去掉过渡和出现动画。系统启用「减少动态效果」时，插件也会自动缩短动画。

## 恢复默认设置

把本页的默认配置完整复制到 Anki 配置窗口，保存后重新打开牌组页。如果配置无法保存，检查是否漏掉逗号、引号或大括号。

旧版本可能保留 `frosted_toolbar`。这个兼容字段已经没有视觉效果，可以安全删除。

## 卡片内容字体没有变化

这是预期行为。Editorial Index 美化 Anki 拥有的复习外层，不会强行覆盖 `#qa` 内部的卡片字段。这样可以避免破坏已经使用的语言字体、代码高亮、图片尺寸或自定义布局。

需要配套卡片排版时，可以单独使用 [`extras/card-template`](../extras/card-template/README.md)。
