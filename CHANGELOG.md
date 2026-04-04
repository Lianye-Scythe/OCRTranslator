# Changelog

繁體中文｜[简体中文](docs/CHANGELOG.zh-CN.md)｜[English](docs/CHANGELOG.en.md)

本檔案用來記錄 OCRTranslator 的重要變更。

## Unreleased

### Added
- 新增主介面與托盤中的截圖 / 輸入框快捷入口
- 保留「選取文字」功能，但改回以全域快捷鍵作為主要入口
- 新增 `app/hotkey_utils.py`，統一快捷鍵切分、修飾鍵判斷與正規化規則
- 新增 `app/crash_handling.py`，把 crash hook 安裝邏輯抽成共用入口
- 新增 `requirements-dev.txt` 與多語系文檔版本
- 新增 `淺色 / 深色 / 跟隨系統` 三態主題設定與 `theme_mode` 設定欄位

### Changed
- 設定表單校驗改為依操作場景拆分，避免 Fetch Models / Test API / 文字請求被無關欄位阻塞
- API Test 的 stale result 判斷現在會納入模型名稱
- 內建提示詞方案改為不可刪除，避免重啟後被自動補回造成語義不一致
- 設定頁資訊架構改為「連線與模型 → 翻譯方式與快捷鍵 → 介面與進階」，強化先完成連線再開始使用的主路徑
- UI 主題 token 重構為偏 Material Design 方法論的語義色彩系統，讓主按鈕、次按鈕、導航 selected、badge、warning / danger 狀態各自有明確角色
- 主視窗、結果浮窗與框選遮罩共用同一套主題角色，深色 / 淺色樣式與執行期切換邏輯一併收斂
- README 改為繁體中文預設版，並補上簡體中文與英文版本
- `docs/` 下的架構、開發與打包文檔補齊三語版本
- 非 QSS 的 UI 色彩常數開始收斂到 `app/ui/theme_tokens.py`

### Fixed
- 修復選取文字或手動輸入流程會被圖片提示詞、快捷鍵等無關欄位阻塞的問題
- 清理未使用的 `app/constants.py` 與未被呼叫的 `ApiClient.translate_image()`
- 修正 `取消目前操作` 與 `刪除` 動作共用危險色的語義錯置，改以 warning / danger 分離處理
- 修正 `儲存設定`、`開啟輸入框`、disabled 與 validation 狀態在淺色主題下容易混淆的問題

## Earlier work

先前版本已完成這些基礎能力：

- Prompt Preset 系統與四組內建方案
- 選取文字與手動輸入入口
- Provider adapter 分層（OpenAI / Gemini compatible）
- `services / providers / platform / settings_service` 模組化拆分
- i18n locale 資源外置
- 背景請求取消、stale result 保護與執行期日誌
- PyInstaller 打包、CI、協作與安全文檔
