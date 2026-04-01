# OCRTranslator

一個可對螢幕任意文字區域做 OCR 與翻譯的桌面工具。

## 現況

專案 UI 已改為 **PySide6 / Qt Widgets**，並開始做第一輪現代化風格重構。

目前方向：

- 主視窗改成更有層次的深色桌面工具風格
- 新增 hero card 與快速操作區
- 設定頁調整為雙欄卡片布局
- monitor 頁面改成大預覽 + 右側 log 面板
- 翻譯浮窗補上陰影與更清楚的分層

## 目前功能

- 框選螢幕任意區域截圖
- 將截圖送給 Gemini / OpenAI 相容多模態 API 做 OCR + 翻譯
- 不限制來源語言，交由模型直接辨識並翻譯成目標語言
- 翻譯結果以浮窗顯示在截圖區域對側
- 支援兩種定位模式：
  - `book_lr`：適合左右閱讀情境，截右側顯示在左邊，截左側顯示在右邊
  - `web_ud`：適合上下閱讀情境，截上半顯示在下方，截下半顯示在上方
- 支援全域快捷鍵觸發截圖
- 支援最小化到 System Tray（系統匣）
- 主視窗右上角 `X` 會直接退出程式
- System Tray 點擊可快速還原主視窗
- 主視窗與系統匣共用同一套程式圖示
- UI 可切換繁體中文 / English
- 支援多個 API 設定檔、模型列表拉取、API 測試
- 同一個 URL 可設定多個 API Key，自動輪循與重試
- API Key 預設遮罩顯示，可用眼睛按鈕切換顯示
- 模型下拉選單會隱藏 `models/` 前綴，顯示更乾淨
- 相容格式改為唯讀下拉選單，不再可自由輸入
- 內建最近 100 條記憶體 log 顯示，不落地保存
- 翻譯浮窗支援自訂字型與字級
- 可在翻譯浮窗內使用 `Ctrl + 滑鼠滾輪` 即時放大 / 縮小字體

## 安裝

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## 專案結構

```text
OCRTranslator/
├─ app/                    # 主程式碼
│  ├─ main.py              # 程式入口，處理單實例與啟動流程
│  ├─ config_store.py      # 設定檔讀寫、遷移、原子保存
│  ├─ api_client.py        # Gemini / OpenAI 相容 API 呼叫
│  ├─ profile_utils.py     # provider / model / key 正規化工具
│  ├─ workers.py           # 背景工作執行與 Qt bridge
│  └─ ui/                  # PySide6 UI 元件
│     ├─ main_window.py            # 主視窗流程編排
│     ├─ main_window_layout.py     # 主視窗布局、樣式、按鈕/圖示建構
│     ├─ main_window_profiles.py   # 設定檔表單、保存、切換邏輯
│     ├─ overlay_positioning.py    # 翻譯浮窗尺寸與定位策略
│     ├─ selection_overlay.py      # 截圖框選浮層
│     └─ translation_overlay.py    # 翻譯結果浮窗
├─ tests/                  # 最小可用測試
│  ├─ test_config_store.py # 設定遷移與欄位正規化測試
│  └─ test_api_client.py   # API 錯誤解析與回應格式測試
├─ launcher.pyw            # GUI 啟動包裝器，負責顯示啟動錯誤
├─ start.bat               # 建議的雙擊啟動入口
├─ build_exe.bat           # 打包腳本，輸出 release\
├─ config.example.json     # 公開分享用設定範本
├─ README.md               # 專案說明
└─ requirements.txt        # Python 依賴
```

- `.limcode/`：本輪設計與實作過程留下的設計/計畫文件，屬於開發輔助資料。
- `config.json`：你的本機設定檔，預設放在專案根目錄 / exe 同層，不進版控，可能包含 API key。

## 設定檔與敏感資訊

- `config.json` 會保存你本機的 API key 與個人使用偏好
- 預設位置就是專案根目錄 / exe 同層：`config.json`
- 這樣整個資料夾可直接搬移、打包、備份，維持便攜式使用方式
- 若把整個 `release\` 資料夾拷到另一台電腦，`config.json` 也可一起帶走
- 建議把程式放在可寫入的普通資料夾中使用；若放到 `Program Files` 之類受保護目錄，可能無法更新 `config.json`

- `config.json` 已加入 `.gitignore`，不會進版控
- 提供 `config.example.json` 當公開/分享用範本
- 若要給別人使用，請只提供 `config.example.json` 或讓程式首次啟動自動生成空白 `config.json`


## 測試

```bash
python -m unittest discover -v
```

## 啟動方式

### 方式 1：命令列

```bash
python -m app.main
```

### 方式 2：雙擊直接啟動

直接雙擊：

- `start.bat`

> 現在主要的雙擊入口已改成 `start.bat`。它會自動檢查 `.venv` 與依賴，並透過 `launcher.pyw` 啟動；若啟動時有例外，也會跳出錯誤視窗，而不是靜默閃退。
>
> 程式已加入單實例保護；若你重複雙擊，第二份不會再真的啟動，而是會通知並喚回已經開啟的主視窗。

你也可以直接用：

- `launcher.pyw`

但一般建議優先雙擊 `start.bat`。

## 打包 exe

雙擊：

- `build_exe.bat`

打包完成後會重新建立 `release\` 發行資料夾，輸出位置：

- `release\OCRTranslator.exe`

### 打包注意

- `release\README.md` 與 `release\config.example.json` 會由打包腳本自動從根目錄複製
- 打包後程式會以 exe 所在目錄作為設定檔根目錄
- 也就是說，分享給別人時可以選擇不附帶 `config.json`，讓對方首次啟動自行建立
- 若你需要真正的便攜包，也可以把 `config.json` 一起放在 exe 同層打包帶走


## API 管理

- 預設提供一個 `Default Gemini` 設定檔
- 預設 URL：`https://generativelanguage.googleapis.com`
- 預設模型：`models/gemini-3.1-flash-lite-preview`
- `API Keys` 欄位可每行放一個 key
- `Fetch Models`：拉取模型列表並回填到目前表單
- `Test API`：驗證 URL / API key 是否可用，結果會寫到 log 區
- `Retry Count` / `Retry Interval`：控制失敗後的自動重試次數與秒數
- 模型顯示會自動去掉 `models/` 前綴，但儲存時仍保留完整模型名稱
- `Fetch Models` / `Test API` 會使用目前表單內容進行請求，不會再偷偷幫你存檔
- 若表單仍有未儲存變更，切換設定檔或退出時會提示你先儲存 / 捨棄

## 翻譯浮窗顯示

- 可在 `閱讀與翻譯設定` 中調整：
  - `翻譯字型 / Translation Font`
  - `翻譯字級 / Translation Font Size`
- 浮窗會依據文字內容長度與字級自動估算寬高
- 浮窗會優先保持在原文對側，降低遮擋原文的機率
- 已顯示浮窗時，可直接用 `Ctrl + 滑鼠滾輪` 即時縮放字體

## Release 包

若要分享給他人，建議提供：

- `release\OCRTranslator.exe`
- `release\config.example.json`
- `release\README.md`

不要提供：

- 你的 `config.json`
- 你的 `.venv`
- 開發過程產生的 `build/`、`dist/`、`*.spec`

## 接下來的 UI 方向

第一輪已先把基礎視覺往現代化方向推進；下一輪還可以繼續做：

- 自訂左側 navigation rail
- 更精緻的卡片層次與顏色系統
- 翻譯浮窗 pin / copy / opacity 控制
- Qt 化的錯誤彈窗與更多細緻互動
