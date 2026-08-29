# Editorial Index 问题排查

## 安装后界面没有变化

按下面的顺序检查。

1. 完整退出 Anki，再重新打开。
2. 进入「工具 > 插件」，确认 Editorial Index 已启用。
3. 打开「工具」菜单，确认「Editorial Index 主题」已经勾选。
4. 确认 Anki Desktop 版本不低于 25.09.4。
5. 暂时停用其他完整 UI 主题，再重启 Anki。

## 只有一部分界面发生变化

打开插件配置，确认 `style_native_chrome` 与 `style_reviewer` 都是 `true`。保存以后重新打开当前窗口。

Anki 的浏览器、统计和设置窗口由不同的原生控件组成。Editorial Index 当前重点覆盖主窗口、牌组、概览和复习流程，少数辅助窗口会保留 Anki 原来的布局。

## 卡片正面或背面的字体没有改变

插件有意保留卡片模板的控制权。打开「浏览 > 卡片」即可继续使用原来的 HTML 与 CSS。需要配套模板时，参考 [`extras/card-template`](../extras/card-template/README.md)。

## 评分按钮或底栏被挤压

先把 Anki 主窗口拉宽并重新进入复习页。如果系统显示缩放很高，尝试使用 Anki 的默认界面缩放。问题仍然存在时，请截图并附上系统、Anki 版本和窗口尺寸。

## 夜间模式颜色异常

确认其他主题已经停用。Editorial Index 会读取 Anki 的日间与夜间状态；另一个插件如果同时修改相同控件，最后加载的样式可能覆盖前一个主题。

## 手机上的界面没有变化

Anki Desktop 插件不会同步到 AnkiMobile 或 AnkiDroid。卡片内容会照常同步，Editorial Index 的程序界面只存在于安装了插件的电脑上。

## 恢复 Anki 原来的界面

最快的方法是在「工具」菜单中取消勾选「Editorial Index 主题」。也可以进入「工具 > 插件」停用或删除 Editorial Index，然后重启 Anki。这个操作不会影响牌组和学习记录。

## 提交问题

在 [GitHub Issues](https://github.com/Damon-GSY/anki-editorial-index/issues/new/choose) 新建问题，并提供下面的信息。

- 操作系统及版本
- Anki 完整版本号
- Editorial Index 版本号
- 是否启用了夜间模式
- 同时启用的其他界面插件
- 能看出问题的完整窗口截图
- 可以稳定重现问题的步骤

不要上传包含私人卡片内容、账号信息或同步凭据的截图。
