# 架构说明

[繁體中文](architecture.md)｜简体中文｜[English](architecture.en.md)

这份文档补回较完整的“项目结构与文件职责”说明，方便后续维护时快速定位每个模块的用途。

## 核心分层

OCRTranslator 当前主要分成这些层：

- `app/ui/`：Qt 视图、表单绑定与交互组件
- `app/services/`：工作流编排、后台任务、托盘、单实例、预览与浮窗呈现
- `app/providers/`：OpenAI / Gemini 相容 API 的 payload / response adapter
- `app/platform/windows/`：Windows 专属能力，例如全局快捷键与选中文本
- `app/settings_service.py` / `app/settings_models.py`：设置快照、纯规则校验与 candidate config 构建
- `app/api_client.py`：重试、Key 轮替、Provider 调度与统一错误处理

## 主要执行路径

1. `app/main.py`
   - 应用入口
   - 单实例锁
   - 已启动实例的动作转发
2. `app/ui/main_window.py`
   - 主窗口协调层
   - 串接 UI、services、tray、instance server
3. `app/services/request_workflow.py`
   - 三种请求入口的工作流编排
4. `app/services/background_task_runner.py`
   - 后台 worker 生命周期与 stale task 保护
5. `app/services/overlay_presenter.py`
   - 浮窗尺寸、位置与重排逻辑
6. `app/settings_service.py`
   - 表单快照校验
   - candidate config 构建

## 详细项目结构

```text
OCRTranslator/
├─ .github/
│  ├─ ISSUE_TEMPLATE/
│  │  ├─ bug_report.yml              # Bug 回报模板
│  │  ├─ config.yml                  # GitHub issue 模板配置
│  │  └─ feature_request.yml         # 功能需求模板
│  ├─ workflows/
│  │  └─ ci.yml                      # CI：运行 unittest 与 compileall
│  └─ PULL_REQUEST_TEMPLATE.md       # Pull Request 检查清单
│
├─ app/
│  ├─ __init__.py                    # app 包标记
│  ├─ api_client.py                  # 统一 API 调用、Key 轮替、重试与 Provider 调度
│  ├─ app_defaults.py                # 默认 Provider / URL / 模型 / 快捷键 / 显示值
│  ├─ app_metadata.py                # 作者与仓库 metadata
│  ├─ config_store.py                # config.json 载入、迁移、保存、损坏恢复
│  ├─ crash_handling.py              # 共用 crash hook 安装与错误对话框入口
│  ├─ crash_reporter.py              # crash log 生成、脱敏、落盘
│  ├─ default_prompts.py             # 内建 Prompt Preset 定义与名称正规化
│  ├─ hotkey_listener.py             # 旧入口 facade，转发到 platform/windows/hotkeys.py
│  ├─ hotkey_utils.py                # 快捷键切分、修饰键判断、正规化共用工具
│  ├─ i18n.py                        # locale 载入、语言正规化、系统语言侦测
│  ├─ main.py                        # GUI 启动主入口、单实例控制、capture 转发
│  ├─ models.py                      # AppConfig / ApiProfile / PromptPreset 数据结构
│  ├─ operation_control.py           # 取消 token、RequestContext、操作错误包装
│  ├─ profile_utils.py               # Provider / 模型值正规化与字符串工具
│  ├─ prompt_utils.py                # Prompt 模板渲染与文本请求包装
│  ├─ runtime_paths.py               # 根目录、锁文件、server 名称、config 路径
│  ├─ selected_text_capture.py       # 旧入口 facade，转发到 platform/windows/selected_text.py
│  ├─ settings_models.py             # 设置表单快照与验证结果模型
│  ├─ settings_service.py            # 设置校验规则、不同操作 scope 验证、candidate config 构建
│  ├─ workers.py                     # 后台线程与 Qt signal bridge
│  │
│  ├─ locales/
│  │  ├─ en.json                     # 英文 UI 文案
│  │  ├─ zh-CN.json                  # 简体中文 UI 文案
│  │  └─ zh-TW.json                  # 繁体中文 UI 文案
│  │
│  ├─ platform/
│  │  └─ windows/
│  │     ├─ hotkeys.py               # Windows 全局快捷键低阶监听与冲突判定
│  │     └─ selected_text.py         # Windows 选中文本抓取、剪贴板保存与还原
│  │
│  ├─ providers/
│  │  ├─ __init__.py                 # 导出可用 Provider adapter
│  │  ├─ gemini_compatible.py        # Gemini Compatible API adapter
│  │  └─ openai_compatible.py        # OpenAI Compatible API adapter
│  │
│  ├─ services/
│  │  ├─ background_task_runner.py   # 后台 worker 执行、错误回传、stale result 保护
│  │  ├─ image_capture.py            # 屏幕截图、跨屏 fallback、预览图生成
│  │  ├─ instance_server.py          # 单实例唤回与 capture 转发 server
│  │  ├─ operation_manager.py        # 后台操作 task id / 取消 / stale 状态管理
│  │  ├─ overlay_presenter.py        # 结果浮窗尺寸、位置与重排控制
│  │  ├─ request_workflow.py         # capture / selected text / manual input 三流程编排
│  │  ├─ runtime_log.py              # 内存中的运行日志 store
│  │  └─ system_tray.py              # 系统托盘建立、更新与动作绑定
│  │
│  └─ ui/
│     ├─ __init__.py                 # UI 包标记
│     ├─ main_window.py              # 主窗口协调层，整合 mixin 与 service 调用
│     ├─ main_window_layout.py       # 主壳层布局、导航、header、样式套用
│     ├─ main_window_profiles.py     # Profile 表单绑定、验证呈现、快捷键录制
│     ├─ main_window_prompts.py      # Prompt Preset 表单逻辑与内建 preset 保护
│     ├─ main_window_settings_layout.py # Settings 页各 section 布局构建
│     ├─ overlay_positioning.py      # 浮窗定位、尺寸与屏幕边界计算
│     ├─ prompt_input_dialog.py      # 手动输入文本请求对话框
│     ├─ selection_overlay.py        # 全屏框选覆盖层
│     ├─ style_utils.py              # QSS 载入与 theme token 渲染
│     ├─ theme_tokens.py             # 非 QSS 与 QSS 共用的颜色 / 字体 token
│     ├─ translation_overlay.py      # 结果浮窗本体与交互逻辑
│     │
│     └─ styles/
│        ├─ main_window.qss          # 主窗口样式
│        └─ translation_overlay.qss  # 结果浮窗样式
│
├─ docs/
│  ├─ index.md                       # 文档总览（繁中）
│  ├─ index.zh-CN.md                 # 文档总览（简中）
│  ├─ index.en.md                    # 文档总览（英文）
│  ├─ architecture.md                # 架构说明（繁中）
│  ├─ architecture.zh-CN.md          # 架构说明（简中）
│  ├─ architecture.en.md             # 架构说明（英文）
│  ├─ development.md                 # 开发指南（繁中）
│  ├─ development.zh-CN.md           # 开发指南（简中）
│  ├─ development.en.md              # 开发指南（英文）
│  ├─ packaging.md                   # 打包与发布（繁中）
│  ├─ packaging.zh-CN.md             # 打包与发布（简中）
│  ├─ packaging.en.md                # 打包与发布（英文）
│  ├─ README.zh-CN.md                # README 的简中镜像版
│  ├─ README.en.md                   # README 的英文镜像版
│  ├─ CONTRIBUTING.zh-CN.md          # Contributing 的简中镜像版
│  ├─ CONTRIBUTING.en.md             # Contributing 的英文镜像版
│  ├─ SECURITY.zh-CN.md              # Security 的简中镜像版
│  ├─ SECURITY.en.md                 # Security 的英文镜像版
│  ├─ CHANGELOG.zh-CN.md             # Changelog 的简中镜像版
│  └─ CHANGELOG.en.md                # Changelog 的英文镜像版
│
├─ tests/
│  ├─ __init__.py                    # tests 包标记
│  ├─ test_api_client.py             # ApiClient、Provider response、重试与 Key 轮替测试
│  ├─ test_config_store.py           # config 迁移、损坏恢复、默认值测试
│  ├─ test_crash_reporter.py         # crash log 生成与脱敏测试
│  ├─ test_hotkey_listener.py        # 快捷键冲突与优先匹配测试
│  ├─ test_i18n.py                   # locale key 对齐与语言正规化测试
│  ├─ test_main_window_runtime.py    # 主窗口运行期状态与保存回滚测试
│  ├─ test_operation_manager.py      # OperationManager 的 task / cancel / stale 逻辑测试
│  ├─ test_overlay_positioning.py    # 浮窗位置与尺寸计算测试
│  ├─ test_prompt_presets_runtime.py # 内建 Prompt Preset 删除保护测试
│  ├─ test_prompt_utils.py           # Prompt 模板渲染与文本包装测试
│  ├─ test_request_workflow.py       # request workflow 的签名与关键规则测试
│  ├─ test_selected_text_capture.py  # 选中文本剪贴板工具函数测试
│  └─ test_settings_service.py       # 设置 scope 验证与 candidate config 测试
│
├─ .gitignore                        # 忽略 venv、build、release、config 与 log
├─ build_exe.bat                     # Windows 一键打包脚本
├─ CHANGELOG.md                      # 变更记录（繁中默认版）
├─ config.example.json               # 设置文件范例
├─ config.json                       # 本机运行设置（runtime 产物，不应提交）
├─ CONTRIBUTING.md                   # 协作与贡献指南（繁中默认版）
├─ launcher.pyw                      # GUI 启动器
├─ README.md                         # 项目说明（繁中默认版）
├─ requirements-dev.txt              # 开发 / 打包依赖
├─ requirements.txt                  # 运行期依赖
├─ SECURITY.md                       # 安全性回报说明（繁中默认版）
└─ start.bat                         # Windows 一键启动脚本
```

## 维护建议

目前这套结构的目标是：

- 根目录保持干净，只保留默认语言与实际入口文件
- 其他语言文档集中到 `docs/`
- `app/` 内维持 `ui / services / providers / platform` 的边界
- 减少把工作流直接塞回 UI 类

如果后续还要继续整理，可优先考虑：

- 将 `app/ui/main_window_*` 再进一步收敛成更明确的 UI 子模块
- 视情况把 `start.bat` / `build_exe.bat` 收到 `scripts/`，但那会一起影响使用与文档入口
