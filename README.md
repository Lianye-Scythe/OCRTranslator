# OCRTranslator

繁體中文｜[简体中文](docs/README.zh-CN.md)｜[English](docs/README.en.md)

[![CI](https://github.com/Lianye-Scythe/OCRTranslator/actions/workflows/ci.yml/badge.svg)](https://github.com/Lianye-Scythe/OCRTranslator/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/Lianye-Scythe/OCRTranslator)](https://github.com/Lianye-Scythe/OCRTranslator/releases/latest)
[![Platform](https://img.shields.io/badge/platform-Windows-0078D6)](docs/FAQ.md)
[![License](https://img.shields.io/badge/license-GPLv3-4F46E5)](LICENSE)

Windows 便攜式 OCR／AI 翻譯工具：框選螢幕、擷取選取文字或手動輸入，透過你設定的模型服務處理內容，並以浮窗顯示結果。

## 下載與需求

**[下載最新 Windows 版本](https://github.com/Lianye-Scythe/OCRTranslator/releases/latest)**

- 下載 Assets 中的 `OCRTranslator-v<版本>-windows-x64.zip`，不要選 GitHub 自動產生的 `Source code`。
- 解壓縮整個 ZIP，再執行 `OCRTranslator.exe`。打包版**不需要安裝 Python**。
- 需自行準備 Gemini 或 OpenAI 相容服務的 API Key；使用服務可能產生費用。
- 目前 Windows 發布包**尚未數位簽署**。請從官方 Releases 下載，可用同頁的 `SHA256SUMS.txt` 核對 ZIP；校驗值不等於數位簽章。

從原始碼執行或開發：請見 [開發指南](docs/development.md)，使用 Python 3.15。WSL 可用於開發與測試；操作 Windows 截圖／全域快捷鍵請在 Windows 執行，亦可透過 `start_wsl.bat` 直接使用 WSL 原始碼。

## 介面預覽

![主視窗：繁體中文、深色主題](docs/images/screenshots/main-window-dark.png)

更多淺色介面、結果浮窗與操作示意：[介面展示](docs/gallery.md)。

## 第一次使用

1. 在「連線與模型」選擇 Gemini 相容或 OpenAI 相容格式。
2. 確認 Base URL，填入自己的 API Key，選擇模型；圖片請求需使用支援圖片輸入的模型。
3. 使用「取得模型（Fetch Models）」與「測試 API（Test API）」檢查連線，再儲存設定。
4. 選擇目標語言與提示詞方案，例如「翻譯」。
5. 按「開始框選截圖」、使用選字快捷鍵，或按「開啟輸入框」發起請求。

Gemini 預設模型為 `gemini-flash-lite-latest`。模型可用性、支援參數與實際輸出仍由你接入的服務決定。

### 預設快捷鍵

| 動作 | 快捷鍵 |
|---|---|
| 框選截圖 | `Shift + Win + X` |
| 選取文字 | `Shift + Win + C` |
| 手動輸入 | `Shift + Win + Z` |

快捷鍵可自行調整；少數應用可能不支援模擬複製，選字擷取不一定適用所有程式。

## 核心功能

- 截圖、選取文字、手動輸入三種入口。
- 翻譯、解答、潤色、OCR 原文四組內建提示詞方案，也可自訂。
- Gemini／OpenAI 相容 API、多組連線設定、多 Key 輪替與失敗重試。
- 流式顯示結果；後端不支援時可回退非流式。
- 可拖曳、縮放、固定與複製的結果浮窗，支援字級及背景透明度調整。
- 思考程度與溫度設定；預設沿用模型溫度，可依模型支援程度自訂。
- 淺色／深色／跟隨系統主題、繁中／簡中／英文介面；Markdown 結果排版可於進階設定啟用，預設關閉。

## 資料、限制與升級

- 選取的圖片或文字會送往**你設定的 API 服務**。請先確認服務的費用、資料保存及隱私政策，不要提交無權分享的內容。
- 不內建離線 OCR 或模型服務；辨識、翻譯品質與內容限制取決於所選模型。提示詞不能保證模型一定辨識正確或一定完成請求。
- 設定通常存於 exe 同層的 `config.json`，可能包含 API Key；請勿公開分享。無法在該位置建立設定時，會回退至使用者設定目錄，詳見 [FAQ](docs/FAQ.md)。
- 升級前備份 `config.json`；建議解壓新版到獨立目錄，再自行帶入原設定。不要用 `config.example.json` 覆蓋個人設定。
- 發生閃退可查看程式所在目錄下的 `logs/`，回報前請檢查並移除敏感內容。

## 文件與協作

[FAQ](docs/FAQ.md) · [文件總覽](docs/index.md) · [開發指南](docs/development.md) · [打包與發布](docs/packaging.md) · [變更記錄](CHANGELOG.md)

[回報問題](https://github.com/Lianye-Scythe/OCRTranslator/issues/new/choose) · [貢獻指南](.github/CONTRIBUTING.md) · [安全性回報](.github/SECURITY.md) · [支援](.github/SUPPORT.md) · [行為準則](.github/CODE_OF_CONDUCT.md)

本專案採用 [GPLv3](LICENSE) 授權。
