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
- Added `light / dark / follow system` theme modes and the `theme_mode` config field

### Changed
- Split settings validation by operation scope so unrelated fields no longer block Fetch Models / Test API / text requests
- API test stale-result detection now includes the selected model
- Built-in prompt presets are no longer deletable, avoiding restart-time reappearance confusion
- Reorganized the settings page into a workflow-first structure: `Connection and model → Translation workflow → Appearance and advanced`
- Rebuilt the UI theme tokens into a Material-inspired semantic color system so primary actions, tonal actions, selected navigation, badges, and warning / danger states no longer compete for the same accent role
- Main window, result overlay, and selection overlay now share the same semantic theme roles, with light / dark styling and runtime switching wired together
- README now defaults to Traditional Chinese and includes Simplified Chinese and English variants
- The architecture, development, and packaging docs under `docs/` are now available in three languages
- Non-QSS UI color constants have started moving into `app/ui/theme_tokens.py`

### Fixed
- Split warning-style interruption actions from destructive delete actions instead of reusing the same danger color treatment
- Reduced ambiguity between `Save Settings`, `Open Input Box`, disabled buttons, and validation states in the light theme
