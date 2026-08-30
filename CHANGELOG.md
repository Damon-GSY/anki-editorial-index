# Changelog

本项目使用语义化版本号。面向普通用户的重要变化会记录在这里。

## 0.3.3 · 2026-08-30

### 调整

- Catppuccin 的可读文字色改为朝中性黑 / 白推导，在继续满足 4.5:1 对比度的同时保留原始色相；Latte 的 Yellow、Green、Sky、Blue 等不再被混成相似的灰蓝色
- Deck Browser 增加 Catppuccin 专属文字层级：页面标题与当前牌组跟随所选强调色，父牌组保持主文字、子牌组使用次文字，展开符号与当前行标记明确表达交互状态
- New / Learn / Due 表头与数值使用同一语义色，当前行使用轻量强调色底，表头使用 Mantle 层，零值改为可读的低权重中性色
- 表头选择器改为匹配 Anki 25.09 的真实 `tbody` DOM；当前行齿轮使用可着色 SVG mask，避免外链 SVG 的 `color` 假染色，同时不改变 Editorial 齿轮表现
- Editorial 的颜色推导、四种 flavor、14 种原始强调色、Anki 工作流以及用户卡片样式所有权保持不变

### 验证

- 新增色相保持、Latte 代表值、普通 / 当前零值、父子牌组、hover / current、真实表头 DOM、齿轮 mask 和选中底色对比回归；Catppuccin Web 运行时现覆盖 29,437 条断言
- Editor `185/185`、Stats / Deck Options `577/577`、主界面 8 个视图 × 8 档宽度的完整 UI 回归全部通过

## 0.3.2 · 2026-08-30

### 修复

- Review Heatmap 的“今天”与“选中日期”现在按每档实际色块派生高对比边框；有复习量时也不会在深色 flavor 或浅色强调色上消失，并用虚线 / 粗实线区分两种状态
- Review Heatmap 五个真实外链 SVG 控件改用保留原节点与事件的 `currentColor` 遮罩显示，修复 Latte 等配色下固定灰色图标不跟随主题且对比不足的问题

### 验证

- 增加 `q20 highlight-now now` 活跃今天、真实 `.hm-btn > img` DOM、图标遮罩、边框对色块 3:1 对比，以及 56 套配色原位切换的回归覆盖

## 0.3.1 · 2026-08-30

### 调整

- Review Heatmap 的历史活动格会跟随当前 Editorial / Catppuccin 强调色，未来到期格使用主题内的中性色阶；空白日、年份标签、导航按钮、提示框与今日 / 选中边框也统一进入当前配色
- 历史活动和未来到期各保留四档清晰强度，切换四种 Catppuccin flavor 与全部 14 种强调色时会原地过渡，不重建热力图，也不修改复习数据、日期导航或 Review Heatmap 设置
- 兼容规则只作用于 Deck Browser、Overview 与 Stats 中真实存在的 `.rh-container`，未安装 Review Heatmap 时没有额外影响

### 验证

- 将回归夹具从三个模拟色块改为 Review Heatmap 的真实 SVG `rect.q1–q20` 结构，覆盖晚加载的第三方样式、空白 / 未来 / 历史 / 今日 / 选中状态，以及 4 × 14 配色实时切换

## 0.3.0 · 2026-08-30

### 新增

- 加入 Catppuccin Latte、Frappé、Macchiato 与 Mocha 四种 flavor，以及 Rosewater、Flamingo、Pink、Mauve、Red、Maroon、Peach、Yellow、Green、Teal、Sky、Sapphire、Blue、Lavender 全部 14 种强调色
- 新增「工具 → Editorial Index 配色」切换器，可直接选择暖纸默认、Catppuccin 自动或固定 flavor，无需编辑 JSON 或重启 Anki
- Catppuccin 自动模式会跟随 Anki 日间 / 夜间设置，分别使用 Latte 与 Mocha

### 调整

- 让配色切换同步到 Qt 原生窗口、Anki WebView、复习页与 Add / Browse Editor；已打开的 Editor 不需要重载，不会丢失未保存内容
- 配色与总开关不再调用 Anki 的全局重置；Reviewer 当前卡片、答案面、计时，以及 Add / Browse 的焦点、光标和滚动状态会保持原位
- 运行时只管理本插件的精确样式地址和语义颜色变量，不会接管其他插件的同名 CSS，也不会覆盖卡片模板自定义的 `--ctp-*` 变量
- 已打开的 Add、原生弹窗与 Card Layout 会在总开关切换时原地应用或恢复语义角色和间距；Browser 侧栏会重建 Anki 自己的 palette 样式但不改写控件名，第三方插件之后修改的值也不会被回滚
- 新安装和从 0.2.x 升级仍使用 Editorial Index 暖纸配色；原有 `accent_color` 配置保留，只有用户主动选择才会切换到 Catppuccin
- 原始 Catppuccin token 按官方 Palette v1.8.0 精确保留；小字、键盘焦点与按钮前景色会在需要时使用高对比度派生色，避免浅色强调色不可读
- 色板快照、版本、commit 与 MIT 许可声明随插件打包，运行时不会访问网络；本项目是独立集成，不是 Catppuccin 官方 port

### 验证

- 新增 4 种 flavor × 14 种强调色的完整数据、语义 token 与对比度回归，并将 Catppuccin 契约测试接入 Validate 与 Release CI

## 0.2.4 · 2026-08-30

### 修复

- 重做 Add 与 Browse 的内嵌编辑器层级：工具栏、字段卡、标签区、禁用态与聚焦态统一为暖纸界面，窄窗口不再溢出
- 补齐 Add / Browse 标签折叠按钮的真实嵌套控件尺寸，并统一 Fields 与 Card Layout 的操作层级；卡片模板预览仍由用户自己的卡片 CSS 控制
- 完成 Stats 筛选栏、Deck Options 的输入框/步进器/开关/Save 操作以及 Preferences 微控件的统一样式
- 用共享的明暗色 token 同步 Qt `QPalette` 与 QSS，修正弹窗、菜单、选择器和禁用状态的混色问题；破坏性操作在禁用时也会回落为中性层级
- 修正 Deck Browser 与 Overview 中 Review Heatmap 统计文字在暖纸背景上几乎不可见的对比度回归，不改动热力图单元格配色
- 重新标定浅色模式的默认编辑蓝、学习中 / Hard 琥珀色和待复习 / Again 红色，使普通牌组行、选中行、Overview 和评分按钮的小字都达到 4.5:1 对比度；暗色模式自动使用可读的浅色强调色
- 重新标定 Good / Easy 的交互色，保证评分按钮在 hover 深纸背景上仍达到 4.5:1；自定义强调色不会再影响危险操作按钮自身的前景色选择
- 收紧 Reviewer 选择器与继承边界：主题不再改写用户卡片中的按钮、链接、圆角、字体、颜色、行高、换行、动画或 transition

### 验证

- 新增真实 Anki 弹窗回归矩阵，覆盖 Add、选择弹窗、Browse、Preferences、Stats、Deck Options 与 Overview
- 将主界面、Editor 以及 Stats / Deck Options 的 Playwright 布局回归接入 Validate 与 Release CI，自动阻止尺寸、溢出、暗色和 CSS 优先级回归

## 0.2.3 · 2026-08-30

### 修复

- 将 Qt 主题从 Anki 主窗口提升到全应用范围，Add、Browse、Stats、Deck Options、Preferences 以及后续打开的选择器/对话框不再退回原生灰色外观
- 接入 Anki 官方 `style_did_init` 过滤器，切换明暗模式或 Widget Style 后仍会保留弹窗主题
- 补全原生按钮、输入框、下拉选择、表格/列表、标签页、滚动条和分割条的圆角、层级与焦点状态
- 为 Add 和 Browse 中的 EditorWebView 增加 CSP 兼容的本地专用样式，统一工具栏、字段卡片与标签区，不会写入或修改卡片字段内容
- 给 Stats、Deck Options、Card Info、导入页和 Image Occlusion 等 Anki Svelte 页面注入同一套暖纸视觉变量

## 0.2.2 · 2026-08-30

### 调整

- 将顶部 Decks / Add / Browse / Stats / Sync 统一为 44px 高的纸面操作按钮，补上 10px 圆角、轻阴影、悬停上浮和按下反馈
- 将 Show Answer、Edit、More 与 Deck Browser / Overview 底部操作纳入同一按钮系统，同时保留主操作、次操作和评分语义的层级
- 修正 Sync 字重和同步动画图标的窄窗口宽度，320px 下五个顶部操作仍完整可见
- 修正 Anki 两键、三键和四键评分模式的语义颜色，并将 Edit / More 的隐藏阈值恢复为 Anki 原生 583px
- 在 Anki 原生 `outline: none !important` 之上恢复按钮键盘焦点，且支持减少动效
- 扩展为 8 档响应式宽度、长语言标签、三类标准底栏组合、Sync 空闲/同步中状态和 2/3/4 评分模式的全量回归检查
- 加固发布验证：安装包会逐文件与源码比对，且已经发布的版本不允许原地覆盖资产

## 0.2.1 · 2026-08-29

### 修复

- 给复习底栏补上明确的上下留白，评分按钮的圆角与阴影不再贴住窗口底边
- 让问题面与答案面的底栏保持同一高度，切换答案时不会裁掉下方空间
- 修正 Reviewer 在 584–660px 、Overview 在 400px 固定表格以及 Deck Browser 在 15em 牌组列上的窄窗口溢出
- 让 360px 概览页自动把统计和“开始学习”改为上下排列，牌组名可收缩而 New/Learn/Due 数字列保持对齐
- 区分可折叠的父牌组与叶子牌组字重，避免所有牌组名都被错误加粗
- 让生产预览使用 Anki 26.5b1 的真实 DOM 与关键基础 CSS，并加入 8 个视图和 720/660/584/583/480/360px 六档检查

## 0.2.0 · 2026-08-29

首个公开发行版本。

### 新增

- 牌组页、牌组概览、复习外层、顶部导航和底栏主题
- Anki 原生菜单栏、菜单和状态栏主题
- 日间与夜间模式
- 可配置的强调色、复习区域、原生窗口样式和动画开关
- Inter 与 Source Serif Pro 本地字体
- 可选卡片模板

### 调整

- 统一原型、Anki WebView 与 Qt 原生窗口的字体规格
- 改善主要按钮和四个复习评分按钮的圆角、阴影和间距
- 保留现有卡片模板的字体与布局控制权

## 0.1.0

内部原型版本，没有作为 GitHub Release 公开发布。
