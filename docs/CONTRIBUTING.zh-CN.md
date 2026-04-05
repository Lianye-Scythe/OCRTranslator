# Contributing

[繁體中文](../CONTRIBUTING.md)｜简体中文｜[English](CONTRIBUTING.en.md)

感谢你关注 OCRTranslator。

这个项目目前仍以个人主导维护为主，但欢迎通过 issue 与 pull request 提出修正与建议。为了降低沟通成本，请先阅读下面的规则。

参与本项目之前，请先阅读并遵守仓库根目录的 `CODE_OF_CONDUCT.md`。

## 开发原则

- 先维持当前 UI 的整体风格与操作方向，不要随意推翻版型
- 优先修复真实可复现问题，再处理风格性调整
- 不要提交包含 API Key、个人配置或本机生成数据的文件
- 对设置结构的改动，请考虑旧版 `config.json` 的迁移兼容性
- 若调整架构，请尽量维持 `ui / services / providers / platform` 的分层边界

## 建议流程

1. Fork / 新建分支
2. 完成修改
3. 执行：
   - `python -m unittest discover -v`
   - `python -m compileall app tests launcher.pyw`
   - 若涉及打包脚本或发布流程，再确认 `pip install -r requirements-dev.txt`
4. 补充必要的 README / docs 或注释
5. 提交 Pull Request
6. 若提交代码贡献，默认同意该贡献以 **GPLv3** 纳入本项目

## Pull Request 建议

PR 内容最好至少包含：

- 变更摘要
- 验证方式
- 风险说明
- 若有 UI 变更，附上截图或简短说明
- 若有架构调整，请说明分层边界改动

## Issue 回报建议

建立 bug issue 时，请尽量附上：

- 复现步骤
- 运行方式（源码 / exe）
- 操作系统与 Python 版本
- 运行记录
- crash log（若程序有写出）

## 不建议直接提交的内容

- `config.json`
- `.venv/`
- `build/`
- `dist/`
- `release/`
- `ocrtranslator-crash-*.log`
- `ocrtranslator-log-*.txt`
