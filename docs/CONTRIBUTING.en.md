# Contributing

[繁體中文](../.github/CONTRIBUTING.md)｜[简体中文](CONTRIBUTING.zh-CN.md)｜English

Thanks for your interest in OCRTranslator.

The project is still primarily maintained by a single owner, but contributions through issues and pull requests are welcome. Please review the following guidelines first.

Before participating, please read and follow the `.github/CODE_OF_CONDUCT.md`.

## Development principles

- Preserve the current UI direction unless there is a strong reason to change it
- Fix reproducible issues before spending time on stylistic tweaks
- Do not commit API keys, personal config, or locally generated artifacts
- If you change the config structure, keep backward migration for older `config.json` files in mind
- If you refactor architecture, keep the `ui / services / providers / platform` boundary intact

## Dependency automation

Only Dependabot pip PRs from this repository targeting `main` can enable auto-merge. The allowlist is limited to stable patch increases for Pillow, requests, and pynput, with matching changes only in `requirements.txt`. Minor/major updates, Qt, PyInstaller, Actions, signing, and release changes remain manual, including security updates outside this policy.

The `test` and `windows-package` checks must pass against an up-to-date branch. Packaging uses no signing credentials and publishes no release. The privileged policy workflow executes only base-commit code, validates metadata and diffs, and resets its decision on every PR update. It never executes PR code, installs its dependencies, submits approval reviews, or bypasses required checks. Policy changes require human review.

## Documentation-only changes

`main` still requires a PR. Changes limited to the root README/CHANGELOG, Markdown under `docs/`, raster previews under `docs/images/`, or Markdown directly under `.github/` use lightweight local-link and image-path checks, without application dependencies, Windows tests, or packaging. Code, dependencies, workflows, policy scripts, packaged documentation (`packaging/windows/README.md`), and manual CI runs still receive full checks.

The `ci-required` gate must succeed; documentation-only runs report `windows-package` as skipped, not built. Non-draft documentation-only PRs created by the repository owner in this repository targeting `main` enable auto-merge after required checks pass. External contributions remain manual. Every PR update resets the old auto-merge decision before rechecking.

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
