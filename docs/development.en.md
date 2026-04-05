# Development Guide

[繁體中文](development.md)｜[简体中文](development.zh-CN.md)｜English

## Environment setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

If you also need packaging or development tooling:

```bash
pip install -r requirements-dev.txt
```

## Common commands

### Start the application

```bash
python launcher.pyw
```

or:

```bash
python -m app.main
```

## Config path note

When running from source, the app prefers `config.json` in the project root. If no portable config exists yet and the current directory is not writable, it falls back to:

- Windows: `%LOCALAPPDATA%\OCRTranslator\config.json`
- other environments: `~/.ocrtranslator/config.json`

When debugging local config behavior, check both the portable path and the fallback path to see which one is currently active.

### Run tests

```bash
python -m unittest discover -v
```

### Run a basic compile check

```bash
python -m compileall app tests launcher.pyw
```

## Test coverage focus

Current automated checks focus on:

- API error parsing and provider adapters
- config migration and broken-config recovery
- crash log generation and redaction
- hotkey conflict detection
- overlay positioning logic
- main-window runtime state control
- settings snapshot validation and candidate config building
- prompt preset and request workflow rules

## Before you commit

1. Run `python -m unittest discover -v`
2. Run `python -m compileall app tests launcher.pyw`
3. If packaging is involved, also confirm `pip install -r requirements-dev.txt`
4. Check that you did not accidentally commit:
   - `config.json`
   - `.venv/`
   - `build/`
   - `dist/`
   - `release/`
   - `ocrtranslator-crash-*.log`
   - `ocrtranslator-log-*.txt`
