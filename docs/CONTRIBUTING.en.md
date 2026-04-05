# Contributing

[繁體中文](../CONTRIBUTING.md)｜[简体中文](CONTRIBUTING.zh-CN.md)｜English

Thanks for your interest in OCRTranslator.

The project is still primarily maintained by a single owner, but contributions through issues and pull requests are welcome. Please review the following guidelines first.

Before participating, please read and follow the repository-root `CODE_OF_CONDUCT.md`.

## Development principles

- Preserve the current UI direction unless there is a strong reason to change it
- Fix reproducible issues before spending time on stylistic tweaks
- Do not commit API keys, personal config, or locally generated artifacts
- If you change the config structure, keep backward migration for older `config.json` files in mind
- If you refactor architecture, keep the `ui / services / providers / platform` boundary intact

## Recommended workflow

1. Fork / create a branch
2. Make your changes
3. Run:
   - `python -m unittest discover -v`
   - `python -m compileall app tests launcher.pyw`
   - if packaging is involved, also confirm `pip install -r requirements-dev.txt`
4. Update README / docs / comments when needed
5. Open a Pull Request
6. By contributing code, you agree that the contribution may be included in this project under **GPLv3**

## Pull Request suggestions

Your PR should ideally include at least:

- a short summary of the change
- how you verified it
- any notable risk or compatibility impact
- screenshots or a short explanation for UI changes
- notes about boundary changes if you adjusted the architecture

## Issue reporting suggestions

When opening a bug report, include as much of the following as possible:

- reproduction steps
- runtime type (source / exe)
- operating system and Python version
- runtime logs
- a crash log if the app produced one

## Files you should not commit directly

- `config.json`
- `.venv/`
- `build/`
- `dist/`
- `release/`
- `ocrtranslator-crash-*.log`
- `ocrtranslator-log-*.txt`
