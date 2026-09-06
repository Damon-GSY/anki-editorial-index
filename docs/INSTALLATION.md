# Editorial Index 安装指南

适用于 Anki Desktop。安装不会迁移或删除你的牌组、卡片、学习记录，也不改变调度算法。AnkiMobile、AnkiDroid 和 AnkiWeb 不支持安装这套桌面插件。

## 先选对安装包

| 想安装的内容 | 下载位置 |
| --- | --- |
| 当前 Cabinet 卡匣、新调色板、展示／折叠设置和间距修正 | [直接下载预览包](https://github.com/Damon-GSY/anki-editorial-index/raw/refs/heads/codex/cabinet-local-migration/dist/Editorial-Index-Cabinet-preview.ankiaddon) |
| 已发布的经典 Editorial 版本，不含上述新功能 | [旧稳定版 Release](https://github.com/Damon-GSY/anki-editorial-index/releases/latest)，在 Assets 下载 `Editorial-Index.ankiaddon` |

当前预览位于 `codex/cabinet-local-migration` 分支，未合并到 main，也未创建新 Release。预览安装包名为 `Editorial-Index-Cabinet-preview.ankiaddon`，插件元数据暂沿用 0.3.7；请用下载来源和配套校验文件确认，不要仅凭版本号判断是否为预览版。

插件声明最低 Anki Desktop 25.09.4；**本次 Cabinet 已实测的是 macOS / Anki 26.05b1 / Qt 6.11.0**，其他版本和 Windows / Linux 尚待实际设备验证。不要为了安装主题盲目升级到 Anki 测试版。

## 第一次安装：约两分钟

1. 下载上表对应的 `.ankiaddon` 文件。**不要解压**，也不要使用 GitHub「Code → Download ZIP」下载的源码压缩包安装。
2. 打开 Anki，进入「工具 → 插件」（英文界面：Tools → Add-ons）。
3. 点击「从文件安装」（Install from file），选中刚下载的文件。
4. 安装完成后，正常退出并重新打开 Anki。
5. 确认「工具」菜单出现「Editorial Index 主题」和「Editorial Index 配色…」。主题总开关应保持勾选。
6. **预览版用户再选择「工具 → Editorial Index 布局 → 卡匣 Cabinet」。** 新安装默认仍是经典布局与暖纸配色，安装完没有自动变成卡匣是正常的。

这条路径不需要 AnkiWeb 插件编号、终端、Python 或前端开发环境。`.ankiaddon` 格式和从文件安装方式见 [Anki 官方分享插件说明](https://addon-docs.ankiweb.net/sharing.html)。

## 安装后怎么配置

- **切换布局**：工具 → Editorial Index 布局 → 卡匣 Cabinet / 经典 Editorial。
- **切换颜色**：卡匣首页右上角「配色」，或工具 → Editorial Index 配色…。先选 Latte、Frappé、Macchiato、Mocha 或自动，再选 14 种强调色之一；点击后立即应用并保存，不需要重启。
- **自动深浅色**：「自动」跟随 Anki 本身的日间／夜间模式，在 Latte 和 Mocha 之间切换。四个具名主题则固定使用相应配色。
- **隐藏与默认收起**：首页「展示设置」，勾选要显示的顶层牌组和收起状态，点击「保存」。只影响首页展示，不删除牌组、不暂停卡片。
- **临时收起／展开**：卡匣右上角折叠按钮，或首页「全部收起／全部展开」。
- **高级配置**：工具 → 插件 → Editorial Index → 配置。日常操作不需要编辑 JSON；字段说明见 [配置指南](./CONFIGURATION.md)。

配色面板的预览使用示例文字和间隔，不能翻面或评分真实卡片。评分颜色保留各自含义，不会全部变成当前强调色。偏好保存在本机，展示设置按 Anki 账户区分，不随学习同步传到其他电脑或手机。

## 已安装用户：直接升级，不要先卸载

1. 可先复制「配置」内容作为额外备份。若改过插件源码，请另外备份这些文件。
2. 在 Anki 中重复「工具 → 插件 → 从文件安装」，选择新的 `.ankiaddon`。
3. 按提示更新已有 Editorial Index，然后正常重启 Anki。

经典版和预览版都使用同一个插件标识 `mistline_ui`，不会新增第二份主题。Anki 的同包重装保留用户配置与 `user_files`；已有配色和展示选择继续使用，缺少的新选项采用默认值。**直接修改过的插件源码会被覆盖**，不要把个人文件放进源码目录期待升级保留。

## 回退、停用与卸载

- 只是不想用卡匣：工具 → Editorial Index 布局 → 经典 Editorial，无需卸载。
- 临时关掉主题：取消勾选工具菜单的「Editorial Index 主题」。需要恢复时重新勾选。
- 回到旧稳定版：从上表的 Release 下载稳定版，使用「从文件安装」覆盖并重启。旧版本不会提供卡匣和新面板。
- 完全卸载：工具 → 插件 → Editorial Index → 删除，然后重启。不会删除牌组和学习记录，但请先备份想保留的插件配置。

如果 Anki 无法正常启动，可按住 Shift 启动，保持到安全模式提示出现后再松开，随后禁用冲突插件；见 [Anki 官方插件故障排查](https://docs.ankiweb.net/troubleshooting.html#2-check-add-ons)。

## 校验下载文件（可选）

预览包对应 [Editorial-Index-Cabinet-preview.sha256](../dist/Editorial-Index-Cabinet-preview.sha256)。打开后将其中的 64 位值与下面的输出比较；旧稳定版则使用同一 Release 附带的 `SHA256SUMS`，不要交叉比较不同包。

macOS / Linux，在下载目录执行：

```sh
shasum -a 256 Editorial-Index-Cabinet-preview.ankiaddon
```

Windows PowerShell：

```powershell
Get-FileHash .\Editorial-Index-Cabinet-preview.ankiaddon -Algorithm SHA256
```

## 安装以后仍没有变化

1. 完整退出再打开 Anki，确认插件已启用、主题总开关已勾选。
2. 想用卡匣却仍显示 Deck Home：确认下载的是本分支的 preview 包，并手动选择「卡匣 Cabinet」。旧 Release 没有布局菜单。
3. 颜色未跟随：检查是否选择了具名固定主题；仅「自动」跟随 Anki 深浅模式。
4. 样式混杂：暂时禁用其他完整 UI 主题，再检查。无需为了本插件卸载 Review Heatmap。
5. 仍有问题：附上 Anki 版本、操作系统、下载来源和截图，参见 [问题排查](./TROUBLESHOOTING.md)。

卡片正文保留原模板的字体与 HTML，因此不保证每个第三方模板都和外层主题完全相同。

## 从源码构建（开发者）

普通安装无需执行此节。在当前分支的项目根目录运行：

```sh
python3 scripts/package_addon.py --preview
python3 scripts/validate_addon.py --preview
```

会生成 `dist/Editorial-Index-Cabinet-preview.ankiaddon` 和对应 `.sha256`，不会覆盖旧稳定版构建文件；随后仍通过 Anki「从文件安装」安装。此操作不会创建 GitHub Release。
