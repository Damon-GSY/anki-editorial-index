# Editorial Index 配置说明

进入「工具 > 插件」，选中 Editorial Index，再点击「配置」。修改 JSON 后点击保存。主界面、已打开的独立窗口和 Editor 会同步更新，不会重载正在编辑的卡片内容。

## 默认配置

```json
{
  "enabled": true,
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
| `color_theme` | 字符串 | `editorial` | 选择 `editorial` 暖纸配色或 `catppuccin` 配色系统 |
| `accent_color` | 字符串 | `#2F5BBC` | 改变 Editorial Index 配色的按钮、链接和焦点色；Catppuccin 不使用此值 |
| `catppuccin_flavor` | 字符串 | `auto` | 选择 `auto`、`latte`、`frappe`、`macchiato` 或 `mocha` |
| `catppuccin_accent` | 字符串 | `blue` | 选择 14 种官方 Catppuccin 强调色之一 |
| `style_native_chrome` | 布尔值 | `true` | 控制 Add、Browse、Stats、Deck Options、Preferences、原生对话框及其内嵌 Anki 页面 |
| `style_reviewer` | 布尔值 | `true` | 控制复习卡片外层、显示答案按钮和评分按钮 |
| `animations` | 布尔值 | `true` | 控制牌组进入、悬停和按下时的短动画 |

## 直接在「工具」菜单切换

日常使用不需要编辑 JSON。打开「工具 → Editorial Index 配色」，可以直接选择：

- Editorial Index（暖纸默认）
- Catppuccin 自动（Latte / Mocha）
- Catppuccin Latte、Frappé、Macchiato 或 Mocha
- 上述 Catppuccin 配色的 14 种强调色

选择后会立即同步到 Anki 主界面、复习页、原生窗口与 Add / Browse Editor，无需重启。「Editorial Index 主题」仍是总开关；关闭时更换配色只会保存选择，不会自动重新启用主题。

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

插件内置的是 [Catppuccin Palette v1.8.0](https://github.com/catppuccin/palette/blob/v1.8.0/palette.json) 官方 26 色 token 快照。原始色值保持不变；为了保证浅色强调色上的小字、键盘焦点和状态文字可读，Editorial Index 会从原色推导高对比度的交互前景色。色板在安装包内本地读取，不会为配色下载或发送任何网络请求。

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
