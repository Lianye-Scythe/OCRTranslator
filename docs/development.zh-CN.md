# 开发指南

[繁體中文](development.md)｜简体中文｜[English](development.en.md)

## 环境准备

开发环境、CI 与 Windows 打包统一使用 Python 3.15 的最新稳定补丁版，不再维护旧版 Python 的兼容性。

WSL / Linux 使用 `python3.15 -m venv .venv` 创建环境，再运行 `source .venv/bin/activate`。Windows 请先确认 `python --version` 为 3.15，再使用下面的命令。

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

如需打包或维护开发工具：

```bash
pip install -r requirements-dev.txt
```

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
