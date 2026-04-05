# 開發指南

繁體中文｜[简体中文](development.zh-CN.md)｜[English](development.en.md)

## 環境準備

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

如需打包或維護開發工具：

```bash
pip install -r requirements-dev.txt
```

## 常用命令

### 啟動應用

```bash
python launcher.pyw
```

或：

```bash
python -m app.main
```

### 設定檔路徑提示

原始碼執行時，程式會優先使用專案根目錄的 `config.json`；若根目錄沒有設定檔且目前目錄不可寫，則會自動回退到：

- Windows：`%LOCALAPPDATA%\OCRTranslator\config.json`
- 其他環境 fallback：`~/.ocrtranslator/config.json`

排查本機設定問題時，請同時確認便攜設定檔與 fallback 設定檔是否有其中一份正在生效。

### 執行測試

```bash
python -m unittest discover -v
```

### 基本編譯檢查

```bash
python -m compileall app tests launcher.pyw
```

## 測試重點

目前測試涵蓋重點包含：

- API 錯誤訊息解析與 Provider 適配
- 設定遷移與損壞恢復
- crash log 生成與脫敏
- 快捷鍵衝突判定
- 浮窗定位邏輯
- 主視窗執行期狀態控制
- 設定快照校驗與 candidate config 建構
- Prompt preset 與請求工作流關鍵規則

## 提交前建議

1. 跑完 `python -m unittest discover -v`
2. 跑完 `python -m compileall app tests launcher.pyw`
3. 若涉及打包流程，再確認 `pip install -r requirements-dev.txt`
4. 檢查是否誤提交：
   - `config.json`
   - `.venv/`
   - `build/`
   - `dist/`
   - `release/`
   - `ocrtranslator-crash-*.log`
   - `ocrtranslator-log-*.txt`
