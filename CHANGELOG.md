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
- 新增 `app/providers/`、`app/services/`、`app/platform/windows/`、`app/settings_service.py`、`app/settings_models.py` 等模組，將 Provider、工作流、平台能力與設定規則進一步解耦
- 新增 `tests/test_hotkey_listener.py`、`tests/test_settings_service.py`，補強快捷鍵衝突與設定快照服務測試

### Changed
- 翻譯結果浮窗支援角落拖曳調整大小，並持久化浮窗尺寸
- README 重新整理，補充三種請求入口、預設快捷鍵、提示詞方案與最新專案結構
- 預設快捷鍵調整為：
  - 截圖：`Shift+Win+X`
  - 選取文字：`Shift+Win+C`
  - 手動輸入：`Shift+Win+Z`
- 主視窗現在以協調層為主，截圖、請求、浮窗呈現與 log store 轉由 service 層處理
- `ApiClient` 改為統一處理重試 / Key 輪替 / Provider 調度，OpenAI 與 Gemini payload / response 細節拆到 adapter
- UI 樣式改為獨立 QSS 資源檔，並由 PyInstaller 一併打包
- README、CONTRIBUTING、SECURITY、PR 模板與 CI 驗證命令已同步更新

### Fixed
- 修復快捷鍵錄製時 `Shift` / `Win` 組合不穩定的問題
- 修復快捷鍵錄製時尾字母重複輸入的問題
- 修復選取文字快捷鍵可能把最後一個字母打回原視窗的問題
- 修復選取文字請求缺少托盤提示的問題
- 修復 `eventFilter` 在部分快速啟動時提前存取熱鍵欄位而導致崩潰的問題
- 修復快捷鍵儲存成功但實際註冊失敗時的狀態不一致問題
- 修復 `Ctrl+X` / `Ctrl+Shift+X` 類型快捷鍵互相包含時可能重複觸發的問題
- 修復單一 API Key 認證失敗時仍重複對同一個 Key 無意義重試的問題
- 修復選取文字流程在外部剪貼簿已變更時強制覆蓋舊內容的風險
- 修復 crash log 可能直接暴露完整本機路徑與敏感參數的問題
