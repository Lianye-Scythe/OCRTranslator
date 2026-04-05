# OCRTranslator

[繁體中文](../README.md)｜[简体中文](README.zh-CN.md)｜English

[![CI](https://github.com/Lianye-Scythe/OCRTranslator/actions/workflows/ci.yml/badge.svg)](https://github.com/Lianye-Scythe/OCRTranslator/actions/workflows/ci.yml)
[![Platform](https://img.shields.io/badge/platform-Windows-0078D6)](packaging.en.md)
[![Release](https://img.shields.io/badge/release-v0.9.8-2563EB)](https://github.com/Lianye-Scythe/OCRTranslator/releases)
[![License](https://img.shields.io/badge/license-GPLv3-4F46E5)](../LICENSE)

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
- Screen capture now sends the original PNG bytes directly after selection completes, reducing the wait from capture to result overlay
- Screen capture itself now runs off the UI thread while keeping original PNG bytes on the direct image-request path, reducing the chance of synchronous capture stalls dragging the main window down
- Runtime logs now report `capture / request / total / png` timing so you can tell whether latency comes from local processing or the model side
- Global hotkeys now include modifier-release pairing and state resynchronization safeguards to reduce stuck-looking `Shift / Ctrl / Win` behavior
- A workflow-first settings page organized as `Connection and model → Translation workflow → Appearance and advanced`
- Advanced settings now include configurable overlay auto-expand top / bottom safe margins so you can tune how close the popup grows toward the taskbar
- Selected-text capture now runs as a non-blocking flow, shows a single processing toast only when the request is submitted, and supports cancellation during capture
- Result overlay supports copy, a pushpin-style keep-visible toggle, surface-only opacity control, direct opacity input, drag to move, corner resize, and `Ctrl + mouse wheel` font zoom
- Pinned result overlays now preserve their previous size and position across capture, selected-text, and manual-input flows; capture hides the overlay only temporarily and restores it with the same geometry
- Unpinned overlays now restart from the saved default size on every new request; temporary manual resizing no longer pollutes the saved default size or triggers unsaved-change prompts
- Pinned overlay size and position changes are now auto-persisted across app restarts; once Pin is turned off, the next new request falls back to the saved default size again
- `Save Settings` no longer auto-scrolls the form down to the target-language field just because it is temporarily blank while you are saving API/profile changes; request-time validation still enforces the required target language when needed
- API Keys / prompt multiline editors and regular single-line fields now share clearer text-selection highlights and a cleaner focus treatment, improving edit-state visibility in both light and dark themes
- The tray context menu and Pin button states now follow the current light / dark theme and use a more restrained Material-style presentation
- Shutdown now includes a watchdog and error-dialog fallback path to reduce the risk of the app becoming hard to close after runtime failures or third-party hook issues
- Message boxes and destructive confirmations now share consistent button semantics, focus handling, and Escape behavior
- Global hotkeys, system tray, and single-instance protection
- Portable config stored next to the project root or packaged exe

## Screenshots

Current visuals for the main workspace and translation overlay:

### Animated preview

<p align="center">
  <img src="images/screenshots/ocrtranslator-preview.gif" width="88%" alt="Animated preview of OCRTranslator" />
</p>

### Static screenshots

### Main window

<p align="center">
  <img src="images/screenshots/main-window-light.png" width="49%" alt="Light theme main window" />
  <img src="images/screenshots/main-window-dark.png" width="49%" alt="Dark theme main window" />
</p>

### Translation overlay

<p align="center">
  <img src="images/screenshots/overlay-light-manga.png" width="49%" alt="Light theme translation overlay for manga text" />
  <img src="images/screenshots/overlay-light-novel.png" width="49%" alt="Light theme translation overlay for novel text" />
</p>
<p align="center">
  <img src="images/screenshots/overlay-dark-novel.png" width="49%" alt="Dark theme translation overlay for novel text" />
  <img src="images/screenshots/overlay-dark-manga.png" width="49%" alt="Dark theme translation overlay for manga text" />
</p>

## Release and trust information

- The official desktop distribution is the versioned ZIP published on GitHub Releases: `OCRTranslator-v<version>-windows-x64.zip`
- Releases are built automatically from `v*` annotated tags through GitHub Actions, and the Release body is intended to prefer the tag annotation text
- The current public Windows package is **unsigned**; the repository already includes SignPath / Trusted Build groundwork and code signing is planned
- Public Releases do not upload a standalone `.exe`; they publish the versioned ZIP plus GitHub's built-in source archives instead
- For sensitive security reports, contact the maintainer privately at `po12017po@gmail.com`

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
- Recent image-request logs also include PNG size plus `capture / request / total` timings for quick bottleneck diagnosis
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
- [FAQ](FAQ.en.md)
- [Code of Conduct](../CODE_OF_CONDUCT.md)
- [Contributing](CONTRIBUTING.en.md)
- [Security Policy](SECURITY.en.md)
- [Changelog](CHANGELOG.en.md)

## License

- This project is released under the **GNU General Public License v3.0 (GPLv3)**
- See the repository-root `LICENSE` file for the full text
- If you distribute a modified or derived version, please provide the corresponding source code under GPLv3 as well

By submitting pull requests, patches, or other code contributions to this repository, you agree that those contributions may be distributed under GPLv3.
