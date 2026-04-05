# Changelog

[繁體中文](../CHANGELOG.md)｜[简体中文](CHANGELOG.zh-CN.md)｜English

This file records important OCRTranslator changes.

## [Unreleased]

## [1.0.2] - 2026-04-05

### Fixed
- Delayed startup update checks now read only the persisted `check_updates_on_startup` setting, so unsaved checkbox changes no longer alter the current launch's automatic-check behavior

### Changed
- The `v1.0.2` release tag annotation is created from BOM-free text so GitHub Release notes do not inherit a hidden leading character

## [1.0.1] - 2026-04-05

### Added
- Added optional GitHub Releases update checks; advanced settings now support both delayed background checks after startup and on-demand manual checks, with direct links to Releases when a newer version is found
- Added explicit guidance for concealed API Keys fields so clicking a masked editor nudges the user toward `Show Keys` without auto-revealing sensitive values

### Changed
- Refined the concealed API Keys interaction to feel more Material-like: the field surface stays visually stable, while only the reveal button and helper copy pulse for guidance
- Reordered the advanced-settings information flow so the overlay / Pin behavior note appears before the update-check block, making the section easier to scan
- Update-check helper text now renders a clickable GitHub Releases link while still staying quiet when startup checks find nothing new or fail

### Fixed
- Fixed the concealed API Keys `eventFilter()` path crashing during early main-window initialization when the visibility state had not been created yet, preventing startup-time crash-log cascades
- Fixed main-thread crash handling writing repeated crash reports for nested or rapid duplicate exceptions by adding reentry and short-window duplicate suppression
- Fixed concealed API Keys guidance pulses leaving mismatched focus / highlight states across light and dark themes

## [1.0.0] - 2026-04-05

### Added
- Added `startup_timing` marks plus an `OCRTRANSLATOR_STARTUP_TIMING_VERBOSE=1` detailed mode for cold-start and post-show prewarm analysis
- Added a shared IME-aware multiline editor to fix placeholder overlap with Chinese IME preedit text in both the manual-input dialog and settings editors
- Added app-managed transient request toasts with configurable display duration; advanced settings can now set the toast duration to `0` to disable them entirely

### Changed
- Reworked the startup path into a lighter bootstrap with delayed UI creation, broader lazy service initialization, and idle prewarm, while keeping single-instance IPC forwarding reliable for rapid relaunches
- Unified global-hotkey conflict detection with the runtime listener's virtual-key semantics, added unknown-primary / modifier-only guardrails, and made recorded shortcuts apply immediately at runtime; the settings page also gained a discard-changes action
- Foreground request feedback now prefers app-managed toasts, while background or minimized scenarios fall back to system-tray notifications with duplicate-message throttling
- Refreshed the main window, sidebar action buttons, direct-input dialog, and the latest screenshots / social preview so the visuals and interaction details feel more cohesive
- Windows packaging keeps the lighter cold-start configuration, including disabled PyInstaller `UPX` plus synchronized versioned assets and `SHA256SUMS.txt` guidance

### Fixed
- Pinned translation overlays now restore their previous content and geometry immediately after screenshot capture instead of waiting for the request result
- Fixed startup-optimization regressions including early tray attribute access, a missing `QTimer` import, and the inability to minimize to tray immediately after the first main-window show
- Fixed request feedback bubbles sticking on screen in some flows, and made success / failure / cancellation paths dismiss short-lived notifications more consistently
- Fixed several manual-input, selected-text, and screenshot workflow edge cases so cancellation, failure handling, and pinned-overlay restoration behave more consistently


## [0.9.9] - 2026-04-05

### Added
- Added trilingual `SUPPORT` docs to document the recommended paths for general questions, bug reports, feature requests, and private security reporting, reflecting the current Discussions-disabled maintenance flow
- Added a GitHub social preview asset at `docs/images/social-preview.png` plus its generator script `tools/generate_social_preview.py`
- Expanded the FAQ with request-latency guidance, clarifying that AI / LLM choice, upstream load, and throttling affect response time, and documenting the common 5–10 second, occasional 30–40 second, and `429` / `503` behavior seen with Google's `gemini-3.1-flash-lite-preview`

### Changed
- Updated the static Release badges in the README set to `v0.9.9`, and refreshed the example ZIP filenames in the packaging docs
- Added a Support entry to issue contact links, and linked `SUPPORT.md` from the README and docs index
- Refined the social preview into a cleaner brand + main-window composition, removing the capsule-style feature labels and unifying the left-panel information colors

### Fixed
- Fixed the YAML / PowerShell structure in `release-build.yml` when generating fallback release notes so the workflow no longer breaks on syntax errors
- Fixed the README Release / License badges showing `repo not found` or `no releases` in a private repository by switching to private-friendly static badges
- Relaxed Dependabot's default label expectations so update jobs do not fail just because labels like `dependencies`, `python`, or `ci` have not been created yet

## [0.9.8] - 2026-04-05

### Added
- Added repository governance and collaboration files: `CODE_OF_CONDUCT.md`, `.github/CODEOWNERS`, `.github/dependabot.yml`, `.editorconfig`, and `.gitattributes`
- Added a trilingual FAQ set: `docs/FAQ.md`, `docs/FAQ.zh-CN.md`, and `docs/FAQ.en.md`, covering platform support, API keys, self-hosted endpoints, offline OCR, signing status, and security reporting
- Added an animated preview asset at `docs/images/screenshots/ocrtranslator-preview.gif` and linked it from the README preview sections

### Changed
- Expanded README / SECURITY / CONTRIBUTING / docs index / packaging docs with public-repository trust information, including the private security contact email, unsigned package status, signing plan, and FAQ / Code of Conduct entry points
- Optimized the CI workflow with `workflow_dispatch`, concurrency, timeouts, and pip cache; the release workflow now also includes concurrency, timeout, pip cache, and annotated-tag release-note forwarding
- Automated GitHub Releases now prefer the annotated tag contents as the Release body instead of relying only on auto-generated changelog text

### Fixed
- Fixed `Save Settings` still jumping to the target-language field after a successful save because of focus fallback and scroll-area auto-visibility; the form now restores the previous scroll position and clears Save-button focus
- Fixed the API Keys, image prompt, and text prompt multiline editors still feeling double-outlined in dark mode, refining them into a cleaner Material-style single-surface focus treatment
- Fixed text selection highlights in both light and dark themes being too faint for single-line and multiline form inputs; input fields now use a clearer unified selection palette
- Added regression coverage for the release workflow, theme tokens, stylesheet rendering, save-time scroll restoration, and validation scope behavior

## [0.9.7] - 2026-04-05

### Changed
- Reworked the API Keys, image prompt, and text prompt multiline editors into a shared single-surface focus treatment, reducing the heavy double-border feel in dark mode
- Unified single-line and multiline input selection colors across light / dark themes so selected text is easier to distinguish at a glance

### Fixed
- Fixed `Save Settings` auto-scrolling to the target-language field when users only wanted to save API profile / key changes while leaving `target_language` blank; request-time image / text validation still requires a target language when needed
- Fixed the dark-theme API Keys and prompt editors showing an awkward layered focus ring, bringing focus / invalid states closer to a cleaner Material-style single-outline treatment
- Fixed text selection highlights in both light and dark themes being too faint to clearly tell whether text was selected inside form inputs
- Added regression coverage for save-time validation scope, theme tokens, and stylesheet rendering

## [0.9.6] - 2026-04-05

### Added
- Added a repository `LICENSE` (GPLv3) plus matching README / contribution guidance so code distribution and incoming contributions now have an explicit license basis
- Added dedicated persisted geometry fields for pinned overlays so pinned translation windows can keep their size and position across app restarts

### Changed
- Raised the default result-overlay font size from `12` to `16`, with matching updates in `config.example.json` and the settings-model defaults
- Moved packaging / signing infrastructure under `packaging/`, with `packaging/windows/OCRTranslator.spec` and `packaging/signpath/` as the canonical locations
- Updated the GitHub Actions workflows to Node 24-compatible action versions and replaced the broken SignPath `if:` secret checks with an explicit gate step
- The main window now shows `License: GPLv3` in the about metadata, and packaged release ZIPs now include the `LICENSE` file
- Runtime guidance text now explains the new overlay behavior: unpinned overlays always re-expand from the saved default size, while pinned overlays remember their current geometry

### Fixed
- Fixed the English `Unsaved Changes` dialog so long button labels no longer overflow, body text no longer clips, and both language layouts keep a more balanced icon / copy / button composition
- Fixed unpinned overlays overwriting `overlay_width` / `overlay_height` after auto-expansion or manual resizing; new unpinned requests now restart from the saved default size every time
- Fixed runtime overlay resizing from polluting the settings form and triggering unsaved-change prompts for temporary unpinned geometry changes
- Fixed pinned overlays failing to reliably reuse persisted geometry when runtime geometry had not yet been restored into memory
- Added regression coverage for pinned-geometry persistence, unpinned-size reset behavior, overlay dialog layout, and release workflow validation

## [0.9.5] - 2026-04-05

### Added
- Added a unified app icon asset directory at `app/assets/icons/`, consolidating the source icon, multi-size PNGs, and the Windows `.ico` so runtime and packaging now share the same icon set
- Added `docs/images/screenshots/` plus README screenshot galleries for the light / dark main window and translation overlay states
- Added a GitHub Actions `release-build.yml` workflow that supports manual runs or `v*` tag builds and publishes only the versioned ZIP while relying on GitHub's built-in source archives
- Added a `.signpath/` bootstrap structure and SignPath artifact configuration so GitHub trusted-build / automatic signing can be connected later with minimal repository reshaping

### Changed
- Formalized packaging around `OCRTranslator.spec` + `build_exe.bat`, moving PyInstaller datas / excludes / icon configuration into the `.spec` file for long-term maintenance
- `build_exe.bat` now cleans stale `~ip`-style pip metadata from `.venv`, supports `BUILD_NO_PAUSE` / `BUILD_SKIP_PIP_INSTALL`, and drives packaging in a more automation-friendly way
- The main window, application-level window icon, system tray, and packaged exe now all use the external icon assets; frozen runtime also resolves resources through `resource_path()` / `_MEIPASS`
- Packaging docs now cover the GitHub Actions / SignPath flow and update the versioned ZIP example to `v0.9.5`

### Fixed
- Fixed the `build_exe.bat` APP_VERSION read step that previously broke because of `for /f` quoting and command parsing
- Fixed build-time `Ignoring invalid distribution ~ip` warnings by cleaning stale virtualenv metadata before packaging
- Added regression coverage for app icon assets and release workflow configuration

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
