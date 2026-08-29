# 参与 Editorial Index

欢迎提交兼容性反馈、界面问题和小范围改进。这个项目优先保证 Anki 原有工作流、卡片模板和学习数据不受影响。

## 报告问题

先查看 [问题排查](./docs/TROUBLESHOOTING.md)。仍然无法解决时，通过 [Issue 模板](https://github.com/Damon-GSY/anki-editorial-index/issues/new/choose) 提交系统、Anki 版本、插件版本、复现步骤和不包含私人内容的截图。

## 本地验证

```bash
python3 scripts/package_addon.py
python3 scripts/validate_addon.py
python3 scripts/smoke_test_addon.py
```

三个命令都通过以后，`dist/Editorial-Index.ankiaddon` 才可以用于安装测试。

## 改动边界

- 不修改 Anki 数据库、调度逻辑或同步流程
- 不使用会覆盖 `#qa` 所有后代元素的通用样式
- 不复制其他主题项目的源码、图标、插画或品牌资产
- 新增字体或素材时同时提交来源与许可证
- 新设置需要默认值、配置说明和旧版本兼容处理

## 提交 Pull Request

保持改动集中，并说明用户能看到的结果、验证方式和仍未覆盖的平台。涉及界面的改动请附上前后截图。
