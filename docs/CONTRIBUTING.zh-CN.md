# Contributing

[繁體中文](../.github/CONTRIBUTING.md)｜简体中文｜[English](CONTRIBUTING.en.md)

感谢你关注 OCRTranslator。

这个项目目前仍以个人主导维护为主，但欢迎通过 issue 与 pull request 提出修正与建议。为了降低沟通成本，请先阅读下面的规则。

参与本项目之前，请先阅读并遵守`.github/CODE_OF_CONDUCT.md`。

## 开发原则

- 先维持当前 UI 的整体风格与操作方向，不要随意推翻版型
- 优先修复真实可复现问题，再处理风格性调整
- 不要提交包含 API Key、个人配置或本机生成数据的文件
- 对设置结构的改动，请考虑旧版 `config.json` 的迁移兼容性
- 若调整架构，请尽量维持 `ui / services / providers / platform` 的分层边界

## 依赖自动化

只有本仓库 Dependabot 创建且目标为 `main` 的 pip PR 可以启用自动合并。白名单仅含 Pillow、requests、pynput 的稳定 patch 更新，且 diff 只能提高 `requirements.txt` 中对应的最低修补版本。minor / major、Qt、PyInstaller、Actions、签名及发布变更仍需人工审核；安全更新也不绕过这些限制。

合并前必须通过 `test` 和 `windows-package`，且分支需与 `main` 保持最新。打包不使用签名凭证、不发布 Release。特权流程只执行 base commit 上的政策代码、检查元数据与 diff，每次 PR 更新都会重新判定；不执行 PR 代码、不安装其依赖、不自动提交 Approve，也不绕过必要检查。政策调整需要人工审核。

## 纯文档修改

`main` 仍要求 PR。仅修改根目录 README／CHANGELOG、`docs/` 下 Markdown、`docs/images/` 下展示图片或 `.github/` 直属 Markdown 时，只检查本地文档链接和图片路径，不安装应用依赖、不跑 Windows 测试或打包。修改程序、依赖、workflow、政策脚本、打包文档（`packaging/windows/README.md`）或手动执行 CI 时，仍运行完整检查。

`ci-required` 汇总关卡必须成功；纯文档流程的 `windows-package` 显示为跳过，而非打包成功。仓库拥有者在本仓库创建、目标为 `main` 的非草稿纯文档 PR，会在必要检查通过后自动合并；外部 PR 仍需人工决定。每次 PR 更新都会先撤销旧的自动合并要求，再重新判断。

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
