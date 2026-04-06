# FAQ

[繁體中文](FAQ.md)｜[简体中文](FAQ.zh-CN.md)｜English

## 1. Which platforms does OCRTranslator currently support?

The project is currently focused on the **Windows** desktop workflow.

Some Python code is portable, but the current hotkey integration, system tray behavior, packaging scripts, and real-world validation are still centered on Windows.

## 2. Do I need my own API key?

Yes.

OCRTranslator does not bundle or proxy any model service. You need to bring your own API key and base URL, then configure them in an API profile.

## 3. Which services are supported right now?

The current integration model is centered around:

- `Gemini Compatible`
- `OpenAI Compatible`

If your endpoint is API-compatible, it may also work with OCRTranslator.

## 4. Is offline OCR included?

Not at the moment.

The current design is focused on connecting screen capture, selected text, and manual input workflows to multimodal / text models, so recognition and output quality depend heavily on the model you actually connect.

## 5. Why is the selected-text workflow unreliable in some apps?

The selected-text flow currently uses a simulated copy-and-restore strategy, so:

- some custom UI apps may not respond to the standard copy shortcut
- some games, remote desktops, or sandboxed environments may intercept hotkeys
- some apps handle focus and text selection in non-standard ways

If you depend on this entry point, validate it first in the applications you actually use every day.

## 6. Why do Releases provide a ZIP instead of a standalone `.exe` asset?

The public release strategy currently prefers a **versioned ZIP** because it:

- keeps the portable distribution structure intact
- ships `README.md`, `LICENSE`, and `config.example.json` together
- reduces the chance that users miss required companion files
- keeps release assets consistent and predictable

## 7. Is the current public Windows package signed?

**Not yet.**

The repository already includes the groundwork for SignPath / Trusted Build integration, and code signing is planned. Until that is in place, treat the versioned ZIP on GitHub Releases as the canonical public desktop package.

## 8. Where is the config file stored?

The app prefers a portable config file:

- source mode: `config.json` in the project root
- packaged exe: `config.json` next to the exe

If no portable config exists yet and the runtime directory is not writable, the app falls back to:

- Windows: `%LOCALAPPDATA%\OCRTranslator\config.json`
- other environments: `~/.ocrtranslator/config.json`

Whenever a portable config exists, it takes precedence. This keeps the app portable while still allowing reliable startup from read-only locations.

## 9. How should I report a security issue?

Please do not post sensitive exploit details directly in a public issue.

If the report involves:

- API key exposure
- a private base URL
- replayable requests
- a vulnerability that could be abused

please contact the maintainer privately at `po12017po@gmail.com`.

## 10. Is the project ready for production use?

Right now it is best treated as:

- a personal-use tool
- a small internal-use tool
- a public beta / early access project for users who are comfortable with active iteration

If you want to rely on it in a production-like environment, review at least:

- model stability
- API key handling requirements
- whether selected-text capture works in your target apps
- whether an unsigned desktop package is acceptable in your environment

## 11. Why are some requests fast while others are slow, or even return 429 / 503?

Response time is strongly affected by the AI / LLM model you connect, upstream service load, network conditions, quota limits, and provider-side rate limiting. It is not something OCRTranslator can fully control on its own.

As a practical example, the Google-hosted `gemini-3.1-flash-lite-preview` model used in the default example setup often feels like it returns in about **5–10 seconds** under normal conditions. When the service is busier, the network is slower, or the upstream queue is longer, it can also stretch to around **30–40 seconds**.

In more extreme cases, the upstream service may return:

- `429 Too Many Requests`
- `503 Service Unavailable`

That usually means provider-side rate limiting, temporary unavailability, or heavier upstream load.

If response speed matters to you, keep an eye on at least:

- latency differences between models
- provider / region / time-of-day variability
- API key quota and throttling status
- whether you should retry later or switch to another model

## 12. Why does a compatible backend sometimes fall back to non-stream mode, and why does `Test API` behave the same way as real requests?

`Stream responses` is now enabled by default, and `Test API` intentionally follows the same setting so it can reproduce the backend behavior you are likely to hit before you save and rely on that profile.

If you connect a third-party compatible backend whose stream endpoint, SSE chunk shape, or compatibility layer does not match the schemas OCRTranslator currently supports, the app may:

- show a streaming retry / fallback status hint
- automatically retry once without streaming
- keep the partial text that has already arrived and label the current state

That also means some incompatible backends may receive a **second request** during fallback. If your backend is consistently unhappy with streaming, disable `Stream responses` in Advanced Settings.
