# Support

[繁體中文](../SUPPORT.md)｜简体中文｜[English](SUPPORT.en.md)

这份文档说明 OCRTranslator 当前建议的提问、回报与联系路径。

## 先看哪些文档

建立 issue 或发邮件前，建议先依次查看：

- [README](README.zh-CN.md)
- [FAQ](FAQ.zh-CN.md)
- [Contributing](CONTRIBUTING.zh-CN.md)
- [Security Policy](SECURITY.zh-CN.md)
- [Changelog](CHANGELOG.zh-CN.md)

## 一般使用问题

如果是：

- 安装 / 启动问题
- 配置方式
- 支持的 provider / Base URL 类型
- 选中文本、截图、浮窗等使用方式

请先查看 [FAQ](FAQ.zh-CN.md) 与 [README](README.zh-CN.md)。

## Bug 回报

如果你确认是可复现的程序错误，请使用 GitHub Issues 的 bug template，并尽量附上：

- 复现步骤
- 运行方式（源码 / 打包 exe）
- 操作系统与 Python 版本
- 关键 log / crash log 片段
- 若有 UI 问题，附上截图或短视频

## 功能建议

如果你想提出：

- 新功能
- UI / UX 改进
- API / Provider 支持建议
- 打包 / 发布流程建议

请使用 GitHub Issues 的 feature request template。

## 安全问题

如果内容涉及：

- API Key
- 私有 Base URL
- 可重放请求
- 敏感 log
- 可被滥用的漏洞细节

请不要公开发 issue，请改发邮件到：`po12017po@gmail.com`

建议邮件标题格式：`[OCRTranslator Security] <简短摘要>`

## 讨论区状态

当前仓库的 GitHub Discussions 已关闭。

因此当前建议的对外入口为：

- 一般问题 / bug / 功能建议：GitHub Issues
- 敏感安全问题：Email

## 版本与下载

公开版本请以 GitHub Releases 页面为准：

- https://github.com/Lianye-Scythe/OCRTranslator/releases

当前公开 Windows 发布包仍属于 **未签名** 状态；Release 会附上 `SHA256SUMS.txt` 供手动校验，正式代码签名流程仍在规划中。
