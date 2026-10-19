# OCRTranslator — Windows ZIP

## 繁體中文

1. 解壓整個 ZIP 後執行 `OCRTranslator.exe`，不需要安裝 Python。
2. 選擇 Gemini 相容或 OpenAI 相容格式，確認 Base URL、填入自己的 API Key 並選擇模型。
3. 使用「取得模型」及「測試 API」確認連線，再儲存設定。圖片請求需支援圖片輸入的模型。
4. 選擇目標語言及方案，按「開始框選截圖」或「開啟輸入框」。

預設快捷鍵：截圖 `Shift + Win + X`；選取文字 `Shift + Win + C`；輸入框 `Shift + Win + Z`。

圖片／文字會送往你設定的 API 服務，可能產生費用，並受該服務的資料保存及內容政策約束。不內建離線 OCR 或模型服務。

設定通常存於 exe 同層的 `config.json`，可能包含 API Key，請勿公開分享。升級前備份設定；建議使用獨立目錄再帶入原設定，不要用 `config.example.json` 覆蓋個人設定。若設定目錄無法建立檔案，可能使用使用者目錄的設定，請參閱 FAQ。閃退日誌位於程式目錄的 `logs/`，回報前請移除敏感資料。

## English

1. Extract the entire ZIP and run `OCRTranslator.exe`. Python is not required.
2. Choose Gemini Compatible or OpenAI Compatible, check the Base URL, enter your own API key, and select a model.
3. Use Fetch Models and Test API, then save settings. Image requests need an image-capable model.
4. Choose a target language and preset, then start a capture or open the input box.

Default hotkeys: capture `Shift + Win + X`; selected text `Shift + Win + C`; manual input `Shift + Win + Z`.

Images/text go to your configured API service, may incur charges, and are subject to its retention and content policies. No offline OCR engine or model service is bundled.

Settings normally live in `config.json` next to the executable and may contain API keys. Do not share it publicly. Back up settings before upgrading; use a separate directory and bring over your configuration. Do not overwrite it with `config.example.json`. If settings cannot be created there, a user-directory fallback may be used; see the FAQ. Crash reports are in `logs/` under the app directory; remove sensitive data before reporting them.

## 简体中文

1. 解压整个 ZIP 后运行 `OCRTranslator.exe`，不需要安装 Python。
2. 选择 Gemini 兼容或 OpenAI 兼容格式，确认 Base URL，填入自己的 API Key 并选择模型。
3. 使用“获取模型”和“测试 API”确认连接，再保存设置。图片请求需要支持图片输入的模型。
4. 选择目标语言和方案，开始框选截图或打开输入框。

默认快捷键：截图 `Shift + Win + X`；选中文本 `Shift + Win + C`；输入框 `Shift + Win + Z`。

图片／文本会发送至你配置的 API 服务，可能产生费用，受其数据保存和内容政策约束。不内置离线 OCR 或模型服务。

设置通常保存在 exe 同目录的 `config.json`，可能包含 API Key，请勿公开分享。升级前备份设置，建议使用独立目录再迁移原设置，不要用 `config.example.json` 覆盖个人设置。若无法在该目录创建设置，可能使用用户目录中的设置，详见 FAQ。崩溃日志位于程序目录的 `logs/`，反馈前请移除敏感信息。

## 下載與校驗 / Downloads and verification / 下载与校验

目前公開版本未簽署；請從官方 Releases 下載 ZIP 與 `SHA256SUMS.txt`，比較 ZIP 的 SHA256。校驗值不是數位簽章。
Current public releases are unsigned. Download the ZIP and `SHA256SUMS.txt` from official Releases and compare the ZIP's SHA256. A checksum is not a digital signature.
目前公开版本未签名，请从官方 Releases 下载 ZIP 与 `SHA256SUMS.txt` 并比较 ZIP 的 SHA256；校验值不等于数字签名。

```powershell
Get-FileHash .\OCRTranslator-v*-windows-x64.zip -Algorithm SHA256
```

`BUILD-INFO.json` records the app version, source commit when available, Python, platform, and installed package versions used for this build. It is a build inventory, not a dependency lockfile or a guarantee of byte-for-byte reproducibility.

## 線上文件 / Online documentation / 在线文档

- [Releases](https://github.com/Lianye-Scythe/OCRTranslator/releases/latest)
- [繁體中文](https://github.com/Lianye-Scythe/OCRTranslator/blob/main/README.md) · [English](https://github.com/Lianye-Scythe/OCRTranslator/blob/main/docs/README.en.md) · [简体中文](https://github.com/Lianye-Scythe/OCRTranslator/blob/main/docs/README.zh-CN.md)
- [FAQ 繁體中文](https://github.com/Lianye-Scythe/OCRTranslator/blob/main/docs/FAQ.md) · [FAQ English](https://github.com/Lianye-Scythe/OCRTranslator/blob/main/docs/FAQ.en.md) · [FAQ 简体中文](https://github.com/Lianye-Scythe/OCRTranslator/blob/main/docs/FAQ.zh-CN.md)
- [Report an issue](https://github.com/Lianye-Scythe/OCRTranslator/issues/new/choose)
- [Security reporting](https://github.com/Lianye-Scythe/OCRTranslator/blob/main/.github/SECURITY.md)

License: GPLv3; see the included `LICENSE` file.
