# Packaging and Distribution

[繁體中文](packaging.md)｜[简体中文](packaging.zh-CN.md)｜English

## One-click packaging

Run:

- `build_exe.bat`

The script will automatically:

1. create or verify `.venv`
2. install `requirements-dev.txt`
3. clean old `build/`, `dist/`, and `release/`
4. produce `release\OCRTranslator.exe` with PyInstaller
5. copy `README.md` and `config.example.json`

## Recommended distribution contents

```text
release\OCRTranslator.exe
release\README.md
release\config.example.json
```

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
