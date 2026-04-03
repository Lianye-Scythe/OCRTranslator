# Changelog

本檔案用來記錄 OCRTranslator 的重要變更。

格式可參考 Keep a Changelog，但目前先維持簡潔的手動維護方式。

## Unreleased

### Added
- 新增提示詞方案系統，支援多組圖片 / 文字提示詞，並內建 `翻譯 (Translate)`、`解答 (Answer)`、`潤色 (Polish)` 三組預設方案
- 新增選取文字請求入口，可透過全域快捷鍵直接處理目前選取內容
- 新增手動輸入請求入口，可快速呼叫輸入框把文字送給 AI
- 新增 `app/prompt_utils.py`、`app/selected_text_capture.py`、`app/hotkey_listener.py` 等模組，以支援更可擴充的請求管線與快捷鍵處理
- 新增 `app/locales/zh-TW.json`、`app/locales/zh-CN.json`、`app/locales/en.json`，將 UI 文案拆成外部 locale 資源檔
- 新增簡體中文 UI locale，並補上 `tests/test_i18n.py` 驗證 locale key 對齊與語言正規化
- 新增 `app/services/background_task_runner.py`、`app/services/instance_server.py`、`app/services/system_tray.py`，進一步把 `MainWindow` 的 runtime 協調職責下沉
- 新增 `tests/test_prompt_utils.py`、`tests/test_selected_text_capture.py` 測試
- 新增 `app/providers/`、`app/services/`、`app/platform/windows/`、`app/settings_service.py`、`app/settings_models.py` 等模組，將 Provider、工作流、平台能力與設定規則進一步解耦
- 新增 `tests/test_hotkey_listener.py`、`tests/test_settings_service.py`，補強快捷鍵衝突與設定快照服務測試
- 新增 `app/operation_control.py`，集中管理背景請求的取消 token 與 request session
- 新增主視窗 / 托盤取消目前操作的入口，改善長請求卡住時的可控性

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
- 浮窗上的 Pin / 透明度 / 字級 / 尺寸調整改為同步回目前設定，但需由 `Save Settings` 顯式持久化，避免與其他表單設定的保存語義不一致
- 新增 `app/services/operation_manager.py`，把背景操作 task / 取消 / stale result 判斷從 `MainWindow` 抽出，降低主視窗協調層耦合
- `i18n.py` 改為負責載入 locale 資源、語言正規化與系統語言偵測，不再維護超大內嵌字典
- 首次啟動在沒有 `config.json` 時，會依系統語言自動選擇 UI 語言，並同步帶出對應的預設目標語言：繁中 → `zh-TW` / `繁體中文`、簡中 → `zh-CN` / `簡體中文`、其他 → `en` / `English`
- 內建三組預設提示詞方案名稱改為雙語顯示，並在載入舊設定時自動把 `翻譯` / `解答` / `潤色` 遷移成 `翻譯 (Translate)` / `解答 (Answer)` / `潤色 (Polish)`

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
- 修復背景執行緒直接寫入 Qt UI log 的執行緒安全風險，改為透過 bridge signal 匯入主執行緒
- 強化 crash log / 錯誤摘要脫敏，額外覆蓋 traceback、URL query、Bearer token 與 `x-goog-api-key`
- 清理主視窗與設定頁中的遺留 helper（未使用的 upsert / wrapper 方法），縮小維護面
- 修復 Provider 標籤與 UI 語言切換對 `zh-CN` 不完整的問題，補上簡體中文 provider 顯示文案
