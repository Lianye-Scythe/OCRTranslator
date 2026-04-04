# OCRTranslator

[繁體中文](../README.md)｜简体中文｜[English](README.en.md)

[![CI](https://github.com/Lianye-Scythe/OCRTranslator/actions/workflows/ci.yml/badge.svg)](https://github.com/Lianye-Scythe/OCRTranslator/actions/workflows/ci.yml)

OCRTranslator 是一款以 **桌面即时阅读** 为核心的 **便携式 OCR / AI 请求工具**。

它不是单纯的截图翻译器，而是一个围绕三种入口打造的桌面 AI 工作台：

1. **屏幕框选**：把截图交给多模态模型做 OCR / 翻译 / 解答 / 润色
2. **选中文本**：抓取当前选中的文字，直接走文本请求
3. **手动输入**：打开输入框，把一段内容直接发送给 AI

## 特性总览

- 支持 **截图 / 选中文本 / 手动输入** 三种请求入口
- 支持 **Prompt Preset** 方案系统
- 内建四组预设方案：
  - `翻译 (Translate)`
  - `解答 (Answer)`
  - `润色 (Polish)`
  - `OCR 原文 (Raw OCR)`
- 支持多个 API Profile
- 支持 `Gemini Compatible` / `OpenAI Compatible`
- 支持多 Key 轮替与失败重试
- 结果浮窗支持：复制、Pin / 取消 Pin、透明度调整、拖拽移动、角落拖拽改尺寸、`Ctrl + 鼠标滚轮` 缩放字体
- 支持全局快捷键、系统托盘、单实例保护
- 配置默认保存在项目根目录 / exe 同层，保持便携

## 默认快捷键

当 `config.json` 不存在或字段缺失时，默认快捷键如下：

| 动作 | 默认快捷键 |
|---|---|
| 屏幕框选 | `Shift + Win + X` |
| 选中文本 | `Shift + Win + C` |
| 手动输入 | `Shift + Win + Z` |

> 实际使用仍以你的 `config.json` 为准。

## 快速开始

### 1. 安装依赖

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

如果你还需要打包或维护开发工具：

```bash
pip install -r requirements-dev.txt
```

### 2. 启动应用

#### 方式 A：推荐双击启动

直接运行：

- `start.bat`

它会自动：

1. 检查 `.venv`
2. 按需安装运行依赖
3. 通过 `launcher.pyw` 启动 GUI
4. 启动期若出错，优先显示错误对话框

#### 方式 B：命令行启动

```bash
python launcher.pyw
```

或：

```bash
python -m app.main
```

#### 方式 C：要求现有实例直接进入截图

```bash
python -m app.main --capture
```

支持参数：

- `--capture`
- `/capture`
- `capture`

## 使用流程

### 1. 先完成 API 设置

设置页至少需要填写：

- Provider
- Base URL
- API Keys
- Model

按需再补：

- Target Language
- Global Hotkeys
- Prompt Preset
- Overlay 偏好

建议顺序：

1. `Fetch Models`
2. `Test API`
3. `Save Settings`

### 2. 从三种入口发起请求

你可以通过这些入口触发：

- 主界面的 `Start Capture`
- 主界面的 `Open Input Box`
- 选中文本快捷键
- 托盘菜单中的截图 / 输入框入口
- 对应的全局快捷键
- `--capture` 启动参数

### 3. 查看结果

- 截图流程会在 `Preview & Log` 页面显示最近一次预览
- 结果会以浮窗形式显示在原文附近或触发点附近
- 执行过程会写入内存日志，可在界面中查看或导出

## Prompt Preset

每组方案都包含：

- `image_prompt`
- `text_prompt`

支持变量：

- `{target_language}`

文本模式会把正文自动附加到提示词后面，因此你只需要维护“指令部分”。

### 内建方案

| 方案 | 用途 |
|---|---|
| `翻译 (Translate)` | 把图片或文字翻译成目标语言 |
| `解答 (Answer)` | 对题目、问题、说明直接作答或解释 |
| `润色 (Polish)` | 把文字改写成更自然流畅的目标语言 |
| `OCR 原文 (Raw OCR)` | 只返回 OCR 原文，不翻译、不润色 |

> 内建方案不可直接删除；如果需要可删除版本，建议先复制成自定义方案。

## 配置文件

默认配置文件位置：

- `config.json`

路径规则：

- 源码模式：项目根目录
- 打包 exe：exe 所在目录

主要保存内容：

- Target Language / UI Language
- 三组全局快捷键
- Overlay 字体 / 字号 / 透明度 / Pin / 默认尺寸
- 是否按 X 最小化到系统托盘
- 当前启用的 API Profile
- 当前启用的 Prompt Preset
- 所有 Profiles / Presets

参考范例：

- `config.example.json`

> `config.json` 可能包含 API Keys 与私有 Base URL，请勿直接分享。

## 托盘、单实例与错误处理

### 单实例

应用会使用锁文件与本地 server 保证单实例。

重复启动时：

- 普通启动：唤回现有主窗口
- `--capture`：唤回现有实例并直接开始截图

### 托盘

托盘菜单提供：

- 显示主窗口
- 开始截图
- 打开输入框
- 取消当前操作
- 退出程序

> “选中文本”流程更适合通过全局快捷键触发。
> 因为一旦从主窗口或托盘点击，焦点通常会被本程序抢走，反而破坏外部应用原本的选中状态。

默认情况下，右上角 `X` 会直接退出程序。
如果你希望 `X` 改成最小化到系统托盘，可在设置页启用对应选项。

### 日志与 Crash Log

- 运行日志默认只保存在内存中
- 最多保留最近 100 条
- 可从界面导出

若程序遇到未处理异常，会在根目录或 exe 同层生成：

```text
ocrtranslator-crash-YYYYMMDD-HHMMSS-xxxxxxxxx.log
```

## 测试与检查

```bash
python -m unittest discover -v
python -m compileall app tests launcher.pyw
```

## 文档导航

- [文档总览](index.zh-CN.md)
- [架构说明](architecture.zh-CN.md)
- [开发指南](development.zh-CN.md)
- [打包与发布](packaging.zh-CN.md)
- [贡献指南](CONTRIBUTING.zh-CN.md)
- [安全性回报](SECURITY.zh-CN.md)
- [变更记录](CHANGELOG.zh-CN.md)
