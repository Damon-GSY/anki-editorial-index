# Catppuccin 语义配色映射

Editorial Index 不把 Catppuccin 当成一组“背景色 + 单一强调色”。四种 flavor 都保留官方 26 色的层级关系，再映射到 Anki 的界面职责。用户选择的 14 种 accent 只控制品牌化和当前状态；链接、焦点、光标与状态信息继续使用 Catppuccin 指定的功能色。

实现参考：

- [Catppuccin 主仓库](https://github.com/catppuccin/catppuccin)
- [官方 Style Guide](https://github.com/catppuccin/catppuccin/blob/d09787dd98ca6fba08af5ef2ae94a7e09f17daca/docs/style-guide.md)
- [Palette v1.8.0 原始色值](https://github.com/catppuccin/palette/blob/v1.8.0/palette.json)

## 中性层与文字层级

| Anki 界面职责 | Catppuccin token | 使用位置 |
| --- | --- | --- |
| 主背景 | `Base` | Deck Browser、Editor、Stats 与弹窗主体 |
| 次级区域 | `Mantle` | 表头、工具架、分组区域 |
| 最深层区域 | `Crust` | 状态栏、底部操作区、内嵌边缘区域 |
| 控件与卡片 | `Surface 0` | 输入框、牌组行、按钮底面 |
| Hover / 普通边界 | `Surface 1` | 悬停态与轻边框 |
| 强边界 | `Surface 2` | 高层级分隔与强调边框 |
| 正文与主标题 | `Text` | 页面标题、普通牌组与正文 |
| 标签与表头 | `Subtext 1` | Deck、New、Learn、Due 等列标签 |
| 次级说明 | `Subtext 0` | 辅助信息、子牌组与元数据 |
| 弱提示 | `Overlay 1` | 空值、禁用态和低优先级信息 |
| 文本选择 | `Overlay 2` 25% + `Base` 75% | 原生窗口与 WebView 选区 |

## 功能色

| 界面职责 | Catppuccin token | 说明 |
| --- | --- | --- |
| 链接与标签 | `Blue` | 不随用户选择的 accent 改色 |
| 键盘焦点 | `Lavender` | 输入框、按钮和可聚焦控件 |
| 文本光标 | `Rosewater` | Add / Browse Editor 与输入控件 |
| 新卡片 | `Teal` | Deck Browser 的 New 数量 |
| 学习中 / 警告 | `Yellow` | Learn、Hard 与警告状态 |
| 待复习 / 错误 | `Red` | Due、Again 与危险操作 |
| 成功 | `Green` | Good 与成功反馈 |
| 简单 / 信息 | `Blue` | Easy 与普通信息状态 |
| 用户选择的 accent | 14 种 accent 之一 | 主按钮、当前牌组、当前标记与 Review Heatmap 历史活动 |

## 四种 flavor

Latte 使用浅色层级；Frappé、Macchiato 与 Mocha 使用各自独立的深色层级。它们不会只替换 `Base`：`Mantle`、`Crust`、三档 `Surface`、三档 `Overlay`、`Text` 与两档 `Subtext` 都会一起切换。README 中的四张实际界面截图统一使用 Blue accent，方便直接比较这套完整层级；56 组合矩阵展示每个 flavor 的全部 14 种官方 accent。

## 可读性规则

插件内保存的官方原始色值不做修改。部分 Latte 色值作为小号文字时达不到界面所需对比度，运行时会沿着同一色相向中性黑或白推导出可读版本：正文和状态文字最低 4.5:1，焦点与光标最低 3:1。填充按钮和主题展示仍保留用户选择的原始 accent。

Editorial Index 是独立集成，并非 Catppuccin 官方 port。
