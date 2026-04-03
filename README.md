# OCRTranslator

[![CI](https://github.com/Lianye-Scythe/OCRTranslator/actions/workflows/ci.yml/badge.svg)](https://github.com/Lianye-Scythe/OCRTranslator/actions/workflows/ci.yml)

OCRTranslator 是一款以 **桌面即時閱讀** 為核心的 **便攜式 OCR / AI 請求工具**。它不只支援框選螢幕後直接交給多模態模型完成 OCR 與翻譯，也支援把**目前選取文字**或**手動輸入內容**直接送給 AI，並使用可切換的提示詞方案輸出翻譯、解答或潤色結果。

它的設計目標很明確：

- **盡量不打斷閱讀節奏**
- **把操作入口集中到桌面快捷鍵**
- **保持便攜式設定與可擴充架構**
- **以現有 UI 為基礎持續迭代，而不是推倒重做**

---

## 這次更新重點

目前版本相較早期版本，已經不再只是單一的「截圖翻譯器」，而是擴充成一個更完整的桌面 AI 工作台。

### 新增 / 強化能力
- 翻譯浮窗支援**角落拖曳調整大小**
- 新增**選取文字快捷鍵**，可直接送出當前選取內容
- 新增**手動輸入快捷鍵**，可呼叫輸入框直接向 AI 發送請求
- 新增**提示詞方案系統**，支援保存多組圖片 / 文字提示詞
- 內建四組預設方案：`翻譯 (Translate)` / `解答 (Answer)` / `潤色 (Polish)` / `OCR 原文 (Raw OCR)`
- 選取文字流程會**盡量保留原剪貼簿內容**
- 快捷鍵錄製與全域快捷鍵處理已補強 `Shift` / `Win` 組合
- 會主動阻止互相包含的快捷鍵組合，避免 `Ctrl+X` / `Ctrl+Shift+X` 類型衝突

---

## 專案定位

OCRTranslator 不是傳統的「先本地 OCR、再送到另一個翻譯服務」的雙階段工具。

它目前的主要使用方式有三種：

1. **框選螢幕區域** → 把圖片交給多模態模型處理
2. **擷取目前選取文字** → 直接把文字交給模型處理
3. **開啟輸入框手動輸入** → 把內容交給模型處理

再搭配提示詞方案，讓同一套流程可被用來：

- 翻譯
- 解題 / 解答
- 潤色
- 其他自定義文字處理需求

---

## 功能特色

### 1. 三種請求入口

| 入口 | 說明 |
|---|---|
| 螢幕框選 | 擷取任意區域，交給模型做 OCR + 翻譯 / 解答 / 潤色 |
| 選取文字 | 擷取目前選取文字，直接用文字模式送出請求 |
| 手動輸入 | 開啟輸入對話框，直接輸入內容送給 AI |

### 2. 可切換提示詞方案
- 內建 `翻譯 (Translate)` / `解答 (Answer)` / `潤色 (Polish)` / `OCR 原文 (Raw OCR)`
- 每組方案都包含：
  - `image_prompt`
  - `text_prompt`
- 可新增、刪除、保存自定義方案
- 目前啟用的方案會同時影響：
  - 螢幕框選請求
  - 選取文字請求
  - 手動輸入請求

### 3. 可交互的結果浮窗
- 自動盡量貼近原文或觸發點
- 支援複製結果
- 支援 Pin / 取消 Pin
- 支援透明度調整
- 支援拖曳移動
- 支援**從角落拖曳調整大小**
- 支援自訂字型與字級
- 浮窗上的 Pin / 透明度 / 字級 / 尺寸調整會同步回目前設定，需按 `Save Settings` 才會持久化到下次啟動
- 支援 `Ctrl + 滑鼠滾輪` 即時縮放字體

### 4. 多 API 設定檔管理
- 支援多個 API Profile
- 支援 `Gemini Compatible` / `OpenAI Compatible`
- 每個設定檔可獨立管理：
  - 名稱
  - Provider
  - Base URL
  - 多個 API Keys
  - 模型
  - 重試次數與間隔

### 5. 多 Key 輪替與重試
- 同一個設定檔可填入多個 API Key
- 失敗時可輪替下一個 Key
- 支援重試次數與重試間隔設定

### 6. 便攜式配置
- `config.json` 預設保存在專案根目錄 / exe 同層
- 可直接整包搬移、備份與分發
- 不依賴 AppData

### 7. 桌面整合
- 支援全域快捷鍵
- 支援 System Tray（系統匣）
- 首次啟動會依系統語言自動選擇 UI 語言，並同步帶出預設目標語言：繁中 → `zh-TW` / `繁體中文`、簡中 → `zh-CN` / `簡體中文`、其他 → `en` / `English`
- 支援單實例保護
- 長時間請求可從主視窗或托盤取消，避免卡住時只能等待
- 重複啟動可喚回主視窗，或把截圖動作轉發給既有實例

---

## 預設快捷鍵

當 `config.json` 不存在或欄位缺失時，預設快捷鍵如下：

| 動作 | 預設快捷鍵 |
|---|---|
| 螢幕框選 | `Shift + Win + X` |
| 選取文字 | `Shift + Win + C` |
| 手動輸入 | `Shift + Win + Z` |

> 實際使用時仍以你的 `config.json` 為準。

---

## 內建提示詞方案

| 方案 | 用途 |
|---|---|
| `翻譯 (Translate)` | 將圖片或文字內容翻譯成目標語言 |
| `解答 (Answer)` | 對題目、問題、說明請求直接作答或解釋 |
| `潤色 (Polish)` | 將文字改寫成更自然、更流暢的目標語言表述 |
| `OCR 原文 (Raw OCR)` | 只回傳 OCR 讀取到的文字內容，不翻譯、不潤色、不補充說明 |

提示詞模板支援 `{target_language}` 變數，文字模式會自動把輸入內容附加到請求中。

---

## 技術棧

- Python 3.11+
- PySide6
- Pillow
- requests
- pynput

安裝依賴：

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

---

## 快速開始

### 方式 1：命令列啟動

```bash
python -m app.main
```

### 方式 2：雙擊啟動（推薦）

直接雙擊：

- `start.bat`

它會自動：

1. 檢查 `.venv`
2. 補裝 `requirements.txt` 依賴
3. 透過 `launcher.pyw` 啟動 GUI
4. 若啟動期有例外，優先跳出錯誤視窗而不是靜默閃退

### 方式 3：直接啟動 GUI 包裝器

- `launcher.pyw`

一般仍建議以 `start.bat` 作為主要入口。

---

## 命令列參數

目前支援直接要求現有實例開始截圖：

```bash
python -m app.main --capture
```

可識別參數：

- `--capture`
- `/capture`
- `capture`

行為如下：

- 若尚未啟動：開啟程式並直接進入截圖
- 若已有執行中的實例：轉發「開始截圖」動作給現有實例

---

## 使用流程

### 1. 先完成 API 設定
在設定頁中填好：

- Provider
- Base URL
- API Keys
- Model
- Target Language
- Global Hotkeys
- Prompt Preset

建議依序執行：

- `Fetch Models`（可選）
- `Test API`（建議）
- `Save Settings`

### 2. 從三種入口發起請求
你可以透過以下任一方式觸發：

- 主畫面的 `Start Screen Capture`
- 托盤選單中的截圖項目
- 螢幕框選快捷鍵
- 選取文字快捷鍵
- 手動輸入快捷鍵
- 用 `--capture` 參數啟動

### 3. 查看結果
請求完成後：

- 若是截圖流程：最近一次截圖會顯示在 `Preview & Log` 頁面
- 結果會以懸浮視窗顯示在原文附近或觸發點附近
- 執行過程會記錄到記憶體日誌

### 4. 操作結果浮窗
浮窗支援：

- `Copy Result`：複製內容
- `Pin`：固定懸浮窗
- `+ / -`：調整透明度
- 滑鼠拖曳：移動位置
- 拖曳浮窗角落：調整大小
- 若要把浮窗上的 Pin / 透明度 / 字級 / 尺寸調整保存到下次啟動，請回到主視窗按 `Save Settings`
- `Ctrl + 滑鼠滾輪`：縮放字體

### 5. 切換提示詞方案
- 可在設定頁切換目前生效的提示詞方案
- 同一組方案會同時影響圖片與文字請求
- 你也可以自建更多方案來對應不同工作流

---

## 設定檔

### 位置

預設設定檔位置：

- `config.json`

路徑規則：

- 原始碼模式：專案根目錄
- 打包 exe 模式：exe 所在目錄

這代表你可以：

- 直接整個資料夾搬到另一台電腦
- 一起帶走 `config.json`
- 或不附帶 `config.json`，讓新環境首次啟動時依系統語言自動建立預設檔（同時決定 UI 語言與預設目標語言）

### 主要保存內容

目前 `config.json` 主要保存：

- 目標語言
- 顯示模式
- 三組全域快捷鍵
- 浮窗字型 / 字級 / 透明度 / 是否固定 / 關閉時是否縮到系統匣 / 預設大小
- 當前啟用的 API Profile
- 當前啟用的提示詞方案
- 全部 API Profiles
- 全部提示詞方案

可參考範例：

- `config.example.json`

### 敏感資訊提醒

`config.json` 可能包含：

- API Keys
- 私有 Base URL
- 個人偏好設定

因此倉庫已忽略：

- `config.json`
- `.venv/`
- `build/`
- `dist/`
- `release/`

如果要分享給別人，建議只提供：

- `OCRTranslator.exe`
- `README.md`
- `config.example.json`

不要直接提供你自己的 `config.json`。

---

## API 設定說明

### 支援的 Provider

#### Gemini Compatible
預設示例：

- Base URL：`https://generativelanguage.googleapis.com`
- 模型：`models/gemini-3.1-flash-lite-preview`

#### OpenAI Compatible
預設示例：

- Base URL：`https://api.openai.com`
- 模型：由使用者自行填寫或拉取

### API Keys
- `API Keys` 欄位支援每行一個 Key
- 同一個設定檔中的 Key 會自動輪替
- 某個 Key 失敗時可繼續嘗試其他 Key
- 若只剩單一 Key 且認證失敗，不會再對同一個 Key 做無意義重試

### 模型列表
- `Fetch Models` 會使用目前表單內容直接請求 API
- 成功後回填模型列表到目前表單
- Gemini 模型顯示時會隱藏 `models/` 前綴，方便閱讀
- 儲存時仍保留正規化模型值

### API 測試
- `Test API` 會用目前表單內容送出一次**極輕量的真實文字請求**，驗證實際請求鏈路
- 不會偷偷自動儲存設定
- 結果會寫入執行紀錄區；若模型沒有遵守測試提示詞，log 中會保留回覆摘要供排查

---

## 介面結構

### Settings
主要負責：

- API Profile 管理
- Provider / URL / Keys / Model 設定
- 目標語言與 UI 語言切換（`zh-TW` / `zh-CN` / `en`）
- 全域快捷鍵錄製
- 提示詞方案管理
- 翻譯字型與字級設定
- 常用操作入口

### Preview & Log
主要負責：

- 顯示最近一次截圖預覽
- 顯示最近 100 筆執行紀錄
- 從這個頁面直接重新發起截圖

### Selection Overlay
截圖時會顯示全螢幕半透明覆蓋層：

- 左鍵拖曳選取範圍
- `Esc` 或右鍵取消

### Translation Overlay
結果使用獨立無邊框置頂視窗顯示：

- 自動貼近原文或觸發位置
- 盡量降低遮擋機率
- 適合持續閱讀與對照

---

## 單實例與托盤行為

### 單實例
應用會使用鎖檔與本地 server 保證單實例。

重複啟動時：

- 普通啟動：喚回現有主視窗
- `--capture` 啟動：喚回現有實例並直接開始截圖

### 托盤
- 若請求耗時過久，可從托盤選單直接取消目前操作
- 點選 `最小化到系統匣` 後會隱藏主視窗
- 點擊托盤圖示可還原主視窗
- 托盤選單提供：
  - 顯示主視窗
  - 開始截圖
  - 退出程式

> 注意：右上角 `X` 預設仍是**直接退出程式**；若需要，也可以在設定裡改成「按 X 時最小化到系統匣」。

---

## 日誌與錯誤處理

### 執行日誌
- 僅保存在記憶體中
- 最多保留最近 100 筆
- 預設不寫入磁碟

### 設定檔損壞恢復
如果 `config.json` 解析失敗：

- 會先嘗試備份舊檔
- 備份檔命名格式：

```text
config.broken-YYYYMMDD-HHMMSS.json
```

- 接著建立新的預設設定檔

### 啟動期錯誤顯示
`launcher.pyw` 會優先使用 Qt 顯示錯誤訊息；若失敗，再退回 Tkinter；再不行才輸出到標準錯誤。

### Crash Log
若程式遇到未處理例外而異常退出，會自動在根目錄留下 crash log：

```text
ocrtranslator-crash-YYYYMMDD-HHMMSS-xxxxxxxxx.log
```

- 原始碼執行時：保存在專案根目錄
- 打包為 exe 時：保存在 exe 同層目錄
- 回報問題時建議附上 crash log，但請先確認其中沒有 API Key 等敏感資訊

---

## 打包成 exe

直接雙擊：

- `build_exe.bat`

它會自動：

1. 建立或檢查 `.venv`
2. 安裝 `requirements.txt` 與 `pyinstaller`
3. 清理舊的 `build/`、`dist/`、`release/`
4. 輸出：

```text
release\OCRTranslator.exe
```

5. 複製：
   - `README.md`
   - `config.example.json`

> 內建 QSS 樣式與 locale 資源會由 PyInstaller 一併打包，不需要額外手動複製。

### 建議分發內容

推薦：

```text
release\OCRTranslator.exe
release\README.md
release\config.example.json
```

不建議：

```text
config.json
.venv\
build\
dist\
*.spec
```

---

## 測試

執行測試：

```bash
python -m unittest discover -v
```

也可先做基本編譯檢查：

```bash
python -m compileall app tests
```

目前測試涵蓋重點包括：

- API 錯誤訊息解析
- OpenAI / Gemini 回應格式處理
- API Key 輪替與重試策略
- 設定遷移與欄位正規化
- 損壞設定檔重建
- crash log 生成與落盤
- 浮窗尺寸與定位邏輯
- 主視窗執行期值與忙碌狀態控制
- 背景操作管理、取消語義與 stale task 保護
- 儲存設定時的熱鍵註冊失敗回滾
- 快捷鍵子集衝突偵測與更具體優先匹配
- 提示詞模板組裝
- 選取文字快捷鍵相關工具函式
- 設定表單快照 / 純規則校驗 / candidate config 建構
- 設定服務層與表單快照模型

---

## 專案結構

### 解耦後的核心分層

- `app/ui/`：Qt 視圖與表單綁定
- `app/locales/`：外部 locale 資源（`zh-TW` / `zh-CN` / `en`）
- `app/services/`：主流程編排、浮窗呈現、截圖、背景 task 與桌面 runtime 服務
- `app/services/operation_manager.py`：背景操作 task / 取消 / stale result 管理
- `app/settings_service.py` / `app/settings_models.py`：設定快照、純規則校驗與 candidate config 建構
- `app/providers/`：不同 Provider 的 API payload / response adapter
- `app/platform/windows/`：Windows 平台專屬的快捷鍵與選取文字能力
- `app/api_client.py`：重試、Key 輪替、Provider 調度與統一錯誤處理

---

```text
OCRTranslator/
├─ app/
│  ├─ __init__.py
│  ├─ app_defaults.py             # 預設模型、URL、快捷鍵與 Provider 顯示定義
│  ├─ app_metadata.py             # 作者 / 倉庫 metadata
│  ├─ api_client.py               # 重試、Key 輪替與 Provider 調度
│  ├─ config_store.py              # 設定載入、遷移、儲存、損壞恢復
│  ├─ constants.py                 # 相容匯出層（整合 defaults / metadata / runtime paths）
│  ├─ crash_reporter.py            # 未處理例外 crash log 生成與落盤
│  ├─ default_prompts.py           # 內建提示詞與預設方案定義
│  ├─ hotkey_listener.py           # 舊入口 facade，轉發到 platform/windows
│  ├─ i18n.py                      # locale 資源載入、語言正規化與系統語言偵測
│  ├─ locales/                     # zh-TW / zh-CN / en locale 資源檔
│  ├─ main.py                      # 入口、單實例控制、啟動流程
│  ├─ models.py                    # AppConfig / ApiProfile / PromptPreset 資料結構
│  ├─ platform/
│  │  ├─ __init__.py
│  │  └─ windows/
│  │     ├─ __init__.py
│  │     ├─ hotkeys.py             # Windows 低階快捷鍵實作
│  │     └─ selected_text.py       # Windows 選取文字與剪貼簿邏輯
│  ├─ operation_control.py         # 背景請求取消 token / request context
│  ├─ profile_utils.py             # Provider / Model 正規化工具
│  ├─ providers/
│  │  ├─ __init__.py
│  │  ├─ gemini_compatible.py      # Gemini Compatible Adapter
│  │  └─ openai_compatible.py      # OpenAI Compatible Adapter
│  ├─ prompt_utils.py              # 提示詞模板渲染與請求文本組裝
│  ├─ runtime_paths.py             # 可攜式執行路徑、鎖檔與單實例 server 名稱
│  ├─ selected_text_capture.py     # 舊入口 facade，轉發到 platform/windows
│  ├─ services/
│  │  ├─ __init__.py
│  │  ├─ background_task_runner.py # Worker / cancellable task 協調
│  │  ├─ image_capture.py          # 螢幕擷取與預覽圖轉換
│  │  ├─ instance_server.py        # 單實例喚回與 capture 轉發
│  │  ├─ operation_manager.py      # 背景操作 task / 取消 / stale result 管理
│  │  ├─ overlay_presenter.py      # 浮窗位置、重排與字級重排服務
│  │  ├─ request_workflow.py       # 請求 / 捕獲工作流編排
│  │  ├─ system_tray.py            # System Tray 建立與更新
│  │  └─ runtime_log.py            # 執行時 log store
│  ├─ settings_models.py           # 設定表單快照與校驗結果模型
│  ├─ settings_service.py          # 設定校驗規則與 candidate config 建構
│  ├─ workers.py                   # 背景執行緒與 Qt bridge
│  └─ ui/
│     ├─ __init__.py
│     ├─ main_window.py            # 主視窗協調層（委派給 services）
│     ├─ main_window_layout.py     # 主介面版面、樣式、元件建構
│     ├─ main_window_settings_layout.py  # Settings 頁版面拆分與各 section 建構
│     ├─ main_window_profiles.py   # 設定表單綁定、UI 驗證呈現、快捷鍵錄製
│     ├─ main_window_prompts.py    # 提示詞方案表單邏輯
│     ├─ overlay_positioning.py    # 浮窗尺寸與位置計算
│     ├─ prompt_input_dialog.py    # 直接輸入文字請求的對話框
│     ├─ selection_overlay.py      # 全螢幕框選覆蓋層
│     ├─ style_utils.py            # QSS 載入工具
│     ├─ styles/
│     │  ├─ __init__.py
│     │  ├─ main_window.qss        # 主視窗樣式
│     │  └─ translation_overlay.qss # 浮窗樣式
│     └─ translation_overlay.py    # 結果懸浮窗
├─ tests/
│  ├─ __init__.py
│  ├─ test_api_client.py
│  ├─ test_config_store.py
│  ├─ test_crash_reporter.py
│  ├─ test_hotkey_listener.py
│  ├─ test_i18n.py
│  ├─ test_main_window_runtime.py
│  ├─ test_operation_manager.py
│  ├─ test_overlay_positioning.py
│  ├─ test_prompt_utils.py
│  ├─ test_selected_text_capture.py
│  └─ test_settings_service.py
├─ launcher.pyw                    # GUI 啟動器，負責啟動期錯誤提示
├─ start.bat                       # 推薦啟動入口
├─ build_exe.bat                   # Windows 打包腳本
├─ .github/                        # CI、Issue/PR 模板
├─ CONTRIBUTING.md                 # 協作與提交建議
├─ SECURITY.md                     # 安全性回報說明
├─ CHANGELOG.md                    # 重要變更紀錄
├─ config.example.json             # 設定範本
├─ requirements.txt
├─ README.md
└─ .gitignore
```

---

## 已知邊界

以下屬於目前產品設計上的已知邊界，不等於故障：

- 辨識與輸出品質高度依賴所接入的多模態模型
- 目前不內建離線 OCR 引擎
- 選取文字流程採用「模擬複製並儘量還原剪貼簿」策略，極少數應用可能不響應標準複製行為
- 工程與啟動腳本主要面向 Windows 使用情境
- 浮窗定位以「閱讀不遮擋」為主，不是嚴格排版系統
- 日誌預設只保留在記憶體，不適合做長期審計

---

## 後續方向

目前版本已具備穩定的產品基線，後續更適合沿著以下方向持續演進：

- 接入更多 Provider / 模型
- 強化文字分段、格式保留與後處理效果
- 繼續補強快捷鍵、選取文字與浮窗細節
- 擴充測試覆蓋與發佈流程
- 增加截圖 / GIF 展示與 Release 說明

---

## 開發者入口建議

如果要繼續維護，建議先從以下檔案開始閱讀：

1. `app/main.py` —— 啟動與單實例入口
2. `app/ui/main_window.py` —— 主視窗協調層，負責串接 services
3. `app/services/request_workflow.py` —— 請求 / 捕獲工作流編排
4. `app/services/operation_manager.py`、`app/services/background_task_runner.py` —— 背景操作與 worker 調度
5. `app/services/instance_server.py`、`app/services/system_tray.py` —— 單實例與桌面整合
6. `app/settings_service.py` —— 設定快照校驗與 candidate config 建構
7. `app/providers/openai_compatible.py`、`app/providers/gemini_compatible.py` —— Provider Adapter 實作

---

## GitHub 協作與治理

目前倉庫已補上較完整的協作檔案，可直接搭配 GitHub 使用：

- `.github/workflows/ci.yml` —— push / PR 自動跑測試與 compile 檢查
- `.github/ISSUE_TEMPLATE/` —— bug / feature issue 模板
- `.github/PULL_REQUEST_TEMPLATE.md` —— PR 檢查清單
- `CONTRIBUTING.md` —— 提交與協作建議
- `SECURITY.md` —— 安全性回報注意事項
- `CHANGELOG.md` —— 重要變更紀錄

---

## License

目前倉庫中尚未看到明確的 `LICENSE` 檔案。

如果之後要公開釋出、接受更多外部協作，建議補上：

- `LICENSE`
- 版本策略
- Release 說明
- 截圖或 GIF 展示

這樣整個專案會更完整。
