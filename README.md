# OCRTranslator

繁體中文｜[简体中文](docs/README.zh-CN.md)｜[English](docs/README.en.md)

[![CI](https://github.com/Lianye-Scythe/OCRTranslator/actions/workflows/ci.yml/badge.svg)](https://github.com/Lianye-Scythe/OCRTranslator/actions/workflows/ci.yml)

OCRTranslator 是一款以 **桌面即時閱讀** 為核心的 **便攜式 OCR / AI 請求工具**。

它不是單純的截圖翻譯器，而是一個圍繞三種入口打造的桌面 AI 工作台：

1. **螢幕框選**：把截圖交給多模態模型做 OCR / 翻譯 / 解答 / 潤色
2. **選取文字**：擷取目前選取的文字，直接走文字請求
3. **手動輸入**：打開輸入框，把一段內容直接送給 AI

## 特色總覽

- 支援 **截圖 / 選取文字 / 手動輸入** 三種請求入口
- 支援 **Prompt Preset** 方案系統
- 內建四組預設方案：
  - `翻譯 (Translate)`
  - `解答 (Answer)`
  - `潤色 (Polish)`
  - `OCR 原文 (Raw OCR)`
- 支援多個 API Profile
- 支援 `Gemini Compatible` / `OpenAI Compatible`
- 支援多 Key 輪替與失敗重試
- 支援 `淺色 / 深色 / 跟隨系統` 三態主題切換
- 結果浮窗支援：
  - 複製、圖釘固定 / 取消固定
  - 只調整表面背景的透明度（文字保持清晰）
  - 直接輸入透明度百分比
  - 拖曳移動與角落拖曳改尺寸
  - `Ctrl + 滑鼠滾輪` 縮放字體
- 設定頁改為「連線與模型 → 翻譯方式與快捷鍵 → 介面與進階」三段式流程，降低第一次使用的理解成本
- 進階設定新增浮窗自動擴展頂部 / 底部安全邊距，可依桌面與 Taskbar 習慣調整自動擴展的極限
- 截圖請求現在會在完成框選後直接送出原始 PNG bytes，縮短從截圖到浮窗出現的等待時間
- 截圖流程改為在背景執行截圖，同時保留原始 PNG bytes 直送圖片請求，降低主視窗被同步截圖拖慢或卡住的風險
- 執行日誌會額外標記 `capture / request / total / png` 耗時，方便排查是本地處理慢還是模型端慢
- 全域快捷鍵加入修飾鍵釋放配對與狀態重同步保險，降低 `Shift / Ctrl / Win` 卡鍵體感
- 訊息框與危險操作確認現在共用一致的按鈕語義、焦點行為與 Escape 路徑
- 選取文字流程改為非阻塞擷取；真正送出請求時才會顯示一次 processing 通知，並支援在擷取階段取消
- Pin 結果浮窗現在會在截圖、選字與手動輸入流程中保留原本的位置與尺寸；截圖期間僅暫時隱藏，完成後直接以既有狀態恢復
- 系統匣右鍵選單與 Pin 按鈕狀態現在會跟隨淺色 / 深色主題，並持續以較低存在感的 Material 風格呈現
- 退出流程新增 watchdog 與錯誤提示 fallback，降低程式因錯誤或第三方 hook 狀態而無法正常關閉的風險
- 支援全域快捷鍵、系統匣、單實例保護
- 設定檔預設保存在專案根目錄 / exe 同層，維持便攜

## 預設快捷鍵

當 `config.json` 不存在或欄位缺失時，預設快捷鍵如下：

| 動作 | 預設快捷鍵 |
|---|---|
| 螢幕框選 | `Shift + Win + X` |
| 選取文字 | `Shift + Win + C` |
| 手動輸入 | `Shift + Win + Z` |

> 實際使用時仍以你的 `config.json` 為準。

## 快速開始

### 1. 安裝依賴

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

如果你還需要打包或維護開發工具：

```bash
pip install -r requirements-dev.txt
```

### 2. 啟動應用

#### 方式 A：推薦雙擊啟動

直接執行：

- `start.bat`

它會自動：

1. 檢查 `.venv`
2. 按需安裝執行依賴
3. 透過 `launcher.pyw` 啟動 GUI
4. 啟動期若出錯，優先顯示錯誤對話框

#### 方式 B：命令列啟動

```bash
python launcher.pyw
```

或：

```bash
python -m app.main
```

#### 方式 C：要求既有實例直接進入截圖

```bash
python -m app.main --capture
```

支援參數：

- `--capture`
- `/capture`
- `capture`

## 使用流程

### 1. 先完成目前設定檔的連線與模型測試

設定頁現在會優先引導你完成「連線與模型」區塊，至少需填寫：

- Provider
- Base URL
- API Keys
- Model

建議順序：

1. 選擇或新增一個 API Profile
2. `Fetch Models`
3. `Test API`
4. `Save Settings`

等連線完成後，再視需求補上：

- Target Language
- Global Hotkeys
- Prompt Preset
- Overlay 偏好
- Theme / UI Language

### 2. 從三種入口發起請求

你可以透過這些入口觸發：

- 主畫面的 `Start Capture`
- 主畫面的 `Open Input Box`
- 選取文字快捷鍵
- 托盤選單中的截圖 / 輸入框入口
- 對應的全域快捷鍵
- 選取文字快捷鍵在擷取期間不會再同步卡住主視窗；若擷取尚未完成，也可用 `取消目前操作` 中止
- `--capture` 啟動參數

### 3. 查看結果

- 截圖流程會在 `Preview & Log` 頁面顯示最近一次預覽
- 結果會以浮窗形式顯示在原文附近或觸發點附近
- 近期版本的圖片請求日誌會額外輸出 PNG 大小與 `capture / request / total` 耗時，方便確認性能瓶頸
- 執行過程會寫入記憶體日誌，可在介面中查看或匯出

## Prompt Preset

每組方案都包含：

- `image_prompt`
- `text_prompt`

支援變數：

- `{target_language}`

文字模式會把正文自動附加到提示詞後方，因此你只需要維護「指令部分」。

### 內建方案

| 方案 | 用途 |
|---|---|
| `翻譯 (Translate)` | 把圖片或文字翻譯成目標語言 |
| `解答 (Answer)` | 對題目、問題、說明直接作答或解釋 |
| `潤色 (Polish)` | 把文字改寫成更自然流暢的目標語言 |
| `OCR 原文 (Raw OCR)` | 只回傳 OCR 原文，不翻譯、不潤色 |

> 內建方案不可直接刪除；若要做可刪除版本，建議先複製成自訂方案。

## 設定檔

預設設定檔位置：

- `config.json`

路徑規則：

- 原始碼模式：專案根目錄
- 打包 exe：exe 所在目錄

主要保存內容：

- Target Language / UI Language
- Theme Mode
- 三組全域快捷鍵
- Overlay 字型 / 字級 / 透明度 / Pin / 預設尺寸
- 是否按 X 最小化到系統匣
- 目前啟用的 API Profile
- 目前啟用的 Prompt Preset
- 所有 Profiles / Presets

參考範例：

- `config.example.json`

> `config.json` 可能包含 API Keys 與私有 Base URL，請勿直接分享。

## 托盤、單實例與錯誤處理

### 單實例

應用會用鎖檔與本地 server 保證單實例。

重複啟動時：

- 普通啟動：喚回既有主視窗
- `--capture`：喚回既有實例並直接開始截圖

### 托盤

托盤選單提供：

- 顯示主視窗
- 開始截圖
- 開啟輸入框
- 取消目前操作
- 退出程式

> 「選取文字」流程更適合透過全域快捷鍵觸發。
> 因為一旦從主視窗或托盤點擊，焦點通常會被本程式搶走，反而破壞外部應用原本的選取狀態。

預設情況下，右上角 `X` 會直接退出程式。
若希望 `X` 改成最小化到系統匣，可在設定頁啟用對應選項。

### 日誌與 Crash Log

- 執行日誌預設只保存在記憶體中
- 最多保留最近 100 筆
- 可從介面匯出

若程式遇到未處理例外，會在根目錄或 exe 同層生成：

```text
ocrtranslator-crash-YYYYMMDD-HHMMSS-xxxxxxxxx.log
```

## 測試與檢查

執行測試：

```bash
python -m unittest discover -v
```

基本編譯檢查：

```bash
python -m compileall app tests launcher.pyw
```

## 文檔導覽

- [文件總覽](docs/index.md)
- [架構說明](docs/architecture.md)
- [開發指南](docs/development.md)
- [打包與發佈](docs/packaging.md)
- [貢獻指南](CONTRIBUTING.md)
- [安全性回報](SECURITY.md)
- [變更記錄](CHANGELOG.md)

## 已知邊界

- 辨識與輸出品質高度依賴所接入的多模態模型
- 目前不內建離線 OCR 引擎
- 選取文字流程採用「模擬複製並盡量還原剪貼簿」策略，少數應用可能不響應標準複製行為
- 工程與啟動腳本主要面向 Windows 使用情境
- 浮窗定位以「盡量不遮擋閱讀」為優先，而非嚴格排版系統
- 執行日誌預設不做長期審計保存

## License

目前倉庫中尚未提供明確的 `LICENSE` 檔案。
若之後要公開發佈並接受更多外部協作，建議補上：

- `LICENSE`
- 版本策略
- Release 說明
- 截圖或 GIF 展示
