# Security Policy

## 支持版本

当前只为最新 GitHub Release 提供安全更新。

## 插件权限

Editorial Index 在 Anki Desktop 进程中运行，因此拥有普通 Anki 插件能够使用的本地权限。当前代码不发送网络请求、不收集遥测，也不读取或修改卡片内容与调度数据。

只从本项目的 [GitHub Releases](https://github.com/Damon-GSY/anki-editorial-index/releases/latest) 下载安装包，并使用随版本提供的 `SHA256SUMS` 校验文件。

## 报告安全问题

请不要在公开 Issue 中粘贴账号、卡片内容、同步凭据或本地文件。可以先提交一条不含敏感细节的 Issue，说明问题类型和受影响版本，维护者会继续协调安全的复现方式。
