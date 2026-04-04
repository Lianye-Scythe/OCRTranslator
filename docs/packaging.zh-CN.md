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
5. 通过 PyInstaller 输出 `release\OCRTranslator.exe`
6. 复制 `README.md` 与 `config.example.json`
7. 自动创建 `release\OCRTranslator-v<version>-windows-x64.zip`

## 推荐分发内容

建议优先上传带版本号的压缩包，文件名包含项目名称、版本号与平台信息，例如：`OCRTranslator-v0.9.4-windows-x64.zip`。

```text
release\OCRTranslator-v<version>-windows-x64.zip
```

如果你希望用户也能单独下载，也可以额外附上 `release\OCRTranslator.exe`。

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

- 源码运行：根目录保存 `config.json` 与 crash log
- exe 运行：exe 同层保存 `config.json` 与 crash log

这样能让应用保持便携，方便整体搬移、备份与分发。
