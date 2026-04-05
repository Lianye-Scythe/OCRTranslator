# Support

繁體中文｜[简体中文](docs/SUPPORT.zh-CN.md)｜[English](docs/SUPPORT.en.md)

這份文件說明 OCRTranslator 目前建議的提問、回報與聯繫方式。

## 先看哪些文件

建立 issue 或寄信前，建議先依序查看：

- [README](README.md)
- [FAQ](docs/FAQ.md)
- [Contributing](CONTRIBUTING.md)
- [Security Policy](SECURITY.md)
- [Changelog](CHANGELOG.md)

## 一般使用問題

如果是：

- 安裝 / 啟動問題
- 設定方式
- 支援的 provider / Base URL 類型
- 選取文字、截圖、浮窗等使用方式

請先查看 [FAQ](docs/FAQ.md) 與 [README](README.md)。

## Bug 回報

如果你確認是可重現的程式錯誤，請使用 GitHub Issues 的 bug template，並盡量附上：

- 重現步驟
- 執行方式（原始碼 / 打包 exe）
- 作業系統與 Python 版本
- 關鍵 log / crash log 片段
- 若有 UI 問題，附上截圖或短影片

## 功能建議

如果你想提出：

- 新功能
- UI / UX 改進
- API / Provider 支援建議
- 打包 / 發佈流程建議

請使用 GitHub Issues 的 feature request template。

## 安全問題

如果內容涉及：

- API Key
- 私有 Base URL
- 可重放請求
- 敏感 log
- 可被濫用的弱點細節

請不要公開發 issue，請改寄：`po12017po@gmail.com`

主旨建議可使用：`[OCRTranslator Security] <簡短摘要>`

## 討論區狀態

目前倉庫的 GitHub Discussions 已關閉。

因此目前建議的對外入口為：

- 一般問題 / bug / 功能建議：GitHub Issues
- 敏感安全問題：Email

## 版本與下載

公開版本請以 GitHub Releases 頁面為準：

- https://github.com/Lianye-Scythe/OCRTranslator/releases

目前公開 Windows 發佈包仍屬 **未簽名** 狀態；Release 會附上 `SHA256SUMS.txt` 供手動校驗，正式代碼簽名流程仍在規劃中。
