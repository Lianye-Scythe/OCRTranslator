# OCRTranslator

一個用來閱讀日文輕小說／網文時，邊截圖邊翻譯的桌面工具。

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
- 翻譯結果以浮窗顯示在截圖區域對側
- 支援兩種定位模式：
  - `book_lr`：適合左右雙頁，截右頁顯示在左邊，截左頁顯示在右邊
  - `web_ud`：適合上到下排版，截上半顯示在下方，截下半顯示在上方
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

## 設定檔與敏感資訊

- `config.json` 會保存你本機的 API key 與個人使用偏好
- `config.json` 已加入 `.gitignore`，不會進版控
- 提供 `config.example.json` 當公開/分享用範本
- 若要給別人使用，請只提供 `config.example.json` 或讓程式首次啟動自動生成空白 `config.json`

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

打包完成後輸出位置：

- `dist\OCRTranslator.exe`

### 打包注意

- 打包後程式會以 exe 所在目錄作為設定檔根目錄
- 也就是說，分享給別人時不需要把你的 `config.json` 一起帶上
- 使用者第一次啟動時可自行建立自己的設定

## API 管理

- 預設提供一個 `Default Gemini` 設定檔
- 預設 URL：`https://generativelanguage.googleapis.com`
- 預設模型：`models/gemini-3.1-flash-lite-preview`
- `API Keys` 欄位可每行放一個 key
- `Fetch Models`：拉取模型列表並寫回目前設定檔
- `Test API`：驗證 URL / API key 是否可用，結果會寫到 log 區
- `Retry Count` / `Retry Interval`：控制失敗後的自動重試次數與秒數
- 模型顯示會自動去掉 `models/` 前綴，但儲存時仍保留完整模型名稱

## 翻譯浮窗顯示

- 可在 `閱讀與翻譯設定` 中調整：
  - `翻譯字型 / Translation Font`
  - `翻譯字級 / Translation Font Size`
- 浮窗會依據文字內容長度與字級自動估算寬高
- 浮窗會優先保持在原文對側，降低遮擋原文的機率
- 已顯示浮窗時，可直接用 `Ctrl + 滑鼠滾輪` 即時縮放字體

## 接下來的 UI 方向

第一輪已先把基礎視覺往現代化方向推進；下一輪還可以繼續做：

- 自訂左側 navigation rail
- 更精緻的卡片層次與顏色系統
- 翻譯浮窗 pin / copy / opacity 控制
- Qt 化的錯誤彈窗與更多細緻互動
