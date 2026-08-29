# Editorial Index 设置

修改后点击「保存」。主题会自动刷新；少数窗口可能需要重新打开。

- `enabled`：总开关。也可以在「工具 → Editorial Index 主题」中快速切换。
- `accent_color`：主强调色，只接受 `#RRGGBB` 格式。
- `style_native_chrome`：美化 Anki 主窗口的原生菜单栏与状态栏。
- `style_reviewer`：将复习区域改为 Editorial Index 阅读页。不会用通用选择器修改 `#qa` 内部字段元素。
- `animations`：启用短促的悬停与出现动画。

默认强调色为 `#315FC4`。如果颜色格式无效，插件会自动回退到默认值。旧版未修改的青色默认值会自动迁移为编辑蓝；自定义颜色保持不变。

旧版本配置中的 `frosted_toolbar` 已没有视觉效果，可以安全删除。运行时仍会识别这个字段，旧配置不会导致插件加载失败。
