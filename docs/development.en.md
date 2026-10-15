# Development Guide

[繁體中文](development.md)｜[简体中文](development.zh-CN.md)｜English

## Environment setup

Use the latest stable Python 3.15 patch for development, CI, and Windows packaging. Compatibility with older Python versions is no longer maintained.

On WSL / Linux, create the environment with `python3.15 -m venv .venv` and activate it with `source .venv/bin/activate`. On Windows, confirm `python --version` is 3.15 before using the commands below.

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

### Test WSL source from Windows

Open the repository through `\\wsl.localhost\Ubuntu\home\po120\Git\OCRTranslator` in File Explorer (adjust the distribution and path), then double-click `start_wsl.bat` in the repository root. Windows Python 3.15 and the `py` launcher are required.

The script creates a Windows-only environment at `%LOCALAPPDATA%\OCRTranslator\venv-win315` and installs `requirements.txt`, leaving the WSL `.venv` separate. Keep the console open until the application exits so the WSL drive mapping remains available. Run `start_wsl.bat --check` to verify imports without launching the GUI; screen capture and hotkeys still require interactive testing.

### Start the application

```bash
python launcher.pyw
```

or:

```bash
python -m app.main
```

### Config path note

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
