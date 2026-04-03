# Changelog

本檔案用來記錄 OCRTranslator 的重要變更。

格式可參考 Keep a Changelog，但目前先維持簡潔的手動維護方式。

## Unreleased

### Added
- 新增提示詞方案系統，支援多組圖片 / 文字提示詞，並內建 `翻譯`、`解答`、`潤色` 三組預設方案
- 新增選取文字請求入口，可透過全域快捷鍵直接處理目前選取內容
- 新增手動輸入請求入口，可快速呼叫輸入框把文字送給 AI
- 新增 `app/prompt_utils.py`、`app/selected_text_capture.py`、`app/hotkey_listener.py` 等模組，以支援更可擴充的請求管線與快捷鍵處理
- 新增 `tests/test_prompt_utils.py`、`tests/test_selected_text_capture.py` 測試

### Changed
- 翻譯結果浮窗支援角落拖曳調整大小，並持久化浮窗尺寸
- README 重新整理，補充三種請求入口、預設快捷鍵、提示詞方案與最新專案結構
- 預設快捷鍵調整為：
  - 截圖：`Shift+Win+X`
  - 選取文字：`Shift+Win+C`
  - 手動輸入：`Shift+Win+Z`

### Fixed
- 修復快捷鍵錄製時 `Shift` / `Win` 組合不穩定的問題
- 修復快捷鍵錄製時尾字母重複輸入的問題
- 修復選取文字快捷鍵可能把最後一個字母打回原視窗的問題
- 修復選取文字請求缺少托盤提示的問題
- 修復 `eventFilter` 在部分快速啟動時提前存取熱鍵欄位而導致崩潰的問題
