# Contributing

繁體中文｜[简体中文](../docs/CONTRIBUTING.zh-CN.md)｜[English](../docs/CONTRIBUTING.en.md)

感謝你對 OCRTranslator 的關注。

這個專案目前仍以個人主導維護為主，但歡迎透過 issue 與 pull request 提出修正與建議。為了降低溝通成本，請先閱讀下列規則。

參與本專案前，請先閱讀並遵守 [Code of Conduct](CODE_OF_CONDUCT.md)。

## 開發原則

- 先維持目前 UI 的整體風格與操作方向，不要任意推翻版型
- 優先修正真實可重現問題，再處理風格性調整
- 不要提交包含 API Key、個人設定或本機生成資料的檔案
- 對設定結構的改動，請考慮舊版 `config.json` 的遷移相容性
- 若調整架構，請盡量維持 `ui / services / providers / platform` 的分層邊界

## 依賴更新與自動合併

- 僅 Dependabot 在本倉庫建立、目標為 `main` 的 pip PR 可進入自動合併判斷。
- 只有 `Pillow`、`requests`、`pynput` 的穩定 patch 更新列入白名單；實際 diff 必須只調高 `requirements.txt` 的最低修補版本或 `constraints.txt` 中對應的固定修補版本。若兩檔一起修改，同套件的目標版本必須一致。
- minor / major、PySide6、PyInstaller、GitHub Actions、簽章與發布流程變更一律人工審核；安全更新也不繞過此限制。
- 合併前必須通過 `test` 與 `windows-package`，且分支需與 `main` 保持最新。CI 打包不使用簽章憑證，也不發布 Release。
- 特權自動化只讀取 PR 的中繼資料與 diff，執行的是 base commit 上的政策程式，不執行 PR 程式碼、不安裝 PR 依賴。
- 每次 PR 更新都重新判斷，先撤銷舊的自動合併要求。此流程不會自動提交 Approve 審核，也不會繞過必要檢查。

新增白名單套件或放寬版本範圍需要人工審核政策與測試。若需調整有問題的套件版本，更新程式以支援新版，而不是跳過驗證。

## 純文件修改

- `main` 仍要求 PR；只修改根目錄 README／CHANGELOG、`docs/` 下 Markdown、`docs/images/` 下點陣展示圖片或 `.github/` 直屬 Markdown 時，CI 僅檢查本地文件連結與圖片路徑，不安裝應用依賴、不跑 Windows 測試或打包。
- 修改程式、依賴、workflow、政策程式或 `packaging/windows/README.md` 等打包內容時，仍執行完整測試與 Windows 打包。手動執行 CI 也保留完整檢查。
- `ci-required` 彙總關卡必須成功；純文件路徑的 `windows-package` 會顯示為跳過，而不是打包成功。
- 倉庫擁有者在本倉庫建立、目標為 `main` 的非草稿純文件 PR，會於必要檢查通過後自動合併。外部 PR 仍需人工決定；更新 PR 時會撤銷舊的自動合併要求並重新判斷。

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
