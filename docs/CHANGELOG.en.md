# Changelog

[繁體中文](../CHANGELOG.md)｜[简体中文](CHANGELOG.zh-CN.md)｜English

This file records important OCRTranslator changes.

## Unreleased

### Added
- Added visible main-window and tray entry points for capture and manual input
- Kept selected-text support, but moved it back to a hotkey-first interaction model
- Added `app/hotkey_utils.py` to centralize hotkey splitting, modifier detection, and normalization
- Added `app/crash_handling.py` to share crash-hook initialization across startup paths
- Added `requirements-dev.txt` and multilingual documentation variants

### Changed
- Split settings validation by operation scope so unrelated fields no longer block Fetch Models / Test API / text requests
- API test stale-result detection now includes the selected model
- Built-in prompt presets are no longer deletable, avoiding restart-time reappearance confusion
- README now defaults to Traditional Chinese and includes Simplified Chinese and English variants
- The architecture, development, and packaging docs under `docs/` are now available in three languages
- Non-QSS UI color constants have started moving into `app/ui/theme_tokens.py`
