# 开发指南

[繁體中文](development.md)｜简体中文｜[English](development.en.md)

## 环境准备

开发环境、CI 与 Windows 打包使用 Python 3.15，不再维护旧版 Python 的兼容性。请在项目根目录执行命令；Windows 与 WSL 的虚拟环境不能共用。

目前最低安全基准为 Python 3.15.2，建议持续使用最新 3.15 稳定修补版。`.python-version` 的 `3.15` 只指定版本系列，不会自动更新现有环境；CI 使用 `check-latest` 避免沿用较旧的缓存版本。

更新 Windows Python 后，对相应环境执行 `py -3.15 -m venv --upgrade .venv`；`start_wsl.bat` 的环境则使用 `py -3.15 -m venv --upgrade "$env:LOCALAPPDATA\OCRTranslator\venv-win315"`（PowerShell）。WSL 若使用 uv 管理 Python，执行 `uv python upgrade 3.15`，再确认 `.venv/bin/python --version`；如果仍连接旧版，使用更新后的 `python3.15 -m venv --upgrade .venv`。最后更新环境内 pip 并重新安装 `requirements.txt`，需要打包时改装 `requirements-dev.txt`。

### Windows PowerShell

```powershell
py -3.15 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\Activate.ps1
```

如果 PowerShell 的执行策略阻止激活脚本，可以直接用 `.\.venv\Scripts\python.exe` 替代下方的 `python`，不必修改全局执行策略。

### Windows CMD

```bat
py -3.15 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
call .venv\Scripts\activate.bat
```

### WSL / Linux Bash

```bash
python3.15 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
source .venv/bin/activate
```

WSL 用于开发与自动化测试；完整 Windows 桌面操作请在 Windows 运行，或使用下方的 `start_wsl.bat`。不要让 Windows 的 `start.bat` 使用 WSL 创建的 `.venv`。

激活对应环境后，如需打包工具，执行：

```text
python -m pip install -r requirements-dev.txt
```

后续 `python` 命令均指已激活环境的 Python；可以用 `python --version` 和 `python -m pip --version` 确认。

## 常用命令

### 从 Windows 测试 WSL 源码

在文件资源管理器打开 `\\wsl.localhost\Ubuntu\home\po120\Git\OCRTranslator`（按自己的发行版与路径调整），双击项目根目录的 `start_wsl.bat`。需要 Windows Python 3.15 与 `py` launcher。

脚本自动在 `%LOCALAPPDATA%\OCRTranslator\venv-win315` 创建 Windows 专用环境并按 `requirements.txt` 安装依赖，不使用 WSL 的 `.venv`。程序关闭前请保留 console，让 WSL 路径映射持续有效。只验证环境可运行 `start_wsl.bat --check`，截图与热键仍需在实际 GUI 中测试。

### 启动应用

```bash
python launcher.pyw
```

或：

```bash
python -m app.main
```

### 配置路径提示

源码运行时，程序会优先使用项目根目录的 `config.json`；如果根目录没有配置文件且当前目录不可写，则会自动回退到：

- Windows：`%LOCALAPPDATA%\OCRTranslator\config.json`
- 其他环境 fallback：`~/.ocrtranslator/config.json`

排查本机配置问题时，请同时确认便携配置文件与 fallback 配置文件是否有其中一份正在生效。

### 运行测试

```bash
python -m unittest discover -v
```

### 基本编译检查

```bash
python -m compileall app tests launcher.pyw
```

## 测试重点

当前测试重点包含：

- API 错误消息解析与 Provider 适配
- 配置迁移与损坏恢复
- crash log 生成与脱敏
- 快捷键冲突判定
- 浮窗定位逻辑
- 主窗口运行期状态控制
- 设置快照校验与 candidate config 构建
- Prompt preset 与请求工作流关键规则

## 提交前建议

CI 按变更范围分流：文档检查链接，`docs/images/` 图片另检查可读性与分享图尺寸；仅修改分享图生成器、其测试及文档时，只安装固定版本的 Pillow 并运行相关测试，不打包 Windows exe。应用程序、依赖、其他工具或 CI 配置变更仍运行完整 Windows 测试与打包。分享图工具的轻量分流不适用纯文档自动合并规则。

1. 跑完 `python -m unittest discover -v`
2. 跑完 `python -m compileall app tests launcher.pyw`
3. 若涉及打包流程，再确认 `pip install -r requirements-dev.txt`
4. 检查是否误提交：
   - `config.json`
   - `.venv/`
   - `build/`
   - `dist/`
   - `release/`
   - `ocrtranslator-crash-*.log`
   - `ocrtranslator-log-*.txt`

## 依赖版本与更新

`requirements.txt` 自动引用根目录的 `constraints.txt`，因此现有启动脚本、安装命令和 CI 都使用相同的固定包版本。Windows 专用依赖不会安装到 WSL，Linux 专用依赖也不会安装到 Windows；打包工具仅在安装 `requirements-dev.txt` 时加入。

更新依赖时，调整 `constraints.txt`，必要时同步最低版本范围，并在 Windows 和 WSL 分别安装、运行 `python -m pip check` 和测试；涉及打包依赖时确认 Windows CI 打包成功。不要用单一环境的完整 `pip freeze` 直接覆盖跨平台约束文件，也不要只更新其中一台的虚拟环境。

约束文件固定包版本，但不固定 pip、Python 补丁版、隔离构建工具或下载文件哈希，不保证逐字节相同的 exe，也不会改变已经发布的 ZIP。

## 分享图维护

运行 `python tools/generate_social_preview.py --thumbnail build/social-preview-320.png`，更新 `docs/images/social-preview.png` 并生成 320 × 160 检查图。产图使用仓库内的宽版主窗口截图，按原比例展示完整界面；更换素材时需要重新检查文字和安全边距，不要裁剪或拉伸界面。

图片提交到 GitHub 后，仍需在仓库 Settings → Social preview → Edit 上传新版 PNG；GitHub 不会自动把仓库内图片设为分享图。各分享平台也可能保留旧预览缓存。
