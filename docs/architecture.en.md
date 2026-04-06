# Architecture

[繁體中文](architecture.md)｜[简体中文](architecture.zh-CN.md)｜English

This document restores the more detailed “project structure and file responsibilities” reference so it is easier to find the right module during maintenance.

## Core layers

OCRTranslator is mainly split into these layers:

- `app/ui/`: Qt views, form binding, overlays, and interactive widgets
- `app/services/`: workflow orchestration, background tasks, tray integration, single-instance support, preview, and overlay presentation
- `app/providers/`: payload / response adapters for OpenAI- and Gemini-compatible APIs
- `app/platform/windows/`: Windows-specific features such as global hotkeys and selected-text capture
- `app/settings_service.py` / `app/settings_models.py`: settings snapshots, pure validation rules, and candidate config building
- `app/api_client.py`: retry, key rotation, provider dispatch, and unified error handling

## Main runtime path

1. `app/main.py`
   - application entry
   - single-instance lock
   - forwarding actions to an existing instance
2. `app/ui/main_window.py`
   - main window coordinator
   - wires UI, services, tray, and instance server together
3. `app/services/request_workflow.py`
   - workflow orchestration for the three request entry points
4. `app/services/background_task_runner.py`
   - background worker lifecycle and stale-task protection
5. `app/services/overlay_presenter.py`
   - overlay sizing, positioning, and reflow logic
6. `app/settings_service.py`
   - form snapshot validation
   - candidate config construction

## Runtime config path resolution

- `app/config_store.py` prefers a portable `config.json`, meaning the project root in source mode or the executable directory in packaged mode
- If no portable config exists yet and the current runtime directory is not writable, config storage falls back to a user-level config directory
- Windows fallback path: `%LOCALAPPDATA%\OCRTranslator\config.json`
- Other-environment fallback path: `~/.ocrtranslator/config.json`
- Crash logs still default to the runtime base directory (project root / executable directory) instead of following the fallback config path

## Detailed project structure

```text
OCRTranslator/
├─ .github/
│  ├─ ISSUE_TEMPLATE/
│  │  ├─ bug_report.yml              # bug report template
│  │  ├─ config.yml                  # GitHub issue template config
│  │  └─ feature_request.yml         # feature request template
│  ├─ workflows/
│  │  └─ ci.yml                      # CI: runs unittest and compileall
│  └─ PULL_REQUEST_TEMPLATE.md       # pull request checklist
│
├─ app/
│  ├─ __init__.py                    # package marker for app
│  ├─ api_client.py                  # unified API calling, key rotation, retry, and provider dispatch
│  ├─ app_defaults.py                # default provider / URL / model / hotkey / theme mode / display values
│  ├─ app_metadata.py                # author and repository metadata
│  ├─ config_store.py                # load, migrate, save, and recover portable / fallback config
│  ├─ crash_handling.py              # shared crash-hook setup and error dialog entry point
│  ├─ crash_reporter.py              # crash log generation, redaction, and persistence
│  ├─ default_prompts.py             # built-in prompt preset definitions and name normalization
│  ├─ hotkey_listener.py             # legacy facade forwarding to platform/windows/hotkeys.py
│  ├─ hotkey_utils.py                # shared hotkey splitting, modifier detection, and normalization helpers
│  ├─ i18n.py                        # locale loading, language normalization, system-language detection
│  ├─ main.py                        # main GUI entry, single-instance control, capture forwarding
│  ├─ models.py                      # AppConfig / ApiProfile / PromptPreset data structures (including theme mode)
│  ├─ operation_control.py           # cancellation tokens, RequestContext, operation error wrapping
│  ├─ profile_utils.py               # provider/model normalization and string helpers
│  ├─ prompt_utils.py                # prompt template rendering and text-request wrapping
│  ├─ runtime_paths.py               # base dir, lock file, server name, config paths
│  ├─ selected_text_capture.py       # legacy facade forwarding to platform/windows/selected_text.py
│  ├─ settings_models.py             # settings snapshot and validation result models
│  ├─ settings_service.py            # validation rules, per-operation validation scopes, candidate config construction
│  ├─ workers.py                     # background threads and Qt signal bridge
│  │
│  ├─ locales/
│  │  ├─ en.json                     # English UI strings
│  │  ├─ zh-CN.json                  # Simplified Chinese UI strings
│  │  └─ zh-TW.json                  # Traditional Chinese UI strings
│  │
│  ├─ platform/
│  │  └─ windows/
│  │     ├─ hotkeys.py               # low-level Windows global hotkeys and conflict detection
│  │     └─ selected_text.py         # Windows selected-text capture, clipboard save/restore
│  │
│  ├─ providers/
│  │  ├─ __init__.py                 # exports available provider adapters
│  │  ├─ gemini_compatible.py        # Gemini-compatible API adapter
│  │  └─ openai_compatible.py        # OpenAI-compatible API adapter
│  │
│  ├─ services/
│  │  ├─ background_task_runner.py   # background worker execution, error propagation, stale-result protection
│  │  ├─ image_capture.py            # screen capture, cross-screen fallback, preview generation
│  │  ├─ instance_server.py          # single-instance wake-up and capture forwarding server
│  │  ├─ operation_manager.py        # background task ids, cancellation, and stale-state management
│  │  ├─ overlay_presenter.py        # result overlay sizing, positioning, and reflow control
│  │  ├─ request_workflow.py         # capture / selected text / manual input workflow orchestration
│  │  ├─ runtime_log.py              # in-memory runtime log store
│  │  └─ system_tray.py              # system tray creation, updates, and action binding
│  │
│  └─ ui/
│     ├─ __init__.py                 # package marker for UI
│     ├─ main_window.py              # main window coordinator, integrating mixins and service calls
│     ├─ main_window_layout.py       # shell layout, workspace surface, navigation, button variants, and style application
│     ├─ main_window_profiles.py     # profile form binding, validation rendering, hotkey recording
│     ├─ main_window_prompts.py      # prompt preset form logic and built-in preset protection
│     ├─ main_window_settings_layout.py # workflow-first settings layout (connection / translation / advanced)
│     ├─ focus_utils.py              # shared post-click focus clearing and safe clearFocus helpers
│     ├─ message_boxes.py            # shared message-box helper, destructive confirmations, and escape hatches
│     ├─ overlay_positioning.py      # overlay position, size, and screen-bound calculations
│     ├─ prompt_input_dialog.py      # manual text input dialog
│     ├─ selection_overlay.py        # full-screen selection overlay
│     ├─ style_utils.py              # theme-aware QSS loading, caching, and token rendering
│     ├─ theme_tokens.py             # Material-inspired semantic color roles, compatibility aliases, and QSS tokens
│     ├─ translation_overlay.py      # result overlay widget and interaction logic
│     │
│     └─ styles/
│        ├─ main_window.qss          # main window stylesheet
│        └─ translation_overlay.qss  # result overlay stylesheet
│
├─ docs/
│  ├─ index.md                       # documentation index (Traditional Chinese)
│  ├─ index.zh-CN.md                 # documentation index (Simplified Chinese)
│  ├─ index.en.md                    # documentation index (English)
│  ├─ architecture.md                # architecture doc (Traditional Chinese)
│  ├─ architecture.zh-CN.md          # architecture doc (Simplified Chinese)
│  ├─ architecture.en.md             # architecture doc (English)
│  ├─ development.md                 # development guide (Traditional Chinese)
│  ├─ development.zh-CN.md           # development guide (Simplified Chinese)
│  ├─ development.en.md              # development guide (English)
│  ├─ packaging.md                   # packaging guide (Traditional Chinese)
│  ├─ packaging.zh-CN.md             # packaging guide (Simplified Chinese)
│  ├─ packaging.en.md                # packaging guide (English)
│  ├─ FAQ.md                         # FAQ (Traditional Chinese)
│  ├─ FAQ.zh-CN.md                   # FAQ (Simplified Chinese)
│  ├─ FAQ.en.md                      # FAQ (English)
│  ├─ README.zh-CN.md                # Simplified Chinese README mirror
│  ├─ README.en.md                   # English README mirror
│  ├─ CONTRIBUTING.zh-CN.md          # Simplified Chinese contributing mirror
│  ├─ CONTRIBUTING.en.md             # English contributing mirror
│  ├─ SUPPORT.zh-CN.md               # Simplified Chinese support mirror
│  ├─ SUPPORT.en.md                  # English support mirror
│  ├─ SECURITY.zh-CN.md              # Simplified Chinese security mirror
│  ├─ SECURITY.en.md                 # English security mirror
│  ├─ CHANGELOG.zh-CN.md             # Simplified Chinese changelog mirror
│  └─ CHANGELOG.en.md                # English changelog mirror
│
├─ tests/
│  ├─ __init__.py                    # package marker for tests
│  ├─ test_api_client.py             # ApiClient, provider response, retry, and key rotation tests
│  ├─ test_config_store.py           # config migration, broken-config recovery, default-value tests
│  ├─ test_crash_reporter.py         # crash log generation and redaction tests
│  ├─ test_hotkey_listener.py        # hotkey conflict and specificity tests
│  ├─ test_i18n.py                   # locale-key alignment and language normalization tests
│  ├─ test_main_window_runtime.py    # main-window runtime state and save-rollback tests
│  ├─ test_operation_manager.py      # OperationManager task / cancel / stale logic tests
│  ├─ test_overlay_positioning.py    # overlay position and sizing tests
│  ├─ test_prompt_presets_runtime.py # built-in prompt preset deletion-protection tests
│  ├─ test_prompt_utils.py           # prompt template rendering and text wrapping tests
│  ├─ test_request_workflow.py       # request workflow signature and rule tests
│  ├─ test_selected_text_capture.py  # selected-text clipboard helper tests
│  └─ test_settings_service.py       # validation scope and candidate config tests
│
├─ .gitignore                        # ignores venv, build, release, config, and logs
├─ build_exe.bat                     # one-click Windows packaging script
├─ CHANGELOG.md                      # changelog (default Traditional Chinese version)
├─ config.example.json               # sample config file
├─ config.json                       # local runtime config (generated file, should not be committed)
├─ CONTRIBUTING.md                   # contribution guide (default Traditional Chinese version)
├─ launcher.pyw                      # GUI launcher
├─ packaging/
│  ├─ signpath/
│  │  ├─ artifact-configurations/
│  │  │  └─ default.xml              # SignPath artifact configuration
│  │  └─ README.md                   # SignPath integration notes
│  └─ windows/
│     └─ OCRTranslator.spec          # PyInstaller packaging definition
├─ README.md                         # project overview (default Traditional Chinese version)
├─ requirements-dev.txt              # development / packaging dependencies
├─ requirements.txt                  # runtime dependencies
├─ SUPPORT.md                        # support and contact guide (default Traditional Chinese version)
├─ SECURITY.md                       # security policy (default Traditional Chinese version)
└─ start.bat                         # one-click Windows startup script
```

## Maintenance suggestions

The current structure is designed to:

- keep the repository root clean, with only the default language and real entry files there
- keep alternate-language docs under `docs/`
- preserve the `ui / services / providers / platform` boundary inside `app/`
- avoid pushing workflow logic back into UI classes

If you want to keep reorganizing later, good next steps are:

- further grouping `app/ui/main_window_*` into more explicit UI submodules
- optionally moving `start.bat` / `build_exe.bat` into `scripts/`, although that would also affect user-facing paths and documentation
