# Cabinet 原生 Anki 验证

这是开发测试环境，不是普通用户的安装入口。安装插件请看 [安装指南](../../docs/INSTALLATION.md)。

## 测试当前正式源码

在仓库根目录运行：

```sh
python3 design-exploration/anki-cabinet-lab/run.py --production --verify
```

只检查配色面板：

```sh
python3 design-exploration/anki-cabinet-lab/run.py --production --palette
```

只检查复习底栏（输出到 `local-tests/reviewer-footer-2026-09-19/`）：

```sh
python3 design-exploration/anki-cabinet-lab/run.py --production --footer
```

需要手动试用隔离窗口时使用 `--production --open`。不带 `--production` 则运行本目录 `addon/` 下保留的早期实验版本；其牌组测试为 `python3 design-exploration/anki-cabinet-lab/test_decks.py`。

每次启动生成新的临时资料库和示例笔记，不读取或复制日常资料库、不登录 AnkiWeb、不自动同步。测试只操作生成的数据。不要在实验资料库中保存需要长期保留的学习内容。

## 覆盖范围

- 原生牌组树、层级、计数、概览、问答、评分与撤销。
- 输入答案比较、挖空、图片、公式、空牌组以及窄窗口。
- 经典／卡匣切换、复习样式开关、已有卡片内容保留。
- 展示设置、隐藏、折叠、取消和恢复默认，以及按账户隔离。
- 四种 Catppuccin flavor × 14 种强调色、配色预览、首页色样、键盘焦点、首开和选中态几何稳定性、680×600 小窗口与面板关闭清理。

2026-09-06 在 macOS / Anki 26.05b1 / Qt 6.11.0 上完成 510 项检查，其中包含功能、几何和截图检查，不代表 510 个独立功能。

报告与截图保存在本地 `production-evidence/`（早期实验模式为 `runtime-report.json` 和 `screenshots/`），它们包含机器路径，已加入 Git 忽略规则。运行后查看新生成报告，不使用旧报告代替本次结果。选定的生成数据截图见 [README](../../README.md)。

启动器当前要求 macOS 的 `/Applications/Anki.app` 及兼容的本地 Python 3.13，不自动下载依赖。它不安装到日常 Anki，不提交代码，不发布版本。详见 [运行隔离说明](./RUNTIME.md)。
