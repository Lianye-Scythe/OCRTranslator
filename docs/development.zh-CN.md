# 开发指南

[繁體中文](development.md)｜简体中文｜[English](development.en.md)

## 环境准备

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
