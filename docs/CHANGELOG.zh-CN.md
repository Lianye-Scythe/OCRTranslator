# Changelog

[繁體中文](../CHANGELOG.md)｜简体中文｜[English](CHANGELOG.en.md)

本文件用于记录 OCRTranslator 的重要变更。

## Unreleased

### Added
- 新增主界面与托盘中的截图 / 输入框快捷入口
- 保留“选中文本”功能，但改回以全局快捷键作为主要入口
- 新增 `app/hotkey_utils.py`，统一快捷键切分、修饰键判断与正规化规则
- 新增 `app/crash_handling.py`，把 crash hook 初始化逻辑抽成共用入口
- 新增 `requirements-dev.txt` 与多语言文档版本

### Changed
- 设置表单校验改为按操作场景拆分，避免 Fetch Models / Test API / 文字请求被无关字段阻塞
- API Test 的 stale result 判断现在会纳入模型名称
- 内建提示词方案改为不可删除，避免重启后被自动补回造成语义不一致
- README 改为繁体中文默认版，并补上简体中文与英文版本
- `docs/` 下的架构、开发与打包文档补齐三语版本
- 非 QSS 的 UI 颜色常量开始收敛到 `app/ui/theme_tokens.py`
