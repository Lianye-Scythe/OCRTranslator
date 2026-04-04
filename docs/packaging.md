# 打包與發佈

繁體中文｜[简体中文](packaging.zh-CN.md)｜[English](packaging.en.md)

## 一鍵打包

直接執行：

- `build_exe.bat`

腳本會自動：

1. 建立或檢查 `.venv`
2. 安裝 `requirements-dev.txt`
3. 清理舊的 `build/`、`dist/`、`release/`
4. 透過 PyInstaller 輸出 `release\OCRTranslator.exe`
5. 複製 `README.md` 與 `config.example.json`

## 建議分發內容

```text
release\OCRTranslator.exe
release\README.md
release\config.example.json
```

## 不建議分發的內容

```text
config.json
.venv\
build\
dist\
*.spec
```

## 執行期路徑

- 原始碼執行：根目錄保存 `config.json` 與 crash log
- exe 執行：exe 同層保存 `config.json` 與 crash log

這讓應用維持便攜，方便整包搬移、備份與分發。
