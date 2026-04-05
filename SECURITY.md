# Security Policy

繁體中文｜[简体中文](docs/SECURITY.zh-CN.md)｜[English](docs/SECURITY.en.md)

如果你發現 OCRTranslator 存在安全性問題，請不要直接在公開 issue 中貼出可被濫用的細節、密鑰或敏感請求內容。

## 回報原則

請至少提供：

- 問題描述
- 影響範圍
- 重現步驟
- 是否需要登入、API Key 或特定設定
- 若有 crash log，請先確認其中不包含敏感資訊

> 目前 crash log 會對部分本機路徑與常見敏感參數做基礎遮罩，但仍不應直接假設可安全公開，送出前請人工再檢查一次。

## 不要公開貼出的內容

- API Keys
- 私有 Base URL
- 使用者個人資料
- 任何可直接重放的敏感請求
- 未經檢查的完整 crash log / 執行日誌

## 建議做法

若問題可能造成敏感資訊外洩或遠端濫用，請優先以私下方式聯繫維護者，再決定是否公開揭露。

## 私下聯繫方式

- Email：`po12017po@gmail.com`
- 建議主旨可標示：`[OCRTranslator Security] <簡短摘要>`
