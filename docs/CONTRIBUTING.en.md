# Contributing

[繁體中文](../CONTRIBUTING.md)｜[简体中文](CONTRIBUTING.zh-CN.md)｜English

Thanks for your interest in OCRTranslator.

The project is still primarily maintained by a single owner, but contributions through issues and pull requests are welcome. Please review the following guidelines first.

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
