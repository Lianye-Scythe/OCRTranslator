# Changelog

[繁體中文](../CHANGELOG.md)｜简体中文｜[English](CHANGELOG.en.md)

本文件用于记录 OCRTranslator 的重要变更。

## [Unreleased]

## [1.0.5] - 2026-04-07

### Added
- 新增 Windows 专用的截图瞬时隐身与 compositor flush 辅助模块，并补上 frozen snapshot / concealment / compositor sync 的回归测试与诊断日志

### Changed
- 屏幕框选流程改为两阶段：先暂时隐藏应用自有窗口并冻结桌面快照，再显示框选遮罩；完成框选后直接从 frozen snapshot 裁切，不再回头对 live desktop 重抓
- 框选遮罩现在会以 frozen desktop background 作为底图，截图提示则延后到裁切完成后再显示，降低截图前自家 UI 干扰画面的概率

### Fixed
- 修复 Win11 下主窗口、结果浮窗或 hover 触发的新 UI 容易在截图过渡期间混入画面的问题
- 修复高 DPI / 多显示器下框选区域与实际截图不一致的问题，同时保持原始 PNG bytes 直送，不做额外图片预处理

## [1.0.4] - 2026-04-06

### Added
- 新增默认启用的“流式响应”设置，并在进阶设置提供显式开关；`OpenAI Compatible` / `Gemini Compatible` 的文本与图片请求现在都支持流式增量更新
- 新增部分结果状态标记与相关提示文案；流式中断时会保留可见内容并标示 `流式接收中 / 已取消 / 请求失败`

### Changed
- `Test API` 现在会跟随当前的流式响应设置，第三方 Compatible 后端在流式不兼容时会显示状态提示并尝试自动回退到非流式
- 浮窗几何策略调整为更稳定的两段式行为：单次流式请求期间锁定宽度、未 Pin 浮窗会沿用用户运行时手动调整过的宽度，并可跨重启保留
- 部分结果 UI 更新改为 16ms latest-only frame coalescing，并减少可见增量更新时不必要的 refresh / topmost / geometry / text work

### Fixed
- 修复 SSE 流式在 UTF-8 / CJK 内容下可能出现乱码的问题
- 修复取消 / 失败 / pinned restore 等中断场景下的部分结果浮窗状态，避免覆盖既有结果，并让复制与标题文案保持一致
- 修复未保存 `overlay_width` 表单改动时，已保存的 `overlay_unpinned_width` 可能被提前写盘清除的边界问题

## [1.0.3] - 2026-04-06

### Added
- 新增 `--capture` 启动兜底：如果因为设置校验或运行期状态无法直接开始截图，会自动回到主窗口并显示明确状态提示
- 新增双配置路径说明与相关测试，补充便携配置文件与用户级 fallback 配置文件的解析规则

### Changed
- 进一步优化启动链路：`--capture` 启动不再先显示主窗口、最小化到系统托盘前会先补齐 tray 初始化，且主窗口隐藏后会继续轻量 prewarm、暂停较重的 UI 实例预热
- 配置解析现在优先沿用项目根目录 / exe 同层的便携 `config.json`；如果该位置没有配置文件且当前目录不可写，则自动回退到用户设置目录

### Fixed
- 把 Qt 主线程未处理事件异常的关闭路径统一到完整清理链路，补上 watchdog、热键 / 托盘 / overlay / 单实例 IPC 清理，降低出错后只能强制结束的风险
- 修复更新检查 worker 如果直接抛异常时可能残留 busy 状态的问题，避免 UI 长时间停在 checking 状态
- 清理旧的同步选中文字与未使用截图死码，降低维护噪音与启动链路理解成本

## [1.0.2] - 2026-04-05

### Fixed
- 启动后延迟执行的自动版本检查现在只会读取已保存的 `check_updates_on_startup` 设置，不再受尚未保存的 checkbox 实时状态影响

### Changed
- `v1.0.2` 的发布 tag annotation 改为使用无 BOM 文案建立，避免 GitHub Release 正文继承隐藏前导字符

## [1.0.1] - 2026-04-05

### Added
- 新增可选 GitHub Releases 更新检查；进阶设置支持启动后延后后台检查与手动立即检查，发现新版本时可直接打开 Releases 链接
- 新增 API Keys 隐藏态的显式引导；当字段保持遮罩时，点击编辑区会通过按钮与说明文提示先按“显示 Key”，不会自动暴露敏感内容

### Changed
- 重新整理 API Keys 隐藏态的 Material 交互细节：隐藏表面保持稳定样式，不再让输入框本体或外框跟着脉冲，提示只聚焦在按钮与说明文
- 进阶设置区块的阅读顺序改为先显示浮窗 / Pin 行为说明，再显示版本检查区块，让信息层级更自然
- 更新检查提示改为可点击的 GitHub Releases 链接，同时保持启动后无新版本 / 失败时的低干扰策略

### Fixed
- 修复 API Keys 隐藏态 `eventFilter()` 在主窗口初始化早期可能先于属性建立而触发 `AttributeError` 的问题，避免启动期连续刷出 crash log
- 修复主线程 crash handling 在嵌套或短时间重复异常下可能连续写出多份 crash log 的问题，加入重入与重复回报抑制
- 修复 API Keys 隐藏态在浅色 / 深色模式下的引导脉冲不同步、焦点残留与高亮残影问题

## [1.0.0] - 2026-04-05

### Added
- 新增 `startup_timing` 埋点与 `OCRTRANSLATOR_STARTUP_TIMING_VERBOSE=1` 详细模式，方便分析冷启动与首屏后预热耗时
- 新增 IME-aware 多行输入控件，修复手动输入与设置页多行编辑器在中文输入法预编辑期间的 placeholder 重叠问题
- 新增应用内短时请求提示气泡与可配置显示秒数；进阶设置现在可将气泡时长设为 `0` 直接禁用

### Changed
- 启动链路改为更轻量的 bootstrap：延后 UI 创建、统一 lazy service 初始化、补充 idle prewarm，同时保留单实例 IPC 与快速二次启动转发的稳定性
- 全局快捷键冲突判定改为与底层 listener 共用相同的虚拟键语义，并新增未知主键 / 纯修饰键防呆；快捷键录制完成后会即时套用到运行时，设置页也新增“放弃更改”操作
- 前台请求提示现在优先使用应用内 toast，后台或最小化场景才回退系统托盘通知，并加入重复消息节流
- 主窗口、侧边动作按钮、直接输入对话框以及最新截图 / social preview 已同步更新，整体视觉与交互细节更加一致
- Windows 打包持续采用更轻量的冷启动配置，包括关闭 PyInstaller `UPX` 并同步维护版本化资源与 `SHA256SUMS.txt` 说明

### Fixed
- 已固定的翻译浮窗在截图完成后，现在会立即恢复旧内容与原位置，而不必一直等到请求结果返回才重新显示
- 修复启动优化过程中引入的回归问题，包括 tray 属性初始化、`QTimer` 漏导入，以及主窗口首次显示后不能立即最小化到系统托盘
- 修复请求提示气泡在部分场景下卡在屏幕上的问题，并让成功 / 失败 / 取消路径都能更一致地收回短时提示
- 修复手动输入、选字与截图翻译流程中的多个边界状态，让取消、失败与已 pin 浮窗还原行为更加一致


## [0.9.9] - 2026-04-05

### Added
- 新增三语 `SUPPORT` 文档，整理一般问题、bug 回报、功能建议与安全问题的推荐联系路径，并反映当前 Discussions 已关闭后的维护方式
- 新增 GitHub social preview 图片资源 `docs/images/social-preview.png` 与生成脚本 `tools/generate_social_preview.py`
- FAQ 补充请求回复速度说明，明确记录 AI / LLM 模型、上游负载与限流会影响延迟，并补充 Google 官方 `gemini-3.1-flash-lite-preview` 常见的 5～10 秒、偶发 30～40 秒以及 `429` / `503` 情况

### Changed
- README / docs README 的静态 Release badge 更新为 `v0.9.9`，打包文档中的示例 ZIP 文件名也同步更新
- Issue contact links 现在补上 Support 入口，README 与 docs index 也同步收录 `SUPPORT.md`
- social preview 改为更简洁的品牌 + 主窗口截图版式，去掉胶囊式功能标签并统一左侧信息色系

### Fixed
- 修复 `release-build.yml` 在生成 fallback release notes 时的 YAML / PowerShell 结构问题，避免 workflow 因语法错误失效
- 修复私有仓库下 README 的 Release / License badge 容易出现 `repo not found` 或 `no releases` 的问题，改为私有仓库也能稳定显示的静态 badge
- 放宽 Dependabot 默认 label 依赖，避免仓库尚未建立 `dependencies`、`python`、`ci` 等 labels 时导致更新任务报错

## [0.9.8] - 2026-04-05

### Added
- 新增项目治理与协作基础文件：`CODE_OF_CONDUCT.md`、`.github/CODEOWNERS`、`.github/dependabot.yml`、`.editorconfig`、`.gitattributes`
- 新增三语 FAQ：`docs/FAQ.md`、`docs/FAQ.zh-CN.md`、`docs/FAQ.en.md`，补充平台支持、API Key、自架服务、离线 OCR、签名状态与安全回报等常见问题
- 新增动态预览 GIF 资源 `docs/images/screenshots/ocrtranslator-preview.gif`，并接入 README 预览区块

### Changed
- README / SECURITY / CONTRIBUTING / docs index / packaging 文档补上公开仓库维护所需的信任信息，包括私下安全联系邮箱、未签名发布包状态、签名计划以及 FAQ / Code of Conduct 入口
- CI workflow 新增 `workflow_dispatch`、concurrency、timeout 与 pip cache；release workflow 也补上 concurrency、timeout、pip cache 与 annotated tag release note 转发
- GitHub Release 自动发布现在会优先使用 annotated tag 内文作为 Release 正文，不再只依赖 GitHub Actions 自动生成 changelog

### Fixed
- 修复 `Save Settings` 在保存成功后仍可能因为焦点回退与滚动区自动保证可见而跳到“目标语言”字段的问题；保存后会恢复原滚动位置并清掉 Save 按钮焦点
- 修复设置页 API Keys、图片提示词与文本提示词多行输入框在深色模式下的双层描边感，改为更接近 Material 的 single-surface 焦点表面
- 修复浅色 / 深色模式下单行与多行输入框文字选取高亮过淡的问题，现在统一采用更清楚的选取配色
- 补上 release workflow、theme token、style sheet、settings save scroll restore 与 validation scope 的回归测试

## [0.9.7] - 2026-04-05

### Changed
- 设置表单中的 API Keys、图片提示词与文本提示词多行输入框改为共用单一焦点表面（single-surface）设计，减少深色模式下双层描边与厚重内框感
- 浅色 / 深色主题下的单行与多行输入框，现在统一使用更清楚的文字选取高亮配色，提高选取状态辨识度

### Fixed
- 修复只想先保存 API Profile / Key 设置时，`Save Settings` 会因 `target_language` 为空而自动把滚动位置拉到目标语言字段的问题；真正发起图片 / 文字请求时仍会保留目标语言校验
- 修复深色模式下 API Keys 与 Prompt 多行输入区的焦点框层次不协调问题，让 focus / invalid 状态回到更接近 Material 的单层轮廓表达
- 修复浅色与深色模式下输入框文字选取高亮过淡、难以判断是否已选中文字的问题
- 补上设置保存校验、theme token 与 style sheet 的回归测试

## [0.9.6] - 2026-04-05

### Added
- 新增 `LICENSE`（GPLv3），并补上 README / 贡献指南中的授权说明，明确代码与后续贡献的授权方式
- 新增 Pin 专用持久化几何字段，让固定中的翻译浮窗位置与尺寸可跨重启保留

### Changed
- 默认结果浮窗字号从 `12` 调整为 `16`，`config.example.json` 与设置模型的默认值同步更新
- 打包 / 签名基础结构移至 `packaging/`，由 `packaging/windows/OCRTranslator.spec` 与 `packaging/signpath/` 集中管理
- GitHub Actions workflow 改为使用 Node 24 兼容 action 版本，并通过 SignPath gate step 避免 workflow 在 `if:` 中直接引用 `secrets.*` 导致失效
- 主窗口关于区块现在会显示 `License: GPLv3`，打包输出的 ZIP 也会一并附上 `LICENSE`
- 运行期提示文案同步更新：未 Pin 浮窗每次都会从已保存的默认尺寸重新自动扩展，Pin 浮窗则自动记住当前几何

### Fixed
- 修复英文 `Unsaved Changes` 对话框按钮文案溢出、说明文字截断与中英文对齐失衡的问题，让警告 icon、文案区与按钮区更稳定
- 修复未 Pin 浮窗在自动扩展或手动 resize 后覆盖 `overlay_width` / `overlay_height` 的问题；未 Pin 状态现在每次新请求都会从已保存的默认尺寸重新起算
- 修复浮窗 runtime resize 会污染设置表单、触发未保存提示的问题；未 Pin 的临时几何不再被当成需要保存的默认值
- 修复 Pin 浮窗在 runtime 几何尚未载入时无法可靠沿用持久化尺寸的问题
- 补上 Pin 几何持久化、未 Pin 尺寸回退、overlay dialog 排版与 release workflow 的回归测试

## [0.9.5] - 2026-04-05

### Added
- 新增统一的应用图标资源目录 `app/assets/icons/`，收敛原始 icon、多尺寸 PNG 与 Windows `.ico`，让运行期与打包流程共用同一套图标资产
- 新增 `docs/images/screenshots/` 与 README 界面预览区块，补上主窗口与翻译浮窗的浅色 / 深色效果图展示
- 新增 GitHub Actions `release-build.yml`，支持手动触发或推送 `v*` tag 自动打包，并只发布版本化 ZIP（GitHub 自带 source code 压缩包）
- 新增 `.signpath/` 预留结构与 SignPath artifact configuration，为后续 GitHub Trusted Build / 自动签名流程预先铺路

### Changed
- 打包流程改为正式采用 `OCRTranslator.spec` + `build_exe.bat` 分工，把 PyInstaller datas / excludes / icon 设置收敛到 `.spec` 管理
- `build_exe.bat` 现在会自动清理 `.venv` 中残留的 `~ip` 类 pip metadata、支持 `BUILD_NO_PAUSE` / `BUILD_SKIP_PIP_INSTALL`，并以更适合自动化的方式驱动打包
- 主窗口、应用级 window icon、系统托盘与打包输出的 exe icon 现在统一使用外部图标资源；冻结运行期也会通过 `resource_path()` 正确读取 `_MEIPASS` 内资源
- 打包文档补上 GitHub Actions / SignPath 接入说明，并同步更新版本化 ZIP 示例到 `v0.9.5`

### Fixed
- 修复 `build_exe.bat` 用 `for /f` 读取 `APP_VERSION` 时的引号解析问题，避免脚本在读版本号阶段提前失败
- 修复打包期 `Ignoring invalid distribution ~ip` 类 warning，降低虚拟环境残留 metadata 对本地与 CI 打包流程的干扰
- 补上应用图标资产与 Release workflow 配置的回归测试

## [0.9.4] - 2026-04-05

### Added
- 新增退出 watchdog、非阻塞错误对话框 fallback 与 crash log 保险，让关闭流程与运行期错误多一层最后防线
- 新增系统托盘右键菜单的浅色 / 深色主题样式，避免菜单背景与文字对比错位

### Changed
- 屏幕框选流程改为在后台执行截图，但仍保留原始 PNG bytes 直送图片请求，兼顾响应速度与主窗口流畅度
- Pin 状态下的结果浮窗现在会在截图、选字与手动输入流程中保留原本的位置与尺寸；截图期间仅暂时隐藏，完成后会直接按既有几何状态恢复
- Pin 按钮改为更接近 Material 风格的 pushpin icon 与更低存在感的 toggle state，主窗口表面阴影也同步收敛到更轻的层次

### Fixed
- 降低全局快捷键 listener、录制 listener 与退出清理流程导致程序卡住、`X` / 托盘退出失效的风险
- 强化 `handle_error()` 的递归保护、错误提示回退与 crash log 记录，降低错误处理本身再次崩溃的风险
- 修复浅色模式下系统托盘右键菜单背景过深、文字难以辨识的问题
- 修复极端情况下空的 `api_profiles` / `prompt_presets` 配置可能导致运行期索引错误的问题
- 补上后台截图、Pin 几何保留、系统托盘主题、退出 watchdog 与配置自愈相关回归测试

## [0.9.3] - 2026-04-04

### Added
- 新增翻译浮窗自动扩展的顶部 / 底部安全边距设置，并纳入“界面与进阶”区块，可按桌面与 Taskbar 习惯微调
- 新增共用 `message_boxes.py`，统一消息框的按钮语义、危险操作确认、Escape 行为与可选 Escape Hatch（`prefer_native` / `preserve_initial_focus`）

### Changed
- 翻译浮窗透明度改为只影响表面背景，不再让翻译文字跟着变淡；透明度 chip 可直接输入，`+ / -` 步进改为 5，topbar hover 会暂时回到 100% 不透明
- 翻译浮窗 Pin 按钮改为更直觉的图钉 icon，并保留 tooltip 与可访问名称
- 自动扩展高度上限改为可更贴近 Taskbar，但仍始终保留可调安全间距，不会自动直接贴住 Taskbar
- 删除 Profile / Prompt Preset 的确认框改为明确动词按钮（取消 / 删除…），降低 `Yes / No` 语义不清的风险
- 进阶设置字段顺序调整：将浮窗边距移到最下方，并补齐浮窗自动扩展安全边距的命名

### Fixed
- 修复深色模式下编辑输入框、数字字段时，选中文字可能变成黑色而难以辨识的问题
- 修复翻译浮窗与确认对话框初始焦点过亮、偶发白框，以及取消按钮关闭后延迟清理焦点导致的错误 log
- 补上浮窗透明度、对话框 helper、可调安全边距与深色选取前景的回归测试

## [0.9.2] - 2026-04-04

### Added
- 新增页头的三态主题快速切换（跟随系统 / 浅色 / 深色），点击后会立即应用并自动保存
- 新增页头工作摘要中的快捷键总览，会同时显示截图、选字与输入框三种快捷键

### Changed
- 将原本藏在高级设置中的主题下拉框改为页头分段切换，并重整页头信息架构
- 重新整理设置页与侧边栏排版：微调品牌区、导航区、开始使用区、使用提示与作者信息的文字脊线、间距与层级
- 微调页头标题、说明与摘要文字的节奏，将当前配置 / 方案 / 语言 / 模式 / 快捷键改为更容易扫读的两行 metadata
- 针对英文界面额外压缩 sidebar 文案、调整栏宽策略并收敛 Author / Repo metadata，降低滚动与换行压力
- 打包文档中的版本化压缩包示例同步更新到 `v0.9.2`

### Fixed
- 修正深色模式下页头快捷键摘要对比不足、阅读感偏弱的问题
- 修正页头快捷键信息与下方内容区之间留白过大，让分隔线与内容区过渡更紧凑
- 修正英文侧边栏因文案与 metadata 过长导致的拥挤与易出现内部滚动的问题

## [0.9.1] - 2026-04-04

### Added
- 新增图片请求链路耗时日志，会记录 `capture / request / total / png`，便于定位本地截图、上传或模型响应哪一段偏慢
- 新增 Windows 可执行文件版本资源生成脚本，打包后的 exe 现在会带有 Product / File Version / Company 等元数据
- 新增版本化发布压缩包输出，`build_exe.bat` 会自动创建 `OCRTranslator-v<version>-windows-x64.zip`
- 新增可选代码签名打包流程，支持 PFX 证书、证书存储 Thumbprint / Subject Name 与签名验证

### Changed
- 屏幕框选现在会在完成截图后直接把原始 PNG bytes 送入图片请求链路，不再先做缩图或额外图像预处理
- 截图预览改为在图片请求启动后非阻塞更新，让翻译请求更早开始
- 启动流程改为下一拍主动唤醒主窗口；单实例转发协议增加换行分隔与 ACK，降低启动后只剩托盘或主窗口没被带到前台的概率
- 翻译浮窗显示时新增 Windows 原生 topmost 兜底，提升结果浮窗不被普通窗口遮挡的稳定性
- 打包文档同步补齐版本资源、签名参数、时间戳与建议发布附件格式

### Fixed
- 修复全局快捷键对修饰键释放事件的抑制不平衡问题，降低 `Shift / Ctrl / Win` 看起来被卡住的风险
- 新增快捷键状态重同步保险：如果释放事件丢失，后续键盘事件会按真实物理按键状态清理内部 pressed state
- 补上单实例 ACK、浮窗 topmost、图片直送 PNG、快捷键卡键防护等回归测试

## [0.9.0] - 2026-04-04

### Added
- 定义应用程序版本号 `v0.9.0`，并显示在主窗口标题与侧边栏底部
- 新增主界面与托盘中的截图 / 输入框快捷入口
- 保留“选中文本”功能，但改回以全局快捷键作为主要入口
- 新增 `app/hotkey_utils.py`，统一快捷键切分、修饰键判断与正规化规则
- 新增 `app/crash_handling.py`，把 crash hook 初始化逻辑抽成共用入口
- 新增 `requirements-dev.txt` 与多语言文档版本
- 新增 `浅色 / 深色 / 跟随系统` 三态主题设置与 `theme_mode` 配置字段
- 新增 `SelectedTextCaptureSession`，用事件循环驱动非阻塞的选中文本抓取流程，并支持抓取阶段取消

### Changed
- 优化设置界面：加入网格布局 50:50 栏宽等比锁定，解决多语言文字长度不一造成的排版跑版问题
- 优化侧边栏界面：放宽宽度限制并调整高度策略，解决英文界面下长单词与多行文字被裁切或挤压的问题
- 优化侧边栏排版：微调组件间距、缩小次要信息字体大小（11px），并加入底部留白，提供更精致舒适的视觉与呼吸空间
- 引入零宽度空格字符（`&#8203;`）处理仓库链接的自然换行，提升多语言排版的灵活性
- 设置表单校验改为按操作场景拆分，避免 Fetch Models / Test API / 文字请求被无关字段阻塞
- API Test 的 stale result 判断现在会纳入模型名称
- 内建提示词方案改为不可删除，避免重启后被自动补回造成语义不一致
- 选中文本流程改为非阻塞抓取：等待热键释放、剪贴板 settle 与剪贴板轮询都改由 Qt 定时器分阶段推进，不再同步卡住主窗口
- `取消当前操作` 现在可以中止选中文本抓取阶段，API 重试退避等待期间也会更快响应取消
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
- 基于“亲密性原则”优化设置页面空间排版，拉大无关联区块间的间距 (32px)、缩小强关联选项内的间距 (10px)，提升视觉层次感与呼吸空间
- 为翻译结果悬浮视窗 (Translation Overlay) 的右下角加入半透明的“缩放把手 (Resize Grip)”SVG 图标，增加拖曳缩放的视觉直觉性 (Affordance)
- 优化无障碍焦点状态 (Focus States)，菜单按钮与输入框在获得焦点时会给予更明确的底色提亮与主题色外框，提升键盘操作的视觉反馈

### Fixed
- 修正“取消当前操作”和“删除”共用危险色的语义错位，改为 warning / danger 分离
- 修正 `保存设置`、`打开输入框`、disabled 与 validation 状态在浅色主题下容易混淆的问题
- 修正选中文本翻译会连续弹出两个 tray 气泡的问题，现在只会在真正发出请求时显示一次 processing 通知
- 修正 pinned 结果浮窗在换屏、拔掉副屏或分辨率变化后可能恢复到可视区域外的问题
- 修正 `load_config()` 会把配置迁移错误误判成坏配置并重建 config 的问题
- 补上选中文本 async 流程、取消行为与浮窗位置夹回逻辑的回归测试
