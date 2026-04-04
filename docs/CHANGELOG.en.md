# Changelog

[繁體中文](../CHANGELOG.md)｜[简体中文](CHANGELOG.zh-CN.md)｜English

This file records important OCRTranslator changes.

## [0.9.4] - 2026-04-05

### Added
- Added a shutdown watchdog, non-blocking error-dialog fallback, and crash-log backstop so app shutdown and runtime failures have a final safety net
- Added light / dark themed styling for the system-tray context menu so tray actions keep readable contrast in both themes

### Changed
- Moved screen capture work off the UI thread while keeping the original PNG bytes on the direct image-request path, preserving responsiveness without slowing the request pipeline
- Pinned result overlays now preserve their existing position and size across capture, selected-text, and manual-input flows; capture hides the overlay only temporarily and restores it with the same geometry
- Refined the Pin button into a more Material-style pushpin toggle with lower-contrast selected / idle states, and toned the main workspace surface shadow down to a lighter depth layer

### Fixed
- Reduced the risk of the app hanging during shutdown because of global-hotkey listeners, recorder listeners, or cleanup paths that could leave `X` / tray exit seemingly unresponsive
- Hardened `handle_error()` with recursion guards, dialog fallbacks, and crash-log recording so the error path is less likely to crash on its own
- Fixed the light-theme tray context menu using a dark-looking background that made the menu text hard to read
- Fixed edge cases where empty `api_profiles` / `prompt_presets` config data could trigger runtime indexing errors
- Added regression coverage for background capture, pinned-overlay geometry preservation, tray theming, shutdown watchdog behavior, and config self-healing

## [0.9.3] - 2026-04-04

### Added
- Added configurable top / bottom safe margins for translation-overlay auto expansion under the Appearance and Advanced section so the popup can better match different desktop and taskbar setups
- Added a shared `message_boxes.py` helper to normalize dialog button semantics, destructive confirmations, escape behavior, and opt-out escape hatches (`prefer_native` / `preserve_initial_focus`)

### Changed
- Translation-overlay opacity now affects only surface layers instead of fading the translated text; the opacity chip now supports direct input, `+ / -` steps are 5, and the top bar temporarily returns to full opacity on hover
- Replaced the overlay Pin text button with a more intuitive pushpin icon while keeping tooltip and accessibility naming intact
- Relaxed overlay auto-expansion limits so the popup can grow closer to the taskbar while still respecting a configurable safe gap and never auto-touching the taskbar
- Reworked destructive confirmations for profile / preset deletion to use explicit action labels (`Cancel` / `Delete …`) instead of ambiguous `Yes / No`
- Reordered advanced settings so overlay margin now sits last, and renamed the auto-expand safe-margin fields to make their overlay scope explicit

### Fixed
- Fixed dark-mode text selection in editable inputs and numeric fields so selected text no longer turns black and unreadable
- Fixed overly bright initial focus rings / occasional white outlines in overlays and confirmation dialogs, plus the delayed focus-clear error log after cancelling a dialog
- Added regression coverage for overlay opacity behavior, message-box helpers, configurable safe margins, and dark-mode selection foregrounds

## [0.9.2] - 2026-04-04

### Added
- Added a header-level three-state theme quick switch (`follow system / light / dark`) that applies immediately and auto-saves on click
- Added a hotkey overview in the header summary so capture, selected-text, and input-box shortcuts are visible together

### Changed
- Replaced the advanced-settings theme dropdown with a header segmented switch and reorganized the header information hierarchy
- Refined settings-page and sidebar layout rhythm by polishing the brand block, navigation group, start-here actions, usage tip, and author metadata alignment
- Tightened the header title / subtitle / summary cadence and restructured current profile / preset / language / mode / hotkeys into an easier-to-scan two-line metadata block
- Added English-specific sidebar adaptation: shorter copy, tuned width limits, and a more compact Author / Repo metadata treatment to reduce scrolling and awkward wrapping
- Updated packaging docs so the versioned release archive example now points to `v0.9.2`

### Fixed
- Improved dark-mode readability for the header hotkey summary, which previously lacked enough contrast
- Reduced excessive whitespace between the header hotkey row and the content area so the divider transition feels tighter
- Fixed overcrowding and internal-scroll pressure in the English sidebar caused by overly long copy and metadata layout

## [0.9.1] - 2026-04-04

### Added
- Added image-request timing logs that report `capture / request / total / png`, making it easier to see whether latency comes from local capture, upload time, or model response time
- Added a Windows version-resource generator so packaged executables now include Product / File Version / Company metadata
- Added versioned release-archive output; `build_exe.bat` now creates `OCRTranslator-v<version>-windows-x64.zip` automatically
- Added an optional code-signing packaging flow with support for PFX certificates, Windows certificate-store thumbprints / subject names, and signature verification

### Changed
- Screen capture now sends the original PNG bytes directly into the image-request pipeline as soon as capture finishes, without extra resizing or additional image preprocessing first
- Capture preview refresh now runs after the image request starts, so translation requests leave the gate earlier
- Startup now reactivates the main window on the next event-loop tick, and the single-instance forwarding protocol now uses newline-delimited messages plus ACK replies to reduce "only tray icon appeared" activation failures
- Translation overlay display now includes a Windows-native topmost fallback so result popups are less likely to be covered by normal desktop windows
- Packaging documentation now covers version resources, signing parameters, timestamping, and the recommended release-asset layout

### Fixed
- Fixed the imbalance between suppressed modifier keydown and keyup handling in the global hotkey hook, reducing the risk of `Shift / Ctrl / Win` appearing to stay stuck
- Added hotkey-state resynchronization: if a release event is missed, the next keyboard event reconciles internal pressed state against the real physical key state
- Added regression coverage for single-instance ACK handling, overlay topmost behavior, direct-PNG image submission, and sticky-modifier prevention

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
- Improved settings page spatial rhythm based on the "Law of Proximity", increasing spacing between unrelated sections (32px) and tightening spacing between strongly related options (10px) to enhance visual hierarchy and breathing room
- Added a semi-transparent "Resize Grip" SVG icon to the bottom-right corner of the Translation Overlay, increasing the visual affordance for drag-to-resize behavior
- Optimized accessibility Focus States: navigation buttons and input fields now display clearer background highlights and theme-colored borders when focused, improving visual feedback for keyboard navigation

### Fixed
- Split warning-style interruption actions from destructive delete actions instead of reusing the same danger color treatment
- Reduced ambiguity between `Save Settings`, `Open Input Box`, disabled buttons, and validation states in the light theme
- Fixed the selected-text translation flow showing two tray bubbles; it now emits a single processing notification only when the request is actually submitted
- Fixed pinned result overlays sometimes restoring outside the visible screen after monitor layout or resolution changes
- Fixed `load_config()` incorrectly treating config-migration errors as broken config files and silently recreating the config
- Added regression tests for the async selected-text flow, cancellation path, and overlay clamping behavior
