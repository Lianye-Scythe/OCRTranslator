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
- 新增 `浅色 / 深色 / 跟随系统` 三态主题设置与 `theme_mode` 配置字段

### Changed
- 设置表单校验改为按操作场景拆分，避免 Fetch Models / Test API / 文字请求被无关字段阻塞
- API Test 的 stale result 判断现在会纳入模型名称
- 内建提示词方案改为不可删除，避免重启后被自动补回造成语义不一致
- 设置页信息架构改为「连接与模型 → 翻译方式与快捷键 → 界面与进阶」，强化先完成连接再开始使用的主路径
- UI 主题 token 重构为偏 Material Design 方法论的语义色彩系统，让主按钮、次按钮、导航 selected、badge、warning / danger 状态各自有明确角色
- 主窗口、结果浮窗与框选遮罩现在共用同一套主题角色，深色 / 浅色样式与运行时切换逻辑一并收敛
- README 改为繁体中文默认版，并补上简体中文与英文版本
- `docs/` 下的架构、开发与打包文档补齐三语版本
- 非 QSS 的 UI 颜色常量开始收敛到 `app/ui/theme_tokens.py`
- 全面重构浅色与深色主题色彩，引入基于 Material Design 3 的“黑白与冷灰阶 (Slate / Graphite)”高质感配色系统
- 移除设置界面多余的边框 (Box-in-box)，改用留白与背景色阶 (Surface Tones) 建立视觉层级
- 优化下拉菜单图标，将方形/减号替换为符合使用直觉的 SVG 箭头
- 强化按钮的视觉层级，根据未保存状态动态强调“保存设置”主要按钮 (Primary Action)
- 改善表单错误状态 (Error States) 显示，移除具攻击性的红色大框，改用内敛的文字与输入框边框提示
- 将深色模式的输入框改为深邃内嵌式 (Recessed Inputs)，搭配柔光白主色提升长时间阅读的舒适度

### Fixed
- 修正“取消当前操作”和“删除”共用危险色的语义错位，改为 warning / danger 分离
- 修正 `保存设置`、`打开输入框`、disabled 与 validation 状态在浅色主题下容易混淆的问题
