# Contributing

感謝你對 OCRTranslator 的關注。

這個專案目前以個人主導維護為主，但仍歡迎透過 issue 與 pull request 提出修正與建議。為了降低溝通成本，請先閱讀下列規則。

## 開發原則

- 先維持目前 UI 的整體風格與操作方向，不要任意推翻版型。
- 優先修正真實可重現問題，再處理風格性調整。
- 不要提交包含 API Key、個人設定或本機生成資料的檔案。
- 對設定結構的改動，請考慮舊版 `config.json` 的遷移相容性。
- 若調整架構，請盡量維持 `ui / services / providers / platform` 的分層邊界，不要把流程邏輯重新塞回 UI 類別。

## 建議流程

1. Fork / 建立分支
2. 完成修改
3. 執行：
   - `python -m unittest discover -v`
   - `python -m compileall app tests launcher.pyw`
4. 補充必要的 README 或註解
5. 送出 Pull Request

## Commit 建議

建議讓 commit 訊息直接描述變更目的，例如：

- `Fix overlay position reset after font zoom`
- `Add crash log persistence for unhandled exceptions`
- `Polish settings sidebar metadata card`

## Pull Request 建議

PR 內容最好至少包含：

- 變更摘要
- 驗證方式
- 風險說明
- 若有 UI 變更，附上截圖或簡短說明
- 若有架構調整，請說明分層邊界改動（例如 `services`、`providers`、`platform`）

## Issue 回報建議

建立 bug issue 時，請盡量附上：

- 重現步驟
- 執行方式（原始碼 / exe）
- 作業系統與 Python 版本
- 執行紀錄
- crash log（若程式有寫出）

## 專案分層簡述

- `app/ui/`：Qt 視圖、表單綁定與互動元件
- `app/services/`：主流程編排、浮窗呈現、截圖與 log store
- `app/providers/`：Provider adapter，負責 payload / response 細節
- `app/platform/windows/`：Windows 平台專屬能力（快捷鍵、選取文字）
- `app/settings_service.py` / `app/settings_models.py`：設定快照、規則校驗與 candidate config 建構

## 不建議直接提交的內容

- `config.json`
- `.venv/`
- `build/`
- `dist/`
- `release/`
- `ocrtranslator-crash-*.log`
