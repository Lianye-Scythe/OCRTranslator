# 打包与发布

[繁體中文](packaging.md)｜简体中文｜[English](packaging.en.md)

## 一键打包

直接执行：

- `build_exe.bat`

脚本会自动：

1. 建立或检查 `.venv`
2. 安装 `requirements-dev.txt`
3. 清理旧的 `build/`、`dist/`、`release/`
4. 通过 PyInstaller 输出 `release\OCRTranslator.exe`
5. 复制 `README.md` 与 `config.example.json`

## 推荐分发内容

```text
release\OCRTranslator.exe
release\README.md
release\config.example.json
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
