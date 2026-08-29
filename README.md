<div align="center">

# Editorial Index

一款给 Anki Desktop 使用的暖纸色编辑索引主题

[English](./README.en.md) · [下载安装](https://github.com/Damon-GSY/anki-editorial-index/releases/latest) · [配置说明](./docs/CONFIGURATION.md) · [问题排查](./docs/TROUBLESHOOTING.md)

[![Latest release](https://img.shields.io/github/v/release/Damon-GSY/anki-editorial-index?label=release)](https://github.com/Damon-GSY/anki-editorial-index/releases/latest)
[![Anki](https://img.shields.io/badge/Anki-25.09.4%2B-315FC4)](https://apps.ankiweb.net/)
[![License](https://img.shields.io/github/license/Damon-GSY/anki-editorial-index)](./LICENSE)

</div>

![Editorial Index 牌组页面](./screenshots/deck-browser.png)

Editorial Index 会把 Anki 的牌组页、复习外层界面和桌面菜单整理成克制的编辑索引风格。安装以后仍然使用原来的牌组、卡片和快捷键，也不会改动学习进度与调度算法。

## 下载与安装

1. 打开 [最新版本页面](https://github.com/Damon-GSY/anki-editorial-index/releases/latest)。
2. 在页面底部的 Assets 中下载 `Editorial-Index.ankiaddon`。
3. 打开 Anki Desktop，进入「工具 > 插件」。
4. 点击「从文件安装」，选择刚才下载的文件。
5. 重新启动 Anki。

安装成功后，「工具」菜单中会出现「Editorial Index 主题」。这里可以随时临时关闭或重新启用主题。

完整步骤包括升级、卸载和校验下载文件，见 [安装指南](./docs/INSTALLATION.md)。

## 它会改变哪些地方

- 牌组首页和牌组树
- 牌组概览与「现在学习」按钮
- 顶部导航、普通底栏和复习评分区
- 复习卡片外层的阅读区域
- Anki 主窗口的菜单栏、菜单和状态栏
- 日间模式与夜间模式

插件不会修改 Anki 数据库、牌组、笔记、卡片模板或 FSRS 调度。禁用或卸载后，Anki 会恢复原来的界面。

![Editorial Index 复习页面](./screenshots/reviewer-answer.png)

## 配置

在 Anki 中进入「工具 > 插件」，选中 Editorial Index，再点击「配置」。保存后主题会自动刷新，已经打开的少数窗口需要重新打开。

| 设置 | 默认值 | 用途 |
| --- | --- | --- |
| `enabled` | `true` | 控制整个主题是否启用 |
| `accent_color` | `#315FC4` | 设置按钮、选中状态和焦点的强调色 |
| `style_native_chrome` | `true` | 美化桌面菜单栏、菜单和状态栏 |
| `style_reviewer` | `true` | 美化复习卡片外层和评分区 |
| `animations` | `true` | 启用短促的出现与悬停动画 |

强调色只接受六位十六进制颜色，例如 `#315FC4`。颜色格式写错时，插件会自动使用默认编辑蓝。

默认配置、配色示例和恢复方法都放在 [配置说明](./docs/CONFIGURATION.md) 中。

## 字体与卡片模板

界面操作文字使用 Inter，页面标题和复习阅读区域使用 Source Serif Pro。两套字体均随插件安装；中文、日文和韩文继续使用系统自带字体，避免缺字。

Editorial Index 只处理 Anki 官方界面拥有的区域。已有卡片模板中的字段排版仍由你的模板控制。想让卡片内容也使用配套样式，可以选择性安装 [`extras/card-template`](./extras/card-template/README.md)，这一步不会影响插件本身。

## 兼容范围

- 需要 Anki Desktop 25.09.4 或更高版本
- macOS 已完成本地安装验证
- Windows 与 Linux 使用相同的 Anki 插件接口，欢迎提交实际设备反馈
- 不适用于 AnkiMobile、AnkiDroid 或 AnkiWeb
- 其他界面主题可能覆盖同一组样式，建议一次只启用一个完整 UI 主题

Anki 更新有时会改变插件接口或页面结构。如果更新 Anki 后出现异常，请先查看 [问题排查](./docs/TROUBLESHOOTING.md)，再提交 [Issue](https://github.com/Damon-GSY/anki-editorial-index/issues/new/choose)。

## 隐私与安全

插件不发送网络请求，不收集使用数据，也不读取或修改卡片内容。它只在 Anki 启动时加载本地字体与样式，并通过 Anki 官方插件钩子把样式应用到桌面界面。

从 GitHub 下载的发行文件会同时提供 SHA-256 校验值。安全说明见 [SECURITY.md](./SECURITY.md)。

## 开发

```bash
python3 scripts/package_addon.py
python3 scripts/validate_addon.py
python3 scripts/smoke_test_addon.py
```

源码位于 [`addon`](./addon/)，生成的安装包位于 [`dist/Editorial-Index.ankiaddon`](./dist/Editorial-Index.ankiaddon)。参与方式见 [CONTRIBUTING.md](./CONTRIBUTING.md)，每个版本的变化见 [CHANGELOG.md](./CHANGELOG.md)。

## 独立实现与许可

Editorial Index 是面向 Anki 的独立实现，不包含 BewlyCat、BewlyBewly 或 Bilibili 的源代码、图标、插画及其他素材，也未获相关项目或权利方背书。完整边界说明见 [INDEPENDENT_DESIGN.md](./INDEPENDENT_DESIGN.md)。

项目源码按 [MIT License](./LICENSE) 发布。随插件分发的 Inter 与 Source Serif Pro 使用 [SIL Open Font License 1.1](./addon/web/fonts/OFL.txt)。Anki 及其他名称归各自权利方所有。
