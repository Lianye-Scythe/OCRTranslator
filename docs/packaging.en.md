# Packaging and Distribution

[繁體中文](packaging.md)｜[简体中文](packaging.zh-CN.md)｜English

## One-click packaging

Run:

- `build_exe.bat`

The script will automatically:

1. create or verify `.venv`
2. install `requirements-dev.txt`
3. clean old `build/`, `dist/`, and `release/`
4. read the current version from `app/app_metadata.py`
5. produce `release\OCRTranslator.exe` through `packaging/windows/OCRTranslator.spec` + PyInstaller
6. copy the standalone `packaging/windows/README.md`, `LICENSE`, and `config.example.json`, and generate `BUILD-INFO.json`
7. automatically create `release\OCRTranslator-v<version>-windows-x64.zip`

The repository now uses a split build model: `packaging/windows/OCRTranslator.spec` keeps the PyInstaller packaging definition, while `build_exe.bat` prepares the environment, generates the Windows version resource, and launches the packaging run. If you need to tweak datas, excluded modules, or onefile behavior, update the `.spec` first.

## Icon asset location

Application icons are now centralized under `app/assets/icons/`:

- `app-icon-source.png`: original source image
- `app-icon-16.png` through `app-icon-256.png`: runtime multi-size PNG assets
- `app-icon.ico`: Windows executable packaging icon

The main window, system tray, and PyInstaller packaging flow all reuse this same icon set.

## Optional build environment variables

`build_exe.bat` also supports a few environment variables that are useful for repeated local packaging runs:

```text
BUILD_NO_PAUSE=1          Do not pause on success or failure; useful for terminals, CI, and automation
BUILD_SKIP_PIP_INSTALL=1  Skip `pip install -r requirements-dev.txt` when dependencies are already prepared
```

Example:

```bat
set BUILD_NO_PAUSE=1
set BUILD_SKIP_PIP_INSTALL=1
build_exe.bat
```

## GitHub Actions release packaging

The repository now includes `.github/workflows/release-build.yml` for automated packaging:

- `workflow_dispatch`: manual packaging test runs
- `push tags: v*`: automatic packaging when version tags are pushed
- workflow artifacts and GitHub Releases contain the versioned ZIP and `SHA256SUMS.txt`
- when the tag is annotated, the Release body is intended to prefer the tag annotation text

> GitHub Releases automatically provide `Source code (zip)` and `Source code (tar.gz)` for a tag, so the workflow does not need to upload those source archives manually, and it does not upload the standalone `.exe` either.

## SignPath bootstrap structure

The repository also includes the baseline files needed for a SignPath setup:

- `packaging/signpath/artifact-configurations/default.xml`
- `packaging/signpath/README.md`

When the following GitHub secret / variables are configured, the workflow will automatically submit the unsigned artifact to SignPath for signing:

### GitHub Secret

- `SIGNPATH_API_TOKEN`

### GitHub Variables

- `SIGNPATH_ORGANIZATION_ID`
- `SIGNPATH_PROJECT_SLUG`
- `SIGNPATH_SIGNING_POLICY_SLUG`

If those values are not configured yet, the workflow still completes the unsigned packaging flow and uploads / publishes the ZIP normally; it simply skips the SignPath signing step.

> The current public Windows package is still **unsigned**. Code signing is planned, and SignPath / Trusted Build is the intended integration path.

## Recommended order before applying for SignPath

1. Push `.github/workflows/release-build.yml` to GitHub
2. Run `Release Build` manually once from the GitHub Actions page
3. Confirm that the ZIP artifact is produced successfully
4. Then apply for SignPath / request GitHub trusted-build access
5. After you receive your SignPath organization / project information, add the secret / variables listed above
6. Finally, validate automatic signing and GitHub Release publishing with a test tag

## Recommended distribution contents

Prefer uploading the versioned archive first. The file name should include the project name, version, and platform, for example: `OCRTranslator-v1.0.13-windows-x64.zip`, and attach a companion `SHA256SUMS.txt` file for manual verification.

```text
release\OCRTranslator-v<version>-windows-x64.zip
release\SHA256SUMS.txt
```

## Build inventory and release notes

The ZIP includes a standalone guide from `packaging/windows/README.md` and `BUILD-INFO.json`, recording the app version, source commit when available, Python, platform, and installed package versions. Environment variables, keys, and package source URLs are not included.

This inventory is **not a lockfile**. `requirements.txt` automatically includes the root `constraints.txt`, pinning installed application and packaging dependency versions for Python 3.15 on Windows and WSL. Platform-specific dependencies use environment markers. Constraints do not install otherwise-unused build tools, and CI cache keys include the constraints file.

These are version pins, not artifact hashes or a complete build-environment lock. pip, isolated build tools, Python patches, and operating systems can still differ, so byte-identical executables are not guaranteed. Continue comparing `BUILD-INFO.json` when reproducing problems.

Annotated tag notes become the Release body. Order them as user-visible improvements, fixes, upgrade instructions (including settings backup/migration), and download/trust information. Keep internal refactoring details in the changelog. Tell users to download the Windows ZIP, verify `SHA256SUMS.txt`, and state the artifact's actual signing status. A checksum is not a digital signature. Documentation changes do not rewrite or rebuild historical releases.

## Optional code signing

`build_exe.bat` now supports an optional Windows code-signing flow. If no signing parameters are provided, signing is skipped. If signing parameters are provided, the script signs and verifies `release\OCRTranslator.exe` before creating the archive.

Available environment variables:

```text
SIGNTOOL_PATH        optional, explicit path to signtool.exe
SIGN_PFX_PATH        optional, path to a PFX certificate
SIGN_PFX_PASSWORD    optional, password for the PFX certificate
SIGN_CERT_SHA1       optional, SHA1 thumbprint for a cert in the Windows certificate store
SIGN_SUBJECT_NAME    optional, subject name used to find a cert in the Windows certificate store
SIGN_TIMESTAMP_URL   optional, timestamp service URL, defaults to http://timestamp.digicert.com
```

Provide at least one of the following to enable signing:

- `SIGN_PFX_PATH` (optionally with `SIGN_PFX_PASSWORD`)
- `SIGN_CERT_SHA1`
- `SIGN_SUBJECT_NAME`

Example (PFX):

```bat
set SIGN_PFX_PATH=C:\certs\ocrtranslator.pfx
set SIGN_PFX_PASSWORD=your-password
build_exe.bat
```

Example (certificate store):

```bat
set SIGN_CERT_SHA1=0123456789ABCDEF0123456789ABCDEF01234567
build_exe.bat
```

## Not recommended for distribution

```text
config.json
.venv\
build\
dist\
*.spec
```

## Runtime paths

- source mode: the app prefers `config.json` in the project root
- exe mode: the app prefers `config.json` next to the executable
- if no portable config exists and the current runtime directory is not writable, config storage falls back to:
  - Windows: `%LOCALAPPDATA%\OCRTranslator\config.json`
  - other environments: `~/.ocrtranslator/config.json`
- crash logs are stored in `logs/` under the project root / executable directory instead of following the fallback config path

This keeps the app portable when the runtime directory is writable while still allowing stable startup and config saves from read-only or otherwise restricted locations.
