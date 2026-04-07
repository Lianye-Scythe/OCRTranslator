# OCRTranslator

[繁體中文](../README.md)｜简体中文｜[English](README.en.md)

[![CI](https://github.com/Lianye-Scythe/OCRTranslator/actions/workflows/ci.yml/badge.svg)](https://github.com/Lianye-Scythe/OCRTranslator/actions/workflows/ci.yml)
[![Platform](https://img.shields.io/badge/platform-Windows-0078D6)](packaging.zh-CN.md)
[![Release](https://img.shields.io/badge/release-v1.0.5-2563EB)](https://github.com/Lianye-Scythe/OCRTranslator/releases)
[![License](https://img.shields.io/badge/license-GPLv3-4F46E5)](../LICENSE)

OCRTranslator 是一款以 **桌面即时阅读** 为核心的 **便携式 OCR / AI 请求工具**。

它不是单纯的截图翻译器，而是一个围绕三种入口打造的桌面 AI 工作台：

1. **屏幕框选**：把截图交给多模态模型做 OCR / 翻译 / 解答 / 润色
2. **选中文本**：抓取当前选中的文字，直接走文本请求
3. **手动输入**：打开输入框，把一段内容直接发送给 AI

## 界面预览

如果你想先快速了解产品外观，可以先看当前主窗口与翻译浮窗的实际效果，再继续往下阅读功能总览。

### 动态预览

<p align="center">
  <img src="images/screenshots/ocrtranslator-preview.gif" width="88%" alt="OCRTranslator 动态预览" />
</p>

### 静态截图

#### 主窗口

<p align="center">
  <img src="images/screenshots/main-window-light.png" width="49%" alt="浅色主题主窗口" />
  <img src="images/screenshots/main-window-dark.png" width="49%" alt="深色主题主窗口" />
</p>

#### 翻译浮窗

<p align="center">
  <img src="images/screenshots/overlay-light-manga.png" width="49%" alt="浅色主题翻译浮窗（漫画）" />
  <img src="images/screenshots/overlay-light-novel.png" width="49%" alt="浅色主题翻译浮窗（小说）" />
</p>
<p align="center">
  <img src="images/screenshots/overlay-dark-novel.png" width="49%" alt="深色主题翻译浮窗（小说）" />
  <img src="images/screenshots/overlay-dark-manga.png" width="49%" alt="深色主题翻译浮窗（漫画）" />
</p>

## 特性总览

- 支持 **截图 / 选中文本 / 手动输入** 三种请求入口
- 支持 **Prompt Preset** 方案系统，内建 `翻译 (Translate)`、`解答 (Answer)`、`润色 (Polish)`、`OCR 原文 (Raw OCR)` 四组预设方案
- 支持多个 API Profile，可接入 `Gemini Compatible` / `OpenAI Compatible`
- 支持多 Key 轮替、失败重试与模型切换
- 流式响应默认启用，可在进阶设置中关闭；`Test API` 也会沿用相同模式验证实际后端行为
- 第三方 Compatible 后端如果不支持流式，会提示当前状态并自动回退到非流式；流式中断时也会保留部分结果与状态标记
- 设置页采用“连接与模型 → 翻译方式与快捷键 → 界面与进阶”三段式流程，更容易完成首次配置
- 屏幕框选现在会先冻结桌面快照再裁切选区，降低高 DPI / 多显示器偏移、hover 新 UI 混入与主窗口残影
- 请求流程尽量保持非阻塞，并通过应用内短时气泡 / 系统托盘通知反馈当前状态
- 结果浮窗支持：
  - 复制、图钉固定 / 取消固定
  - 仅调整表面背景的透明度（文字保持清晰）
  - 直接输入透明度百分比
  - 拖拽移动与角落拖拽改尺寸
  - `Ctrl + 鼠标滚轮` 缩放字体
- 已 Pin 的结果浮窗可保留位置与尺寸；未 Pin 状态则会从默认尺寸重新展开，并记住你最近一次手动调整过的宽度
- 支持 `浅色 / 深色 / 跟随系统` 三态主题切换
- 支持全局快捷键、系统托盘、单实例唤回与 `--capture` 快速启动
- 提供版本化 ZIP 发布、`SHA256SUMS.txt` 校验与完整三语文档

## 发布与信任信息

- 官方桌面发布以 GitHub Releases 中的版本化 ZIP 为准：`OCRTranslator-v<version>-windows-x64.zip`
- 推送 `v*` annotated tag 后，GitHub Actions 会自动构建 Release，并优先沿用 tag annotation 作为 Release 正文
- 当前公开 Windows 发布包 **尚未签名**；仓库已预留 SignPath / Trusted Build 集成，后续计划导入正式签名流程
- 公开 Release 不会额外上传独立 `.exe`，而是只提供版本化 ZIP 与 GitHub 自带 source archives
- Release 也会额外附上 `SHA256SUMS.txt`，方便手动校验下载的 ZIP 文件
- 若要私下回报敏感安全问题，请发送邮件到 `po12017po@gmail.com`

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

### 1. 先完成当前配置的连接与模型测试

设置页现在会优先引导你完成“连接与模型”区块，至少需要填写：

- Provider
- Base URL
- API Keys
- Model

建议顺序：

1. 选择或新增一个 API Profile
2. `Fetch Models`
3. `Test API`
4. `Save Settings`

等连接完成后，再按需补上：

- Target Language
- Global Hotkeys
- Prompt Preset
- Overlay 偏好
- Theme / UI Language

### 2. 从三种入口发起请求

你可以通过这些入口触发：

- 主界面的 `Start Capture`
- 主界面的 `Open Input Box`
- 选中文本快捷键
- 托盘菜单中的截图 / 输入框入口
- 对应的全局快捷键
- 选中文本快捷键在抓取期间不会再同步卡住主窗口；如果抓取尚未完成，也可以用“取消当前操作”中止
- `--capture` 启动参数

### 3. 查看结果

- 截图流程会在 `Preview & Log` 页面显示最近一次预览
- 结果会以浮窗形式显示在原文附近或触发点附近
- 新版本的图片请求日志还会输出 PNG 大小与 `capture / request / total` 耗时，便于确认性能瓶颈
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

默认会优先使用便携配置文件 `config.json`。

路径解析规则：

- 源码模式：如果项目根目录已有 `config.json`，就继续沿用；如果根目录可写且还没有配置文件，也会直接在根目录创建
- 打包 exe：如果 exe 同层已有 `config.json`，就继续沿用；如果 exe 目录可写且还没有配置文件，也会直接在 exe 同层创建
- 如果便携位置没有配置文件，且当前运行目录不可写，则自动回退到用户设置目录：
  - Windows：`%LOCALAPPDATA%\OCRTranslator\config.json`
  - 其他环境 fallback：`~/.ocrtranslator/config.json`

只要便携配置文件存在，就会优先使用便携路径。

主要保存内容：

- Target Language / UI Language
- Theme Mode
- 三组全局快捷键
- Overlay 字体 / 字号 / 透明度 / Pin / 默认尺寸 / Pin 几何
- 是否按 X 最小化到系统托盘
- 当前启用的 API Profile
- 当前启用的 Prompt Preset
- 所有 Profiles / Presets

参考范例：

- `config.example.json`

> `config.json` 可能包含 API Keys 与私有 Base URL，请勿直接分享。
> crash log 仍会优先写回项目根目录或 exe 同层，不会跟着 fallback 配置路径移动。

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
- [常见问题 FAQ](FAQ.zh-CN.md)
- [Code of Conduct](../CODE_OF_CONDUCT.md)
- [Support](../SUPPORT.md)
- [贡献指南](CONTRIBUTING.zh-CN.md)
- [安全性回报](SECURITY.zh-CN.md)
- [变更记录](CHANGELOG.zh-CN.md)

## 已知边界

- 识别与输出质量高度依赖所接入的多模态模型
- 当前不内建离线 OCR 引擎
- 选中文本流程采用“模拟复制并尽量还原剪贴板”策略，少数应用可能不响应标准复制行为
- 工程与启动脚本主要面向 Windows 使用场景
- 浮窗定位以“尽量不遮挡阅读”为优先，而不是严格排版系统
- 运行日志默认不作为长期审计记录保存

## 许可证

- 本项目采用 **GNU General Public License v3.0（GPLv3）** 发布
- 详细条款见仓库根目录 `LICENSE`
- 若你修改后再对外分发衍生版本，请一并提供对应源代码并继续使用 GPLv3

向本项目提交 Pull Request、补丁或其他代码贡献时，默认也会以 GPLv3 纳入本项目。
