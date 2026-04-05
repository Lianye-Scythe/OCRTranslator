# 打包与发布

[繁體中文](packaging.md)｜简体中文｜[English](packaging.en.md)

## 一键打包

直接执行：

- `build_exe.bat`

脚本会自动：

1. 建立或检查 `.venv`
2. 安装 `requirements-dev.txt`
3. 清理旧的 `build/`、`dist/`、`release/`
4. 从 `app/app_metadata.py` 读取当前版本号
5. 通过 `packaging/windows/OCRTranslator.spec` + PyInstaller 输出 `release\OCRTranslator.exe`
6. 复制 `README.md`、`LICENSE` 与 `config.example.json`
7. 自动创建 `release\OCRTranslator-v<version>-windows-x64.zip`

当前仓库采用“`packaging/windows/OCRTranslator.spec` 保存 PyInstaller 打包定义、`build_exe.bat` 负责准备环境 / 生成版本资源 / 启动打包”的分工方式。后续如果要调整 datas、exclude modules 或 onefile 行为，优先修改 `.spec` 即可。

## 图标资源位置

应用图标现在统一收敛到 `app/assets/icons/`：

- `app-icon-source.png`：原始来源图
- `app-icon-16.png` ~ `app-icon-256.png`：运行期多尺寸 PNG
- `app-icon.ico`：Windows 可执行文件打包图标

主窗口、系统托盘与 PyInstaller 打包都会共用这组图标资源。

## 可选打包环境变量

`build_exe.bat` 还支持几个对本地重复打包很实用的环境变量：

```text
BUILD_NO_PAUSE=1          完成或失败后不 pause，方便在终端、CI 或自动化脚本中调用
BUILD_SKIP_PIP_INSTALL=1  跳过 `pip install -r requirements-dev.txt`，适合依赖已经就绪的重复打包
```

示例：

```bat
set BUILD_NO_PAUSE=1
set BUILD_SKIP_PIP_INSTALL=1
build_exe.bat
```

## GitHub Actions 自动打包

仓库现在已预留 `.github/workflows/release-build.yml`，用途如下：

- `workflow_dispatch`：手动触发打包测试
- `push tags: v*`：推送版本 tag 时自动打包
- 上传的 workflow artifact 只包含版本化 ZIP
- 创建 GitHub Release 时也只附上版本化 ZIP
- 如果 tag 是 annotated tag，Release 正文会优先使用 tag annotation 文案

> GitHub Release 页面本身会自动附带 `Source code (zip)` 与 `Source code (tar.gz)`，因此 workflow 不需要另外上传这两个源码压缩包，也不会额外上传 `.exe`。

## SignPath 预留结构

仓库也已预留 SignPath 需要的基础结构：

- `packaging/signpath/artifact-configurations/default.xml`
- `packaging/signpath/README.md`

当前 workflow 会在已配置以下 GitHub Secret / Variable 时，自动把 unsigned artifact 送到 SignPath 签名：

### GitHub Secret

- `SIGNPATH_API_TOKEN`

### GitHub Variables

- `SIGNPATH_ORGANIZATION_ID`
- `SIGNPATH_PROJECT_SLUG`
- `SIGNPATH_SIGNING_POLICY_SLUG`

如果上述值尚未配置，workflow 仍会正常完成“未签名打包 + 上传 ZIP artifact / GitHub Release”流程，只是会跳过 SignPath 签名步骤。

> 当前公开发布包仍属于 **未签名** 状态；代码签名已纳入后续规划，并以 SignPath / Trusted Build 作为预定集成方向。

## 申请 SignPath 前建议顺序

1. 先把 `.github/workflows/release-build.yml` 推上 GitHub
2. 到 GitHub Actions 页面手动执行一次 `Release Build`
3. 确认能正常产出 ZIP artifact
4. 再向 SignPath 申请 / 开通 GitHub Trusted Build System 权限
5. 拿到 SignPath 组织与项目参数后，再补上前述 Secret / Variables
6. 最后以测试 tag 验证自动签名与 GitHub Release 流程

## 推荐分发内容

建议优先上传带版本号的压缩包，文件名包含项目名称、版本号与平台信息，例如：`OCRTranslator-v1.0.3-windows-x64.zip`，并额外附上一份 `SHA256SUMS.txt` 供手动校验。

```text
release\OCRTranslator-v<version>-windows-x64.zip
release\SHA256SUMS.txt
```

## 可选代码签名

`build_exe.bat` 现在支持可选的 Windows 代码签名流程。如果没有提供签名参数，脚本会跳过签名；如果提供了签名参数，脚本会在压缩前先对 `release\OCRTranslator.exe` 执行签名和验证。

可用环境变量：

```text
SIGNTOOL_PATH        可选，指定 signtool.exe 路径
SIGN_PFX_PATH        可选，PFX 证书路径
SIGN_PFX_PASSWORD    可选，PFX 证书密码
SIGN_CERT_SHA1       可选，使用证书存储中的 SHA1 Thumbprint
SIGN_SUBJECT_NAME    可选，按证书主题名称搜索证书
SIGN_TIMESTAMP_URL   可选，时间戳服务，默认 http://timestamp.digicert.com
```

至少提供以下其中一组即可启用签名：

- `SIGN_PFX_PATH`（可搭配 `SIGN_PFX_PASSWORD`）
- `SIGN_CERT_SHA1`
- `SIGN_SUBJECT_NAME`

示例（PFX）：

```bat
set SIGN_PFX_PATH=C:\certs\ocrtranslator.pfx
set SIGN_PFX_PASSWORD=your-password
build_exe.bat
```

示例（证书存储）：

```bat
set SIGN_CERT_SHA1=0123456789ABCDEF0123456789ABCDEF01234567
build_exe.bat
```

## 不建议分发的内容

```text
config.json
.venv\
build\
dist\
*.spec
```

## 运行时路径

- 源码运行：优先使用项目根目录的 `config.json`
- exe 运行：优先使用 exe 同层的 `config.json`
- 如果便携位置没有配置文件，且当前运行目录不可写，配置文件会自动回退到：
  - Windows：`%LOCALAPPDATA%\OCRTranslator\config.json`
  - 其他环境 fallback：`~/.ocrtranslator/config.json`
- crash log 仍然会写回项目根目录 / exe 同层，不会跟着 fallback 配置路径移动

这样能让应用在可写目录中保持便携，同时也能在只读或受限目录下稳定启动、保存配置与分发。
