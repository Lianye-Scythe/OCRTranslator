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
