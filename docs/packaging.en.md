# Packaging and Distribution

[繁體中文](packaging.md)｜[简体中文](packaging.zh-CN.md)｜English

## One-click packaging

Run:

- `build_exe.bat`

The script will automatically:

1. create or verify `.venv`
2. install `requirements-dev.txt`
3. clean old `build/`, `dist/`, and `release/`
4. read the current version from `app/app_metadata.py`
5. produce `release\OCRTranslator.exe` with PyInstaller
6. copy `README.md` and `config.example.json`
7. automatically create `release\OCRTranslator-v<version>-windows-x64.zip`

## Recommended distribution contents

Prefer uploading the versioned archive first. The file name should include the project name, version, and platform, for example: `OCRTranslator-v0.9.1-windows-x64.zip`.

```text
release\OCRTranslator-v<version>-windows-x64.zip
```

If you also want users to download a standalone binary, you can upload `release\OCRTranslator.exe` as an extra asset.

## Not recommended for distribution

```text
config.json
.venv\
build\
dist\
*.spec
```

## Runtime paths

- source mode: `config.json` and crash logs are stored in the project root
- exe mode: `config.json` and crash logs are stored next to the executable

This keeps the app portable and easy to move, back up, and redistribute.
