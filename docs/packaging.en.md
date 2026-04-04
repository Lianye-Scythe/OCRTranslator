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
5. produce `release\OCRTranslator.exe` with PyInstaller
6. copy `README.md` and `config.example.json`
7. automatically create `release\OCRTranslator-v<version>-windows-x64.zip`

## Recommended distribution contents

Prefer uploading the versioned archive first. The file name should include the project name, version, and platform, for example: `OCRTranslator-v0.9.3-windows-x64.zip`.

```text
release\OCRTranslator-v<version>-windows-x64.zip
```

If you also want users to download a standalone binary, you can upload `release\OCRTranslator.exe` as an extra asset.

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

- source mode: `config.json` and crash logs are stored in the project root
- exe mode: `config.json` and crash logs are stored next to the executable

This keeps the app portable and easy to move, back up, and redistribute.
