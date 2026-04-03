# OCRTranslator

[![CI](https://github.com/Lianye-Scythe/OCRTranslator/actions/workflows/ci.yml/badge.svg)](https://github.com/Lianye-Scythe/OCRTranslator/actions/workflows/ci.yml)

OCRTranslator 是一款以**桌面即時閱讀**為核心的**便攜式 OCR 翻譯軟體**。你可以直接框選螢幕上的任意區域，將截圖交給多模態模型進行文字辨識與翻譯，並把結果以懸浮面板顯示在原文附近，適合用於漫畫、網頁、PDF、遊戲介面、文件截圖與各種桌面內容。

目前版本的 UI 已完成一輪較完整的迭代，後續功能開發會**延續現有的 UI 設計與互動方向**，在這個基礎上持續擴充，而不是重頭推翻重做。

---

## 專案定位

OCRTranslator 不是傳統的「先本地 OCR，再把文字送去另一個翻譯服務」的雙階段工具。

它目前的核心流程是：

1. 擷取你選取的螢幕區域
2. 將圖片送到 **Gemini / OpenAI 相容多模態 API**
3. 直接讓模型完成：
   - 圖中文字辨識
   - 原始語言判斷
   - 翻譯成目標語言
   - 依閱讀順序整理輸出
4. 將翻譯結果顯示在原文附近的懸浮視窗中

這讓它更適合「快速閱讀、隨手理解、盡量不打斷視線」的桌面使用情境。

---

## 目前特色

### 即時框選翻譯
- 可直接框選螢幕任意區域
- 將截圖送給多模態模型進行 OCR + 翻譯
- 不限制來源語言，由模型自行辨識
- 可自訂目標語言

### 兩種閱讀定位模式
- `book_lr`
  - 適合左右閱讀情境，例如漫畫、雙頁內容
  - 優先把翻譯浮窗放在原文左右對側
- `web_ud`
  - 適合上下閱讀情境，例如網頁、長文、聊天記錄
  - 優先把翻譯浮窗放在原文上下對側

### 多 API 設定檔管理
- 支援多個 API Profile
- 支援 `Gemini Compatible` / `OpenAI Compatible`
- 每個設定檔都可獨立設定：
  - 名稱
  - Provider
  - Base URL
  - 多個 API Keys
  - 模型
  - 重試次數與間隔

### 多 Key 輪循與重試
- 同一個設定檔可填入多個 API Key
- 請求失敗時會輪替下一個 Key
- 支援自動重試與重試間隔

### 可交互的翻譯浮窗
- 會盡量顯示在原文附近且避免遮擋
- 可複製翻譯結果
- 可 Pin / 取消 Pin
- 可調整透明度
- 可拖曳移動
- 可自訂字型與字級
- 支援 `Ctrl + 滑鼠滾輪` 即時縮放字體

### 桌面工具整合
- 支援全域快捷鍵啟動截圖
- 支援 System Tray（系統匣）
- 支援單實例保護
- 重複啟動時可喚回現有視窗或直接轉發截圖動作

### 便攜式配置
- `config.json` 預設保存在專案根目錄 / exe 同層
- 可直接整包搬移、備份與分發
- 不依賴使用者 AppData 路徑

### 工程化細節
- 損壞的 `config.json` 會自動備份後重建
- 可遷移舊版單一 API 設定格式
- 執行紀錄保存在記憶體中，不預設落地
- 提供基礎單元測試
- 提供 Windows 雙擊啟動與打包腳本

---

## 目前產品狀態

目前這個版本已經不是原型，而是一個功能閉環完整的桌面工具版本：

- 現有 UI 已可作為後續版本的設計基線
- 核心 OCR / 翻譯 / 顯示流程已可穩定使用
- 接下來更適合做的是**增量優化與功能擴充**
- 當前定位非常清楚：**便攜、快速、為閱讀體驗服務的 OCR 翻譯工作台**

---

## 功能總覽

| 模組 | 目前能力 |
|---|---|
| 螢幕擷取 | 框選任意區域，多螢幕環境下盡量依目標螢幕定位 |
| 翻譯 | 透過多模態模型直接完成 OCR + 翻譯 |
| API | 支援 Gemini / OpenAI 相容接口 |
| 設定檔 | 多 Profile 管理、切換、建立、刪除 |
| 模型管理 | 拉取模型列表、模型名稱正規化顯示 |
| 快捷鍵 | 全域快捷鍵觸發截圖 |
| 浮窗 | 複製、固定、透明度調整、拖曳、字體縮放 |
| 托盤 | 還原主視窗、托盤截圖、退出程式 |
| 配置 | 根目錄 `config.json`，便攜式保存 |
| 日誌 | 最近 100 筆執行紀錄，記憶體保存 |
| 啟動 | 單實例保護、重複啟動轉發動作 |
| 打包 | `build_exe.bat` 打包成單檔 exe |

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
4. 若啟動期有例外，跳出錯誤視窗而不是靜默閃退

### 方式 3：直接啟動 GUI 包裝器

也可以直接執行：

- `launcher.pyw`

但一般仍建議以 `start.bat` 作為主要入口。

---

## 命令列參數

支援直接要求現有實例開始截圖：

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

## 設定檔

### 位置

預設設定檔位置：

- `config.json`

路徑規則：

- 原始碼模式：專案根目錄
- 打包 exe 模式：exe 所在目錄

這代表：

- 可以整個資料夾直接搬到另一台電腦
- 可以選擇把 `config.json` 一起帶走
- 也可以不附帶 `config.json`，讓新環境首次啟動時自動建立預設檔

### 設定內容

目前 `config.json` 主要保存：

- 目標語言
- 顯示模式
- 全域快捷鍵
- 浮窗字型 / 字級 / 透明度 / 是否固定
- 當前啟用的 API Profile
- 全部 API Profiles

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

### 模型列表

- `Fetch Models` 會使用目前表單內容直接請求 API
- 成功後回填模型列表到目前表單
- Gemini 模型顯示時會隱藏 `models/` 前綴，方便閱讀
- 儲存時仍保留正規化模型值

### API 測試

- `Test API` 會用目前表單內容實際驗證連線
- 不會偷偷自動儲存設定
- 結果會寫入執行紀錄區

---

## 使用流程

### 1. 先完成 API 設定
在設定頁中填好：

- Provider
- Base URL
- API Keys
- Model
- Target Language
- Global Hotkey

然後建議依序執行：

- `Fetch Models`（可選）
- `Test API`（建議）
- `Save Settings`

### 2. 開始截圖
你可以透過以下任一方式啟動截圖：

- 主畫面的 `Start Screen Capture`
- 托盤選單中的截圖項目
- 全域快捷鍵
- 用 `--capture` 參數啟動

### 3. 查看翻譯結果
截圖完成後：

- 最近一次截圖會顯示在 `Preview & Log` 頁面
- 翻譯結果會以懸浮視窗顯示在原文旁邊
- 執行過程會記錄到記憶體日誌

### 4. 操作翻譯浮窗
浮窗目前支援：

- `Copy Result`：複製翻譯內容
- `Pin`：固定懸浮窗
- `+ / -`：調整透明度
- `Ctrl + 滑鼠滾輪`：縮放字體
- 滑鼠拖曳：移動位置

---

## 介面結構

### Settings
主要負責：

- API Profile 管理
- Provider / URL / Keys / Model 設定
- 目標語言與 UI 語言切換
- 全域快捷鍵錄製
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
翻譯結果使用獨立無邊框置頂視窗顯示：

- 自動貼近原文
- 盡量降低遮擋原文的機率
- 可維持較好的閱讀節奏

---

## 單實例與托盤行為

### 單實例
應用會使用鎖檔與本地 server 保證單實例。

重複啟動時：

- 普通啟動：喚回現有主視窗
- `--capture` 啟動：喚回現有實例並直接開始截圖

### 托盤
- 點選 `最小化到系統匣` 後會隱藏主視窗
- 點擊托盤圖示可還原主視窗
- 托盤選單提供：
  - 顯示主視窗
  - 開始截圖
  - 退出程式

> 注意：目前右上角 `X` 的行為是**直接退出程式**，不是縮到系統匣。

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
ocrtranslator-crash-YYYYMMDD-HHMMSS.log
```

- 原始碼執行時：保存在專案根目錄
- 打包為 exe 時：保存在 exe 同層目錄
- 建議回報問題時附上 crash log 內容，但請先確認其中沒有 API Key 等敏感資訊

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

執行單元測試：

```bash
python -m unittest discover -v
```

目前測試涵蓋的重點包括：

- API 錯誤訊息解析
- OpenAI / Gemini 回應格式處理
- 設定遷移與欄位正規化
- 損壞設定檔重建
- crash log 生成與落盤
- 便攜式設定讀取路徑

---

## 專案結構

```text
OCRTranslator/
├─ app/
│  ├─ __init__.py
│  ├─ api_client.py                # Gemini / OpenAI compatible API 呼叫
│  ├─ config_store.py              # 設定載入、遷移、儲存、損壞恢復
│  ├─ constants.py                 # 常數、預設值、多語系文案
│  ├─ crash_reporter.py            # 未處理例外 crash log 生成與落盤
│  ├─ main.py                      # 入口、單實例控制、啟動流程
│  ├─ models.py                    # AppConfig / ApiProfile 資料結構
│  ├─ profile_utils.py             # Provider / Model 正規化工具
│  ├─ workers.py                   # 背景執行緒與 Qt bridge
│  └─ ui/
│     ├─ __init__.py
│     ├─ main_window.py            # 主流程、截圖、翻譯、托盤、錯誤處理
│     ├─ main_window_layout.py     # 主介面版面、樣式、元件建構
│     ├─ main_window_profiles.py   # 設定表單邏輯、驗證、儲存
│     ├─ overlay_positioning.py    # 翻譯浮窗尺寸與位置計算
│     ├─ selection_overlay.py      # 全螢幕框選覆蓋層
│     └─ translation_overlay.py    # 翻譯結果懸浮窗
├─ tests/
│  ├─ __init__.py
│  ├─ test_api_client.py
│  ├─ test_crash_reporter.py
│  └─ test_config_store.py
├─ launcher.pyw                    # GUI 啟動器，負責啟動期錯誤提示
├─ start.bat                       # 推薦啟動入口
├─ build_exe.bat                   # Windows 打包腳本
├─ .github/                        # CI、Issue/PR 模板
├─ CONTRIBUTING.md                 # 協作與提交建議
├─ SECURITY.md                     # 安全性回報說明
├─ CHANGELOG.md                    # 重要變更紀錄骨架
├─ config.example.json             # 設定範本
├─ requirements.txt
├─ README.md
└─ .gitignore
```

---

## 已知邊界

以下屬於目前產品設計上的已知邊界，不等於故障：

- 辨識與翻譯品質高度依賴所接入的多模態模型
- 目前不內建離線 OCR 引擎
- 工程與啟動腳本主要面向 Windows 使用情境
- 浮窗定位以「閱讀不遮擋」為主，不是嚴格排版系統
- 日誌預設只保留在記憶體，不適合做長期審計

---

## 後續方向

目前版本已具備穩定的產品基線，後續更適合沿著這些方向繼續演進：

- 接入更多 Provider / 模型
- 增強翻譯結果後處理與分段表現
- 補強浮窗定位與操作細節
- 提升錯誤提示與可觀測性
- 擴充測試覆蓋與發布流程

整體來說，下一步不是「重新定義 UI 長什麼樣」，而是持續沿用現在這套設計系統做功能延伸與體驗打磨。

---

## 開發者入口建議

如果要繼續維護，建議先從以下檔案開始閱讀：

1. `app/main.py` —— 啟動與單實例入口
2. `app/ui/main_window.py` —— 主工作流程
3. `app/ui/main_window_profiles.py` —— 設定表單與驗證邏輯
4. `app/ui/translation_overlay.py` —— 翻譯浮窗互動
5. `app/api_client.py` —— Provider 請求實作

---

## GitHub 協作與治理

目前倉庫已補上較正式的協作檔案，可直接搭配 GitHub 使用：

- `.github/workflows/ci.yml` —— push / PR 自動跑測試與 compile 檢查
- `.github/ISSUE_TEMPLATE/` —— bug / feature issue 模板
- `.github/PULL_REQUEST_TEMPLATE.md` —— PR 檢查清單
- `CONTRIBUTING.md` —— 提交與協作建議
- `SECURITY.md` —— 安全性回報注意事項
- `CHANGELOG.md` —— 重要變更紀錄骨架

如果之後要對外發布版本，建議開始固定維護 `CHANGELOG.md`。

---

## License

目前倉庫中尚未看到明確的 License 檔案。

如果之後要公開釋出、讓其他人協作，建議補上：

- `LICENSE`
- 版本策略
- Release 說明
- 截圖或 GIF 展示

這樣整個專案會更完整。
