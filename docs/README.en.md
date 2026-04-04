# OCRTranslator

[繁體中文](../README.md)｜[简体中文](README.zh-CN.md)｜English

[![CI](https://github.com/Lianye-Scythe/OCRTranslator/actions/workflows/ci.yml/badge.svg)](https://github.com/Lianye-Scythe/OCRTranslator/actions/workflows/ci.yml)

OCRTranslator is a **portable OCR / AI request tool** built around **desktop reading workflows**.

It is not just a screenshot translator. It is a desktop AI workspace organized around three entry points:

1. **Screen capture**: send a screenshot to a multimodal model for OCR / translation / answering / polishing
2. **Selected text**: capture the currently selected text and submit it as a text request
3. **Manual input**: open an input dialog and send text directly to AI

## Highlights

- Three request entry points: capture / selected text / manual input
- Prompt preset system
- Four built-in presets
- Multiple API profiles
- `Gemini Compatible` and `OpenAI Compatible` providers
- API key rotation and retry support
- Light / dark / follow-system theme modes
- A workflow-first settings page organized as `Connection and model → Translation workflow → Appearance and advanced`
- Selected-text capture now runs as a non-blocking flow, shows a single processing toast only when the request is submitted, and supports cancellation during capture
- Result overlay supports copy, pin / unpin, opacity adjustment, drag to move, corner resize, and `Ctrl + mouse wheel` font zoom
- Global hotkeys, system tray, and single-instance protection
- Portable config stored next to the project root or packaged exe

## Default hotkeys

| Action | Default hotkey |
|---|---|
| Screen capture | `Shift + Win + X` |
| Selected text | `Shift + Win + C` |
| Manual input | `Shift + Win + Z` |

## Quick start

### 1. Install dependencies

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

If you also need packaging or development tooling:

```bash
pip install -r requirements-dev.txt
```

### 2. Start the app

#### Option A: double-click startup

Run:

- `start.bat`

#### Option B: command-line startup

```bash
python launcher.pyw
```

or:

```bash
python -m app.main
```

#### Option C: ask an existing instance to start capture immediately

```bash
python -m app.main --capture
```

## Basic workflow

### 1. Finish the connection and model check first

The settings page now guides first-run setup through the `Connection and model` section. At minimum, fill in:

- Provider
- Base URL
- API Keys
- Model

Recommended order:

1. Select or create an API profile
2. `Fetch Models`
3. `Test API`
4. `Save Settings`

After the connection works, fine-tune translation behavior, hotkeys, theme mode, and overlay preferences.

### 2. Trigger one of the three entry points

You can start requests from:

- `Start Capture` in the main window
- `Open Input Box` in the main window
- the selected-text hotkey
- the capture / input-box tray entries
- the corresponding global hotkeys
- the selected-text hotkey no longer blocks the main window while capture is in progress, and `Cancel Action` can stop it before request submission completes
- the `--capture` startup argument

### 3. Review the result

- Capture requests update the latest preview in `Preview & Log`
- Results appear in a floating overlay near the source area or trigger point
- Runtime activity is stored in memory and can be viewed or exported

## Prompt presets

Each preset contains:

- `image_prompt`
- `text_prompt`

Supported variable:

- `{target_language}`

Built-in presets cannot be deleted directly. Duplicate one first if you want a removable custom version.

## Tray and selected-text behavior

The tray menu provides:

- Show Window
- Capture Screen
- Open Input Box
- Cancel Action
- Quit

> The selected-text flow works best as a global-hotkey action.
> If you click it from the main window or tray, the app will usually steal focus first and break the original selection state in the external application.

## Checks

```bash
python -m unittest discover -v
python -m compileall app tests launcher.pyw
```

## Documentation

- [Documentation index](index.en.md)
- [Architecture](architecture.en.md)
- [Development Guide](development.en.md)
- [Packaging and Distribution](packaging.en.md)
- [Contributing](CONTRIBUTING.en.md)
- [Security Policy](SECURITY.en.md)
- [Changelog](CHANGELOG.en.md)
