# 開發指南

繁體中文｜[简体中文](development.zh-CN.md)｜[English](development.en.md)

## 環境準備

開發環境、CI 與 Windows 打包使用 Python 3.15，不再維護舊版 Python 的相容性。請在專案根目錄執行命令；Windows 與 WSL 的虛擬環境不能共用。

### Windows PowerShell

```powershell
py -3.15 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\Activate.ps1
```

若 PowerShell 的執行原則阻擋啟用腳本，可直接以 `.\.venv\Scripts\python.exe` 取代下方的 `python`，不必修改全域執行原則。

### Windows CMD

```bat
py -3.15 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
call .venv\Scripts\activate.bat
```

### WSL / Linux Bash

```bash
python3.15 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
source .venv/bin/activate
```

WSL 用於開發與自動化測試；完整 Windows 桌面操作請在 Windows 執行，或使用下方的 `start_wsl.bat`。不要讓 Windows 的 `start.bat` 使用 WSL 建立的 `.venv`。

啟用對應環境後，如需打包工具，執行：

```text
python -m pip install -r requirements-dev.txt
```

後續 `python` 命令皆指已啟用環境的 Python；可以用 `python --version` 與 `python -m pip --version` 確認。

## 常用命令

### 從 Windows 測試 WSL 原始碼

在檔案總管開啟 `\\wsl.localhost\Ubuntu\home\po120\Git\OCRTranslator`（依自己的發行版與路徑調整），雙擊專案根目錄的 `start_wsl.bat`。需要 Windows Python 3.15 與 `py` launcher。

腳本自動在 `%LOCALAPPDATA%\OCRTranslator\venv-win315` 建立 Windows 專用環境並依 `requirements.txt` 安裝依賴，不使用 WSL 的 `.venv`。程式關閉前請保留 console，讓 WSL 路徑映射持續有效。只驗證環境可執行 `start_wsl.bat --check`，截圖與熱鍵仍需在實際 GUI 中測試。

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

CI 依變更範圍分流：文件跑連結檢查，`docs/images/` 圖片另驗證可讀性與分享圖尺寸；僅修改分享圖產生器、其測試及文件時，只安裝固定版本的 Pillow 並執行相關測試，不打包 Windows exe。應用程式、依賴、其他工具或 CI 設定變更仍跑完整 Windows 測試與打包。分享圖工具的輕量分流不適用純文件自動合併規則。

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

## 依賴版本與更新

`requirements.txt` 自動引用根目錄的 `constraints.txt`，因此現有啟動腳本、安裝命令與 CI 都會使用相同的固定套件版本。Windows 專屬依賴不會安裝到 WSL，Linux 專屬依賴也不會安裝到 Windows；打包工具僅在安裝 `requirements-dev.txt` 時加入。

更新依賴時，調整 `constraints.txt`，必要時同步最低版本範圍，並在 Windows 與 WSL 分別安裝、執行 `python -m pip check` 和測試；涉及打包依賴時確認 Windows CI 打包成功。不要將單一環境的完整 `pip freeze` 直接覆蓋跨平台約束檔，也不要只更新其中一台的虛擬環境。

約束檔固定套件版本，但不固定 pip、Python 修補版、隔離建置工具或下載檔案雜湊，不保證逐位元組相同的 exe。已發布 ZIP 不會因更新原始碼的約束檔而改變。

## 分享圖維護

執行 `python tools/generate_social_preview.py --thumbnail build/social-preview-320.png`，更新 `docs/images/social-preview.png` 並產生 320 × 160 檢查圖。產圖使用倉庫內的寬版主視窗截圖，等比例呈現完整介面；更換來源素材時需重新檢查文字與安全邊界，不要裁切或拉伸介面。

圖片提交到 GitHub 後，仍須在倉庫 Settings → Social preview → Edit 上傳新版 PNG；GitHub 不會自動把倉庫內圖片設為分享圖。各分享平台也可能保留舊預覽快取。
