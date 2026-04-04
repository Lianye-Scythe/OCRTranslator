# Changelog

[繁體中文](../CHANGELOG.md)｜[简体中文](CHANGELOG.zh-CN.md)｜English

This file records important OCRTranslator changes.

## [0.9.0] - 2026-04-04

### Added
- Added app version `v0.9.0` and displayed it in the main window title and bottom of the sidebar
- Added visible main-window and tray entry points for capture and manual input
- Kept selected-text support, but moved it back to a hotkey-first interaction model
- Added `app/hotkey_utils.py` to centralize hotkey splitting, modifier detection, and normalization
- Added `app/crash_handling.py` to share crash-hook initialization across startup paths
- Added `requirements-dev.txt` and multilingual documentation variants
- Added `light / dark / follow system` theme modes and the `theme_mode` config field
- Added `SelectedTextCaptureSession` to drive selected-text capture as a non-blocking event-loop workflow with cancellation support during the capture phase

### Changed
- Optimized settings layout: Applied 50:50 column stretch to grid layouts to prevent multi-language text wrapping inconsistencies
- Optimized sidebar layout: Widened min/max limits and adjusted height policies to prevent English text truncation or squeezing
- Refined sidebar spacing: Reduced component gaps, decreased secondary text font size (11px), and added bottom padding for a more compact and elegant look
- Introduced zero-width space (`&#8203;`) to elegantly wrap long repository URLs, improving multilingual layout flexibility
- Split settings validation by operation scope so unrelated fields no longer block Fetch Models / Test API / text requests
- API test stale-result detection now includes the selected model
- Built-in prompt presets are no longer deletable, avoiding restart-time reappearance confusion
- Reworked selected-text capture into a non-blocking flow: hotkey release waiting, clipboard settle time, and clipboard polling now advance in Qt timer phases instead of synchronously stalling the main window
- `Cancel Action` can now stop the selected-text capture stage, and API retry backoff waits respond to cancellation more quickly
- Reorganized the settings page into a workflow-first structure: `Connection and model → Translation workflow → Appearance and advanced`
- Rebuilt the UI theme tokens into a Material-inspired semantic color system so primary actions, tonal actions, selected navigation, badges, and warning / danger states no longer compete for the same accent role
- Main window, result overlay, and selection overlay now share the same semantic theme roles, with light / dark styling and runtime switching wired together
- README now defaults to Traditional Chinese and includes Simplified Chinese and English variants
- The architecture, development, and packaging docs under `docs/` are now available in three languages
- Non-QSS UI color constants have started moving into `app/ui/theme_tokens.py`
- Overhauled light and dark theme colors, introducing a high-quality "Slate / Graphite" monochrome system based on Material Design 3
- Removed excessive borders (box-in-box) in settings UI, using whitespace and surface tones to establish visual hierarchy
- Replaced custom square/minus dropdown icons with standard SVG caretsfor better affordance
- Enhanced button visual hierarchy, dynamically emphasizing the "Save Settings" primary action when unsaved changes exist
- Refined form error states by replacing aggressive red blocks with subtle text and input border highlights
- Upgraded dark mode with recessed inputs and a soft off-white primary accent to improve comfort during extended use

### Fixed
- Split warning-style interruption actions from destructive delete actions instead of reusing the same danger color treatment
- Reduced ambiguity between `Save Settings`, `Open Input Box`, disabled buttons, and validation states in the light theme
- Fixed the selected-text translation flow showing two tray bubbles; it now emits a single processing notification only when the request is actually submitted
- Fixed pinned result overlays sometimes restoring outside the visible screen after monitor layout or resolution changes
- Fixed `load_config()` incorrectly treating config-migration errors as broken config files and silently recreating the config
- Added regression tests for the async selected-text flow, cancellation path, and overlay clamping behavior
