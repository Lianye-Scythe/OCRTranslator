## TODO LIST

<!-- LIMCODE_TODO_LIST_START -->
- [ ] 更新 README 與驗證啟動/語法  `#docs_verify`
- [ ] 實作第一輪現代化 UI 視覺優化  `#modern_ui_impl`
- [x] 規劃更有質感的現代化 PySide6 UI 方向  `#modern_ui_plan`
- [ ] 建立可雙擊啟動的 start.bat 並更新啟動入口  `#rename_launcher`
<!-- LIMCODE_TODO_LIST_END -->

# PySide6 現代化 UI 與啟動入口計畫

## 目標
1. 提供可雙擊直接啟動的 `start.bat`
2. 將目前 Qt 主介面往更有質感的現代化桌面工具風格推進
3. 保持現有 OCR / 翻譯 / tray / 快捷鍵功能不回退

## 實作拆分

### 1. 啟動入口
- 新增 `start.bat` 作為主要雙擊入口
- 保留 `launcher.pyw` 當實際 Python 啟動包裝器
- README 改為以 `start.bat` 為主說明
- 視需要移除或停用舊的中文 bat 入口，避免雙入口混淆

### 2. 主視窗現代化
- 新增 hero card 作為第一視覺焦點
- 將高頻操作放到 hero 區與快速操作卡
- 調整 tabs 質感與階層
- 設定頁改成左右雙欄卡片布局

### 3. Monitor 頁整理
- 讓預覽圖成為主視覺區塊
- Log 面板獨立成右側卡片
- 統一陰影、圓角、背景與輸入框樣式

### 4. 翻譯浮窗微調
- 補上陰影與更清楚的 header/body 分層
- 保持 `Ctrl + 滑鼠滾輪` 縮放與重定位

### 5. 驗證
- 更新 README 啟動說明
- 用 `py_compile` 驗證語法
- 建議後續手動驗證：雙擊啟動、tray、hotkey、capture、overlay

## 風險
- 目前 `pynput` 與 Qt 主事件迴圈並存，需要保留現有熱鍵執行方式並避免 UI thread 阻塞
- Qt 樣式表過度堆疊會讓某些控制項可讀性下降，需以可用性優先

## 本輪完成標準
- 可以雙擊 `start.bat` 啟動
- 主畫面已明顯不同於初始 Qt 過渡版
- README 與實際啟動入口一致
- 語法檢查通過
