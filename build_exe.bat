@echo off
setlocal
cd /d "%~dp0"

set "VENV_DIR=.venv"
set "PYTHON_EXE=%VENV_DIR%\Scripts\python.exe"

echo [OCRTranslator] Preparing build environment...

if not exist "%PYTHON_EXE%" (
    echo [OCRTranslator] Virtual environment not found. Creating .venv ...
    where python >nul 2>nul
    if errorlevel 1 goto :no_python
    python -m venv "%VENV_DIR%"
    if errorlevel 1 goto :venv_failed
)

echo [OCRTranslator] Installing build dependencies...
"%PYTHON_EXE%" -m pip install -r requirements.txt pyinstaller
if errorlevel 1 goto :install_failed

if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "release" rmdir /s /q "release"
mkdir "release"
if errorlevel 1 goto :prepare_failed

echo [OCRTranslator] Running PyInstaller...
"%PYTHON_EXE%" -m PyInstaller ^
    --noconfirm ^
    --clean ^
    --noconsole ^
    --onefile ^
    --name OCRTranslator ^
    --distpath release ^
    --workpath build ^
    --add-data "app\ui\styles;app\ui\styles" ^
    launcher.pyw
if errorlevel 1 goto :build_failed

echo [OCRTranslator] Copying release assets...
copy /y "README.md" "release\README.md" >nul
if errorlevel 1 goto :copy_failed
copy /y "config.example.json" "release\config.example.json" >nul
if errorlevel 1 goto :copy_failed
if exist "OCRTranslator.spec" del /q "OCRTranslator.spec"

if not exist "release\OCRTranslator.exe" goto :missing_output

echo.
echo [SUCCESS] Build complete. Package: release\OCRTranslator.exe
pause
exit /b 0

:no_python
echo.
echo [ERROR] Python was not found on PATH.
echo Please install Python 3.11+ and enable "Add Python to PATH", then run this file again.
pause
exit /b 1

:venv_failed
echo.
echo [ERROR] Failed to create .venv.
pause
exit /b 1

:install_failed
echo.
echo [ERROR] Failed to install build dependencies.
echo You can try this command manually:
echo   .venv\Scripts\python -m pip install -r requirements.txt pyinstaller
pause
exit /b 1

:prepare_failed
echo.
echo [ERROR] Failed to prepare the release directory.
pause
exit /b 1

:build_failed
echo.
echo [ERROR] PyInstaller build failed.
pause
exit /b 1

:copy_failed
echo.
echo [ERROR] Failed to copy release assets.
pause
exit /b 1

:missing_output
echo.
echo [ERROR] Build finished without producing release\OCRTranslator.exe.
pause
exit /b 1
