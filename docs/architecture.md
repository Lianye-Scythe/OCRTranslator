# 架構說明

繁體中文｜[简体中文](architecture.zh-CN.md)｜[English](architecture.en.md)

這份文件補回較完整的「專案結構與檔案職責」說明，方便後續維護時快速定位每個模組的用途。

## 核心分層

OCRTranslator 目前主要分成這幾層：

- `app/ui/`：Qt 視圖、表單綁定、浮窗與互動元件
- `app/services/`：工作流編排、背景任務、托盤、單實例、預覽與浮窗呈現
- `app/providers/`：OpenAI / Gemini 相容 API 的 payload / response adapter
- `app/platform/windows/`：Windows 專屬能力，例如全域快捷鍵與選取文字
- `app/settings_service.py` / `app/settings_models.py`：設定快照、純規則校驗與 candidate config 建構
- `app/api_client.py`：重試、Key 輪替、Provider 調度與統一錯誤處理

## 主要執行路徑

1. `app/main.py`
   - 應用入口
   - 單實例鎖
   - 已啟動實例的動作轉發
2. `app/ui/main_window.py`
   - 主視窗協調層
   - 串接 UI、services、tray、instance server
3. `app/services/request_workflow.py`
   - 三種請求入口的工作流編排
4. `app/services/background_task_runner.py`
   - 背景 worker 生命週期與 stale task 保護
5. `app/services/overlay_presenter.py`
   - 浮窗尺寸、位置與重排邏輯
6. `app/settings_service.py`
   - 表單快照校驗
   - candidate config 建構

## 詳細專案結構

```text
OCRTranslator/
├─ .github/
│  ├─ ISSUE_TEMPLATE/
│  │  ├─ bug_report.yml              # Bug 回報模板
│  │  ├─ config.yml                  # GitHub issue 模板設定
│  │  └─ feature_request.yml         # 功能需求模板
│  ├─ workflows/
│  │  └─ ci.yml                      # CI：跑 unittest 與 compileall
│  └─ PULL_REQUEST_TEMPLATE.md       # Pull Request 檢查清單
│
├─ app/
│  ├─ __init__.py                    # app 套件標記
│  ├─ api_client.py                  # 統一 API 呼叫、Key 輪替、重試與 Provider 調度
│  ├─ app_defaults.py                # 預設 Provider / URL / 模型 / 快捷鍵 / theme mode / 顯示值
│  ├─ app_metadata.py                # 作者與倉庫 metadata
│  ├─ config_store.py                # config.json 載入、遷移、儲存、損壞恢復
│  ├─ crash_handling.py              # 共用 crash hook 安裝與錯誤對話框入口
│  ├─ crash_reporter.py              # crash log 生成、脫敏、落盤
│  ├─ default_prompts.py             # 內建 Prompt Preset 定義與名稱正規化
│  ├─ hotkey_listener.py             # 舊入口 facade，轉發到 platform/windows/hotkeys.py
│  ├─ hotkey_utils.py                # 快捷鍵切分、修飾鍵判斷、正規化共用工具
│  ├─ i18n.py                        # locale 載入、語言正規化、系統語言偵測
│  ├─ main.py                        # GUI 啟動主入口、單實例控制、capture 轉發
│  ├─ models.py                      # AppConfig / ApiProfile / PromptPreset 資料結構（含 theme mode）
│  ├─ operation_control.py           # 取消 token、RequestContext、操作錯誤包裝
│  ├─ profile_utils.py               # Provider / 模型值正規化與字串工具
│  ├─ prompt_utils.py                # Prompt 模板渲染與文字請求包裝
│  ├─ runtime_paths.py               # 根目錄、鎖檔、server 名稱、config 路徑
│  ├─ selected_text_capture.py       # 舊入口 facade，轉發到 platform/windows/selected_text.py
│  ├─ settings_models.py             # 設定表單快照與驗證結果模型
│  ├─ settings_service.py            # 設定校驗規則、不同操作 scope 驗證、candidate config 建構
│  ├─ workers.py                     # 背景執行緒與 Qt signal bridge
│  │
│  ├─ locales/
│  │  ├─ en.json                     # 英文 UI 文案
│  │  ├─ zh-CN.json                  # 簡體中文 UI 文案
│  │  └─ zh-TW.json                  # 繁體中文 UI 文案
│  │
│  ├─ platform/
│  │  └─ windows/
│  │     ├─ hotkeys.py               # Windows 全域快捷鍵低階監聽與衝突判定
│  │     └─ selected_text.py         # Windows 選取文字擷取、剪貼簿保存與還原
│  │
│  ├─ providers/
│  │  ├─ __init__.py                 # 匯出可用 Provider adapter
│  │  ├─ gemini_compatible.py        # Gemini Compatible API adapter
│  │  └─ openai_compatible.py        # OpenAI Compatible API adapter
│  │
│  ├─ services/
│  │  ├─ background_task_runner.py   # 背景 worker 執行、錯誤回傳、stale result 保護
│  │  ├─ image_capture.py            # 螢幕截圖、跨螢幕 fallback、預覽圖生成
│  │  ├─ instance_server.py          # 單實例喚回與 capture 轉發 server
│  │  ├─ operation_manager.py        # 背景操作 task id / 取消 / stale 狀態管理
│  │  ├─ overlay_presenter.py        # 結果浮窗尺寸、位置與重排控制
│  │  ├─ request_workflow.py         # capture / selected text / manual input 三流程編排
│  │  ├─ runtime_log.py              # 記憶體中的執行日誌 store
│  │  └─ system_tray.py              # 系統匣建立、更新與動作綁定
│  │
│  └─ ui/
│     ├─ __init__.py                 # UI 套件標記
│     ├─ main_window.py              # 主視窗協調層，整合 mixin 與 service 呼叫
│     ├─ main_window_layout.py       # 主殼層版面、workspace surface、導航、button variant 與樣式套用
│     ├─ main_window_profiles.py     # Profile 表單綁定、驗證呈現、快捷鍵錄製
│     ├─ main_window_prompts.py      # Prompt Preset 表單邏輯與內建 preset 保護
│     ├─ main_window_settings_layout.py # workflow-first Settings 版面（連線 / 翻譯 / 進階）
│     ├─ focus_utils.py              # 共用滑鼠點擊後焦點清理與安全 clearFocus 工具
│     ├─ message_boxes.py            # 共用訊息框 helper、危險操作確認與 Escape Hatch
│     ├─ overlay_positioning.py      # 浮窗定位、尺寸與螢幕邊界計算
│     ├─ prompt_input_dialog.py      # 手動輸入文字請求對話框
│     ├─ selection_overlay.py        # 全螢幕框選覆蓋層
│     ├─ style_utils.py              # 依 theme name 載入並快取 QSS / theme token 渲染結果
│     ├─ theme_tokens.py             # Material 風格語義色彩角色、相容別名與 QSS token
│     ├─ translation_overlay.py      # 結果浮窗本體與互動邏輯
│     │
│     └─ styles/
│        ├─ main_window.qss          # 主視窗樣式
│        └─ translation_overlay.qss  # 結果浮窗樣式
│
├─ docs/
│  ├─ index.md                       # 文件總覽（繁中）
│  ├─ index.zh-CN.md                 # 文件總覽（簡中）
│  ├─ index.en.md                    # 文件總覽（英文）
│  ├─ architecture.md                # 架構說明（繁中）
│  ├─ architecture.zh-CN.md          # 架構說明（簡中）
│  ├─ architecture.en.md             # 架構說明（英文）
│  ├─ development.md                 # 開發指南（繁中）
│  ├─ development.zh-CN.md           # 開發指南（簡中）
│  ├─ development.en.md              # 開發指南（英文）
│  ├─ packaging.md                   # 打包與發佈（繁中）
│  ├─ packaging.zh-CN.md             # 打包與發佈（簡中）
│  ├─ packaging.en.md                # 打包與發佈（英文）
│  ├─ README.zh-CN.md                # README 的簡中鏡像版
│  ├─ README.en.md                   # README 的英文鏡像版
│  ├─ CONTRIBUTING.zh-CN.md          # Contributing 的簡中鏡像版
│  ├─ CONTRIBUTING.en.md             # Contributing 的英文鏡像版
│  ├─ SECURITY.zh-CN.md              # Security 的簡中鏡像版
│  ├─ SECURITY.en.md                 # Security 的英文鏡像版
│  ├─ CHANGELOG.zh-CN.md             # Changelog 的簡中鏡像版
│  └─ CHANGELOG.en.md                # Changelog 的英文鏡像版
│
├─ tests/
│  ├─ __init__.py                    # tests 套件標記
│  ├─ test_api_client.py             # ApiClient、Provider response、重試與 Key 輪替測試
│  ├─ test_config_store.py           # config 遷移、損壞恢復、預設值測試
│  ├─ test_crash_reporter.py         # crash log 生成與脫敏測試
│  ├─ test_hotkey_listener.py        # 快捷鍵衝突與優先匹配測試
│  ├─ test_i18n.py                   # locale key 對齊與語言正規化測試
│  ├─ test_main_window_runtime.py    # 主視窗執行期狀態與保存回滾測試
│  ├─ test_operation_manager.py      # OperationManager 的 task / cancel / stale 邏輯測試
│  ├─ test_overlay_positioning.py    # 浮窗位置與尺寸計算測試
│  ├─ test_prompt_presets_runtime.py # 內建 Prompt Preset 刪除保護測試
│  ├─ test_prompt_utils.py           # Prompt 模板渲染與文字包裝測試
│  ├─ test_request_workflow.py       # request workflow 的簽名與關鍵規則測試
│  ├─ test_selected_text_capture.py  # 選取文字剪貼簿工具函式測試
│  └─ test_settings_service.py       # 設定 scope 驗證與 candidate config 測試
│
├─ .gitignore                        # 忽略 venv、build、release、config 與 log
├─ build_exe.bat                     # Windows 一鍵打包腳本
├─ CHANGELOG.md                      # 變更記錄（繁中預設版）
├─ config.example.json               # 設定檔範例
├─ config.json                       # 本機執行設定（runtime 產物，不應提交）
├─ CONTRIBUTING.md                   # 協作與貢獻指南（繁中預設版）
├─ launcher.pyw                      # GUI 啟動器
├─ README.md                         # 專案說明（繁中預設版）
├─ requirements-dev.txt              # 開發 / 打包依賴
├─ requirements.txt                  # 執行期依賴
├─ SECURITY.md                       # 安全性回報說明（繁中預設版）
└─ start.bat                         # Windows 一鍵啟動腳本
```

## 維護建議

目前這套結構的目標是：

- 根目錄保持乾淨，只保留預設語言與實際入口檔案
- 其他語言文件集中到 `docs/`
- `app/` 內維持 `ui / services / providers / platform` 的邊界
- 減少把工作流直接塞回 UI 類別

如果後續還要再整理，可優先考慮：

- 將 `app/ui/main_window_*` 再進一步收斂成更明確的 UI 子模組
- 視需要把 `start.bat` / `build_exe.bat` 收到 `scripts/`，但那會一起影響使用與文件入口
