# Security Policy

[繁體中文](../SECURITY.md)｜简体中文｜[English](SECURITY.en.md)

如果你发现 OCRTranslator 存在安全性问题，请不要直接在公开 issue 中贴出可被滥用的细节、密钥或敏感请求内容。

## 回报原则

请至少提供：

- 问题描述
- 影响范围
- 复现步骤
- 是否需要登录、API Key 或特定配置
- 如果有 crash log，请先确认其中不包含敏感信息

> 当前 crash log 会对部分本机路径与常见敏感参数做基础遮罩，但仍不应直接假设可安全公开，提交前请人工再检查一次。

## 不要公开贴出的内容

- API Keys
- 私有 Base URL
- 用户个人资料
- 任何可直接重放的敏感请求
- 未经检查的完整 crash log / 运行日志

## 建议做法

如果问题可能造成敏感信息泄露或远程滥用，请优先通过私下方式联系维护者，再决定是否公开披露。

## 私下联系方式

- Email：`po12017po@gmail.com`
- 建议邮件标题：`[OCRTranslator Security] <简短摘要>`
