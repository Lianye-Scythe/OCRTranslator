# 打包與發佈

繁體中文｜[简体中文](packaging.zh-CN.md)｜[English](packaging.en.md)

## 一鍵打包

直接執行：

- `build_exe.bat`

腳本會自動：

1. 建立或檢查 `.venv`
2. 安裝 `requirements-dev.txt`
3. 清理舊的 `build/`、`dist/`、`release/`
4. 從 `app/app_metadata.py` 讀取目前版本號
5. 透過 `packaging/windows/OCRTranslator.spec` + PyInstaller 輸出 `release\OCRTranslator.exe`
6. 複製 `README.md`、`LICENSE` 與 `config.example.json`
7. 自動建立 `release\OCRTranslator-v<version>-windows-x64.zip`

目前倉庫採用「`packaging/windows/OCRTranslator.spec` 保存 PyInstaller 打包定義、`build_exe.bat` 負責準備環境 / 生成版本資源 / 啟動打包」的分工方式，後續若要調整 datas、exclude modules 或 onefile 行為，優先修改 `.spec` 即可。

## 圖示資源位置

應用圖示現在統一收斂到 `app/assets/icons/`：

- `app-icon-source.png`：原始來源圖
- `app-icon-16.png` ~ `app-icon-256.png`：執行期多尺寸 PNG
- `app-icon.ico`：Windows 可執行檔打包圖示

主視窗、系統匣與 PyInstaller 打包都會共用這組圖示資源。

## 可選打包環境變數

`build_exe.bat` 另外支援幾個對本機反覆打包很實用的環境變數：

```text
BUILD_NO_PAUSE=1          完成或失敗後不 pause，方便在終端、CI 或自動化腳本中呼叫
BUILD_SKIP_PIP_INSTALL=1  略過 `pip install -r requirements-dev.txt`，適合依賴已就緒的重複打包
```

範例：

```bat
set BUILD_NO_PAUSE=1
set BUILD_SKIP_PIP_INSTALL=1
build_exe.bat
```

## GitHub Actions 自動打包

倉庫現在已預留 `.github/workflows/release-build.yml`，用途如下：

- `workflow_dispatch`：手動觸發打包測試
- `push tags: v*`：推送版本 tag 時自動打包
- 上傳的 workflow artifact 只包含版本化 ZIP
- 建立 GitHub Release 時也只附上版本化 ZIP
- 若 tag 是 annotated tag，Release 正文會優先使用 tag annotation 文案

> GitHub Release 頁面本身會自動附帶 `Source code (zip)` 與 `Source code (tar.gz)`，因此 workflow 不需要另外上傳這兩個來源碼壓縮檔，也不會額外上傳 `.exe`。

## SignPath 預留結構

倉庫也已預留 SignPath 需要的基礎結構：

- `packaging/signpath/artifact-configurations/default.xml`
- `packaging/signpath/README.md`

目前 workflow 會在已配置下列 GitHub Secret / Variable 時，自動把 unsigned artifact 送到 SignPath 簽名：

### GitHub Secret

- `SIGNPATH_API_TOKEN`

### GitHub Variables

- `SIGNPATH_ORGANIZATION_ID`
- `SIGNPATH_PROJECT_SLUG`
- `SIGNPATH_SIGNING_POLICY_SLUG`

若上述值尚未配置，workflow 仍會正常完成「未簽名打包 + 上傳 ZIP artifact / GitHub Release」流程，只是會略過 SignPath 簽名步驟。

> 目前公開發佈包仍屬 **未簽名** 狀態；程式碼簽名已列入後續規劃，並以 SignPath / Trusted Build 作為預定整合方向。

## 申請 SignPath 前建議順序

1. 先把 `.github/workflows/release-build.yml` 推上 GitHub
2. 到 GitHub Actions 頁面手動執行一次 `Release Build`
3. 確認能正常產出 ZIP artifact
4. 再向 SignPath 申請 / 開通 GitHub Trusted Build System 權限
5. 取得 SignPath 組織與專案資訊後，再補上前述 Secret / Variables
6. 最後以測試 tag 驗證自動簽名與 GitHub Release 流程

## 建議分發內容

建議優先上傳版本化壓縮包，檔名包含專案名稱、版本號與平台資訊，例如：`OCRTranslator-v0.9.9-windows-x64.zip`，並額外附上一份 `SHA256SUMS.txt` 供手動驗證。

```text
release\OCRTranslator-v<version>-windows-x64.zip
release\SHA256SUMS.txt
```

## 可選代碼簽名

`build_exe.bat` 現在支援可選的 Windows 代碼簽名流程。若未提供簽名參數，腳本會略過簽名；若提供簽名參數，腳本會在壓縮前先對 `release\OCRTranslator.exe` 進行簽名與驗證。

可用環境變數：

```text
SIGNTOOL_PATH        可選，指定 signtool.exe 路徑
SIGN_PFX_PATH        可選，PFX 憑證路徑
SIGN_PFX_PASSWORD    可選，PFX 憑證密碼
SIGN_CERT_SHA1       可選，使用憑證存放區中的 SHA1 Thumbprint
SIGN_SUBJECT_NAME    可選，使用憑證主體名稱搜尋憑證
SIGN_TIMESTAMP_URL   可選，時間戳服務，預設 http://timestamp.digicert.com
```

至少提供下列其中一組即可啟用簽名：

- `SIGN_PFX_PATH`（可搭配 `SIGN_PFX_PASSWORD`）
- `SIGN_CERT_SHA1`
- `SIGN_SUBJECT_NAME`

範例（PFX）：

```bat
set SIGN_PFX_PATH=C:\certs\ocrtranslator.pfx
set SIGN_PFX_PASSWORD=your-password
build_exe.bat
```

範例（憑證存放區）：

```bat
set SIGN_CERT_SHA1=0123456789ABCDEF0123456789ABCDEF01234567
build_exe.bat
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
