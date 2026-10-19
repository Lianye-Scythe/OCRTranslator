# OCRTranslator

[繁體中文](../README.md)｜[简体中文](README.zh-CN.md)｜English

[![CI](https://github.com/Lianye-Scythe/OCRTranslator/actions/workflows/ci.yml/badge.svg)](https://github.com/Lianye-Scythe/OCRTranslator/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/Lianye-Scythe/OCRTranslator)](https://github.com/Lianye-Scythe/OCRTranslator/releases/latest)
[![Platform](https://img.shields.io/badge/platform-Windows-0078D6)](FAQ.en.md)
[![License](https://img.shields.io/badge/license-GPLv3-4F46E5)](../LICENSE)

A portable Windows OCR and AI translation tool. Capture a screen region, use selected text, or enter text manually; your configured model service processes the content and results appear in an overlay.

## Download and requirements

**[Download the latest Windows release](https://github.com/Lianye-Scythe/OCRTranslator/releases/latest)**

- Under Assets, download `OCRTranslator-v<version>-windows-x64.zip`, not GitHub's generated `Source code` archives.
- Extract the entire ZIP, then run `OCRTranslator.exe`. The packaged app **does not require Python**.
- Bring your own API key for a Gemini- or OpenAI-compatible service. Provider usage may incur charges.
- Windows releases are currently **unsigned**. Download from official Releases and compare the ZIP against the accompanying `SHA256SUMS.txt`; a checksum is not a digital signature.

To run from source or develop, use Python 3.15 and follow the [development guide](development.en.md). WSL supports development and tests; run on Windows for Windows screen capture and global hotkeys. `start_wsl.bat` can run WSL-hosted source using Windows Python.

## Preview

### Animation

The animation and translation overlays are historical workflow examples. The main-window screenshots show the current interface with example settings.

![Historical workflow animation](images/screenshots/ocrtranslator-preview.gif)

### Main window

<p>
  <img src="images/screenshots/main-window-light.png" width="49%" alt="Main window: light theme" />
  <img src="images/screenshots/main-window-dark.png" width="49%" alt="Main window: dark theme" />
</p>

### Translation overlays

<p>
  <img src="images/screenshots/overlay-light-manga.png" width="49%" alt="Manga overlay: light theme (historical example)" />
  <img src="images/screenshots/overlay-light-novel.png" width="49%" alt="Novel overlay: light theme (historical example)" />
</p>
<p>
  <img src="images/screenshots/overlay-dark-manga.png" width="49%" alt="Manga overlay: dark theme (historical example)" />
  <img src="images/screenshots/overlay-dark-novel.png" width="49%" alt="Novel overlay: dark theme (historical example)" />
</p>

[View full-size images](gallery.md).

## First run

1. Select Gemini Compatible or OpenAI Compatible under Connection and model.
2. Check the Base URL, enter your API key, and choose a model. Image requests require a model that accepts images.
3. Use Fetch Models and Test API to check the connection, then save settings.
4. Choose a target language and a prompt preset, such as Translate.
5. Start a screen capture, use the selected-text hotkey, or open the manual input box.

The default Gemini model is `gemini-flash-lite-latest`. Availability, supported parameters, and actual output depend on the service you connect.

### Default hotkeys

| Action | Hotkey |
|---|---|
| Capture a screen region | `Shift + Win + X` |
| Use selected text | `Shift + Win + C` |
| Enter text manually | `Shift + Win + Z` |

Hotkeys are configurable. Some applications do not support simulated copying, so selected-text capture cannot work everywhere.

## Core features

- Screen capture, selected-text capture, and manual input.
- Built-in Translate, Answer, Polish, and Raw OCR presets, plus custom prompts.
- Gemini/OpenAI-compatible APIs, multiple connection profiles, key rotation, and retries.
- Streaming output, with a non-streaming fallback for unsupported backends.
- Movable, resizable, pinnable result overlays with copy, font-size, and background-opacity controls.
- Reasoning effort and temperature controls; temperature defaults to the model's setting. Custom options depend on model support.
- Light/dark/system themes and Traditional Chinese, Simplified Chinese, and English interfaces. Optional Markdown result formatting is off by default.

## Data, limitations, and upgrades

- Selected images or text are sent to **your configured API service**. Review its pricing, retention, and privacy policy before use. Do not submit content you are not authorized to share.
- No offline OCR engine or model service is bundled. Recognition, translation quality, and content restrictions depend on the selected model; prompts cannot guarantee correct recognition or a completed request.
- Settings normally live in `config.json` next to the executable and may contain API keys. Do not share this file publicly. If the app cannot create settings there, it falls back to a user directory; see the [FAQ](FAQ.en.md).
- Back up `config.json` before upgrading. Extract the new version into a separate directory, then bring over your settings. Do not overwrite personal settings with `config.example.json`.
- Crash reports are stored in `logs/` under the application directory. Review and remove sensitive information before reporting them.

## Documentation and contribution

[FAQ](FAQ.en.md) · [Documentation index](index.en.md) · [Development](development.en.md) · [Packaging](packaging.en.md) · [Changelog](CHANGELOG.en.md)

[Report an issue](https://github.com/Lianye-Scythe/OCRTranslator/issues/new/choose) · [Contributing](CONTRIBUTING.en.md) · [Security](SECURITY.en.md) · [Support](SUPPORT.en.md) · [Code of Conduct](../.github/CODE_OF_CONDUCT.md)

Licensed under [GPLv3](../LICENSE).
