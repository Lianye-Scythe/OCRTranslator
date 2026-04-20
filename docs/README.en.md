# OCRTranslator

[繁體中文](../README.md)｜[简体中文](README.zh-CN.md)｜English

[![CI](https://github.com/Lianye-Scythe/OCRTranslator/actions/workflows/ci.yml/badge.svg)](https://github.com/Lianye-Scythe/OCRTranslator/actions/workflows/ci.yml)
[![Platform](https://img.shields.io/badge/platform-Windows-0078D6)](packaging.en.md)
[![Release](https://img.shields.io/badge/release-v1.0.10-2563EB)](https://github.com/Lianye-Scythe/OCRTranslator/releases)
[![License](https://img.shields.io/badge/license-GPLv3-4F46E5)](../LICENSE)

OCRTranslator is a **portable OCR / AI request tool** built around **desktop reading workflows**.

It is not just a screenshot translator. It is a desktop AI workspace organized around three entry points:

1. **Screen capture**: send a screenshot to a multimodal model for OCR / translation / answering / polishing
2. **Selected text**: capture the currently selected text and submit it as a text request
3. **Manual input**: open an input dialog and send text directly to AI

## Screenshots

If you want a quick feel for the product first, start with the current main-window and overlay visuals, then continue into the feature highlights below.

### Animated preview

<p align="center">
  <img src="images/screenshots/ocrtranslator-preview.gif" width="88%" alt="Animated preview of OCRTranslator" />
</p>

### Static screenshots

#### Main window

<p align="center">
  <img src="images/screenshots/main-window-light.png" width="49%" alt="Light theme main window" />
  <img src="images/screenshots/main-window-dark.png" width="49%" alt="Dark theme main window" />
</p>

#### Translation overlay

<p align="center">
  <img src="images/screenshots/overlay-light-manga.png" width="49%" alt="Light theme translation overlay for manga text" />
  <img src="images/screenshots/overlay-light-novel.png" width="49%" alt="Light theme translation overlay for novel text" />
</p>
<p align="center">
  <img src="images/screenshots/overlay-dark-novel.png" width="49%" alt="Dark theme translation overlay for novel text" />
  <img src="images/screenshots/overlay-dark-manga.png" width="49%" alt="Dark theme translation overlay for manga text" />
</p>

## Highlights

- Three request entry points: capture / selected text / manual input
- Prompt preset system with four built-in presets: `Translate`, `Answer`, `Polish`, and `Raw OCR`
- Multiple API profiles for `Gemini Compatible` and `OpenAI Compatible` providers
- API key rotation, retry, and model-switching support
- Stream responses are enabled by default and can be disabled in Advanced Settings; `Test API` now uses the same mode so backend behavior is easier to validate before saving
- The manual-input dialog can now override the target language for a single request, offers common-language suggestions, and remembers the last manual-input language
- Third-party compatible backends can surface an explicit status hint and retry without streaming when stream mode is unsupported; interrupted streams also keep visible partial results with state labels
- A workflow-first settings layout: `Connection and model → Translation workflow → Appearance and advanced`
- In-app selected text now prefers a direct read from the current focused widget's text selection; only when no usable in-app selection exists does it fall back to the system clipboard capture path
- Screen capture now freezes a desktop snapshot before selection and crops from that frozen frame, reducing high-DPI / multi-monitor mismatch, hover-triggered UI leakage, and app-window ghosting
- Each capture now recreates the selection overlay, reducing the chance that Windows briefly flashes the previous screenshot background on the first frame
- Settings-page action buttons such as `Fetch Models`, `Test API`, and `Save Settings` now use steadier focus handling so busy-state transitions do not auto-scroll the form to the bottom
- In left-right mode, the result overlay now measures header and toolbar width more accurately, so the first visible placement is less likely to overlap the captured selection
- Streaming image-translation overlays are now more stable: the first partial result seeds its width from the available selection-side space to reduce cold-start sideways jumps, and ongoing updates still try to avoid jitter when the window grows near the bottom edge
- Request flows stay as non-blocking as possible, with app-managed toasts and tray notifications for status feedback
- Result overlay supports:
  - copy, pin / unpin
  - surface-only opacity changes so text stays clear
  - direct opacity percentage input
  - drag to move and corner resize
  - `Ctrl + mouse wheel` font zoom
- Pinned overlays keep their size and position; unpinned overlays expand dynamically for the current scene, and any runtime-resized width now stays only for the current app session instead of being written across restarts
- The built-in `Translate` preset now uses a more neutral OCR / translation prompt; when backend safety rules block only part of the content, the preset falls back to `[REDACTED]` for the triggered fragments and continues the rest of the translation whenever possible
- Light / dark / follow-system theme modes
- Global hotkeys, system tray, single-instance forwarding, and quick `--capture` launch support
- Advanced Settings now include a toggleable debug log mode; default runtime logs stay user-facing, while positioning diagnostics, capture planning, and low-level API retry details appear only when debug logging is enabled
- Versioned ZIP releases, `SHA256SUMS.txt`, and trilingual documentation

## Release and trust information

- The official desktop distribution is the versioned ZIP published on GitHub Releases: `OCRTranslator-v<version>-windows-x64.zip`
- Pushing a `v*` annotated tag triggers GitHub Actions to build the Release and reuse the tag annotation as the Release body when available
- The current public Windows package is **unsigned**; the repository already includes SignPath / Trusted Build groundwork and code signing is planned
- Public Releases do not upload a standalone `.exe`; they publish the versioned ZIP plus GitHub's built-in source archives instead
- Releases also attach `SHA256SUMS.txt` so the ZIP can be verified manually after download
- For sensitive security reports, contact the maintainer privately at `po12017po@gmail.com`

## Default hotkeys

| Action | Default hotkey |
|---|---|
| Screen capture | `Shift + Win + X` |
| Selected text | `Shift + Win + C` |
| Manual input | `Shift + Win + Z` |

> If `config.json` already exists, the app uses the hotkeys stored there instead of these defaults.

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

It will automatically:

1. check `.venv`
2. install runtime dependencies when needed
3. launch the GUI through `launcher.pyw`
4. show a startup error dialog first if the app fails early

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

Supported arguments:

- `--capture`
- `/capture`
- `capture`

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
- the manual-input dialog can override the target language for the current request, even when the settings-page target-language field is temporarily blank
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

Text requests automatically append the source text after the prompt, so you only need to maintain the instruction part.

Built-in presets:

| Preset | Purpose |
|---|---|
| `Translate` | Translate image or text content into the target language |
| `Answer` | Answer or explain a question, prompt, or problem directly |
| `Polish` | Rewrite text into more natural, polished target-language output |
| `Raw OCR` | Return OCR text only, without translation or polishing |

> Built-in presets cannot be deleted directly. Duplicate one first if you want a removable custom version.

## Config storage

The app prefers a portable `config.json`.

Resolution order:

- source mode: if `config.json` already exists in the project root, it is reused; if the root is writable and no config exists yet, the app creates it there
- packaged exe: if `config.json` already exists next to the executable, it is reused; if the exe directory is writable and no config exists yet, the app creates it there
- if no portable config exists and the current runtime directory is not writable, the app falls back to a user-level config path:
  - Windows: `%LOCALAPPDATA%\OCRTranslator\config.json`
  - other environments: `~/.ocrtranslator/config.json`

Whenever a portable config exists, it wins over the fallback path.

Typical contents include:

- active API / prompt preset selections
- UI language, target language, theme mode, and hotkeys
- the last target language used by the manual-input workflow
- overlay font, opacity, default size, and pinned geometry

> `config.json` may contain API keys and private base URLs. Do not share it directly.
> Crash logs still default to the project root or the executable directory instead of following the fallback config path.

## Tray, single-instance, and error handling

### Single-instance behavior

The app uses a lock file and a local server to keep a single running instance.

When you launch it again:

- a normal launch reactivates the existing main window
- `--capture` asks the existing instance to jump directly into capture

### Tray menu

The tray menu provides:

- Show Window
- Capture Screen
- Open Input Box
- Cancel Action
- Quit

> Selected-text capture works best as a global hotkey action.
> If you trigger it from the main window or tray, the app will usually steal focus first and break the original selection in the external app.

By default, clicking the window `X` exits the app.
Enable the corresponding setting if you want `X` to minimize to the system tray instead.

### Logs and crash logs

- runtime activity stays in memory by default
- the latest 100 entries are kept
- logs can be viewed or exported from the UI

Unhandled exceptions create a crash log in the project root or next to the executable:

```text
ocrtranslator-crash-YYYYMMDD-HHMMSS-xxxxxxxxx.log
```

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
- [Support](../SUPPORT.md)
- [Contributing](CONTRIBUTING.en.md)
- [Security Policy](SECURITY.en.md)
- [Changelog](CHANGELOG.en.md)

## Known limitations

- recognition and output quality depend heavily on the multimodal model you connect
- there is currently no built-in offline OCR engine
- the selected-text flow relies on simulated copy plus clipboard restoration, so some apps may not respond to standard copy behavior
- the engineering setup and startup scripts are primarily tuned for Windows
- overlay positioning prioritizes readability and minimal obstruction instead of strict layout rules
- runtime logs are not intended to be a long-term audit trail

## License

- This project is released under the **GNU General Public License v3.0 (GPLv3)**
- See the repository-root `LICENSE` file for the full text
- If you distribute a modified or derived version, please provide the corresponding source code under GPLv3 as well

By submitting pull requests, patches, or other code contributions to this repository, you agree that those contributions may be distributed under GPLv3.
