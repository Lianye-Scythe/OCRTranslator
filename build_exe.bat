@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"

set "VENV_DIR=.venv"
set "VENV_SITE_PACKAGES=%VENV_DIR%\Lib\site-packages"
set "PYTHON_EXE=%VENV_DIR%\Scripts\python.exe"
set "BUILD_DIR=build"
set "RELEASE_DIR=release"
set "DIST_NAME=OCRTranslator"
set "SPEC_FILE=packaging\windows\%DIST_NAME%.spec"
set "ARCHIVE_PREFIX=%DIST_NAME%"
set "ARCHIVE_SUFFIX=windows-x64"
set "APP_VERSION="
set "ARCHIVE_NAME="
set "ARCHIVE_PATH="
set "CHECKSUM_PATH=%RELEASE_DIR%\SHA256SUMS.txt"
set "VERSION_INFO_FILE=%BUILD_DIR%\%DIST_NAME%.version-info.txt"
set "SIGNTOOL_EXE=%SIGNTOOL_PATH%"
set "APP_VERSION_FILE=%TEMP%\%DIST_NAME%.app-version.%RANDOM%.txt"
if not defined SIGN_TIMESTAMP_URL set "SIGN_TIMESTAMP_URL=http://timestamp.digicert.com"
set "SIGNING_CONFIGURED="

echo [OCRTranslator] Preparing build environment...

if not exist "%PYTHON_EXE%" (
    echo [OCRTranslator] Virtual environment not found. Creating .venv ...
    where python >nul 2>nul
    if errorlevel 1 goto :no_python
    python -m venv "%VENV_DIR%"
    if errorlevel 1 goto :venv_failed
)

call :cleanup_invalid_pip_metadata
if errorlevel 1 goto :venv_metadata_failed

if defined BUILD_SKIP_PIP_INSTALL (
    echo [OCRTranslator] Skipping dependency installation because BUILD_SKIP_PIP_INSTALL is set.
) else (
    echo [OCRTranslator] Installing build dependencies...
    "%PYTHON_EXE%" -m pip install --disable-pip-version-check -r requirements-dev.txt
    if errorlevel 1 goto :install_failed
    call :cleanup_invalid_pip_metadata
    if errorlevel 1 goto :venv_metadata_failed
)



if exist "%BUILD_DIR%" rmdir /s /q "%BUILD_DIR%"
if exist "dist" rmdir /s /q "dist"
if exist "%RELEASE_DIR%" rmdir /s /q "%RELEASE_DIR%"
mkdir "%RELEASE_DIR%"
if errorlevel 1 goto :prepare_failed
if not exist "%SPEC_FILE%" goto :spec_missing

if exist "%APP_VERSION_FILE%" del /q "%APP_VERSION_FILE%" >nul 2>nul
"%PYTHON_EXE%" -c "from app.app_metadata import APP_VERSION; print(APP_VERSION, end='')" > "%APP_VERSION_FILE%"
if errorlevel 1 goto :version_failed
set /p APP_VERSION=<"%APP_VERSION_FILE%"
del /q "%APP_VERSION_FILE%" >nul 2>nul
if not defined APP_VERSION goto :version_failed

set "ARCHIVE_NAME=%ARCHIVE_PREFIX%-v%APP_VERSION%-%ARCHIVE_SUFFIX%.zip"
set "ARCHIVE_PATH=%RELEASE_DIR%\%ARCHIVE_NAME%"

if defined SIGN_PFX_PATH set "SIGNING_CONFIGURED=1"
if defined SIGN_CERT_SHA1 set "SIGNING_CONFIGURED=1"
if defined SIGN_SUBJECT_NAME set "SIGNING_CONFIGURED=1"

echo [OCRTranslator] Target release archive: %ARCHIVE_NAME%

echo [OCRTranslator] Generating Windows version resource...
"%PYTHON_EXE%" tools\generate_windows_version_info.py --output "%VERSION_INFO_FILE%"
if errorlevel 1 goto :version_file_failed

echo [OCRTranslator] Running PyInstaller...
set "OCRT_VERSION_FILE=%CD%\%VERSION_INFO_FILE%"
"%PYTHON_EXE%" -m PyInstaller ^
    --noconfirm ^
    --clean ^
    --distpath "%RELEASE_DIR%" ^
    --workpath "%BUILD_DIR%" ^
    "%SPEC_FILE%"
set "OCRT_VERSION_FILE="
if errorlevel 1 goto :build_failed

echo [OCRTranslator] Copying release assets...
copy /y "README.md" "%RELEASE_DIR%\README.md" >nul
if errorlevel 1 goto :copy_failed
copy /y "LICENSE" "%RELEASE_DIR%\LICENSE" >nul
if errorlevel 1 goto :copy_failed
copy /y "config.example.json" "%RELEASE_DIR%\config.example.json" >nul
if errorlevel 1 goto :copy_failed

if not exist "%RELEASE_DIR%\%DIST_NAME%.exe" goto :missing_output

call :sign_release_binary "%RELEASE_DIR%\%DIST_NAME%.exe"
if errorlevel 1 goto :sign_failed

echo [OCRTranslator] Creating release archive...
powershell -NoProfile -ExecutionPolicy Bypass -Command "Compress-Archive -Path '%RELEASE_DIR%\%DIST_NAME%.exe','%RELEASE_DIR%\README.md','%RELEASE_DIR%\LICENSE','%RELEASE_DIR%\config.example.json' -DestinationPath '%ARCHIVE_PATH%' -Force"
if errorlevel 1 goto :archive_failed

if not exist "%ARCHIVE_PATH%" goto :archive_failed

echo [OCRTranslator] Generating SHA256SUMS.txt ...
"%PYTHON_EXE%" tools\generate_sha256sums.py --output "%CHECKSUM_PATH%" "%ARCHIVE_PATH%"
if errorlevel 1 goto :checksum_failed

echo.
echo [SUCCESS] Build complete.
echo [SUCCESS] EXE: %RELEASE_DIR%\%DIST_NAME%.exe
echo [SUCCESS] ZIP: %ARCHIVE_PATH%
echo [SUCCESS] SHA256: %CHECKSUM_PATH%
call :maybe_pause
exit /b 0

:no_python
echo.
echo [ERROR] Python was not found on PATH.
echo Please install Python 3.11+ and enable "Add Python to PATH", then run this file again.
call :maybe_pause
exit /b 1

:venv_failed
echo.
echo [ERROR] Failed to create .venv.
call :maybe_pause
exit /b 1

:venv_metadata_failed
echo.
echo [ERROR] Failed to clean invalid pip metadata under %VENV_SITE_PACKAGES%.
call :maybe_pause
exit /b 1

:install_failed
echo.
echo [ERROR] Failed to install build dependencies.
echo You can try this command manually:
echo   .venv\Scripts\python -m pip install -r requirements-dev.txt
call :maybe_pause
exit /b 1

:prepare_failed
echo.
echo [ERROR] Failed to prepare the release directory.
call :maybe_pause
exit /b 1

:spec_missing
echo.
echo [ERROR] Spec file was not found: %SPEC_FILE%
call :maybe_pause
exit /b 1

:build_failed
echo.
echo [ERROR] PyInstaller build failed.
call :maybe_pause
exit /b 1

:copy_failed
echo.
echo [ERROR] Failed to copy release assets.
call :maybe_pause
exit /b 1

:missing_output
echo.
echo [ERROR] Build finished without producing %RELEASE_DIR%\%DIST_NAME%.exe.
call :maybe_pause
exit /b 1

:version_failed
del /q "%APP_VERSION_FILE%" >nul 2>nul
echo.
echo [ERROR] Failed to read APP_VERSION from app\app_metadata.py.
call :maybe_pause
exit /b 1

:version_file_failed
echo.
echo [ERROR] Failed to generate Windows version resource file.
echo Expected file: %VERSION_INFO_FILE%
call :maybe_pause
exit /b 1

:sign_failed
echo.
echo [ERROR] Failed to sign or verify %RELEASE_DIR%\%DIST_NAME%.exe.
call :maybe_pause
exit /b 1

:sign_release_binary
set "TARGET_FILE=%~1"
if not defined SIGNING_CONFIGURED (
    echo [OCRTranslator] Code signing skipped. Set SIGN_PFX_PATH, SIGN_CERT_SHA1, or SIGN_SUBJECT_NAME to enable signing.
    exit /b 0
)
if not defined SIGNTOOL_EXE (
    for /f "delims=" %%s in ('where signtool 2^>nul') do if not defined SIGNTOOL_EXE set "SIGNTOOL_EXE=%%s"
)
if not defined SIGNTOOL_EXE (
    echo [ERROR] signtool.exe was not found. Set SIGNTOOL_PATH or install Windows SDK signing tools.
    exit /b 1
)
echo [OCRTranslator] Signing %TARGET_FILE% ...
if defined SIGN_PFX_PATH (
    if defined SIGN_PFX_PASSWORD (
        "%SIGNTOOL_EXE%" sign /fd sha256 /tr "%SIGN_TIMESTAMP_URL%" /td sha256 /f "%SIGN_PFX_PATH%" /p "%SIGN_PFX_PASSWORD%" "%TARGET_FILE%"
    ) else (
        "%SIGNTOOL_EXE%" sign /fd sha256 /tr "%SIGN_TIMESTAMP_URL%" /td sha256 /f "%SIGN_PFX_PATH%" "%TARGET_FILE%"
    )
) else if defined SIGN_CERT_SHA1 (
    "%SIGNTOOL_EXE%" sign /fd sha256 /tr "%SIGN_TIMESTAMP_URL%" /td sha256 /sha1 "%SIGN_CERT_SHA1%" "%TARGET_FILE%"
) else (
    "%SIGNTOOL_EXE%" sign /fd sha256 /tr "%SIGN_TIMESTAMP_URL%" /td sha256 /n "%SIGN_SUBJECT_NAME%" "%TARGET_FILE%"
)
if errorlevel 1 exit /b 1
echo [OCRTranslator] Verifying signature...
"%SIGNTOOL_EXE%" verify /pa /v "%TARGET_FILE%"
if errorlevel 1 exit /b 1
exit /b 0

:archive_failed
echo.
echo [ERROR] Failed to create release archive.
echo Expected archive: %ARCHIVE_PATH%
call :maybe_pause
exit /b 1

:checksum_failed
echo.
echo [ERROR] Failed to generate %CHECKSUM_PATH%.
call :maybe_pause
exit /b 1

:cleanup_invalid_pip_metadata
if not exist "%VENV_SITE_PACKAGES%" exit /b 0
set "REMOVED_INVALID_PIP="
for /d %%d in ("%VENV_SITE_PACKAGES%\~*") do (
    echo [OCRTranslator] Removing stale virtualenv metadata: %%~nxd
    rmdir /s /q "%%~fd"
    if errorlevel 1 exit /b 1
    set "REMOVED_INVALID_PIP=1"
)
if defined REMOVED_INVALID_PIP echo [OCRTranslator] Cleaned stale pip metadata from %VENV_SITE_PACKAGES%.
exit /b 0

:maybe_pause
if defined BUILD_NO_PAUSE exit /b 0
if defined CI exit /b 0
if defined GITHUB_ACTIONS exit /b 0
pause
exit /b 0
