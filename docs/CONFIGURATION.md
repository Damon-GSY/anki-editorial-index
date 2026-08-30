# Editorial Index 配置说明

进入「工具 > 插件」，选中 Editorial Index，再点击「配置」。修改 JSON 后点击保存。大部分界面会立即刷新，已经打开的独立窗口可能需要重新打开。

## 默认配置

```json
{
  "enabled": true,
  "accent_color": "#2F5BBC",
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
| `accent_color` | 字符串 | `#2F5BBC` | 改变按钮、选中状态、链接和键盘焦点的颜色 |
| `style_native_chrome` | 布尔值 | `true` | 控制 Add、Browse、Stats、Deck Options、Preferences、原生对话框及其内嵌 Anki 页面 |
| `style_reviewer` | 布尔值 | `true` | 控制复习卡片外层、显示答案按钮和评分按钮 |
| `animations` | 布尔值 | `true` | 控制牌组进入、悬停和按下时的短动画 |

`accent_color` 只接受 `#RRGGBB` 格式。下面这些都可以直接使用。

| 名称 | 色值 | 感觉 |
| --- | --- | --- |
| 编辑蓝 | `#2F5BBC` | 默认，在暖纸和选中行上保持可读 |
| 墨绿 | `#0F766E` | 安静，适合长时间阅读 |
| 深紫 | `#6D4AFF` | 更鲜明，仍能保持对比度 |
| 焦糖棕 | `#A14F16` | 更接近纸张和印刷品 |

过浅的颜色会降低按钮文字和键盘焦点的辨识度。建议使用中等或偏深的颜色。

## 只美化牌组页

如果希望卡片复习区保持原样，可以使用下面的配置。

```json
{
  "enabled": true,
  "accent_color": "#2F5BBC",
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
