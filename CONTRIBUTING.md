# Contributing

繁體中文｜[简体中文](docs/CONTRIBUTING.zh-CN.md)｜[English](docs/CONTRIBUTING.en.md)

感謝你對 OCRTranslator 的關注。

這個專案目前仍以個人主導維護為主，但歡迎透過 issue 與 pull request 提出修正與建議。為了降低溝通成本，請先閱讀下列規則。

參與本專案前，請先閱讀並遵守根目錄的 `CODE_OF_CONDUCT.md`。

## 開發原則

- 先維持目前 UI 的整體風格與操作方向，不要任意推翻版型
- 優先修正真實可重現問題，再處理風格性調整
- 不要提交包含 API Key、個人設定或本機生成資料的檔案
- 對設定結構的改動，請考慮舊版 `config.json` 的遷移相容性
- 若調整架構，請盡量維持 `ui / services / providers / platform` 的分層邊界

## 建議流程

1. Fork / 建立分支
2. 完成修改
3. 執行：
   - `python -m unittest discover -v`
   - `python -m compileall app tests launcher.pyw`
   - 若涉及打包腳本或發佈流程，再確認 `pip install -r requirements-dev.txt`
4. 補充必要的 README / docs 或註解
5. 送出 Pull Request
6. 若提交程式碼貢獻，預設同意該貢獻以 **GPLv3** 納入本專案

## Pull Request 建議

PR 內容最好至少包含：

- 變更摘要
- 驗證方式
- 風險說明
- 若有 UI 變更，附上截圖或簡短說明
- 若有架構調整，請說明分層邊界改動

## Issue 回報建議

建立 bug issue 時，請盡量附上：

- 重現步驟
- 執行方式（原始碼 / exe）
- 作業系統與 Python 版本
- 執行紀錄
- crash log（若程式有寫出）

## 不建議直接提交的內容

- `config.json`
- `.venv/`
- `build/`
- `dist/`
- `release/`
- `ocrtranslator-crash-*.log`
- `ocrtranslator-log-*.txt`
