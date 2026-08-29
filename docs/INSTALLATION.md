# Editorial Index 安装指南

安装完成后，Anki 的牌组页、复习外层界面、顶部导航和桌面菜单会使用 Editorial Index 主题。你的牌组、卡片、学习记录和调度设置不会改变。

## 安装前准备

- Anki Desktop 25.09.4 或更高版本
- 从本项目 GitHub Release 下载的 `.ankiaddon` 文件
- 重启一次 Anki 的时间

这是一款桌面插件。AnkiMobile、AnkiDroid 和 AnkiWeb 不会安装或同步这套界面。

## 第一次安装

1. 打开 [Editorial Index 最新版本](https://github.com/Damon-GSY/anki-editorial-index/releases/latest)。
2. 展开页面底部的 Assets。
3. 下载 `Editorial-Index.ankiaddon`。
4. 打开 Anki Desktop。
5. 进入「工具 > 插件」。
6. 点击「从文件安装」，选中下载的安装包。
7. 安装完成后关闭并重新打开 Anki。

重新进入牌组页以后，应当看到暖纸色背景和新的 Deck Home 标题。「工具」菜单中也会出现「Editorial Index 主题」。这两处都出现，说明插件已经正常加载。

Anki 官方说明确认 `.ankiaddon` 是桌面插件的分发格式，安装包内部不应再包一层顶级文件夹。Editorial Index 的发行包按照这项规则生成。相关说明见 [Anki 插件分享文档](https://addon-docs.ankiweb.net/sharing.html)。

## 更新版本

1. 下载新版本的 `Editorial-Index.ankiaddon`。
2. 在「工具 > 插件」中再次选择「从文件安装」。
3. 允许 Anki 更新现有的 Editorial Index。
4. 重新启动 Anki。

更新前可以复制当前配置，以便保留自定义颜色。配置入口位于「工具 > 插件 > Editorial Index > 配置」。

## 临时停用

打开「工具」菜单，取消勾选「Editorial Index 主题」。界面会刷新，插件文件和配置仍会保留。需要恢复时重新勾选即可。

也可以进入「工具 > 插件」，选中 Editorial Index，再点击「切换启用」。这种方式通常需要重启 Anki。

## 卸载

1. 进入「工具 > 插件」。
2. 选中 Editorial Index。
3. 点击「删除」。
4. 重新启动 Anki。

卸载不会删除牌组、卡片或学习记录。Anki 官方插件手册也把删除插件列为插件故障时的恢复方式，见 [Anki Add-ons](https://docs.ankiweb.net/addons.html)。

## 校验下载文件

每个 GitHub Release 都附带 `SHA256SUMS`。如果需要确认下载文件没有损坏，可以在安装前进行校验。

macOS 或 Linux

```bash
shasum -a 256 Editorial-Index.ankiaddon
```

Windows PowerShell

```powershell
Get-FileHash .\Editorial-Index.ankiaddon -Algorithm SHA256
```

命令显示的值应当与同一 Release 中 `SHA256SUMS` 的内容完全一致。

## 安装以后没有变化

先完整退出 Anki并重新打开。问题仍然存在时，检查 Anki 版本、插件启用状态和其他完整 UI 主题。更完整的处理步骤见 [问题排查](./TROUBLESHOOTING.md)。
