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

建议优先上传带版本号的压缩包，文件名包含项目名称、版本号与平台信息，例如：`OCRTranslator-v0.9.1-windows-x64.zip`。

```text
release\OCRTranslator-v<version>-windows-x64.zip
```

如果你希望用户也能单独下载，也可以额外附上 `release\OCRTranslator.exe`。

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
